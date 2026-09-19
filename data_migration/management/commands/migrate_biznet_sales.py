"""Phase C: sales-side history.

Sales (21857 rows) -> sales.Invoice+InvoiceItem, created directly with a final status
(paid/partially_paid/sent) - Invoice.save()'s inventory/ledger cascade only fires on a
draft->confirmed *transition*, never on first create, so creating it directly this way
deliberately never triggers it (which would otherwise run today's live FIFO stock-
picking against a historical sale). The correct historical StockMovement/
CustomerLedger/ProductTracking effects are created explicitly ourselves instead, same
approach as Phase B's Bills.

SaleReturns (1471 rows): only 17 have a real SaleID, and of those only 34 of 2313 body
lines actually match a real SalesBody line - the other 98.5% have no evidence of what
they were originally sold against (same situation as Phase B's PurReturns, which was
100% unlinked). CreditNoteItem.invoice_item is a required FK, so - for consistency and
simplicity, applied uniformly rather than special-casing the 34 - every SaleReturn gets
its own synthetic placeholder Invoice+InvoiceItem (status='cancelled', clearly noted)
purely to anchor the required FK. This placeholder invoice gets NO StockMovement/
CustomerLedger effect of its own (we have no evidence the original sale really
happened) - only the CreditNote itself (the real, evidenced event: stock came back,
customer was credited) gets real ledger/stock postings.

Serial handling mirrors Phase B: only "clean" serials (exactly 15 numeric digits,
appearing once in saleserials) get an individual ProductTracking update/create; a clean
sold serial that was also cleanly purchased in Phase B updates that same row to
status='sold' rather than creating a duplicate.

CustomerLedger.balance is written as a placeholder (0) here too - see Phase B's
SupplierLedger docstring for why; a dedicated recompute pass fixes up real running
balances once Phase B/C/D have all written their ledger facts.

Usage:
    python manage.py migrate_biznet_sales --company "Mobile Corner"           # dry run
    python manage.py migrate_biznet_sales --company "Mobile Corner" --apply   # write
"""
import re
from collections import defaultdict

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from crm.models import Customer, CustomerLedger
from data_migration.legacy import (
    already_migrated_pks, biznet_fetch_all, bulk_create_chunked, bulk_record_map, load_map,
)
from inventory.models import StockItem, StockMovement, Warehouse
from products.models import Product, ProductTracking
from sales.models import CreditNote, CreditNoteItem, Invoice, InvoiceItem
from user_auth.models import Company, User

MIGRATION_USER_EMAIL = 'data-migration@mobilecorner.local'
CLEAN_SERIAL_RE = re.compile(r'^\d{15}$')


def aware(dt):
    return timezone.make_aware(dt) if timezone.is_naive(dt) else dt


