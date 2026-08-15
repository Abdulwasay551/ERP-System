"""
Full company-data snapshot export/import for the desktop app's first-run pairing
(Phase 3 of the desktop app plan) - pulls one company's complete dataset down to a new
desktop install, preserving primary keys so the same Invoice with id=42 is genuinely the
same row on both the cloud and the local SQLite copy (this matters for Phase 4/5's
ongoing sync, which identifies rows by PK).

Scope matches the rest of the desktop app work: sales, purchase, inventory, accounting,
crm, products, user_auth, core - the same active-modules boundary the whole ERP revamp
already drew (manufacturing/hr/project_mgmt/dormant CRM stay out).

MANIFEST was built by exhaustively auditing every model in every in-scope app.py for how
it's scoped to a single company - either a direct `company` FK, or an indirect path
through a parent FK (including three genuine two-hop chains: SalesOrderItemTracking,
GRNItemTracking, BillItemTracking). Six models turned out to have no reliable path to a
company at all (AccountingAuditLog, AccountTemplate/Group/Account,
ImportExportOperation, user_auth.ActivityLog) - audit/operational logs and a pre-existing
chart-of-accounts-template scoping gap unrelated to this work, deliberately excluded
rather than guessed at. Two models are genuinely global reference data shared across
every company (accounting.Currency, user_auth.Role) and are exported unconditionally,
not filtered by company - other exported rows (User.role, Account.currency-ish FKs) may
depend on them existing locally.

Uses Django's own fixture (de)serialization machinery, the same mechanism `loaddata`
uses for arbitrary-order fixture loading: `connection.constraint_checks_disabled()`
during import means the MANIFEST order below doesn't need to be a perfect topological
sort, and `save_base(raw=True)` (which `DeserializedObject.save()` calls under the hood)
writes the raw row data only, without re-running any model's overridden `save()` side
effects (numbering, stock reduction, ledger posting) - importing historical data must
not re-trigger any of that.
"""
import json

from django.core import serializers
from django.db import IntegrityError, connection, transaction
from django.utils.dateparse import parse_datetime

from core.sync_classification import is_delta_eligible, since_field_for
from user_auth.models import Company, User

