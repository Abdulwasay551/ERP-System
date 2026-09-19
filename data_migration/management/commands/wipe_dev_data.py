"""Phase 0 (part 2): wipe the live ERP's dev/test-scale rows before the BizNet
historical import, keeping the Company and Warehouse rows themselves.

Deleting Partner and Product cascades nearly everything else (Customer/Supplier and
everything hanging off them via CASCADE, and any remaining Product-linked rows) - see
the FK audit done before writing this command. Accounts/AccountCategory/AccountGroup
are wiped too even though the live DB currently has 0 of them, so this command is safe
to re-run. Company and Warehouse rows are updated in place by migrate_biznet_master,
not deleted here.

Usage:
    python manage.py wipe_dev_data --company "Mobile Corner"          # dry run
    python manage.py wipe_dev_data --company "Mobile Corner" --yes    # actually delete
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounting.models import Account, AccountCategory, AccountGroup
from crm.models import Partner
from products.models import Product, ProductCategory
from user_auth.models import Company


class Command(BaseCommand):
    help = "Wipe dev/test data for a company before the BizNet historical import (keeps Company/Warehouse/User rows)."

    def add_arguments(self, parser):
        parser.add_argument('--company', required=True, help="Exact Company.name to wipe")
        parser.add_argument('--yes', action='store_true', help="Actually delete. Without this, only prints counts.")

    def handle(self, *args, **options):
        try:
            company = Company.objects.get(name=options['company'])
        except Company.DoesNotExist:
            raise CommandError(f"No Company named {options['company']!r} found.")

        partner_count = Partner.objects.filter(company=company).count()
        product_count = Product.all_objects.filter(company=company).count()
        category_count = ProductCategory.objects.filter(company=company).count()
        account_count = Account.objects.filter(company=company).count()
        group_count = AccountGroup.objects.filter(company=company).count()
        cat_count = AccountCategory.objects.filter(company=company).count()

        self.stdout.write(f"Company: {company.name} (id={company.id})")
        self.stdout.write(f"  Partner rows (cascades Customer/Supplier/Invoice/Bill/etc.): {partner_count}")
        self.stdout.write(f"  Product rows (cascades ProductTracking/StockItem/etc.): {product_count}")
        self.stdout.write(f"  ProductCategory rows: {category_count}")
        self.stdout.write(f"  Account / AccountGroup / AccountCategory rows: {account_count} / {group_count} / {cat_count}")

        if not options['yes']:
            self.stdout.write(self.style.WARNING("Dry run only - pass --yes to actually delete."))
            return

        with transaction.atomic():
            deleted_partners = Partner.objects.filter(company=company).delete()
            deleted_products = Product.all_objects.filter(company=company).delete()
            deleted_categories = ProductCategory.objects.filter(company=company).delete()
            deleted_accounts = Account.objects.filter(company=company).delete()
            deleted_groups = AccountGroup.objects.filter(company=company).delete()
            deleted_cats = AccountCategory.objects.filter(company=company).delete()

        self.stdout.write(self.style.SUCCESS("Deleted:"))
        for label, result in [
            ('Partner (+cascades)', deleted_partners),
            ('Product (+cascades)', deleted_products),
            ('ProductCategory', deleted_categories),
            ('Account', deleted_accounts),
            ('AccountGroup', deleted_groups),
            ('AccountCategory', deleted_cats),
        ]:
            self.stdout.write(f"  {label}: {result}")
