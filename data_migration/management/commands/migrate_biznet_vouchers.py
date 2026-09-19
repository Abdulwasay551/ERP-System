"""Phase D: manual accounting vouchers.

JournalVouchers (38 headers/86 lines) already carry real debit/credit pairs per line -
mapped directly to one accounting.JournalEntry per voucher + one JournalItem per line.

CreditVouchers (1613/6198) and DebitVouchers (3604/11645) only carry a single `Amount`
per body line (no debit/credit split) against a Parties sub-ledger account - inspecting
real data (see conversation) confirms these are classic cash/bank Receipt and Payment
vouchers: a CreditVoucher body line credits the named party's account (money received -
their balance owed decreases) with an implicit offsetting debit to Cash or Bank; a
DebitVoucher line debits the party (money paid out - what we owe them decreases) with
an implicit offsetting credit to Cash or Bank. There is no header-level or per-line
column recording which of Cash/Bank was used - only the free-text `Narration`
distinguishes them (e.g. "Net cash" vs "Bank Transfer"), so that text is parsed for a
"bank" keyword (case-insensitive) to choose the counter-account per line; ambiguous/
unlabelled lines default to Cash In Hand (account 111), which is the more common case
(1961 of 6198 CreditVouchers lines mention "bank" explicitly; the rest are cash).

AllVouchers/AccountsBalances are NOT loaded here or anywhere in this migration - see
migrate_biznet_master's docstring; they are cross-checked in the verification phase
instead.

Usage:
    python manage.py migrate_biznet_vouchers --company "Mobile Corner"           # dry run
    python manage.py migrate_biznet_vouchers --company "Mobile Corner" --apply   # write
"""
from collections import defaultdict

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounting.models import Journal, JournalEntry, JournalItem
from data_migration.legacy import (
    already_migrated_pks, biznet_fetch_all, bulk_create_chunked, bulk_record_map, load_map,
)
from user_auth.models import Company, User

MIGRATION_USER_EMAIL = 'data-migration@mobilecorner.local'
CASH_ACCOUNTNO = '111'
BANK_ACCOUNTNO = '112'