# (app_label, model_name, scope) - scope is 'direct', ('via', field), ('via2', f1, f2),
# or 'global' (no company filter, exported unconditionally - shared reference data).
MANIFEST = [
    # --- global reference data (export unconditionally, other rows depend on these) ---
    ('user_auth', 'Role', 'global'),
    ('accounting', 'Currency', 'global'),

    # --- user_auth ---
    ('user_auth', 'User', 'direct'),

    # --- crm ---
    ('crm', 'Partner', 'direct'),
    ('crm', 'Customer', 'direct'),
    ('crm', 'CustomerLedger', 'direct'),
    ('crm', 'Lead', 'direct'),
    ('crm', 'Opportunity', 'direct'),
    ('crm', 'CommunicationLog', 'direct'),
    ('crm', 'Campaign', 'direct'),
    ('crm', 'CampaignTarget', ('via', 'campaign')),
    ('crm', 'SupplierRating', 'direct'),
    ('crm', 'CRMConfiguration', 'direct'),

    # --- products ---
    ('products', 'ProductCategory', 'direct'),
    ('products', 'Attribute', 'direct'),
    ('products', 'AttributeValue', ('via', 'attribute')),
    ('products', 'Product', 'direct'),
    ('products', 'ProductVariant', ('via', 'product')),
    ('products', 'ProductAttribute', ('via', 'product')),
    ('products', 'ProductTracking', ('via', 'product')),

    # --- purchase ---
    ('purchase', 'UnitOfMeasure', 'direct'),
    ('purchase', 'TaxChargesTemplate', 'direct'),
    ('purchase', 'Supplier', 'direct'),
    ('purchase', 'SupplierContact', ('via', 'supplier')),
    ('purchase', 'SupplierProductCatalog', ('via', 'supplier')),
    ('purchase', 'PurchaseRequisition', 'direct'),
    ('purchase', 'PurchaseRequisitionItem', ('via', 'purchase_requisition')),
    ('purchase', 'RequestForQuotation', 'direct'),
    ('purchase', 'RFQItem', ('via', 'rfq')),
    ('purchase', 'SupplierQuotation', 'direct'),
    ('purchase', 'SupplierQuotationItem', ('via', 'quotation')),
    ('purchase', 'PurchaseOrder', 'direct'),
    ('purchase', 'PurchaseOrderItem', ('via', 'purchase_order')),
    ('purchase', 'PurchaseOrderTaxCharge', ('via', 'purchase_order')),
    ('purchase', 'GoodsReceiptNote', 'direct'),
    ('purchase', 'GRNItem', ('via', 'grn')),
    ('purchase', 'GRNItemTracking', ('via2', 'grn_item', 'grn')),
    ('purchase', 'GRNInventoryLock', ('via', 'grn')),
    ('purchase', 'QualityInspection', 'direct'),
    ('purchase', 'QualityInspectionResult', ('via', 'inspection')),
    ('purchase', 'Bill', 'direct'),
    ('purchase', 'BillItem', ('via', 'bill')),
    ('purchase', 'BillItemTracking', ('via2', 'bill_item', 'bill')),
    ('purchase', 'PurchasePayment', 'direct'),
    ('purchase', 'SupplierLedger', 'direct'),
    ('purchase', 'PurchaseReturn', 'direct'),
    ('purchase', 'PurchaseReturnItem', ('via', 'purchase_return')),
    ('purchase', 'PurchaseApproval', 'direct'),

    # --- inventory ---
    ('inventory', 'Warehouse', 'direct'),
    ('inventory', 'WarehouseZone', ('via', 'warehouse')),
    ('inventory', 'WarehouseBin', ('via', 'warehouse')),
    ('inventory', 'StockItem', 'direct'),
    ('inventory', 'StockLot', ('via', 'stock_item')),
    ('inventory', 'StockSerial', ('via', 'stock_item')),
    ('inventory', 'StockReservation', ('via', 'stock_item')),
    ('inventory', 'InventoryLock', ('via', 'stock_item')),
    ('inventory', 'StockMovement', 'direct'),
    ('inventory', 'StockAlert', 'direct'),
    ('inventory', 'StockAdjustment', 'direct'),
    ('inventory', 'StockAdjustmentItem', ('via', 'adjustment')),
    ('inventory', 'StockTransfer', 'direct'),
    ('inventory', 'StockTransferItem', ('via', 'transfer')),

    # --- sales ---
    ('sales', 'Currency', 'direct'),
    ('sales', 'PriceList', 'direct'),
    ('sales', 'PriceListItem', ('via', 'price_list')),
    ('sales', 'Tax', 'direct'),
    ('sales', 'Quotation', 'direct'),
    ('sales', 'QuotationItem', ('via', 'quotation')),
    ('sales', 'SalesOrder', 'direct'),
    ('sales', 'SalesOrderItem', ('via', 'sales_order')),
    ('sales', 'SalesOrderItemTracking', ('via2', 'sales_order_item', 'sales_order')),
    ('sales', 'SalesOrderDiscount', ('via', 'sales_order')),
    ('sales', 'DeliveryNote', 'direct'),
    ('sales', 'DeliveryNoteItem', ('via', 'delivery_note')),
    ('sales', 'Invoice', 'direct'),
    ('sales', 'InvoiceItem', ('via', 'invoice')),
    ('sales', 'Payment', 'direct'),
    ('sales', 'SalesCommission', 'direct'),
    ('sales', 'CreditNote', 'direct'),
    ('sales', 'CreditNoteItem', ('via', 'credit_note')),
    ('sales', 'LegacyProduct', 'direct'),  # confirmed dead code elsewhere, kept here only for completeness

    # --- accounting ---
    ('accounting', 'AccountCategory', 'direct'),
    ('accounting', 'AccountGroup', 'direct'),
    ('accounting', 'Account', 'direct'),
    ('accounting', 'COASettings', 'direct'),
    ('accounting', 'Journal', 'direct'),
    ('accounting', 'JournalEntry', 'direct'),
    ('accounting', 'JournalItem', ('via', 'entry')),
    ('accounting', 'JournalTemplate', 'direct'),
    ('accounting', 'JournalTemplateItem', ('via', 'template')),
    ('accounting', 'RecurringJournal', ('via', 'journal')),
    ('accounting', 'AccountReconciliation', ('via', 'account')),
    ('accounting', 'AccountPayable', 'direct'),
    ('accounting', 'AccountReceivable', 'direct'),
    ('accounting', 'BankAccount', 'direct'),
    ('accounting', 'BankReconciliation', 'direct'),
    ('accounting', 'TaxConfig', 'direct'),
    ('accounting', 'ModuleAccountMapping', 'direct'),
    ('accounting', 'AutoJournalEntry', 'direct'),
    ('accounting', 'FinancialStatement', 'direct'),
    ('accounting', 'Expense', 'direct'),

    # --- core ---
    ('core', 'RecordDeletionLog', 'direct'),
    ('core', 'IdempotencyKey', 'direct'),
    ('core', 'NumberSequence', 'direct'),
]

