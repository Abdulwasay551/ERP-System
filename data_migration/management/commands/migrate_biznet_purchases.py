"""Phase B: purchase-side history.

Per BizNet Purchase row: a stub PurchaseOrder (PurchaseReturn requires one - see below)
+ a GoodsReceiptNote left effectively "already received" (status='received', but
created via bulk_create so its own save()-driven cascades never fire - stock effects
are recorded ourselves, explicitly, to control historical dates/costs) + GRNItem per
PurchaseBody line + Bill/BillItem + a StockMovement per line + ProductTracking for
"clean" individually-serialized lines.

PurReturns (477 rows) ALL have a NULL PurchaseID in the source data (verified - not a
sampling artifact), so there is no real link back to an originating purchase to hang a
PurchaseReturnItem.grn_item (required FK) off of. Each return therefore gets its own
minimal synthetic PurchaseOrder+GRN+GRNItem "as if" it were the original receipt - this
is a limitation of the source data, not of this migration.

Serial numbers: SaleSerials/PurchaseSerials rows are NOT all real per-unit IMEIs - many
values repeat 4-6+ times (dummy/placeholder codes for non-serialized lines pushed
through the same serial-tracking mechanism; ~3200 values aren't even 15 digits).
products.ProductTracking.imei_number is globally unique, so blindly creating one row
per raw serial row would both violate that constraint and misrepresent shared
placeholder codes as real units. Individual ProductTracking rows are only created for
"clean" serials: exactly 15 numeric digits AND appearing exactly once in
PurchaseSerials (the dominant single-purchase pattern). Everything else still counts
toward the aggregate StockMovement quantity for its line - it just doesn't get its own
trackable unit. Phase C (sales) updates these same rows to status='sold' rather than
creating new ones, for serials that were also sold cleanly.

SupplierLedger.balance is written as a placeholder (0) here, not a true running total -
Phase D adds earlier-dated opening-balance rows once real ChartOfAccounts balances are
available, which would make a Phase-B-computed running total wrong anyway. A dedicated
recompute pass (recompute_ledger_balances) fixes up the real cumulative balance once
all of Phase B/C/D have written their ledger facts.

Usage:
    python manage.py migrate_biznet_purchases --company "Mobile Corner"           # dry run
    python manage.py migrate_biznet_purchases --company "Mobile Corner" --apply   # write
"""
import re
from collections import defaultdict

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from data_migration.legacy import (
    already_migrated_pks, biznet_fetch_all, bulk_create_chunked, bulk_record_map, load_map,
)
from inventory.models import StockItem, StockMovement, Warehouse
from products.models import Product, ProductTracking
from purchase.models import (
    Bill, BillItem, GoodsReceiptNote, GRNItem, PurchaseOrder, PurchaseReturn,
    PurchaseReturnItem, Supplier, SupplierLedger,
)
from user_auth.models import Company, User

MIGRATION_USER_EMAIL = 'data-migration@mobilecorner.local'
CLEAN_SERIAL_RE = re.compile(r'^\d{15}$')


def aware(dt):
    """BizNet timestamps come back as naive datetimes; USE_TZ=True expects aware ones."""
    return timezone.make_aware(dt) if timezone.is_naive(dt) else dt


