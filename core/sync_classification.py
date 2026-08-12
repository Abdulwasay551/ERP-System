"""
Encodes `desktop/model-sync-classification.md`'s STATE/EVENT/DERIVED design as code -
the single source of truth Phase A's delta export (and any future Phase C push-back)
consult at runtime, rather than the classification living only in a design doc.

Three kinds, matching the doc exactly:

- STATE - a mutable entity with a current row edited over time. Delta-filtered by
  `since_field__gt since` (an `updated_at`-shaped field - the actual field name varies
  per model, see `since_field_for()` below), synced as upsert-by-PK.
- EVENT - happened once, essentially never edited afterward (an audit-trail/ledger
  entry). Delta-filtered by its own creation-timestamp field, synced as append-only.
- DERIVED - always recomputed from other already-synced data, never synced directly
  (e.g. `StockItem`'s running quantity balances, `StockAlert`, `FinancialStatement`).
  Excluded from DELTA_MANIFEST entirely - desktop must recompute these locally after
  the events they depend on have synced, never receive them as their own source of
  truth. A DERIVED *field* on an otherwise-synced STATE/EVENT row (`Invoice.paid_amount`,
  `Bill.paid_amount`, `SupplierRating.overall_rating`) is different - the row itself
  still syncs normally, that one field's value just comes along for the ride as
  whatever production last computed it to be, since desktop has no independent stream
  of the underlying events to recompute it from anyway.

Models scoped ('via', ...) or ('via2', ...) in `snapshot.MANIFEST` (line items /
per-unit tracking rows that are children of a STATE or EVENT parent) deliberately have
NO entry here and need none: `export_snapshot_delta()` always includes every child row
belonging to any parent that's in the current delta batch, regardless of the child's own
timestamp - editing a document typically rewrites its whole item set anyway, and item
rows are cheap. This is why the four inventory models classified STATE in the design doc
(`StockLot`/`StockSerial`/`StockReservation`/`InventoryLock`) DO still need their own
entry here despite being `('via', 'stock_item')` in MANIFEST - their scoping parent,
`StockItem`, is DERIVED and therefore never appears in a delta batch for them to ride
along with, so they need independent since-filtering same as a top-level model would.

Models absent from both this dict and `desktop/model-sync-classification.md` (CRM
leads/opportunities/campaigns, `sales.LegacyProduct`) are OUT OF SCOPE - confirmed dead
or explicitly dormant, excluded from sync entirely, matching the same boundary the rest
of the desktop app work already drew.
"""

STATE = 'STATE'
EVENT = 'EVENT'