# Deliberately excluded (see module docstring): no reliable path to a single company.
# accounting.AccountingAuditLog, accounting.AccountTemplate, accounting.AccountTemplateGroup,
# accounting.AccountTemplateAccount, accounting.ImportExportOperation, user_auth.ActivityLog


def _queryset_for(app_label, model_name, scope, company):
    from django.apps import apps
    model = apps.get_model(app_label, model_name)
    manager = getattr(model, 'all_objects', None) or model.objects
    if scope == 'global':
        return manager.all()
    if scope == 'direct':
        return manager.filter(company=company)
    if isinstance(scope, tuple) and scope[0] == 'via':
        return manager.filter(**{f'{scope[1]}__company': company})
    if isinstance(scope, tuple) and scope[0] == 'via2':
        return manager.filter(**{f'{scope[1]}__{scope[2]}__company': company})
    raise ValueError(f'Unknown scope spec: {scope!r}')


def export_snapshot(company):
    """Returns a list of serialized objects (django.core.serializers 'python' format -
    [{'model': 'app.model', 'pk': ..., 'fields': {...}}, ...]) for every in-scope model,
    scoped to `company`. Caller wraps this in the desired output format (the
    export-snapshot API view wraps it in JSON alongside metadata).

    Uses the 'json' serializer format, not 'python' - the 'python' format leaves
    datetime/Decimal/etc. as native Python objects (an intermediate representation, not
    meant to be JSON-dumped directly), which would blow up json.dumps() one layer up in
    the API view. Round-tripping through json.dumps()+json.loads() here gets the same
    JSON-safe shape (ISO date strings, decimal-as-string) that deserialize() expects back
    on the import side, without forcing every caller to know that distinction.

    `company` itself is NOT in MANIFEST (MANIFEST is only for models scoped *to* a
    company - Company is the tenant root, not scoped to itself) - serialized explicitly
    here instead, first, so it exists locally before any company-scoped row that a
    (possibly raw-unguarded) post_save signal might try to dereference during import.
    """
    objects = json.loads(serializers.serialize('json', [company]))
    for app_label, model_name, scope in MANIFEST:
        qs = _queryset_for(app_label, model_name, scope, company)
        objects.extend(json.loads(serializers.serialize('json', qs)))
    return objects


def export_all_companies_snapshot():
    """Disaster-recovery export (Phase B): every company's complete data in one
    payload, for seeding a brand-new backend if production's database is ever lost -
    unlike export_snapshot(), which is scoped to the one company the desktop app pairs
    with, this covers the whole system.

    Loops export_snapshot() per company and dedupes the 'global' scope MANIFEST
    entries (user_auth.Role, accounting.Currency) - _queryset_for() ignores the company
    filter entirely for those, so calling export_snapshot() once per company would
    otherwise serialize the exact same Role/Currency rows N times over.
    """
    objects = []
    seen_global = set()
    for company in Company.objects.all():
        for obj in export_snapshot(company):
            if obj['model'] in ('user_auth.role', 'accounting.currency'):
                key = (obj['model'], obj['pk'])
                if key in seen_global:
                    continue
                seen_global.add(key)
            objects.append(obj)
    return objects


