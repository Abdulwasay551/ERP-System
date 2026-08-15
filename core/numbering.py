"""
Shared document-numbering: a single atomic counter per (company, sequence_key) replaces
each numbered model's old "peek the last real row's number and add 1" logic.

That old pattern had a real correctness gap surfaced while designing the desktop app's
offline support: a lease-grant endpoint handing the desktop app a batch of numbers ahead
of time could only "reserve" them by peeking too - if the cloud created a document at the
same moment, using the same peek-last-row logic, it could independently compute the exact
same "next" number, since nothing recorded that a range had already been handed out. A
shared counter table closes that gap for every caller (the cloud's own normal creation
AND a desktop lease-grant) at once, since they all go through the same
select_for_update()'d NumberSequence row.

Existing per-model numbering formats/prefixes/year-resets are preserved exactly - each
model still calls next_number() with its own prefix/digit-width/year-scoping, and the
counter is seeded from that model's current last row the first time it's used, so shipping
this never causes a gap or jump in an already-live sequence.

`lease_range()` (used only by the desktop app's lease-grant endpoint, see
core/api_views.py::lease_numbers) shares the exact same counter, so a leased range can
never be independently re-issued by a concurrent single next_number() call.
"""
from django.db import models, transaction
from django.utils import timezone


class NumberSequence(models.Model):
    """One atomic counter per (company, sequence_key) - e.g. ('<company>', 'invoice') or
    ('<company>', 'purchase_order-2026') for a year-scoped sequence. `next_value` is the
    next integer to hand out. Callers always go through next_number()/lease_range()
    below, never touch this directly - that's what guarantees the select_for_update()
    locking actually serializes every caller."""
    # String reference, not an eager `from user_auth.models import Company` - see
    # core/idempotency.py's matching comment for why (this module is imported from
    # core/models.py, which user_auth/models.py itself imports before `Company` is
    # defined - an eager import here would deadlock that circular import).
    company = models.ForeignKey('user_auth.Company', on_delete=models.CASCADE, related_name='number_sequences')
    sequence_key = models.CharField(max_length=64)
    # PositiveBigIntegerField, not PositiveIntegerField: seed_device_ranges() (see
    # core/device_registry.py) deliberately pushes this counter up to a desktop
    # device's reserved range floor (10_000_000_000+) for every sequence_key, and
    # _seed_value() below can independently seed a brand-new counter from an existing
    # row's already-huge trailing number too - both already exceed Postgres's plain
    # `integer` max (~2.1B). A real production row (a desktop-range PurchasePayment)
    # hit this exact overflow in testing before this fix.
    next_value = models.PositiveBigIntegerField(default=1)

    class Meta:
        unique_together = ('company', 'sequence_key')

    def __str__(self):
        return f'{self.company_id}:{self.sequence_key} -> {self.next_value}'


def _seed_value(company, key, model_cls, manager_name, field_name, prefix, year):
    """First-ever use of a (company, key) counter: seed it from whatever the highest
    existing number for this sequence already is (the old peek-last-row logic), so
    switching to the counter-based scheme is a no-op for an already-live sequence - the
    very next number issued is exactly what the old logic would have produced too.

    Always filters by the prefix (year-qualified when year-scoped) before taking the
    last row, not just "whatever the highest id happens to be" - some fields (customer_
    code in particular) allow manual entry that may not match the generated format, and
    without this filter a manually-entered value could be misread as the sequence's
    current high-water mark.
    """
    manager = getattr(model_cls, manager_name)
    qs = manager.filter(company=company)
    starts_with = f'{prefix}-{year}' if year is not None else f'{prefix}-'
    qs = qs.filter(**{f'{field_name}__startswith': starts_with})
    last = qs.order_by('-id').first()
    if not last:
        return 1
    raw = getattr(last, field_name)
    if not raw:
        return 1
    try:
        return int(raw.split('-')[-1]) + 1
    except (ValueError, IndexError):
        return 1


def _locked_sequence(company, sequence_key, year_scoped, model_cls, manager_name, field_name, prefix):
    """Must be called inside transaction.atomic(). Returns the locked NumberSequence row
    for this (company, key), seeding it on first creation."""
    year = timezone.now().year if year_scoped else None
    key = f'{sequence_key}-{year}' if year_scoped else sequence_key
    seq, created = NumberSequence.objects.select_for_update().get_or_create(
        company=company, sequence_key=key, defaults={'next_value': 1},
    )
    if created and model_cls is not None:
        seq.next_value = _seed_value(company, key, model_cls, manager_name, field_name, prefix, year)
    return seq, year


def format_number(prefix, digits, value, year=None):
    if year is not None:
        return f'{prefix}-{year}-{value:0{digits}d}'
    return f'{prefix}-{value:0{digits}d}'


def next_number(company, sequence_key, prefix, digits, model_cls, field_name, manager_name='objects', year_scoped=False, label_year=False):
    """Atomically issues and returns the next formatted number for (company,
    sequence_key). Drop-in replacement for each model's old per-save() peek-last-row
    block - same output format, same year-reset behavior, just backed by one shared
    counter instead of a table scan for the "last" row every time.

    `year_scoped` and `label_year` are deliberately separate, not one flag - most
    year-labeled models (PurchaseOrder/GRN/QualityInspection/Bill) both reset their
    counter each year AND show that year in the number. PurchasePayment is the one
    exception found while auditing all 13 models for this refactor: its number shows
    the current year but its underlying counter never resets (the original code's "last
    row" lookup only filtered `payment_number__isnull=False`, not a year prefix) - so it
    needs `label_year=True` with `year_scoped=False` to reproduce that exact behavior.
    """
    with transaction.atomic():
        seq, year = _locked_sequence(company, sequence_key, year_scoped, model_cls, manager_name, field_name, prefix)
        value = seq.next_value
        seq.next_value = value + 1
        seq.save(update_fields=['next_value'])
    display_year = timezone.now().year if (label_year and year is None) else year
    return format_number(prefix, digits, value, display_year)