# (app_label, model_name) -> {'kind': STATE|EVENT, 'since_field': '<field name>' (optional
# override; omit to use the STATE->'updated_at'/EVENT->'created_at' default), or
# 'since_field': None to mean "always export this model in full, never delta-filter"
# (small, rarely-changing reference tables where filtering isn't worth the complexity).
CLASSIFICATION = {
    # --- global reference data: small, rarely-changing - always exported in full ---
    ('user_auth', 'Role'): {'kind': STATE, 'since_field': None},
    ('accounting', 'Currency'): {'kind': STATE, 'since_field': None},
    ('core', 'NumberSequence'): {'kind': STATE, 'since_field': None},

    # --- user_auth ---
    ('user_auth', 'User'): {'kind': STATE},

    # --- crm ---
    ('crm', 'Partner'): {'kind': STATE},
    ('crm', 'Customer'): {'kind': STATE},
    ('crm', 'CustomerLedger'): {'kind': EVENT},
    ('crm', 'SupplierRating'): {'kind': STATE},
    ('crm', 'CRMConfiguration'): {'kind': STATE},

    # --- products ---
    ('products', 'ProductCategory'): {'kind': STATE},
    ('products', 'Attribute'): {'kind': STATE},
    ('products', 'Product'): {'kind': STATE},
    ('products', 'ProductVariant'): {'kind': STATE},
    ('products', 'ProductTracking'): {'kind': STATE},

    # --- purchase ---
    ('purchase', 'UnitOfMeasure'): {'kind': STATE},
    ('purchase', 'TaxChargesTemplate'): {'kind': STATE},
    ('purchase', 'Supplier'): {'kind': STATE},
    ('purchase', 'SupplierContact'): {'kind': STATE},
    ('purchase', 'SupplierProductCatalog'): {'kind': STATE},
    ('purchase', 'PurchaseRequisition'): {'kind': STATE},
    ('purchase', 'RequestForQuotation'): {'kind': STATE},
    ('purchase', 'SupplierQuotation'): {'kind': STATE},
    ('purchase', 'PurchaseOrder'): {'kind': STATE},
    ('purchase', 'GoodsReceiptNote'): {'kind': STATE},
    ('purchase', 'QualityInspection'): {'kind': STATE},
    ('purchase', 'Bill'): {'kind': STATE},
    ('purchase', 'PurchasePayment'): {'kind': EVENT},
    ('purchase', 'SupplierLedger'): {'kind': EVENT},
    ('purchase', 'PurchaseReturn'): {'kind': EVENT},
    ('purchase', 'PurchaseApproval'): {'kind': EVENT},

    # --- inventory --- (StockItem/StockAlert deliberately absent - DERIVED, excluded)
    ('inventory', 'Warehouse'): {'kind': STATE},
    ('inventory', 'StockLot'): {'kind': STATE},
    ('inventory', 'StockSerial'): {'kind': STATE},
    ('inventory', 'StockReservation'): {'kind': STATE},
    ('inventory', 'InventoryLock'): {'kind': STATE},
    ('inventory', 'StockMovement'): {'kind': EVENT, 'since_field': 'timestamp'},
    ('inventory', 'StockAdjustment'): {'kind': EVENT},
    ('inventory', 'StockTransfer'): {'kind': EVENT},

    # --- sales ---
    ('sales', 'Currency'): {'kind': STATE},
    ('sales', 'PriceList'): {'kind': STATE},
    ('sales', 'Tax'): {'kind': STATE},
    ('sales', 'Quotation'): {'kind': STATE},
    ('sales', 'SalesOrder'): {'kind': STATE},
    ('sales', 'DeliveryNote'): {'kind': STATE},
    ('sales', 'Invoice'): {'kind': STATE},
    ('sales', 'Payment'): {'kind': EVENT},
    ('sales', 'SalesCommission'): {'kind': EVENT},
    ('sales', 'CreditNote'): {'kind': STATE},

    # --- accounting ---
    ('accounting', 'AccountCategory'): {'kind': STATE},
    ('accounting', 'AccountGroup'): {'kind': STATE},
    ('accounting', 'Account'): {'kind': STATE},
    ('accounting', 'Journal'): {'kind': STATE},
    ('accounting', 'JournalTemplate'): {'kind': STATE},
    ('accounting', 'TaxConfig'): {'kind': STATE},
    ('accounting', 'ModuleAccountMapping'): {'kind': STATE},
    ('accounting', 'AutoJournalEntry'): {'kind': STATE},
    ('accounting', 'JournalEntry'): {'kind': EVENT},
    ('accounting', 'AccountPayable'): {'kind': STATE},
    ('accounting', 'AccountReceivable'): {'kind': STATE},
    ('accounting', 'BankAccount'): {'kind': STATE},
    ('accounting', 'BankReconciliation'): {'kind': EVENT},
    ('accounting', 'Expense'): {'kind': EVENT},

    # --- core --- (IdempotencyKey deliberately absent - per-instance dedup infra, has
    # no meaning synced across devices; RecordDeletionLog deliberately absent -
    # operational audit log, same "excluded" precedent as AccountingAuditLog/
    # ActivityLog in snapshot.py's own docstring, not business data the shop needs
    # mirrored)
}

# DERIVED models - never appear in DELTA_MANIFEST, kept here only as an explicit,
# greppable "yes, deliberately excluded" record rather than a silent omission.
DERIVED_MODELS = {
    ('inventory', 'StockItem'),
    ('inventory', 'StockAlert'),
    ('accounting', 'FinancialStatement'),
}

# DERIVED *fields* on models that otherwise sync normally as STATE - never trust these
# fields' synced value as authoritative on either side; always recompute locally the
# same way the model's own save()/signal logic already does.
DERIVED_FIELDS = {
    ('sales', 'Invoice'): ['paid_amount'],
    ('purchase', 'Bill'): ['paid_amount'],
    ('crm', 'SupplierRating'): ['overall_rating'],
}


def since_field_for(app_label, model_name):
    """Returns the field name to filter delta exports by for this model, or None if
    the model should always be exported in full (small reference tables). Defaults to
    'updated_at' for STATE / 'created_at' for EVENT unless CLASSIFICATION overrides it.
    Callers should check is_delta_eligible() first - this returns None for both "always
    full" and "not classified at all", which mean different things."""
    entry = CLASSIFICATION.get((app_label, model_name))
    if entry is None:
        return None
    if 'since_field' in entry:
        return entry['since_field']
    return 'updated_at' if entry['kind'] == STATE else 'created_at'


def is_delta_eligible(app_label, model_name):
    return (app_label, model_name) in CLASSIFICATION