class Command(BaseCommand):
    help = "BizNet -> ERP Phase B: purchase-side history (Purchase/PurReturns)."

    def add_arguments(self, parser):
        parser.add_argument('--company', required=True)
        parser.add_argument('--apply', action='store_true')

    def handle(self, *args, **options):
        self.apply = options['apply']
        try:
            self.company = Company.objects.get(name=options['company'])
        except Company.DoesNotExist:
            raise CommandError(f"No Company named {options['company']!r} found.")
        try:
            self.migration_user = User.all_objects.get(email=MIGRATION_USER_EMAIL)
        except User.DoesNotExist:
            raise CommandError("Migration system user not found - run migrate_biznet_master first.")
        self.warehouse = Warehouse.objects.filter(company=self.company).first()
        if not self.warehouse:
            raise CommandError("No Warehouse found - run migrate_biznet_master first.")

        self.product_map = load_map(self.company, 'products')          # legacy productid -> Product id
        self.supplier_map = load_map(self.company, 'parties_as_supplier')  # legacy partyid -> Supplier id
        self.product_tracking_method = dict(
            Product.all_objects.filter(company=self.company).values_list('id', 'tracking_method')
        )

        with transaction.atomic():
            self.ensure_stock_items()
            self.migrate_purchases()
            self.migrate_returns()
            if not self.apply:
                self.stdout.write(self.style.WARNING("Dry run only - re-run with --apply to write."))
                transaction.set_rollback(True)

    # ------------------------------------------------------------ StockItem shells
    def ensure_stock_items(self):
        existing = set(StockItem.objects.filter(warehouse=self.warehouse).values_list('product_id', flat=True))
        product_ids = set(self.product_map.values())
        missing = product_ids - existing
        shells = [
            StockItem(company=self.company, product_id=pid, warehouse=self.warehouse, quantity=0)
            for pid in missing
        ]
        bulk_create_chunked(StockItem, shells, ignore_conflicts=True)
        self.stock_item_map = dict(
            StockItem.objects.filter(warehouse=self.warehouse, product_id__in=product_ids)
            .values_list('product_id', 'id')
        )
        self.stdout.write(f"StockItem shells: {len(missing)} created, {len(self.stock_item_map)} total mapped")

    # ------------------------------------------------------------------ Purchases
    def migrate_purchases(self):
        already = already_migrated_pks(self.company, 'purchase')
        purchases = [r for r in biznet_fetch_all(
            "SELECT purchaseid, purchasedate, vendorid, paidamount, narration "
            "FROM purchase ORDER BY purchaseid"
        ) if str(r['purchaseid']) not in already]
        self.stdout.write(f"Purchases to migrate: {len(purchases)}")
        if not purchases:
            return

        body_rows = biznet_fetch_all(
            "SELECT purchaseid, productid, qty, bonus, price, discvalue, stvalue, "
            "ttlvalue, ttlsalestax, cost FROM purchasebody WHERE isdeleted = false"
        )
        body_by_purchase = defaultdict(list)
        for r in body_rows:
            body_by_purchase[r['purchaseid']].append(r)

        clean_serials = self._clean_purchase_serials()
        serials_by_purchase_product = defaultdict(list)
        for r in clean_serials:
            serials_by_purchase_product[(r['purchaseid'], r['productid'].strip())].append(r)

        # --- PurchaseOrder shells (satisfy PurchaseReturn.purchase_order's required FK
        # uniformly, and give every Bill a real PO->GRN->Bill chain) ---
        po_list, po_meta = [], []
        for p in purchases:
            supplier_id = self.supplier_map.get(p['vendorid'].strip())
            if not supplier_id:
                continue  # vendor not classified as a supplier in Phase A (shouldn't happen - vendorid always drives supplier creation)
            po_list.append(PurchaseOrder(
                company=self.company, po_number=f"PO-LEG-{p['purchaseid']}",
                supplier_id=supplier_id, created_by=self.migration_user,
                warehouse=self.warehouse, status='fully_received',
            ))
            po_meta.append(p)
        bulk_create_chunked(PurchaseOrder, po_list)
        po_by_purchaseid = {}
        for p, po in zip(po_meta, po_list):
            po.order_date = p['purchasedate'].date()
            po_by_purchaseid[p['purchaseid']] = po
        PurchaseOrder.objects.bulk_update(po_list, ['order_date'], batch_size=2000)

        # --- GoodsReceiptNote ---
        grn_list = []
        for p in purchases:
            po = po_by_purchaseid.get(p['purchaseid'])
            if not po:
                continue
            grn_list.append(GoodsReceiptNote(
                company=self.company, grn_number=f"GRN-LEG-{p['purchaseid']}",
                purchase_order=po, supplier_id=po.supplier_id, received_by=self.migration_user,
                warehouse=self.warehouse, status='completed',
                requires_inspection=False, requires_quality_inspection=False,
            ))
        bulk_create_chunked(GoodsReceiptNote, grn_list)
        grn_by_purchaseid = {}
        i = 0
        for p in purchases:
            if p['purchaseid'] not in po_by_purchaseid:
                continue
            grn = grn_list[i]; i += 1
            grn.received_date = aware(p['purchasedate'])
            grn_by_purchaseid[p['purchaseid']] = grn
        GoodsReceiptNote.objects.bulk_update(grn_list, ['received_date'], batch_size=2000)

        # --- Bill ---
        bill_list = []
        bill_meta = []  # (purchase_row,) aligned with bill_list
        for p in purchases:
            grn = grn_by_purchaseid.get(p['purchaseid'])
            if not grn:
                continue
            lines = body_by_purchase.get(p['purchaseid'], [])
            subtotal = sum((r['ttlvalue'] or 0) for r in lines)
            tax_amount = sum((r['ttlsalestax'] or 0) for r in lines)
            total_amount = subtotal + tax_amount
            paid = p['paidamount'] or 0
            status = 'paid' if paid >= total_amount and total_amount > 0 else ('partially_paid' if paid > 0 else 'approved')
            bill_list.append(Bill(
                company=self.company, bill_number=f"BILL-LEG-{p['purchaseid']}",
                supplier_id=grn.supplier_id, purchase_order=grn.purchase_order, grn=grn,
                warehouse=self.warehouse, goods_received=True, created_by=self.migration_user,
                bill_date=p['purchasedate'].date(), due_date=p['purchasedate'].date(),
                subtotal=subtotal, tax_amount=tax_amount, total_amount=total_amount,
                paid_amount=paid, outstanding_amount=total_amount - paid,
                status=status, matching_type='two_way_grn',
                notes=(p['narration'] or '').strip()[:1000],
            ))
            bill_meta.append(p)
        bulk_create_chunked(Bill, bill_list)
        bill_by_purchaseid = {p['purchaseid']: bill for p, bill in zip(bill_meta, bill_list)}

        # --- GRNItem + BillItem + StockMovement + ProductTracking ---
        grnitem_list, grnitem_meta = [], []  # meta: (purchaseid, body_row)
        for p in bill_meta:
            grn = grn_by_purchaseid[p['purchaseid']]
            for b in body_by_purchase.get(p['purchaseid'], []):
                product_id = self.product_map.get(b['productid'].strip())
                if not product_id:
                    continue
                qty = (b['qty'] or 0) + (b['bonus'] or 0)
                tm = self.product_tracking_method.get(product_id, 'none')
                grnitem_list.append(GRNItem(
                    grn=grn, product_id=product_id, ordered_qty=qty, received_qty=qty,
                    accepted_qty=qty, quality_status='passed',
                    tracking_type=tm, tracking_required=tm != 'none',
                    warehouse=self.warehouse,
                ))
                grnitem_meta.append((p, b, product_id, qty))
        bulk_create_chunked(GRNItem, grnitem_list)

        billitem_list = []
        movement_list = []
        tracking_list = []
        for (p, b, product_id, qty), grnitem in zip(grnitem_meta, grnitem_list):
            bill = bill_by_purchaseid[p['purchaseid']]
            unit_price = b['price'] or 0
            billitem_list.append(BillItem(
                bill=bill, product_id=product_id, quantity=qty, unit_price=unit_price,
                discount_amount=b['discvalue'] or 0, line_total=b['ttlvalue'] or 0,
                grn_item=grnitem, item_source='grn',
                tracking_required=grnitem.tracking_required, tracking_type=grnitem.tracking_type,
            ))
            stock_item_id = self.stock_item_map.get(product_id)
            if stock_item_id and qty > 0:
                movement_list.append(StockMovement(
                    company=self.company, stock_item_id=stock_item_id, movement_type='grn_receipt',
                    quantity=qty, unit_cost=b['cost'] or unit_price, grn_item=grnitem,
                    to_warehouse=self.warehouse, reference_type='bill',
                    reference_id=bill.id, reference_number=bill.bill_number,
                    performed_by=self.migration_user, posting_required=False,
                    notes='BizNet historical import',
                ))
                movement_list[-1]._legacy_timestamp = aware(p['purchasedate'])

            for s in serials_by_purchase_product.get((p['purchaseid'], b['productid'].strip()), []):
                tracking_list.append(ProductTracking(
                    product_id=product_id, imei_number=s['startingserialno'].strip(),
                    status='available', quality_status='passed',
                    current_warehouse=self.warehouse, grn_item=grnitem,
                    purchase_price=s['cost'] or unit_price, purchase_date=p['purchasedate'].date(),
                    supplier_id=bill.supplier_id, created_by=self.migration_user,
                ))
        bulk_create_chunked(BillItem, billitem_list)
        bulk_create_chunked(StockMovement, movement_list)
        for m in movement_list:
            m.timestamp = m._legacy_timestamp
        StockMovement.objects.bulk_update(movement_list, ['timestamp'], batch_size=2000)
        bulk_create_chunked(ProductTracking, tracking_list, ignore_conflicts=True)

        # --- SupplierLedger (placeholder balance - see module docstring) ---
        ledger_list = [
            SupplierLedger(
                company=self.company, supplier_id=bill.supplier_id, transaction_date=bill.bill_date,
                reference_type='bill', reference_id=bill.id, description=f'Bill {bill.bill_number}',
                debit_amount=bill.total_amount, credit_amount=0, balance=0,
                created_by=self.migration_user,
            )
            for bill in bill_list
        ]
        bulk_create_chunked(SupplierLedger, ledger_list)

        bulk_record_map(self.company, 'purchase', [(p['purchaseid'], bill_by_purchaseid[p['purchaseid']]) for p in bill_meta])

        self.stdout.write(self.style.SUCCESS(
            f"Purchases migrated: {len(bill_list)} bills, {len(grnitem_list)} GRN items, "
            f"{len(movement_list)} stock movements, {len(tracking_list)} tracking units"
        ))

    def _clean_purchase_serials(self):
        counts = defaultdict(int)
        rows = biznet_fetch_all(
            "SELECT purchaseid, productid, startingserialno, cost FROM purchaseserials WHERE isdeleted = false"
        )
        for r in rows:
            counts[r['startingserialno'].strip()] += 1
        return [
            r for r in rows
            if counts[r['startingserialno'].strip()] == 1 and CLEAN_SERIAL_RE.match(r['startingserialno'].strip())
        ]

    # -------------------------------------------------------------------- Returns
    def migrate_returns(self):
        already = already_migrated_pks(self.company, 'purreturns')
        returns = [r for r in biznet_fetch_all(
            "SELECT returnid, returndate, vendorid, receivedamount, narration "
            "FROM purreturns ORDER BY returnid"
        ) if str(r['returnid']) not in already]
        self.stdout.write(f"PurReturns to migrate: {len(returns)}")
        if not returns:
            return

        body_rows = biznet_fetch_all(
            "SELECT returnid, productid, qty, bonus, price, discvalue, ttlvalue, ttlsalestax, cost "
            "FROM purreturnsbody WHERE isdeleted = false"
        )
        body_by_return = defaultdict(list)
        for r in body_rows:
            body_by_return[r['returnid']].append(r)

        # Every PurReturns row has NULL purchaseid (verified against the real data) -
        # there is no original purchase to link back to, so each return gets its own
        # minimal synthetic PO+GRN+GRNItem chain purely to satisfy required FKs.
        po_list, meta = [], []
        for r in returns:
            supplier_id = self.supplier_map.get(r['vendorid'].strip())
            if not supplier_id:
                continue
            po_list.append(PurchaseOrder(
                company=self.company, po_number=f"PO-LEG-RET-{r['returnid']}",
                supplier_id=supplier_id, created_by=self.migration_user,
                warehouse=self.warehouse, status='cancelled',
                notes='Synthetic PO for a BizNet purchase return with no recorded original purchase',
            ))
            meta.append(r)
        bulk_create_chunked(PurchaseOrder, po_list)
        for r, po in zip(meta, po_list):
            po.order_date = r['returndate'].date()
        PurchaseOrder.objects.bulk_update(po_list, ['order_date'], batch_size=2000)

        grn_list = [
            GoodsReceiptNote(
                company=self.company, grn_number=f"GRN-LEG-RET-{r['returnid']}",
                purchase_order=po, supplier_id=po.supplier_id, received_by=self.migration_user,
                warehouse=self.warehouse, status='cancelled',
                requires_inspection=False, requires_quality_inspection=False,
            )
            for r, po in zip(meta, po_list)
        ]
        bulk_create_chunked(GoodsReceiptNote, grn_list)
        for r, grn in zip(meta, grn_list):
            grn.received_date = aware(r['returndate'])
        GoodsReceiptNote.objects.bulk_update(grn_list, ['received_date'], batch_size=2000)

        pr_list = [
            PurchaseReturn(
                company=self.company, return_number=f"PR-LEG-{r['returnid']}",
                supplier_id=po.supplier_id, purchase_order=po, grn=grn,
                return_type='excess', reason=(r['narration'] or 'BizNet historical return').strip()[:1000] or 'BizNet historical return',
                total_amount=sum((b['ttlvalue'] or 0) for b in body_by_return.get(r['returnid'], [])),
                status='processed', created_by=self.migration_user,
            )
            for r, po, grn in zip(meta, po_list, grn_list)
        ]
        bulk_create_chunked(PurchaseReturn, pr_list)
        for r, pr in zip(meta, pr_list):
            pr.return_date = r['returndate'].date()
        PurchaseReturn.objects.bulk_update(pr_list, ['return_date'], batch_size=2000)

        grnitem_list, gi_meta = [], []
        for r, grn in zip(meta, grn_list):
            for b in body_by_return.get(r['returnid'], []):
                product_id = self.product_map.get(b['productid'].strip())
                if not product_id:
                    continue
                qty = (b['qty'] or 0) + (b['bonus'] or 0)
                tm = self.product_tracking_method.get(product_id, 'none')
                grnitem_list.append(GRNItem(
                    grn=grn, product_id=product_id, ordered_qty=qty, received_qty=qty,
                    accepted_qty=qty, quality_status='passed',
                    tracking_type=tm, tracking_required=tm != 'none', warehouse=self.warehouse,
                ))
                gi_meta.append((r, b, product_id, qty))
        bulk_create_chunked(GRNItem, grnitem_list)

        pr_by_returnid = {r['returnid']: pr for r, pr in zip(meta, pr_list)}
        pritem_list = []
        movement_list = []
        for (r, b, product_id, qty), grnitem in zip(gi_meta, grnitem_list):
            unit_price = b['price'] or 0
            pritem_list.append(PurchaseReturnItem(
                purchase_return=pr_by_returnid[r['returnid']], grn_item=grnitem,
                return_quantity=qty, unit_price=unit_price, line_total=b['ttlvalue'] or 0,
                return_reason='excess',
            ))
            stock_item_id = self.stock_item_map.get(product_id)
            if stock_item_id and qty > 0:
                movement_list.append(StockMovement(
                    company=self.company, stock_item_id=stock_item_id, movement_type='purchase_return',
                    quantity=qty, unit_cost=b['cost'] or unit_price, grn_item=grnitem,
                    from_warehouse=self.warehouse, reference_type='purchase_return',
                    reference_id=pr_by_returnid[r['returnid']].id,
                    performed_by=self.migration_user, posting_required=False,
                    notes='BizNet historical import',
                ))
                movement_list[-1]._legacy_timestamp = aware(r['returndate'])
        bulk_create_chunked(PurchaseReturnItem, pritem_list)
        bulk_create_chunked(StockMovement, movement_list)
        for m in movement_list:
            m.timestamp = m._legacy_timestamp
        StockMovement.objects.bulk_update(movement_list, ['timestamp'], batch_size=2000)

        ledger_list = [
            SupplierLedger(
                company=self.company, supplier_id=pr.supplier_id, transaction_date=pr.return_date,
                reference_type='credit_note', reference_id=pr.id,
                description=f'Purchase return {pr.return_number}',
                debit_amount=0, credit_amount=pr.total_amount, balance=0,
                created_by=self.migration_user,
            )
            for pr in pr_list
        ]
        bulk_create_chunked(SupplierLedger, ledger_list)

        bulk_record_map(self.company, 'purreturns', [(r['returnid'], pr_by_returnid[r['returnid']]) for r in meta])

        self.stdout.write(self.style.SUCCESS(
            f"PurReturns migrated: {len(pr_list)} returns, {len(pritem_list)} items, "
            f"{len(movement_list)} stock movements"
        ))
