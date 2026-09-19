"""Data-correction pass for the BizNet sales migration: link InvoiceItem.tracking_unit.

migrate_biznet_sales updated each sold ProductTracking row's `sold_invoice`, but never
set the reverse `InvoiceItem.tracking_unit` FK the app's serializers/UI actually read
from (sales.InvoiceItemSerializer's `tracking_identifier`/`tracking_status`) - so
migrated invoices show no tracking info despite the underlying data existing. This
mirrors the same gap found and fixed for purchase.BillItem/ProductTracking.bill_item.

Unlike the Bill side, this isn't a pure backfill: the live app's convention (POS,
returns) is one InvoiceItem per tracked unit (quantity=1, one tracking_unit each), but
the migration created one InvoiceItem per legacy SalesBody line, which can have
quantity>1 when several IMEIs were sold together on one BizNet line. Those lines are
split into one quantity=1 InvoiceItem per tracked unit, redistributing the original
line's discount_amount/tax_amount/line_total evenly across the split rows (remainder
placed on the last row so the original totals are preserved exactly). Confirmed safe:
no CreditNoteItem in this migration references a real (non-synthetic-placeholder)
InvoiceItem, so nothing else holds a FK to the rows being replaced.

Usage:
    python manage.py fix_invoice_tracking_links --company "Mobile Corner"           # dry run
    python manage.py fix_invoice_tracking_links --company "Mobile Corner" --apply   # write
"""
from collections import defaultdict
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from data_migration.legacy import bulk_create_chunked
from products.models import ProductTracking
from sales.models import InvoiceItem
from user_auth.models import Company


class Command(BaseCommand):
    help = "Fix InvoiceItem.tracking_unit links for the BizNet sales migration (see module docstring)."

    def add_arguments(self, parser):
        parser.add_argument('--company', required=True)
        parser.add_argument('--apply', action='store_true')

    def handle(self, *args, **options):
        self.apply = options['apply']
        try:
            self.company = Company.objects.get(name=options['company'])
        except Company.DoesNotExist:
            raise CommandError(f"No Company named {options['company']!r} found.")

        with transaction.atomic():
            self._fix()
            if not self.apply:
                self.stdout.write(self.style.WARNING("Dry run only - re-run with --apply to write."))
                transaction.set_rollback(True)

    def _fix(self):
        items = list(InvoiceItem.objects.filter(
            invoice__company=self.company, tracking_unit=None,
            product__tracking_method__in=['imei', 'serial'],
        ).select_related('invoice'))
        self.stdout.write(f"Tracked InvoiceItem rows missing tracking_unit: {len(items)}")
        if not items:
            return

        # Group available sold-tracking units by (invoice_id, product_id) once.
        pairs = {(it.invoice_id, it.product_id) for it in items}
        tracking_by_pair = defaultdict(list)
        for pt in ProductTracking.all_objects.filter(
            sold_invoice_id__in={p[0] for p in pairs}, product_id__in={p[1] for p in pairs},
        ).order_by('id'):
            tracking_by_pair[(pt.sold_invoice_id, pt.product_id)].append(pt)

        simple_updates = []
        split_originals = []
        new_items = []
        no_data = 0
        mismatched = 0

        for it in items:
            units = tracking_by_pair.get((it.invoice_id, it.product_id), [])
            qty = int(it.quantity)
            if not units:
                no_data += 1
                continue
            # Consume up to `qty` units for this line (units list is shared across
            # possibly-multiple lines for the same invoice+product - pop as used).
            take = units[:qty]
            del units[:qty]
            remaining = qty - len(take)
            if not take:
                no_data += 1
                continue
            if remaining:
                mismatched += 1
            if qty == 1 and len(take) == 1:
                it.tracking_unit = take[0]
                simple_updates.append(it)
                continue

            # Split into one qty=1 line per tracked unit, plus (if some of this line's
            # units have no tracking data at all) one extra untracked line carrying the
            # leftover quantity - so both total quantity and total amounts are preserved
            # exactly, rather than silently dropping the untracked portion. Amounts are
            # allocated per unit of the ORIGINAL quantity (not per split row), with the
            # remainder placed on the last chunk.
            chunks = [(1, unit) for unit in take]
            if remaining:
                chunks.append((remaining, None))
            per_unit_discount = it.discount_amount / qty
            per_unit_tax = it.tax_amount / qty
            per_unit_total = it.line_total / qty
            running_discount = running_tax = running_total = Decimal('0.00')
            for idx, (chunk_qty, unit) in enumerate(chunks):
                is_last = idx == len(chunks) - 1
                if is_last:
                    discount = it.discount_amount - running_discount
                    tax = it.tax_amount - running_tax
                    total = it.line_total - running_total
                else:
                    discount = (per_unit_discount * chunk_qty).quantize(Decimal('0.01'))
                    tax = (per_unit_tax * chunk_qty).quantize(Decimal('0.01'))
                    total = (per_unit_total * chunk_qty).quantize(Decimal('0.01'))
                    running_discount += discount
                    running_tax += tax
                    running_total += total
                new_items.append(InvoiceItem(
                    invoice_id=it.invoice_id, product_id=it.product_id, tracking_unit=unit,
                    quantity=chunk_qty, uom=it.uom, unit_price=it.unit_price,
                    discount_type=it.discount_type, discount_value=it.discount_value,
                    discounts=it.discounts, discount_amount=discount, tax_amount=tax, line_total=total,
                    tracking_required=unit is not None,
                ))
            split_originals.append(it.id)

        if self.apply:
            InvoiceItem.objects.bulk_update(simple_updates, ['tracking_unit'], batch_size=2000)
            if split_originals:
                InvoiceItem.objects.filter(id__in=split_originals).delete()
            bulk_create_chunked(InvoiceItem, new_items)

        self.stdout.write(self.style.SUCCESS(
            f"Simple 1:1 links: {len(simple_updates)}; lines split: {len(split_originals)} "
            f"-> {len(new_items)} new qty=1 lines; no tracking data available: {no_data}; "
            f"quantity/unit-count mismatches: {mismatched}"
        ))