def export_snapshot_delta(company, since):
    """Like export_snapshot(), but scoped to what's changed since `since` (an ISO
    timestamp string, or None for a full export identical to export_snapshot()'s
    behavior). Only exports models `core.sync_classification` marks delta-eligible
    (STATE/EVENT top-level models) plus their MANIFEST-declared children - DERIVED
    models (StockItem, StockAlert, FinancialStatement) and anything not classified at
    all (CRM leads/campaigns, LegacyProduct) are never included, matching
    sync_classification's own module docstring.

    Top-level ('direct'/'global') models are filtered by their own since_field
    (`since_field__gt since`), or exported in full every cycle if since_field is None
    (small reference tables - Role, Currency, NumberSequence). Child ('via'/'via2')
    models NOT independently classified ride along with whichever of their parent
    rows fell in this batch (filtered by the parent's already-computed PK set, not
    their own timestamp) - editing a document typically rewrites its whole item set
    anyway. The four child models that ARE independently classified (StockLot,
    StockSerial, StockReservation, InventoryLock - their scoping parent, StockItem, is
    DERIVED and never in a delta batch for them to ride along with) are filtered by
    their own since_field instead, same as a top-level model.

    Returns the same {'model', 'pk', 'fields'} shape as export_snapshot() - a caller
    round-trips it through JSON as usual before importing.
    """
    since_dt = parse_datetime(since) if since else None
    objects = []
    included_pks = {}  # (app_label, model_name) -> set of pks in this batch, for children to reference

    for app_label, model_name, scope in MANIFEST:
        classified = is_delta_eligible(app_label, model_name)

        if scope in ('global', 'direct'):
            if not classified:
                continue  # DERIVED or out-of-scope top-level model - never delta-synced
            since_field = since_field_for(app_label, model_name)
            qs = _queryset_for(app_label, model_name, scope, company)
            if since_dt is not None and since_field is not None:
                qs = qs.filter(**{f'{since_field}__gt': since_dt})
            pks = set(qs.values_list('pk', flat=True))
            included_pks[(app_label, model_name)] = pks
            objects.extend(json.loads(serializers.serialize('json', qs)))
            continue

        # ('via', parent_field) or ('via2', f1, f2) - a child/line-item model.
        if classified:
            # Independently classified (StockLot etc.) - filter by its own since_field,
            # same as a top-level model, ignoring the parent chain entirely.
            since_field = since_field_for(app_label, model_name)
            qs = _queryset_for(app_label, model_name, scope, company)
            if since_dt is not None and since_field is not None:
                qs = qs.filter(**{f'{since_field}__gt': since_dt})
            objects.extend(json.loads(serializers.serialize('json', qs)))
            continue

        if since_dt is None:
            # First/full sync - export every child in full, matching export_snapshot().
            qs = _queryset_for(app_label, model_name, scope, company)
            objects.extend(json.loads(serializers.serialize('json', qs)))
            continue

        # Delta sync, unclassified child - ride along with whichever parent rows this
        # batch already included. `scope[1]` is always the immediate parent FK field
        # name on this model, whether scope is ('via', parent) or ('via2', parent, _).
        from django.apps import apps
        model = apps.get_model(app_label, model_name)
        parent_field = model._meta.get_field(scope[1])
        parent_model = parent_field.related_model
        parent_key = (parent_model._meta.app_label, parent_model._meta.object_name)
        parent_pks = included_pks.get(parent_key)
        if not parent_pks:
            continue  # nothing from this child's parent changed in this batch
        manager = getattr(model, 'all_objects', None) or model.objects
        qs = manager.filter(**{f'{scope[1]}_id__in': parent_pks})
        objects.extend(json.loads(serializers.serialize('json', qs)))

    return objects


