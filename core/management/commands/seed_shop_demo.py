"""
Seeds realistic mobile-shop demo data on top of seed_erp's base (company, shop roles,
users, warehouses). Unlike seed_erp (generic enterprise fixtures), this creates data
through the actual shop-specific API flows (vendor-invoice -> receive-items ->
confirm-received, POS checkout, expenses, supplier payments) using DRF's test client
with force_authenticate, so ledgers/stock/tracking are populated by the real business
logic instead of hand-crafted rows that could drift from it.

Run after `seed_erp`: python manage.py seed_shop_demo
"""
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone
from rest_framework.test import APIClient

from user_auth.models import Company, User
from crm.models import Partner, Customer
from products.models import Product, ProductCategory
from purchase.models import Supplier
from inventory.models import Warehouse


class Command(BaseCommand):
    help = "Seed realistic mobile-shop demo data (products, vendors, customers, sales, expenses) via the real API flows."

    def handle(self, *args, **options):
        company = Company.objects.first()
        if not company:
            self.stderr.write("No Company found - run `seed_erp` first.")
            return
        warehouse = Warehouse.objects.filter(company=company).first()

        owner = User.objects.get(email='admin@techcorp.com')
        manager = User.objects.get(email='finance@techcorp.com')
        cashier = User.objects.get(email='sales@techcorp.com')
        salesman = User.objects.get(email='salesman@techcorp.com')
        warehouse_user = User.objects.get(email='inventory@techcorp.com')

        self.stdout.write('Creating product catalog...')
        phones_cat, _ = ProductCategory.objects.get_or_create(company=company, name='Mobile Phones', defaults={'code': 'PHONE'})
        acc_cat, _ = ProductCategory.objects.get_or_create(company=company, name='Accessories', defaults={'code': 'ACC'})

        def product(sku, name, brand, tracking, cost, selling, category, barcode=None):
            obj, _ = Product.objects.get_or_create(
                company=company, sku=sku,
                defaults={
                    'name': name, 'brand': brand, 'tracking_method': tracking,
                    'cost_price': Decimal(cost), 'selling_price': Decimal(selling),
                    'category': category, 'product_type': 'product', 'unit_of_measure': 'piece',
                    'is_active': True, 'is_saleable': True, 'is_purchasable': True, 'is_stockable': True,
                    'valuation_method': 'fifo', 'barcode': barcode, 'created_by': owner,
                }
            )
            return obj

        phone_s24 = Product.objects.filter(company=company, sku='PHN-001').first()
        earbuds = Product.objects.filter(company=company, sku='ACC-001').first()
        iphone15 = product('IPH-001', 'iPhone 15 128GB', 'Apple', 'imei', 650, 850, phones_cat)
        redmi = product('XIA-001', 'Redmi Note 13', 'Xiaomi', 'imei', 180, 250, phones_cat)
        galaxy_a15 = product('SAM-002', 'Galaxy A15', 'Samsung', 'imei', 140, 190, phones_cat)
        phone_case = product('CASE-001', 'Universal Phone Case', 'Generic', 'none', 3, 8, acc_cat, barcode='8901111111111')
        charger = product('CHG-001', 'Fast Charger 25W', 'Generic', 'none', 8, 15, acc_cat, barcode='8902222222222')
        powerbank = product('PWR-001', 'Power Bank 10000mAh', 'Generic', 'none', 15, 25, acc_cat, barcode='8903333333333')

        self.stdout.write('Creating vendors (suppliers)...')
        def supplier(name, email, phone, city):
            partner, _ = Partner.objects.get_or_create(
                company=company, name=name,
                defaults={'partner_type': 'company', 'email': email, 'phone': phone, 'city': city, 'is_supplier': True, 'created_by': owner}
            )
            sup, _ = Supplier.objects.get_or_create(partner=partner, defaults={'company': company, 'supplier_type': 'distributor', 'created_by': owner})
            return sup

        mnp = supplier('M&P Distributor', 'sales@mnpdist.com', '021-3456789', 'Karachi')
        gnext = supplier('Gnext Trading', 'info@gnext.pk', '042-1234567', 'Lahore')
        electronics_supply = Supplier.objects.filter(company=company, partner__name='Electronics Supply Co.').first()

        self.stdout.write('Creating customers...')
        def customer(name, phone, email, cnic):
            # Link a Partner so sales.Invoice.create_tracking_movements() (which reads
            # self.customer.partner) can record ProductTracking.sold_to_customer - that
            # field is an FK to crm.Partner, not crm.Customer.
            partner, _ = Partner.objects.get_or_create(
                company=company, name=name,
                defaults={'partner_type': 'individual', 'email': email, 'phone': phone, 'is_customer': True, 'created_by': owner}
            )
            return Customer.objects.get_or_create(
                company=company, name=name,
                defaults={'partner': partner, 'phone': phone, 'email': email, 'cnic': cnic, 'created_by': owner}
            )[0]

        ahmed = customer('Ahmed Raza', '0300-1234567', 'ahmed.raza@example.com', '42101-1234567-1')
        bilal = customer('Bilal Traders', '0321-9876543', 'bilal.traders@example.com', '35202-7654321-3')
        sana = customer('Sana Malik', '0333-4567890', 'sana.malik@example.com', '61101-2345678-9')

        client = APIClient()

        def as_user(user):
            client.force_authenticate(user=user)
            return client

        def imeis(prefix, count):
            return [f'35{prefix}{i:09d}' for i in range(1, count + 1)]

        self.stdout.write('Recording vendor invoices and receiving stock...')

        # 1. M&P Distributor -> 5x iPhone 15 (fully received)
        as_user(warehouse_user)
        resp = client.post('/api/purchase/vendor-invoice/', {
            'supplier_id': mnp.id,
            'supplier_invoice_number': 'MNP-2026-0091',
            'items': [{'product_id': iphone15.id, 'unit_price': '650.00', 'expected_quantity': 5}],
        }, format='json')
        bill_id = resp.data['bill_id']
        item_id = resp.data['items'][0]['bill_item_id']
        client.post(f'/api/purchase/bills/{bill_id}/receive-items/', {
            'warehouse_id': warehouse.id,
            'items': [{'bill_item_id': item_id, 'codes': imeis('9001', 5)}],
        }, format='json')
        client.post(f'/api/purchase/bills/{bill_id}/confirm-received/', {'receipt_notes': 'Checked against packing slip.'}, format='json')

        # 2. Gnext Trading -> 8x Redmi Note 13 + 30x cases + 20x chargers (fully received)
        resp = client.post('/api/purchase/vendor-invoice/', {
            'supplier_id': gnext.id,
            'supplier_invoice_number': 'GNX-2026-0234',
            'items': [
                {'product_id': redmi.id, 'unit_price': '180.00', 'expected_quantity': 8},
                {'product_id': phone_case.id, 'unit_price': '3.00', 'expected_quantity': 30},
                {'product_id': charger.id, 'unit_price': '8.00', 'expected_quantity': 20},
            ],
        }, format='json')
        bill_id = resp.data['bill_id']
        items = {it['product_id']: it['bill_item_id'] for it in resp.data['items']}
        client.post(f'/api/purchase/bills/{bill_id}/receive-items/', {
            'warehouse_id': warehouse.id,
            'items': [
                {'bill_item_id': items[redmi.id], 'codes': imeis('9002', 8)},
                {'bill_item_id': items[phone_case.id], 'quantity': 30},
                {'bill_item_id': items[charger.id], 'quantity': 20},
            ],
        }, format='json')
        client.post(f'/api/purchase/bills/{bill_id}/confirm-received/', {}, format='json')

        # 3. Restock existing Galaxy S24 + Earbuds via Electronics Supply Co. (fully received)
        if phone_s24 and earbuds and electronics_supply:
            resp = client.post('/api/purchase/vendor-invoice/', {
                'supplier_id': electronics_supply.id,
                'supplier_invoice_number': 'ESC-2026-0567',
                'items': [
                    {'product_id': phone_s24.id, 'unit_price': '700.00', 'expected_quantity': 6},
                    {'product_id': earbuds.id, 'unit_price': '25.00', 'expected_quantity': 25},
                ],
            }, format='json')
            bill_id = resp.data['bill_id']
            items = {it['product_id']: it['bill_item_id'] for it in resp.data['items']}
            client.post(f'/api/purchase/bills/{bill_id}/receive-items/', {
                'warehouse_id': warehouse.id,
                'items': [
                    {'bill_item_id': items[phone_s24.id], 'codes': imeis('9003', 6)},
                    {'bill_item_id': items[earbuds.id], 'quantity': 25},
                ],
            }, format='json')
            client.post(f'/api/purchase/bills/{bill_id}/confirm-received/', {}, format='json')

        # 4. Electronics Supply Co. -> 4x Galaxy A15 + 15x Power Bank - LEFT PENDING (not received yet)
        client.post('/api/purchase/vendor-invoice/', {
            'supplier_id': (electronics_supply or mnp).id,
            'supplier_invoice_number': 'ESC-2026-0611',
            'items': [
                {'product_id': galaxy_a15.id, 'unit_price': '140.00', 'expected_quantity': 4},
                {'product_id': powerbank.id, 'unit_price': '15.00', 'expected_quantity': 15},
            ],
        }, format='json')

        self.stdout.write('Recording a partial payment to M&P Distributor...')
        as_user(manager)
        client.post('/api/purchase/purchase-payments/', {
            'supplier': mnp.id, 'amount': '1625.00', 'payment_method': 'bank_transfer',
            'payment_date': timezone.now().date().isoformat(), 'reference_number': 'TXN-88213',
        }, format='json')

        self.stdout.write('Running POS sales...')

        def tracking_id_for(product, imei):
            from products.models import ProductTracking
            unit = ProductTracking.objects.get(product=product, imei_number=imei)
            return unit.id

        as_user(cashier)
        # Sale 1: iPhone to Ahmed Raza, partial payment (creates outstanding balance)
        iphone_imei = imeis('9001', 5)[0]
        client.post('/api/sales/pos/checkout/', {
            'customer_id': ahmed.id,
            'items': [{'product_id': iphone15.id, 'tracking_id': tracking_id_for(iphone15, iphone_imei)}],
            'payment': {'method': 'cash', 'amount': '500.00'},
        }, format='json')

        # Sale 2: Galaxy S24 to walk-in, fully paid
        if phone_s24:
            s24_imei = imeis('9003', 6)[0]
            client.post('/api/sales/pos/checkout/', {
                'items': [{'product_id': phone_s24.id, 'tracking_id': tracking_id_for(phone_s24, s24_imei)}],
                'payment': {'method': 'cash', 'amount': '900.00'},
            }, format='json')

        as_user(salesman)
        # Sale 3: accessories to Bilal Traders, fully paid
        client.post('/api/sales/pos/checkout/', {
            'customer_id': bilal.id,
            'items': [
                {'product_id': phone_case.id, 'quantity': 2, 'unit_price': '8.00'},
                {'product_id': charger.id, 'quantity': 1, 'unit_price': '15.00'},
            ],
            'payment': {'method': 'cash', 'amount': '31.00'},
        }, format='json')

        # Sale 4: Redmi to Sana Malik, fully paid
        redmi_imei = imeis('9002', 8)[0]
        client.post('/api/sales/pos/checkout/', {
            'customer_id': sana.id,
            'items': [{'product_id': redmi.id, 'tracking_id': tracking_id_for(redmi, redmi_imei)}],
            'payment': {'method': 'online', 'amount': '250.00'},
        }, format='json')

        self.stdout.write('Recording shop expenses...')
        as_user(manager)
        for category, amount, desc, method in [
            ('rent', '50000.00', 'Shop rent - August', 'bank_transfer'),
            ('utilities', '8000.00', 'Electricity bill', 'cash'),
            ('petrol', '3000.00', 'Delivery bike fuel', 'cash'),
            ('salary', '40000.00', 'Salesman salary - August', 'bank_transfer'),
        ]:
            client.post('/api/accounting/expenses/', {
                'category': category, 'amount': amount, 'description': desc,
                'payment_method': method, 'expense_date': timezone.now().date().isoformat(),
            }, format='json')

        self.stdout.write(self.style.SUCCESS('\nShop demo data seeded successfully.\n'))
        self.stdout.write('Login credentials (all @techcorp.com):')
        self.stdout.write('  Owner     : admin@techcorp.com / admin123')
        self.stdout.write('  Manager   : finance@techcorp.com / finance123')
        self.stdout.write('  Cashier   : sales@techcorp.com / sales123')
        self.stdout.write('  Salesman  : salesman@techcorp.com / salesman123')
        self.stdout.write('  Warehouse : inventory@techcorp.com / inventory123')
        self.stdout.write('\nFrontend: http://localhost:3000  |  Backend: http://127.0.0.1:8000')