class Command(BaseCommand):
    help = "BizNet -> ERP Phase C: sales-side history (Sales/SaleReturns/Recovery)."

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

        self.product_map = load_map(self.company, 'products')
        self.customer_map = load_map(self.company, 'parties_as_customer')
        self.product_tracking_method = dict(
            Product.all_objects.filter(company=self.company).values_list('id', 'tracking_method')
        )
        self.product_cost = dict(
            Product.all_objects.filter(company=self.company).values_list('id', 'cost_price')
        )
        self.customer_partner = dict(
            Customer.all_objects.filter(company=self.company).values_list('id', 'partner_id')
        )
        self.stock_item_map = dict(
            StockItem.objects.filter(warehouse=self.warehouse).values_list('product_id', 'id')
        )

        with transaction.atomic():
            self.migrate_sales()
            self.migrate_returns()
            self.migrate_recovery()
            if not self.apply:
                self.stdout.write(self.style.WARNING("Dry run only - re-run with --apply to write."))
                transaction.set_rollback(True)

    # ---------------------------------------------------------------------- Sales
    def migrate_sales(self):
        already = already_migrated_pks(self.company, 'sales')
        sales = [r for r in biznet_fetch_all(
            "SELECT saleid, saledate, customerid, receivedamount, narration, "
            "defcustomername, defcustomerphone, defcustomeraddress "
            "FROM sales ORDER BY saleid"
        ) if str(r['saleid']) not in already]
        self.stdout.write(f"Sales to migrate: {len(sales)}")
        if not sales:
            return

        body_rows = biznet_fetch_all(
            "SELECT saleid, productid, qty, bonus, price, discvalue, ttlvalue, ttlsalestax "
            "FROM salesbody WHERE isdeleted = false"
        )
        body_by_sale = defaultdict(list)
        for r in body_rows:
            body_by_sale[r['saleid']].append(r)

        clean_serials = self._clean_serials('saleserials')
        serials_by_sale_product = defaultdict(list)
        for r in clean_serials:
            serials_by_sale_product[(r['saleid'], r['productid'].strip())].append(r)

        invoice_list, meta = [], []
        for s in sales:
            customer_id = self.customer_map.get(s['customerid'].strip())
            if not customer_id:
                continue
            lines = body_by_sale.get(s['saleid'], [])
            subtotal = sum((r['ttlvalue'] or 0) for r in lines)
            tax_amount = sum((r['ttlsalestax'] or 0) for r in lines)
            total = subtotal + tax_amount
            paid = s['receivedamount'] or 0
            status = 'paid' if paid >= total and total > 0 else ('partially_paid' if paid > 0 else 'sent')
            notes_bits = []
            if s['narration'] and s['narration'].strip():
                notes_bits.append(s['narration'].strip())
            if s['defcustomername'] and s['defcustomername'].strip():
                notes_bits.append(f"Walk-in name on receipt: {s['defcustomername'].strip()}")
            if s['defcustomerphone'] and s['defcustomerphone'].strip():
                notes_bits.append(f"Phone: {s['defcustomerphone'].strip()}")
            invoice_list.append(Invoice(
                company=self.company, customer_id=customer_id, created_by=self.migration_user,
                invoice_number=f"INV-LEG-{s['saleid']}", invoice_date=s['saledate'].date(),
                subtotal=subtotal, tax_amount=tax_amount, total=total, paid_amount=paid,
                status=status, billing_address=(s['defcustomeraddress'] or '').strip(),
                notes='; '.join(notes_bits)[:2000],
            ))
            meta.append(s)
        bulk_create_chunked(Invoice, invoice_list)
        invoice_by_saleid = {s['saleid']: inv for s, inv in zip(meta, invoice_list)}

        item_list, item_meta = [], []
        for s in meta:
            invoice = invoice_by_saleid[s['saleid']]
            for b in body_by_sale.get(s['saleid'], []):
                product_id = self.product_map.get(b['productid'].strip())
                if not product_id:
                    continue
                qty = (b['qty'] or 0) + (b['bonus'] or 0)
                if qty <= 0:
                    continue
                tm = self.product_tracking_method.get(product_id, 'none')
                item_list.append(InvoiceItem(
                    invoice=invoice, product_id=product_id, quantity=qty,
                    unit_price=b['price'] or 0, discount_type='amount',
                    discount_value=b['discvalue'] or 0, discount_amount=b['discvalue'] or 0,
                    tax_amount=b['ttlsalestax'] or 0, line_total=b['ttlvalue'] or 0,
                    tracking_required=tm != 'none',
                ))
                item_meta.append((s, b, product_id, qty, invoice))
        bulk_create_chunked(InvoiceItem, item_list)

        movement_list = []
        ledger_list = []
        seen_invoice_for_ledger = set()
        tracking_updates = []  # (imei, invoice, sale_date, partner_id)
        tracking_creates = []
        for (s, b, product_id, qty, invoice), item in zip(item_meta, item_list):
            stock_item_id = self.stock_item_map.get(product_id)
            if stock_item_id:
                unit_cost = self.product_cost.get(product_id) or 0
                mv = StockMovement(
                    company=self.company, stock_item_id=stock_item_id, movement_type='sale',
                    quantity=qty, unit_cost=unit_cost, from_warehouse=self.warehouse,
                    reference_type='invoice', reference_id=invoice.id,
                    reference_number=invoice.invoice_number, performed_by=self.migration_user,
                    posting_required=False, notes='BizNet historical import',
                )
                mv._legacy_timestamp = aware(s['saledate'])
                movement_list.append(mv)

            customer_id = invoice.customer_id
            partner_id = self.customer_partner.get(customer_id)
            for ser in serials_by_sale_product.get((s['saleid'], b['productid'].strip()), []):
                imei = ser['startingserialno'].strip()
                tracking_updates.append((imei, invoice, aware(s['saledate']), partner_id, product_id, s['saledate'].date()))

        if invoice_list:
            for s in meta:
                invoice = invoice_by_saleid[s['saleid']]
                if invoice.id in seen_invoice_for_ledger:
                    continue
                seen_invoice_for_ledger.add(invoice.id)
                ledger_list.append(CustomerLedger(
                    company=self.company, customer_id=invoice.customer_id,
                    transaction_date=invoice.invoice_date, reference_type='invoice',
                    reference_id=invoice.id, description=f'Invoice {invoice.invoice_number}',
                    debit_amount=invoice.total, credit_amount=0, balance=0,
                    created_by=self.migration_user,
                ))

        bulk_create_chunked(StockMovement, movement_list)
        for m in movement_list:
            m.timestamp = m._legacy_timestamp
        StockMovement.objects.bulk_update(movement_list, ['timestamp'], batch_size=2000)
        bulk_create_chunked(CustomerLedger, ledger_list)

        self._apply_sold_tracking(tracking_updates)

        bulk_record_map(self.company, 'sales', [(s['saleid'], invoice_by_saleid[s['saleid']]) for s in meta])

        self.stdout.write(self.style.SUCCESS(
            f"Sales migrated: {len(invoice_list)} invoices, {len(item_list)} items, "
            f"{len(movement_list)} stock movements, {len(tracking_updates)} serials marked sold"
        ))

    def _apply_sold_tracking(self, tracking_updates):
        """tracking_updates: list of (imei, invoice, aware_datetime, partner_id, product_id, sale_date)."""
        if not tracking_updates:
            return
        imeis = [t[0] for t in tracking_updates]
        existing = {
            pt.imei_number: pt
            for pt in ProductTracking.all_objects.filter(imei_number__in=imeis)
        }
        to_update, to_create = [], []
        for imei, invoice, sale_dt, partner_id, product_id, sale_date in tracking_updates:
            pt = existing.get(imei)
            if pt:
                pt.status = 'sold'
                pt.sold_invoice = invoice
                pt.sold_date = sale_dt
                pt.sold_to_customer_id = partner_id
                to_update.append(pt)
            else:
                to_create.append(ProductTracking(
                    product_id=product_id, imei_number=imei, status='sold',
                    sold_invoice=invoice, sold_date=sale_dt, sold_to_customer_id=partner_id,
                    current_warehouse=self.warehouse, created_by=self.migration_user,
                ))
        if to_update:
            ProductTracking.all_objects.bulk_update(
                to_update, ['status', 'sold_invoice', 'sold_date', 'sold_to_customer'], batch_size=2000,
            )
        if to_create:
            bulk_create_chunked(ProductTracking, to_create, ignore_conflicts=True)

    def _clean_serials(self, table):
        counts = defaultdict(int)
        rows = biznet_fetch_all(
            f"SELECT {'saleid' if table == 'saleserials' else 'salereturnid'} AS doc_id, "
            f"productid, startingserialno FROM {table} WHERE isdeleted = false"
        )
        for r in rows:
            counts[r['startingserialno'].strip()] += 1
        clean = [
            r for r in rows
            if counts[r['startingserialno'].strip()] == 1 and CLEAN_SERIAL_RE.match(r['startingserialno'].strip())
        ]
        key = 'saleid' if table == 'saleserials' else 'salereturnid'
        return [{**r, key: r['doc_id']} for r in clean]

    # -------------------------------------------------------------------- Returns
    def migrate_returns(self):
        already = already_migrated_pks(self.company, 'salereturns')
        returns = [r for r in biznet_fetch_all(
            "SELECT salereturnid, returndate, customerid, narration FROM salereturns ORDER BY salereturnid"
        ) if str(r['salereturnid']) not in already]
        self.stdout.write(f"SaleReturns to migrate: {len(returns)}")
        if not returns:
            return

        body_rows = biznet_fetch_all(
            "SELECT salereturnid, productid, qty, bonus, price, ttlvalue, ttlsalestax "
            "FROM salereturnsbody WHERE isdeleted = false"
        )
        body_by_return = defaultdict(list)
        for r in body_rows:
            body_by_return[r['salereturnid']].append(r)

        # Placeholder Invoice per return - see module docstring: 98.5% of return body
        # lines have no evidence of what they were originally sold against.
        placeholder_list, meta = [], []
        for r in returns:
            customer_id = self.customer_map.get(r['customerid'].strip())
            if not customer_id:
                continue
            lines = body_by_return.get(r['salereturnid'], [])
            subtotal = sum((b['ttlvalue'] or 0) for b in lines)
            tax_amount = sum((b['ttlsalestax'] or 0) for b in lines)
            placeholder_list.append(Invoice(
                company=self.company, customer_id=customer_id, created_by=self.migration_user,
                invoice_number=f"INV-LEG-RET-{r['salereturnid']}", invoice_date=r['returndate'].date(),
                subtotal=subtotal, tax_amount=tax_amount, total=subtotal + tax_amount,
                status='cancelled',
                notes='Synthetic placeholder - BizNet has no recorded link from this '
                      'return to an original sale. No stock/ledger effect of its own.',
            ))
            meta.append(r)
        bulk_create_chunked(Invoice, placeholder_list)
        invoice_by_returnid = {r['salereturnid']: inv for r, inv in zip(meta, placeholder_list)}

        item_list, item_meta = [], []
        for r in meta:
            invoice = invoice_by_returnid[r['salereturnid']]
            for b in body_by_return.get(r['salereturnid'], []):
                product_id = self.product_map.get(b['productid'].strip())
                if not product_id:
                    continue
                qty = (b['qty'] or 0) + (b['bonus'] or 0)
                if qty <= 0:
                    continue
                item_list.append(InvoiceItem(
                    invoice=invoice, product_id=product_id, quantity=qty,
                    unit_price=b['price'] or 0, line_total=b['ttlvalue'] or 0,
                    tax_amount=b['ttlsalestax'] or 0,
                ))
                item_meta.append((r, b, product_id, qty, invoice))
        bulk_create_chunked(InvoiceItem, item_list)

        cn_list = [
            CreditNote(
                company=self.company, customer_id=invoice_by_returnid[r['salereturnid']].customer_id,
                invoice=invoice_by_returnid[r['salereturnid']], created_by=self.migration_user,
                credit_number=f"CN-LEG-{r['salereturnid']}", credit_date=r['returndate'].date(),
                subtotal=sum((b['ttlvalue'] or 0) for b in body_by_return.get(r['salereturnid'], [])),
                tax_amount=sum((b['ttlsalestax'] or 0) for b in body_by_return.get(r['salereturnid'], [])),
                total=sum((b['ttlvalue'] or 0) + (b['ttlsalestax'] or 0) for b in body_by_return.get(r['salereturnid'], [])),
                reason='return', notes=(r['narration'] or 'BizNet historical return').strip()[:1000],
            )
            for r in meta
        ]
        bulk_create_chunked(CreditNote, cn_list)
        cn_by_returnid = {r['salereturnid']: cn for r, cn in zip(meta, cn_list)}

        cnitem_list = []
        movement_list = []
        for (r, b, product_id, qty, invoice), item in zip(item_meta, item_list):
            cnitem_list.append(CreditNoteItem(
                credit_note=cn_by_returnid[r['salereturnid']], invoice_item=item,
                product_id=product_id, quantity=qty, unit_price=b['price'] or 0,
                line_total=b['ttlvalue'] or 0,
            ))
            stock_item_id = self.stock_item_map.get(product_id)
            if stock_item_id:
                mv = StockMovement(
                    company=self.company, stock_item_id=stock_item_id, movement_type='sales_return',
                    quantity=qty, unit_cost=self.product_cost.get(product_id) or 0,
                    to_warehouse=self.warehouse, reference_type='invoice',
                    reference_id=cn_by_returnid[r['salereturnid']].id, performed_by=self.migration_user,
                    posting_required=False, notes='BizNet historical import (sales return)',
                )
                mv._legacy_timestamp = aware(r['returndate'])
                movement_list.append(mv)
        bulk_create_chunked(CreditNoteItem, cnitem_list)
        bulk_create_chunked(StockMovement, movement_list)
        for m in movement_list:
            m.timestamp = m._legacy_timestamp
        StockMovement.objects.bulk_update(movement_list, ['timestamp'], batch_size=2000)

        ledger_list = [
            CustomerLedger(
                company=self.company, customer_id=cn.customer_id, transaction_date=cn.credit_date,
                reference_type='credit_note', reference_id=cn.id,
                description=f'Sales return {cn.credit_number}',
                debit_amount=0, credit_amount=cn.total, balance=0, created_by=self.migration_user,
            )
            for cn in cn_list
        ]
        bulk_create_chunked(CustomerLedger, ledger_list)

        bulk_record_map(self.company, 'salereturns', [(r['salereturnid'], cn_by_returnid[r['salereturnid']]) for r in meta])

        self.stdout.write(self.style.SUCCESS(
            f"SaleReturns migrated: {len(cn_list)} credit notes, {len(cnitem_list)} items, "
            f"{len(movement_list)} stock movements"
        ))

    # ------------------------------------------------------------------- Recovery
    def migrate_recovery(self):
        """Only 1 row in this dataset - handled directly via the ORM (not bulk), letting
        Payment.save()'s unconditional CustomerLedger-credit + Invoice.paid_amount sync
        do its normal, correct thing (unlike Invoice's, Payment's cascade fires on
        first create too - see Phase C's docstring reasoning in migrate_biznet_purchases
        for the general policy this follows)."""
        from sales.models import Payment

        already = already_migrated_pks(self.company, 'recoverybody')
        rows = [r for r in biznet_fetch_all(
            "SELECT rb.serialno, rb.recoveryid, rb.saleid, rb.customerid, rb.amount, "
            "r.recoverydate "
            "FROM recoverybody rb JOIN recovery r ON r.recoveryid = rb.recoveryid "
            "WHERE rb.isdeleted = false ORDER BY rb.serialno"
        ) if str(r['serialno']) not in already]
        self.stdout.write(f"RecoveryBody to migrate: {len(rows)}")
        for r in rows:
            customer_id = self.customer_map.get(r['customerid'].strip())
            if not customer_id:
                continue
            invoice_id = None
            if r['saleid']:
                sale_map = load_map(self.company, 'sales')
                invoice_id = sale_map.get(str(r['saleid']))
            payment = Payment.objects.create(
                company=self.company, customer_id=customer_id, invoice_id=invoice_id,
                payment_number=f"PAY-LEG-REC-{r['serialno']}", amount=r['amount'] or 0,
                payment_date=r['recoverydate'].date(), method='cash',
                received_by=self.migration_user, processed_by=self.migration_user,
            )
            bulk_record_map(self.company, 'recoverybody', [(r['serialno'], payment)])
        if rows:
            self.stdout.write(self.style.SUCCESS(f"Recovery payments migrated: {len(rows)}"))