class Command(BaseCommand):
    help = "BizNet -> ERP Phase D: manual accounting vouchers (Journal/Credit/DebitVouchers)."

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

        self.account_map = load_map(self.company, 'chartofaccounts')  # trimmed AccountNo -> Account id
        self.cash_account_id = self.account_map.get(CASH_ACCOUNTNO)
        self.bank_account_id = self.account_map.get(BANK_ACCOUNTNO)
        if not self.cash_account_id or not self.bank_account_id:
            raise CommandError("Cash (111) / Bank (112) accounts not found - run migrate_biznet_master first.")

        self.journal, _ = Journal.objects.get_or_create(
            company=self.company, name='Legacy Vouchers', defaults={'type': 'general'},
        )
        self.unresolved_accounts = defaultdict(int)

        with transaction.atomic():
            self.migrate_journal_vouchers()
            self.migrate_credit_or_debit_vouchers('creditvouchers', 'creditvouchersbody', is_receipt=True)
            self.migrate_credit_or_debit_vouchers('debitvouchers', 'debitvouchersbody', is_receipt=False)
            if self.unresolved_accounts:
                self.stdout.write(self.style.WARNING(
                    f"Skipped lines with unresolved AccountNo: {dict(self.unresolved_accounts)}"
                ))
            if not self.apply:
                self.stdout.write(self.style.WARNING("Dry run only - re-run with --apply to write."))
                transaction.set_rollback(True)

    def _resolve_account(self, raw_accountno, source_table):
        acc_id = self.account_map.get(raw_accountno.strip())
        if not acc_id:
            self.unresolved_accounts[source_table] += 1
        return acc_id

    # ------------------------------------------------------------- JournalVouchers
    def migrate_journal_vouchers(self):
        already = already_migrated_pks(self.company, 'journalvouchers')
        headers = [r for r in biznet_fetch_all(
            "SELECT voucherno, voucherdate FROM journalvouchers ORDER BY voucherno"
        ) if str(r['voucherno']) not in already]
        self.stdout.write(f"JournalVouchers to migrate: {len(headers)}")
        if not headers:
            return

        body_rows = biznet_fetch_all(
            "SELECT voucherno, accountno, debit, credit, narration FROM journalvouchersbody"
        )
        body_by_voucher = defaultdict(list)
        for r in body_rows:
            body_by_voucher[r['voucherno']].append(r)

        entries = [
            JournalEntry(
                company=self.company, journal=self.journal, date=h['voucherdate'].date(),
                reference=f"JV-LEG-{h['voucherno']}", created_by=self.migration_user,
            )
            for h in headers
        ]
        bulk_create_chunked(JournalEntry, entries)
        entry_by_voucher = {h['voucherno']: e for h, e in zip(headers, entries)}

        items = []
        for h in headers:
            entry = entry_by_voucher[h['voucherno']]
            for b in body_by_voucher.get(h['voucherno'], []):
                acc_id = self._resolve_account(b['accountno'], 'journalvouchersbody')
                if not acc_id:
                    continue
                items.append(JournalItem(
                    entry=entry, account_id=acc_id, debit=b['debit'] or 0, credit=b['credit'] or 0,
                    description=(b['narration'] or '').strip()[:255],
                ))
        bulk_create_chunked(JournalItem, items)

        bulk_record_map(self.company, 'journalvouchers', [(h['voucherno'], entry_by_voucher[h['voucherno']]) for h in headers])
        self.stdout.write(self.style.SUCCESS(f"JournalVouchers migrated: {len(entries)} entries, {len(items)} items"))

    # ------------------------------------------------------ Credit/Debit vouchers
    def migrate_credit_or_debit_vouchers(self, header_table, body_table, is_receipt):
        prefix = 'CV' if is_receipt else 'DV'
        already = already_migrated_pks(self.company, header_table)
        headers = [r for r in biznet_fetch_all(
            f"SELECT voucherno, voucherdate FROM {header_table} ORDER BY voucherno"
        ) if str(r['voucherno']) not in already]
        self.stdout.write(f"{header_table} to migrate: {len(headers)}")
        if not headers:
            return

        body_rows = biznet_fetch_all(
            f"SELECT voucherno, accountno, amount, narration FROM {body_table}"
        )
        body_by_voucher = defaultdict(list)
        for r in body_rows:
            body_by_voucher[r['voucherno']].append(r)

        entries = [
            JournalEntry(
                company=self.company, journal=self.journal, date=h['voucherdate'].date(),
                reference=f"{prefix}-LEG-{h['voucherno']}", created_by=self.migration_user,
            )
            for h in headers
        ]
        bulk_create_chunked(JournalEntry, entries)
        entry_by_voucher = {h['voucherno']: e for h, e in zip(headers, entries)}

        items = []
        for h in headers:
            entry = entry_by_voucher[h['voucherno']]
            for b in body_by_voucher.get(h['voucherno'], []):
                party_acc_id = self._resolve_account(b['accountno'], body_table)
                if not party_acc_id:
                    continue
                amount = b['amount'] or 0
                narration = (b['narration'] or '').strip()
                counter_acc_id = self.bank_account_id if 'bank' in narration.lower() else self.cash_account_id
                if is_receipt:
                    # Receipt: Dr Cash/Bank, Cr Party (their balance owed decreases)
                    items.append(JournalItem(entry=entry, account_id=counter_acc_id, debit=amount, credit=0, description=narration[:255]))
                    items.append(JournalItem(entry=entry, account_id=party_acc_id, debit=0, credit=amount, description=narration[:255]))
                else:
                    # Payment: Dr Party (what we owe them decreases), Cr Cash/Bank
                    items.append(JournalItem(entry=entry, account_id=party_acc_id, debit=amount, credit=0, description=narration[:255]))
                    items.append(JournalItem(entry=entry, account_id=counter_acc_id, debit=0, credit=amount, description=narration[:255]))
        bulk_create_chunked(JournalItem, items)

        bulk_record_map(self.company, header_table, [(h['voucherno'], entry_by_voucher[h['voucherno']]) for h in headers])
        self.stdout.write(self.style.SUCCESS(f"{header_table} migrated: {len(entries)} entries, {len(items)} items"))
