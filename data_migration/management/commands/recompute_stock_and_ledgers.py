"""Final recompute pass, run once after Phases A-D have all written their facts.

StockItem.quantity/average_cost and CustomerLedger/SupplierLedger.balance were left as
0/placeholder throughout the migration (see migrate_biznet_purchases's and
migrate_biznet_sales's docstrings) - inserting real running totals via bulk_create would
have needed a strictly time-ordered single pass across every phase at once, and would
have been wrong the moment migrate_biznet_opening_balances added earlier-dated rows
after Phase B/C already ran. Recomputing once, here, after everything is loaded, is both
simpler and actually correct.

Safe to re-run any time (e.g. after a later manual correction) - it always recomputes
from scratch rather than incrementing.

Usage:
    python manage.py recompute_stock_and_ledgers --company "Mobile Corner"           # dry run (prints only)
    python manage.py recompute_stock_and_ledgers --company "Mobile Corner" --apply   # write
"""
from collections import defaultdict
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from crm.models import CustomerLedger
from inventory.models import StockItem, StockMovement
from purchase.models import SupplierLedger
from user_auth.models import Company

INCREASE_TYPES = {'grn_receipt', 'sales_return'}
DECREASE_TYPES = {'sale', 'purchase_return'}


class Command(BaseCommand):
    help = "Recompute StockItem quantities/costs and CustomerLedger/SupplierLedger running balances."

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
            self.recompute_stock_items()
            self.recompute_ledger('customer')
            self.recompute_ledger('supplier')
            if not self.apply:
                self.stdout.write(self.style.WARNING("Dry run only - re-run with --apply to write."))
                transaction.set_rollback(True)

    # ------------------------------------------------------------------ Stock
    def recompute_stock_items(self):
        movements = StockMovement.objects.filter(company=self.company).values(
            'stock_item_id', 'movement_type', 'quantity', 'unit_cost'
        )
        qty_by_item = defaultdict(Decimal)
        cost_numerator = defaultdict(Decimal)   # sum(qty * unit_cost) for grn_receipt only
        cost_denominator = defaultdict(Decimal)  # sum(qty) for grn_receipt only
        for m in movements:
            sid = m['stock_item_id']
            if m['movement_type'] in INCREASE_TYPES:
                qty_by_item[sid] += m['quantity']
            elif m['movement_type'] in DECREASE_TYPES:
                qty_by_item[sid] -= m['quantity']
            if m['movement_type'] == 'grn_receipt':
                cost_numerator[sid] += m['quantity'] * m['unit_cost']
                cost_denominator[sid] += m['quantity']

        items = list(StockItem.objects.filter(company=self.company))
        for item in items:
            qty = qty_by_item.get(item.id, Decimal('0'))
            denom = cost_denominator.get(item.id, Decimal('0'))
            avg_cost = (cost_numerator.get(item.id, Decimal('0')) / denom) if denom else Decimal('0')
            item.quantity = qty
            item.available_quantity = max(Decimal('0'), qty)
            item.average_cost = avg_cost.quantize(Decimal('0.01'))
            item.total_cost_value = (qty * item.average_cost).quantize(Decimal('0.01'))
            item.last_purchase_cost = item.average_cost

        if self.apply:
            StockItem.objects.bulk_update(
                items, ['quantity', 'available_quantity', 'average_cost', 'total_cost_value', 'last_purchase_cost'],
                batch_size=2000,
            )
        negative = [i for i in items if i.quantity < 0]
        self.stdout.write(self.style.SUCCESS(
            f"StockItem recomputed: {len(items)} items, {len(negative)} with negative quantity "
            f"(sold/returned more than was ever recorded as purchased - data quality artifact of "
            f"the source, not a bug in this recompute)"
        ))

    # ---------------------------------------------------------------- Ledgers
    def recompute_ledger(self, kind):
        Model = CustomerLedger if kind == 'customer' else SupplierLedger
        party_field = 'customer_id' if kind == 'customer' else 'supplier_id'

        rows = list(
            Model.objects.filter(company=self.company)
            .order_by(party_field, 'transaction_date', 'id')
            .values('id', party_field, 'debit_amount', 'credit_amount')
        )
        running = defaultdict(Decimal)
        to_update = []
        for r in rows:
            party_id = r[party_field]
            running[party_id] += (r['debit_amount'] or 0) - (r['credit_amount'] or 0)
            obj = Model(id=r['id'])
            obj.balance = running[party_id]
            to_update.append(obj)

        if self.apply:
            Model.objects.bulk_update(to_update, ['balance'], batch_size=2000)
        self.stdout.write(self.style.SUCCESS(f"{Model.__name__} balances recomputed: {len(to_update)} rows across {len(running)} parties"))