def import_snapshot_data(objects_data, expected_company_id=None):
    """Loads a snapshot (as produced by export_snapshot(), already round-tripped through
    JSON) into the current database, preserving every row's original primary key.

    `expected_company_id`: if given, every 'user_auth.company' object in the data must
    have this pk, and no *other* Company row may already exist locally - the single-
    tenant guard this data is going into a fresh or matching-company local database, not
    silently merging a second company's data into it (see desktop_server.py's own
    startup guard, which checks the same invariant from the other direction after import
    has already happened).

    A delta payload (from export_snapshot_delta()) normally contains NO
    'user_auth.company' object at all - unlike a full export, nothing changed about the
    Company row itself, so it's just not in the batch. That must NOT be read as "no
    company is expected to exist locally yet": when `expected_company_id` is given, it
    is trusted directly for the "no other company" check below, rather than deriving
    the allowed-company set purely from what happens to be present in this specific
    payload (which a full export happens to always include, but a delta export usually
    won't).

    Returns the count of objects imported.
    """
    company_pks_in_data = {
        obj['pk'] for obj in objects_data if obj['model'] == 'user_auth.company'
    }
    if expected_company_id is not None:
        if company_pks_in_data - {expected_company_id}:
            raise ValueError(
                f'Snapshot contains company id(s) {company_pks_in_data} other than the '
                f'expected {expected_company_id} - refusing to import.'
            )
        existing_other_companies = Company.objects.exclude(pk=expected_company_id).exists()
    else:
        existing_other_companies = Company.objects.exclude(pk__in=company_pks_in_data).exists()
    if existing_other_companies:
        raise ValueError(
            'Local database already has company data that is not part of this snapshot - '
            'refusing to import into what should be a single-tenant local database.'
        )

    count = 0
    skipped = []
    # SQLite's PRAGMA foreign_keys is a no-op once a transaction is already open (see
    # sqlite3/base.py's disable_constraint_checking(): "Foreign key constraints cannot
    # be turned off while in a multi-statement transaction") - constraint_checks_
    # disabled() must wrap transaction.atomic(), not be nested inside it, or every
    # deserialized_obj.save() below still enforces FK order despite this call. Has no
    # effect on Postgres either way (the base backend's default is a no-op there;
    # Postgres import instead relies on MANIFEST already being topologically ordered).
    with connection.constraint_checks_disabled():
        with transaction.atomic():
            for deserialized_obj in serializers.deserialize('python', objects_data):
                instance = deserialized_obj.object
                # Each row gets its own SAVEPOINT (nested atomic(), not the whole
                # import's outer one) - a single bad row must never silently block every
                # OTHER row in the same payload from ever syncing down again (this
                # function reruns identically every cycle - one permanently-bad row
                # would otherwise wedge the desktop's pull-sync forever), the same "one
                # bad entry doesn't block the rest of the queue" principle
                # core.desktop_sync.DesktopSyncLoop.drain() already applies to push-back.
                try:
                    with transaction.atomic():
                        deserialized_obj.save()
                    count += 1
                    continue
                except IntegrityError as exc:
                    # `except ... as exc` deletes the `exc` binding when this block
                    # ends (ordinary Python exception-scoping behavior) - captured into
                    # a plain variable so it's still usable below.
                    error_text = str(exc)

                # A production-side hard delete followed by a NEW row reusing the same
                # natural key (a fired-then-rehired staff email, most concretely - User
                # has no SoftDeleteMixin, so its deletions are exactly the "can never be
                # represented as gone by an upsert-only mechanism" gap this module's own
                # docstring already calls out) is the one case reliably reconcilable
                # without guessing: production's own export can never contain an
                # internal email collision (its own unique constraint already prevents
                # that), so a local collision here can only be against a row production
                # no longer has - safe to remove and retry.
                reconciled = False
                if isinstance(instance, User) and 'email' in error_text.lower():
                    stale = User.objects.filter(email=instance.email).exclude(pk=instance.pk).first()
                    if stale is not None:
                        stale.delete()
                        try:
                            with transaction.atomic():
                                deserialized_obj.save()
                            count += 1
                            reconciled = True
                        except IntegrityError as exc2:
                            error_text = str(exc2)
                if not reconciled:
                    skipped.append(f'{instance._meta.label}#{instance.pk}: {error_text}')

    if skipped:
        print(f'[snapshot] {len(skipped)} row(s) could not be imported this cycle (the rest of '
              f'the sync still applied): ' + '; '.join(skipped[:10]))
    return count


def import_all_companies_snapshot(objects_data, allow_nonempty=False):
    """Disaster-recovery restore (Phase B): seeds a brand-new backend from a full
    multi-company backup (export_all_companies_snapshot()'s output). Deliberately
    separate from import_snapshot_data() rather than a shared code path with a flag -
    that function's single-tenant guard is exactly right for the routine desktop-
    pairing case and must stay untouched; this is a different, far more dangerous
    operation (seeding/overwriting an entire system's data) that needs its own,
    stricter default: refuse unless the target database has NO company rows at all.

    Not reachable through the API at all (see core/management/commands/
    restore_all_companies.py) - a genuine "production's database is gone" scenario
    means seeding a brand-new database that has no User rows yet to authenticate as,
    so this can only ever be run with direct server/database access, never as an
    authenticated web action. Exposing a "restore everything" button reachable by any
    Owner login would also just be a needless way to let one bad click nuke a live,
    populated database - the CLI-only path is a deliberate safety choice, not a
    missing feature.

    `allow_nonempty=True` overrides the empty-target guard for advanced/scripted use
    (the management command exposes it as an explicit --allow-nonempty flag - never
    the default).

    Returns the count of objects imported.
    """
    if not allow_nonempty and Company.objects.exists():
        raise ValueError(
            'This database already has company data - refusing a full disaster-recovery '
            'restore into a non-empty database. This restore path is meant to seed a '
            'brand-new, empty backend only. Pass allow_nonempty=True to override.'
        )
    count = 0
    # SQLite's PRAGMA foreign_keys is a no-op once a transaction is already open (see
    # sqlite3/base.py's disable_constraint_checking(): "Foreign key constraints cannot
    # be turned off while in a multi-statement transaction") - constraint_checks_
    # disabled() must wrap transaction.atomic(), not be nested inside it, or every
    # deserialized_obj.save() below still enforces FK order despite this call. Has no
    # effect on Postgres either way (the base backend's default is a no-op there;
    # Postgres import instead relies on MANIFEST already being topologically ordered).
    with connection.constraint_checks_disabled():
        with transaction.atomic():
            for deserialized_obj in serializers.deserialize('python', objects_data):
                deserialized_obj.save()
                count += 1
    return count