def lease_range(company, sequence_key, prefix, digits, count, model_cls, field_name, manager_name='objects', year_scoped=False, label_year=False):
    """Atomically reserves `count` consecutive numbers for (company, sequence_key) in one
    call - the desktop app's lease-grant endpoint uses this to hand out a batch to spend
    offline. Shares the exact same NumberSequence counter as next_number(), so a reserved
    range can never be re-issued by a concurrent single next_number() call elsewhere
    (e.g. someone creating an invoice on the web app at the same moment) - that's the
    correctness gap a peek-last-row-only lease would have had.
    Returns (range_start, range_end, display_year) - display_year is None unless
    year_scoped or label_year (see next_number()'s docstring for the distinction).
    """
    with transaction.atomic():
        seq, year = _locked_sequence(company, sequence_key, year_scoped, model_cls, manager_name, field_name, prefix)
        range_start = seq.next_value
        range_end = range_start + count - 1
        seq.next_value = range_end + 1
        seq.save(update_fields=['next_value'])
    display_year = timezone.now().year if (label_year and year is None) else year
    return range_start, range_end, display_year


# Registry mapping each numbered model to its sequence config - the single place that
# knows every (prefix, digit-width, year-scoping, manager) combination, consulted by the
# lease-grant endpoint (core/api_views.py::lease_numbers). Each numbered model's own
# save() calls next_number() directly with its own literal config (see e.g.
# sales/models.py::Invoice.save()) rather than looking itself up here, to keep each
# model's save() self-contained and readable - this registry exists for the endpoint,
# which needs to go from a client-supplied sequence_key string to the right config
# without hardcoding a long if/elif chain. `model_label` is 'app_label.ModelName',
# resolved lazily via django.apps.apps.get_model() to avoid a circular import between
# core and sales/purchase/crm (which already import from core).
#
# Product's SKU (products/models.py) deliberately isn't here - it's an id-based
# candidate+uniqueness-loop scheme, not a "last number + 1" sequence, and isn't printed
# on customer receipts, so it's a lower-priority follow-up rather than forced into this
# shape.
SEQUENCES = {
    'quotation': dict(model_label='sales.Quotation', prefix='QUO', digits=6, field_name='quotation_number', manager_name='objects', year_scoped=False),
    'sales_order': dict(model_label='sales.SalesOrder', prefix='SO', digits=6, field_name='order_number', manager_name='objects', year_scoped=False),
    'delivery_note': dict(model_label='sales.DeliveryNote', prefix='DN', digits=6, field_name='delivery_number', manager_name='objects', year_scoped=False),
    'invoice': dict(model_label='sales.Invoice', prefix='INV', digits=6, field_name='invoice_number', manager_name='all_objects', year_scoped=False),
    'payment': dict(model_label='sales.Payment', prefix='PAY', digits=6, field_name='payment_number', manager_name='all_objects', year_scoped=False),
    'credit_note': dict(model_label='sales.CreditNote', prefix='CN', digits=6, field_name='credit_number', manager_name='objects', year_scoped=False),
    'supplier': dict(model_label='purchase.Supplier', prefix='SUP', digits=6, field_name='supplier_code', manager_name='all_objects', year_scoped=False),
    'purchase_order': dict(model_label='purchase.PurchaseOrder', prefix='PO', digits=4, field_name='po_number', manager_name='objects', year_scoped=True),
    'grn': dict(model_label='purchase.GoodsReceiptNote', prefix='GRN', digits=4, field_name='grn_number', manager_name='objects', year_scoped=True),
    'quality_inspection': dict(model_label='purchase.QualityInspection', prefix='QI', digits=4, field_name='inspection_number', manager_name='objects', year_scoped=True),
    'bill': dict(model_label='purchase.Bill', prefix='BILL', digits=4, field_name='bill_number', manager_name='all_objects', year_scoped=True),
    'purchase_payment': dict(model_label='purchase.PurchasePayment', prefix='PAY', digits=6, field_name='payment_number', manager_name='all_objects', year_scoped=False, label_year=True),
    'customer': dict(model_label='crm.Customer', prefix='CUST', digits=6, field_name='customer_code', manager_name='all_objects', year_scoped=False),
    # Manual ledger debit/credit adjustments - one sequence_key per (entity, direction)
    # since the model's own save() picks its prefix (DR/CR) at save time from a single
    # `entry_type` field, and each prefix needs its own independent counter.
    'customer_ledger_debit': dict(model_label='crm.CustomerLedgerAdjustment', prefix='DR', digits=6, field_name='adjustment_number', manager_name='all_objects', year_scoped=False),
    'customer_ledger_credit': dict(model_label='crm.CustomerLedgerAdjustment', prefix='CR', digits=6, field_name='adjustment_number', manager_name='all_objects', year_scoped=False),
    'supplier_ledger_debit': dict(model_label='purchase.SupplierLedgerAdjustment', prefix='DR', digits=6, field_name='adjustment_number', manager_name='all_objects', year_scoped=False),
    'supplier_ledger_credit': dict(model_label='purchase.SupplierLedgerAdjustment', prefix='CR', digits=6, field_name='adjustment_number', manager_name='all_objects', year_scoped=False),
}


def resolve_model(model_label):
    from django.apps import apps
    return apps.get_model(model_label)
