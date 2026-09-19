"""Phase D (continued): opening balances.

Only 44 of BizNet's 610 ChartOfAccounts rows carry a non-zero OpeningDebit/OpeningCredit
- all 44 are party sub-ledger accounts (customers/vendors), none are "real" GL accounts
(cash, inventory, fixed assets, etc. all opened at zero in this dataset). Their opening
figures do NOT balance on their own (total OpeningCredit 26,902,486 vs OpeningDebit
5,984,455 - a difference of 20,918,031): BizNet's original setup recorded known
payables/receivables at go-live without a fully balanced opening trial balance, which is
common for a small business's first bookkeeping setup. A dedicated "Opening Balance
Equity" account absorbs that plug, exactly as e.g. QuickBooks does automatically in the
same situation - this keeps every JournalEntry in the system balanced (verified after
Phase D: 0 unbalanced entries) rather than silently breaking that invariant for this one
entry.

Dated one day before the earliest transaction found anywhere in the source data (a 2002
sale row - the actual earliest activity, even though the bulk of the data starts 2017),
so it sits chronologically before everything else once ledgers are recomputed.

Usage:
    python manage.py migrate_biznet_opening_balances --company "Mobile Corner"           # dry run
    python manage.py migrate_biznet_opening_balances --company "Mobile Corner" --apply   # write
"""
import datetime

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounting.models import Account, AccountGroup, Journal, JournalEntry, JournalItem
from crm.models import CustomerLedger
from data_migration.legacy import already_migrated_pks, biznet_fetch_all, bulk_create_chunked, bulk_record_map, load_map
from purchase.models import SupplierLedger
from user_auth.models import Company, User

MIGRATION_USER_EMAIL = 'data-migration@mobilecorner.local'
OPENING_DATE = datetime.date(2002, 12, 19)


class Command(BaseCommand):
    help = "BizNet -> ERP Phase D continued: opening balances for the 44 party accounts that carry one."

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

        self.account_map = load_map(self.company, 'chartofaccounts')
        self.supplier_map = load_map(self.company, 'parties_as_supplier')
        self.customer_map = load_map(self.company, 'parties_as_customer')

        already = already_migrated_pks(self.company, 'chartofaccounts_opening')
        rows = [r for r in biznet_fetch_all(
            "SELECT accountno, accountname, openingdebit, openingcredit FROM chartofaccounts "
            "WHERE openingdebit <> 0 OR openingcredit <> 0 ORDER BY accountno"
        ) if r['accountno'].strip() not in already]
        self.stdout.write(f"Accounts with opening balances to migrate: {len(rows)}")
        if not rows:
            return

        with transaction.atomic():
            self._migrate(rows)
            if not self.apply:
                self.stdout.write(self.style.WARNING("Dry run only - re-run with --apply to write."))
                transaction.set_rollback(True)

    def _migrate(self, rows):
        total_debit = sum(r['openingdebit'] or 0 for r in rows)
        total_credit = sum(r['openingcredit'] or 0 for r in rows)
        plug = total_credit - total_debit  # positive => need an extra debit to balance

        equity_group = AccountGroup.objects.filter(company=self.company, code='31').first()
        obe_account, _ = Account.objects.get_or_create(
            company=self.company, code='OBE-LEG',
            defaults={
                'group': equity_group, 'name': 'Opening Balance Equity (BizNet legacy import)',
                'type': 'equity', 'balance_side': 'credit',
            },
        )

        journal, _ = Journal.objects.get_or_create(
            company=self.company, name='Legacy Vouchers', defaults={'type': 'general'},
        )
        entry = JournalEntry.objects.create(
            company=self.company, journal=journal, date=OPENING_DATE,
            reference='OPENING-BALANCES-LEG', created_by=self.migration_user,
        )

        items = [
            JournalItem(
                entry=entry, account_id=self.account_map[r['accountno'].strip()],
                debit=r['openingdebit'] or 0, credit=r['openingcredit'] or 0,
                description=f"Opening balance - {r['accountname'].strip()}",
            )
            for r in rows
        ]
        if plug > 0:
            items.append(JournalItem(entry=entry, account_id=obe_account.id, debit=plug, credit=0, description='Opening balance plug'))
        elif plug < 0:
            items.append(JournalItem(entry=entry, account_id=obe_account.id, debit=0, credit=-plug, description='Opening balance plug'))
        bulk_create_chunked(JournalItem, items)

        supplier_ledger, customer_ledger = [], []
        for r in rows:
            accountno = r['accountno'].strip()
            debit, credit = r['openingdebit'] or 0, r['openingcredit'] or 0
            supplier_id = self.supplier_map.get(accountno)
            customer_id = self.customer_map.get(accountno)
            if supplier_id:
                # BizNet credit on a party account = amount WE owe them (payable) ->
                # SupplierLedger.debit_amount ("amount owed TO supplier"), and vice versa.
                supplier_ledger.append(SupplierLedger(
                    company=self.company, supplier_id=supplier_id, transaction_date=OPENING_DATE,
                    reference_type='opening_balance', reference_id=supplier_id,
                    description=f"Opening balance - {r['accountname'].strip()}",
                    debit_amount=credit, credit_amount=debit, balance=0,
                    created_by=self.migration_user,
                ))
            if customer_id:
                customer_ledger.append(CustomerLedger(
                    company=self.company, customer_id=customer_id, transaction_date=OPENING_DATE,
                    reference_type='opening_balance', reference_id=customer_id,
                    description=f"Opening balance - {r['accountname'].strip()}",
                    debit_amount=debit, credit_amount=credit, balance=0,
                    created_by=self.migration_user,
                ))
        bulk_create_chunked(SupplierLedger, supplier_ledger)
        bulk_create_chunked(CustomerLedger, customer_ledger)

        bulk_record_map(self.company, 'chartofaccounts_opening', [(r['accountno'].strip(), entry) for r in rows])

        self.stdout.write(self.style.SUCCESS(
            f"Opening balances migrated: {len(items)} journal items (plug={plug}), "
            f"{len(supplier_ledger)} supplier ledger rows, {len(customer_ledger)} customer ledger rows"
        ))
