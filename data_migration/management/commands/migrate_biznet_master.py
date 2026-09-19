"""Phase A: master/reference data.

    ChartOfAccounts (610) -> accounting.AccountCategory / AccountGroup / Account
    Godowns (1)           -> update the existing Warehouse in place
    Companies (59, brand) -> Product.brand string only (not a modeled entity)
    Products (2024)       -> products.Product (+ ProductCategory from GroupID)
    Parties (458)         -> crm.Partner + Customer/Supplier

Parties are NOT classified by the legacy PartyType column: real data only uses 'C'
(11 rows) and 'O' (447 rows), and 'O' parties are used as BOTH Purchase.VendorID (232
of them) and Sales.CustomerID (302 of them) - the single-letter flag does not track
actual role. Instead each party's Customer/Supplier flags are derived from whether its
PartyID actually appears as a vendor in `purchase`/`purreturns` and/or as a customer in
`sales`/`salereturns`/`recoverybody` - a party can become both a Customer and a Supplier,
matching crm.Partner's is_customer/is_supplier design.

ChartOfAccounts.AccountDepth is NOT trusted as a literal tree depth - spot-checking
found leaf party accounts one level shallower than their real ParentAccountNo chain
(e.g. account 6201002 stored AccountDepth=2 but its real chain is
6 -> 62 -> 6201 -> 6201002, i.e. real depth 3). Real depth is computed here by walking
ParentAccountNo ourselves. Opening/Adjusted debit-credit balances on ChartOfAccounts are
NOT loaded here - they have no home on accounting.Account (which carries no balance
field itself); non-party account balances are seeded as journal entries in Phase D, and
party account balances as CustomerLedger/SupplierLedger 'opening_balance' rows in
Phase B/C.

Usage:
    python manage.py migrate_biznet_master --company "Mobile Corner"           # dry run
    python manage.py migrate_biznet_master --company "Mobile Corner" --apply   # write
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounting.models import Account, AccountCategory, AccountGroup
from crm.models import Customer, Partner
from data_migration.legacy import already_migrated_pks, biznet_fetch_all, record_map
from inventory.models import Warehouse
from products.models import Product, ProductCategory
from purchase.models import Supplier, UnitOfMeasure
from user_auth.models import Company, User

MIGRATION_USER_EMAIL = 'data-migration@mobilecorner.local'

# Real depth-0 AccountNo -> Account.type. '6' (Parties) has no single type - see
# per-account resolution below.
ROOT_ACCOUNT_TYPE = {'1': 'asset', '2': 'liability', '3': 'equity', '4': 'income', '5': 'expense'}
BALANCE_SIDE_BY_TYPE = {
    'asset': 'debit', 'expense': 'debit',
    'liability': 'credit', 'equity': 'credit', 'income': 'credit',
}


def get_or_create_migration_user(company):
    user, created = User.objects.get_or_create(
        email=MIGRATION_USER_EMAIL,
        defaults={'first_name': 'Data', 'last_name': 'Migration', 'company': company, 'is_active': False},
    )
    if created:
        user.set_unusable_password()
        user.save(update_fields=['password'])
    return user


class Command(BaseCommand):
    help = "BizNet -> ERP Phase A: chart of accounts, warehouse, products, parties."

    def add_arguments(self, parser):
        parser.add_argument('--company', required=True)
        parser.add_argument('--apply', action='store_true', help="Actually write. Without this, dry run only.")

    def handle(self, *args, **options):
        self.apply = options['apply']
        try:
            self.company = Company.objects.get(name=options['company'])
        except Company.DoesNotExist:
            raise CommandError(f"No Company named {options['company']!r} found.")

        self.migration_user = get_or_create_migration_user(self.company) if self.apply else None

        with transaction.atomic():
            self.build_chart_of_accounts()
            self.update_warehouse()
            self.load_products()
            self.load_parties()
            self.load_unit_of_measure()
            if not self.apply:
                self.stdout.write(self.style.WARNING("Dry run only - re-run with --apply to write."))
                transaction.set_rollback(True)

    # ------------------------------------------------------------------ COA
    def build_chart_of_accounts(self):
        rows = biznet_fetch_all(
            "SELECT accountno, accountname, parentaccountno, isdetailed, plflag "
            "FROM chartofaccounts ORDER BY accountno"
        )
        by_no = {r['accountno'].strip(): r for r in rows}

        def real_depth(accountno, _seen=None):
            _seen = _seen or set()
            if accountno in _seen:
                return 0  # cycle guard, shouldn't happen
            row = by_no.get(accountno)
            if row is None or not row['parentaccountno'] or not row['parentaccountno'].strip():
                return 0
            parent = row['parentaccountno'].strip()
            return 1 + real_depth(parent, _seen | {accountno})

        depths = {no: real_depth(no) for no in by_no}

        already = already_migrated_pks(self.company, 'chartofaccounts')
        pending = [r for r in rows if r['accountno'].strip() not in already]
        self.stdout.write(f"ChartOfAccounts: {len(rows)} total, {len(pending)} to migrate")
        if not pending:
            return

        categories = {}   # accountno -> AccountCategory
        groups = {}        # accountno -> AccountGroup
        accounts = {}       # accountno -> Account

        # Categories (real depth 0) first, then groups (depth 1), then leaf accounts
        # (depth 2+) in depth order so each one's `parent` Account already exists.
        for no in sorted(by_no, key=lambda n: depths[n]):
            row = by_no[no]
            depth = depths[no]
            name = row['accountname'].strip()

            if depth == 0:
                cat, _ = AccountCategory.objects.get_or_create(
                    company=self.company, code=no, defaults={'name': name},
                )
                categories[no] = cat
                record_map(self.company, 'chartofaccounts', no, cat)
                continue

            if depth == 1:
                parent_no = row['parentaccountno'].strip()
                cat = categories[parent_no]
                grp, _ = AccountGroup.objects.get_or_create(
                    company=self.company, code=no, defaults={'category': cat, 'name': name},
                )
                groups[no] = grp
                record_map(self.company, 'chartofaccounts', no, grp)
                continue

            # depth >= 2: leaf/grouping Account. Walk up to the nearest real-depth-1
            # ancestor for `group`, and use the immediate parent Account (if any, i.e.
            # depth >= 3) for `parent`.
            parent_no = row['parentaccountno'].strip()
            parent_account = accounts.get(parent_no)  # set only if parent is itself depth>=2
            group = groups.get(parent_no)
            walk = parent_no
            while group is None and walk:
                walk = by_no[walk]['parentaccountno'].strip() if by_no[walk]['parentaccountno'] else ''
                group = groups.get(walk)
            root_no = no
            while depths[root_no] > 0:
                root_no = by_no[root_no]['parentaccountno'].strip()

            acc_type = ROOT_ACCOUNT_TYPE.get(root_no, 'asset')
            acc, _ = Account.objects.get_or_create(
                company=self.company, code=no,
                defaults={
                    'group': group,
                    'name': name,
                    'type': acc_type,
                    'parent': parent_account,
                    'is_group': not row['isdetailed'],
                    'balance_side': BALANCE_SIDE_BY_TYPE.get(acc_type, 'debit'),
                },
            )
            accounts[no] = acc
            record_map(self.company, 'chartofaccounts', no, acc)

        self.stdout.write(self.style.SUCCESS(
            f"COA: {len(categories)} categories, {len(groups)} groups, {len(accounts)} accounts"
        ))

    # ------------------------------------------------------------- Warehouse
    def update_warehouse(self):
        rows = biznet_fetch_all("SELECT godownid, godownname FROM godowns ORDER BY godownid")
        if not rows:
            return
        row = rows[0]  # single-warehouse legacy install (confirmed: 1 row)
        warehouse = Warehouse.objects.filter(company=self.company).first()
        if warehouse is None:
            warehouse = Warehouse(company=self.company, warehouse_type='main')
        warehouse.name = row['godownname'].strip()
        warehouse.code = warehouse.code or 'MAIN'
        warehouse.save()
        record_map(self.company, 'godowns', row['godownid'], warehouse)
        self.stdout.write(self.style.SUCCESS(f"Warehouse: {warehouse.name!r} (id={warehouse.id})"))

    # --------------------------------------------------------------- Products
    def load_products(self):
        brands = {r['companyid'].strip(): r['companyname'].strip()
                  for r in biznet_fetch_all("SELECT companyid, companyname FROM companies")}

        group_ids = [r['groupid'] for r in biznet_fetch_all(
            "SELECT DISTINCT groupid FROM products WHERE groupid IS NOT NULL ORDER BY groupid"
        )]
        categories = {}
        for gid in group_ids:
            cat, _ = ProductCategory.objects.get_or_create(
                company=self.company, code=f'BN-{gid}', defaults={'name': f'Product Group {gid}'},
            )
            categories[gid] = cat

        rows = biznet_fetch_all(
            "SELECT productid, companyid, productname, purchaseprice, saleprice, "
            "purstratio, salestratio, iseasyload, groupid, model "
            "FROM products ORDER BY productid"
        )
        already = already_migrated_pks(self.company, 'products')
        pending = [r for r in rows if r['productid'].strip() not in already]
        self.stdout.write(f"Products: {len(rows)} total, {len(pending)} to migrate")

        to_create = []
        for r in pending:
            pid = r['productid'].strip()
            is_easyload = bool(r['iseasyload'])
            product = Product(
                company=self.company,
                name=r['productname'].strip(),
                brand=brands.get(r['companyid'].strip(), ''),
                sku=pid,
                category=categories.get(r['groupid']),
                product_type='service' if is_easyload else 'product',
                unit_of_measure='piece',
                cost_price=r['purchaseprice'] or 0,
                selling_price=r['saleprice'] or 0,
                is_stockable=not is_easyload,
                is_saleable=True,
                is_purchasable=True,
                tracking_method='none',  # refined per-product in Phase B from serials usage
                notes=f"Legacy model: {r['model'].strip()}" if r['model'] and r['model'].strip() else '',
                created_by=self.migration_user,
            )
            to_create.append((pid, product))

        for pid, product in to_create:
            product.save()  # not bulk_create: SKU is pre-set so save()'s generator path is skipped, but we still want per-row PK/id back for the map
            record_map(self.company, 'products', pid, product)

        self.stdout.write(self.style.SUCCESS(f"Products migrated: {len(to_create)}"))

    # ---------------------------------------------------------------- Parties
    def load_parties(self):
        vendor_ids = {r['vendorid'].strip() for r in biznet_fetch_all(
            "SELECT DISTINCT vendorid FROM purchase WHERE vendorid IS NOT NULL "
            "UNION SELECT DISTINCT vendorid FROM purreturns WHERE vendorid IS NOT NULL"
        )}
        customer_ids = {r['customerid'].strip() for r in biznet_fetch_all(
            "SELECT DISTINCT customerid FROM sales WHERE customerid IS NOT NULL "
            "UNION SELECT DISTINCT customerid FROM salereturns WHERE customerid IS NOT NULL"
        )}

        rows = biznet_fetch_all(
            "SELECT partyid, partyname, address, city, phone1, mobile, email, "
            "contactperson, cnic "
            "FROM parties ORDER BY partyid"
        )
        already = already_migrated_pks(self.company, 'parties')
        pending = [r for r in rows if r['partyid'].strip() not in already]
        self.stdout.write(
            f"Parties: {len(rows)} total, {len(pending)} to migrate "
            f"({len(vendor_ids)} used as vendor, {len(customer_ids)} used as customer)"
        )

        n_customer = n_supplier = n_both = n_neither = 0
        for r in pending:
            pid = r['partyid'].strip()
            is_vendor = pid in vendor_ids
            is_customer = pid in customer_ids

            partner = Partner.objects.create(
                company=self.company,
                name=r['partyname'].strip(),
                display_name=r['partyname'].strip(),
                partner_type='company',
                email=(r['email'] or '').strip()[:254],
                phone=(r['phone1'] or '').strip()[:50],
                mobile=(r['mobile'] or '').strip()[:50],
                contact_person=(r['contactperson'] or '').strip(),
                street=(r['address'] or '').strip(),
                city=(r['city'] or '').strip(),
                tax_id=(r['cnic'] or '').strip(),
                is_customer=is_customer,
                is_supplier=is_vendor,
                created_by=self.migration_user,
            )
            record_map(self.company, 'parties', pid, partner)

            if is_customer:
                customer = Customer.objects.create(
                    partner=partner, company=self.company, name=partner.name,
                    email=partner.email, phone=partner.phone,
                    customer_code=f'CUST-LEG-{pid}',
                    created_by=self.migration_user,
                )
                record_map(self.company, 'parties_as_customer', pid, customer)
            if is_vendor:
                supplier = Supplier.objects.create(
                    partner=partner, company=self.company,
                    supplier_code=f'SUP-LEG-{pid}',
                    created_by=self.migration_user,
                )
                record_map(self.company, 'parties_as_supplier', pid, supplier)

            n_customer += is_customer
            n_supplier += is_vendor
            n_both += is_customer and is_vendor
            n_neither += not is_customer and not is_vendor

        self.stdout.write(self.style.SUCCESS(
            f"Parties migrated: customers={n_customer} suppliers={n_supplier} "
            f"both={n_both} neither={n_neither}"
        ))

        # One synthetic walk-in customer for Sales rows with no real Parties link
        # (Sales.DefCustomerName populated instead) - used in Phase C.
        walkin_partner, created = Partner.objects.get_or_create(
            company=self.company, name='Walk-in Customer',
            defaults={'display_name': 'Walk-in Customer', 'partner_type': 'individual',
                      'is_customer': True, 'created_by': self.migration_user},
        )
        if created:
            walkin_customer = Customer.objects.create(
                partner=walkin_partner, company=self.company, name='Walk-in Customer',
                customer_code='CUST-LEG-WALKIN', created_by=self.migration_user,
            )
            record_map(self.company, 'synthetic', 'walkin_customer', walkin_customer)
            self.stdout.write(self.style.SUCCESS("Created synthetic Walk-in Customer"))

    # --------------------------------------------------------------- UOM
    def load_unit_of_measure(self):
        uom, created = UnitOfMeasure.objects.get_or_create(
            company=self.company, name='Piece',
            defaults={'abbreviation': 'pc', 'uom_type': 'quantity', 'is_base_unit': True},
        )
        if created:
            self.stdout.write(self.style.SUCCESS("Created default UnitOfMeasure 'Piece'"))
