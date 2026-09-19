"""Data-correction pass: PurchasePayment / sales.Payment were never created from the
BizNet migration, even though the underlying cash movement is real and already posted
to the GL (migrate_biznet_vouchers).

BizNet has no dedicated "vendor payment" or "customer payment" table - those events are
recorded as CreditVouchers (money received) and DebitVouchers (money paid out) against
whichever party account was involved, and migrate_biznet_vouchers already turned every
line into a JournalEntry/JournalItem. But nothing ever created the domain-level
PurchasePayment/sales.Payment rows the Supplier/Customer "Payments" tabs actually read,
or credited SupplierLedger/CustomerLedger for them - so those ledgers were overstated
(bills/invoices counted, payments never netted against them).

Only the two HIGH-CONFIDENCE directions are handled here:
  - DebitVouchers -> a Supplier's account = we paid that supplier (PurchasePayment).
  - CreditVouchers -> a Customer's account = that customer paid us (sales.Payment).

Deliberately NOT handled (ambiguous given BizNet's one-account-per-party design, where
the same account can be a customer's receivable in one transaction and effectively a
payable in another): CreditVouchers -> a Supplier's account (PKR 338M - could be a
vendor refund/rebate) and DebitVouchers -> a Customer's account (PKR 2.28B - unusually
large; could be commissions/advances to trade-partners, needs a human decision on
semantics before recording it as anything specific).

Not tied to any specific Bill/Invoice - BizNet's PaidAmount fields don't record which
voucher paid which bill, so these post as unattributed payments against the party
(bill=None / invoice=None), same as a real "payment on account" would.

Usage:
    python manage.py migrate_biznet_payments --company "Mobile Corner"           # dry run
    python manage.py migrate_biznet_payments --company "Mobile Corner" --apply   # write
"""
from collections import defaultdict

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from crm.models import Customer, CustomerLedger
from data_migration.legacy import already_migrated_pks, biznet_fetch_all, bulk_create_chunked, bulk_record_map, load_map
from purchase.models import PurchasePayment, Supplier, SupplierLedger
from sales.models import Payment
from user_auth.models import Company, User

MIGRATION_USER_EMAIL = 'data-migration@mobilecorner.local'


class Command(BaseCommand):
    help = "BizNet -> ERP: backfill PurchasePayment/sales.Payment from Debit/CreditVouchers (see module docstring)."

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

        self.supplier_map = load_map(self.company, 'parties_as_supplier')  # legacy accountno -> Supplier id
        self.customer_map = load_map(self.company, 'parties_as_customer')  # legacy accountno -> Customer id

        with transaction.atomic():
            self.migrate_supplier_payments()
            self.migrate_customer_payments()
            if not self.apply:
                self.stdout.write(self.style.WARNING("Dry run only - re-run with --apply to write."))
                transaction.set_rollback(True)

    def _method_from_narration(self, narration):
        return 'bank_transfer' if 'bank' in (narration or '').lower() else 'cash'

    # ---------------------------------------------------------- Supplier payments
    def migrate_supplier_payments(self):
        already = already_migrated_pks(self.company, 'debitvouchers_as_payment')
        headers = {h['voucherno']: h['voucherdate'] for h in biznet_fetch_all(
            "SELECT voucherno, voucherdate FROM debitvouchers"
        )}
        rows = [r for r in biznet_fetch_all(
            "SELECT serialno, voucherno, accountno, amount, narration FROM debitvouchersbody"
        ) if str(r['serialno']) not in already and r['accountno'].strip() in self.supplier_map]
        self.stdout.write(f"DebitVoucher lines to suppliers to migrate: {len(rows)}")
        if not rows:
            return

        payments = []
        for r in rows:
            voucher_date = headers.get(r['voucherno'])
            if not voucher_date:
                continue
            payments.append(PurchasePayment(
                company=self.company, payment_number=f"PAY-LEG-DV-{r['serialno']}",
                supplier_id=self.supplier_map[r['accountno'].strip()],
                payment_type='bill_payment', amount=r['amount'] or 0,
                payment_method=self._method_from_narration(r['narration']),
                payment_date=voucher_date.date(), status='completed',
                reference_number=(r['narration'] or '').strip()[:255],
                created_by=self.migration_user,
            ))
        bulk_create_chunked(PurchasePayment, payments)

        ledger = [
            SupplierLedger(
                company=self.company, supplier_id=p.supplier_id, transaction_date=p.payment_date,
                reference_type='payment', reference_id=p.id, description=f'Payment {p.payment_number}',
                debit_amount=0, credit_amount=p.amount, balance=0, created_by=self.migration_user,
            )
            for p in payments
        ]
        bulk_create_chunked(SupplierLedger, ledger)

        bulk_record_map(self.company, 'debitvouchers_as_payment', [(r['serialno'], p) for r, p in zip(rows, payments)])
        self.stdout.write(self.style.SUCCESS(f"Supplier payments migrated: {len(payments)}, ledger credits: {len(ledger)}"))

    # ---------------------------------------------------------- Customer payments
    def migrate_customer_payments(self):
        already = already_migrated_pks(self.company, 'creditvouchers_as_payment')
        headers = {h['voucherno']: h['voucherdate'] for h in biznet_fetch_all(
            "SELECT voucherno, voucherdate FROM creditvouchers"
        )}
        rows = [r for r in biznet_fetch_all(
            "SELECT serialno, voucherno, accountno, amount, narration FROM creditvouchersbody"
        ) if str(r['serialno']) not in already and r['accountno'].strip() in self.customer_map]
        self.stdout.write(f"CreditVoucher lines from customers to migrate: {len(rows)}")
        if not rows:
            return

        payments = []
        for r in rows:
            voucher_date = headers.get(r['voucherno'])
            if not voucher_date:
                continue
            payments.append(Payment(
                company=self.company, payment_number=f"PAY-LEG-CV-{r['serialno']}",
                customer_id=self.customer_map[r['accountno'].strip()],
                amount=r['amount'] or 0, payment_date=voucher_date.date(),
                method=self._method_from_narration(r['narration']),
                reference=(r['narration'] or '').strip()[:100],
                received_by=self.migration_user, processed_by=self.migration_user,
            ))
        bulk_create_chunked(Payment, payments)

        ledger = [
            CustomerLedger(
                company=self.company, customer_id=p.customer_id, transaction_date=p.payment_date,
                reference_type='payment', reference_id=p.id, description=f'Payment {p.payment_number}',
                debit_amount=0, credit_amount=p.amount, balance=0, created_by=self.migration_user,
            )
            for p in payments
        ]
        bulk_create_chunked(CustomerLedger, ledger)

        bulk_record_map(self.company, 'creditvouchers_as_payment', [(r['serialno'], p) for r, p in zip(rows, payments)])
        self.stdout.write(self.style.SUCCESS(f"Customer payments migrated: {len(payments)}, ledger credits: {len(ledger)}"))
