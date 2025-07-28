from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
import random

# Import all models based on your schema
from user_auth.models import Company, User, Role, ActivityLog
from crm.models import Customer, Partner
from products.models import Product, ProductCategory, ProductVariant, Attribute, AttributeValue, ProductAttribute, ProductTracking
from inventory.models import Warehouse, StockItem, StockMovement, StockLot, StockReservation
from accounting.models import Account, AccountCategory, AccountGroup, JournalEntry, JournalItem
from purchase.models import (
    Supplier, UnitOfMeasure, PurchaseRequisition, PurchaseRequisitionItem,
    RequestForQuotation, RFQItem, SupplierQuotation, SupplierQuotationItem,
    PurchaseOrder, PurchaseOrderItem, GoodsReceiptNote, GRNItem, GRNItemTracking,
    Bill, BillItem, PurchasePayment, PurchaseReturn, PurchaseReturnItem,
    QualityInspection, QualityInspectionResult, PurchaseApproval, TaxChargesTemplate
)
from sales.models import Product as SalesProduct, SalesOrder, SalesOrderItem, Invoice, Payment, Quotation, QuotationItem, Tax
from hr.models import Employee, Payroll, Leave, Attendance
from manufacturing.models import BillOfMaterials, BillOfMaterialsItem, WorkOrder, Subcontractor, SubcontractWorkOrder
from project_mgmt.models import Project, Task, TimeEntry, ProjectContractor, ProjectReport

class Command(BaseCommand):
    help = 'Seed the ERP database with comprehensive demo data for all modules.'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting ERP database seeding...')
        
        # ===============================
        # 1. COMPANY & AUTHENTICATION
        # ===============================
        self.stdout.write('Creating company and user authentication data...')
        
        # Companies
        company1, _ = Company.objects.get_or_create(
            name='TechCorp Solutions Ltd.',
            defaults={
                'address': '123 Business District, Tech City, TC 12345',
                'is_active': True
            }
        )
        
        company2, _ = Company.objects.get_or_create(
            name='Manufacturing Industries Inc.',
            defaults={
                'address': '456 Industrial Avenue, Factory Town, FT 67890',
                'is_active': True
            }
        )
        
        # Roles
        admin_role, _ = Role.objects.get_or_create(
            name='System Administrator',
            defaults={'description': 'Full system access', 'department': 'IT', 'level': 1, 'is_active': True}
        )
        
        finance_manager_role, _ = Role.objects.get_or_create(
            name='Finance Manager',
            defaults={'description': 'Financial operations management', 'department': 'Finance', 'level': 2, 'is_active': True}
        )
        
        purchase_manager_role, _ = Role.objects.get_or_create(
            name='Purchase Manager',
            defaults={'description': 'Procurement and purchasing', 'department': 'Purchase', 'level': 2, 'is_active': True}
        )
        
        sales_manager_role, _ = Role.objects.get_or_create(
            name='Sales Manager',
            defaults={'description': 'Sales operations management', 'department': 'Sales', 'level': 2, 'is_active': True}
        )
        
        inventory_manager_role, _ = Role.objects.get_or_create(
            name='Inventory Manager',
            defaults={'description': 'Inventory and warehouse management', 'department': 'Inventory', 'level': 2, 'is_active': True}
        )
        
        hr_manager_role, _ = Role.objects.get_or_create(
            name='HR Manager',
            defaults={'description': 'Human resources management', 'department': 'HR', 'level': 2, 'is_active': True}
        )
        
        production_manager_role, _ = Role.objects.get_or_create(
            name='Production Manager',
            defaults={'description': 'Manufacturing operations', 'department': 'Production', 'level': 2, 'is_active': True}
        )
        
        project_manager_role, _ = Role.objects.get_or_create(
            name='Project Manager',
            defaults={'description': 'Project management and coordination', 'department': 'Projects', 'level': 2, 'is_active': True}
        )
        
        # Users
        admin_user, _ = User.objects.get_or_create(
            email='admin@techcorp.com',
            defaults={
                'first_name': 'System',
                'last_name': 'Administrator',
                'company': company1,
                'role': admin_role,
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
                'password': make_password('admin123')
            }
        )
        
        finance_user, _ = User.objects.get_or_create(
            email='finance@techcorp.com',
            defaults={
                'first_name': 'Sarah',
                'last_name': 'Johnson',
                'company': company1,
                'role': finance_manager_role,
                'is_active': True,
                'password': make_password('finance123')
            }
        )
        
        purchase_user, _ = User.objects.get_or_create(
            email='purchase@techcorp.com',
            defaults={
                'first_name': 'Michael',
                'last_name': 'Chen',
                'company': company1,
                'role': purchase_manager_role,
                'is_active': True,
                'password': make_password('purchase123')
            }
        )
        
        sales_user, _ = User.objects.get_or_create(
            email='sales@techcorp.com',
            defaults={
                'first_name': 'Emma',
                'last_name': 'Davis',
                'company': company1,
                'role': sales_manager_role,
                'is_active': True,
                'password': make_password('sales123')
            }
        )
        
        inventory_user, _ = User.objects.get_or_create(
            email='inventory@techcorp.com',
            defaults={
                'first_name': 'David',
                'last_name': 'Wilson',
                'company': company1,
                'role': inventory_manager_role,
                'is_active': True,
                'password': make_password('inventory123')
            }
        )
        
        hr_user, _ = User.objects.get_or_create(
            email='hr@techcorp.com',
            defaults={
                'first_name': 'Lisa',
                'last_name': 'Rodriguez',
                'company': company1,
                'role': hr_manager_role,
                'is_active': True,
                'password': make_password('hr123')
            }
        )
        
        production_user, _ = User.objects.get_or_create(
            email='production@techcorp.com',
            defaults={
                'first_name': 'James',
                'last_name': 'Thompson',
                'company': company1,
                'role': production_manager_role,
                'is_active': True,
                'password': make_password('production123')
            }
        )
        
        project_user, _ = User.objects.get_or_create(
            email='projects@techcorp.com',
            defaults={
                'first_name': 'Rachel',
                'last_name': 'Brown',
                'company': company1,
                'role': project_manager_role,
                'is_active': True,
                'password': make_password('projects123')
            }
        )
        
        # ===============================
        # 2. CHART OF ACCOUNTS
        # ===============================
        self.stdout.write('Creating chart of accounts...')
        
        # Account Categories
        asset_cat, _ = AccountCategory.objects.get_or_create(
            company=company1, code='1', name='Assets',
            defaults={'description': 'Asset accounts', 'is_active': True}
        )
        
        liability_cat, _ = AccountCategory.objects.get_or_create(
            company=company1, code='2', name='Liabilities',
            defaults={'description': 'Liability accounts', 'is_active': True}
        )
        
        equity_cat, _ = AccountCategory.objects.get_or_create(
            company=company1, code='3', name='Equity',
            defaults={'description': 'Equity accounts', 'is_active': True}
        )
        
        income_cat, _ = AccountCategory.objects.get_or_create(
            company=company1, code='4', name='Income',
            defaults={'description': 'Income accounts', 'is_active': True}
        )
        
        expense_cat, _ = AccountCategory.objects.get_or_create(
            company=company1, code='5', name='Expenses',
            defaults={'description': 'Expense accounts', 'is_active': True}
        )
        
        # Account Groups
        cash_group, _ = AccountGroup.objects.get_or_create(
            company=company1, category=asset_cat, code='1.1', name='Cash & Bank',
            defaults={'description': 'Cash and bank accounts', 'is_active': True}
        )
        
        ar_group, _ = AccountGroup.objects.get_or_create(
            company=company1, category=asset_cat, code='1.2', name='Accounts Receivable',
            defaults={'description': 'Customer receivables', 'is_active': True}
        )
        
        inventory_group, _ = AccountGroup.objects.get_or_create(
            company=company1, category=asset_cat, code='1.3', name='Inventory',
            defaults={'description': 'Inventory assets', 'is_active': True}
        )
        
        ap_group, _ = AccountGroup.objects.get_or_create(
            company=company1, category=liability_cat, code='2.1', name='Accounts Payable',
            defaults={'description': 'Supplier payables', 'is_active': True}
        )
        
        sales_group, _ = AccountGroup.objects.get_or_create(
            company=company1, category=income_cat, code='4.1', name='Sales Revenue',
            defaults={'description': 'Sales income', 'is_active': True}
        )
        
        expense_group, _ = AccountGroup.objects.get_or_create(
            company=company1, category=expense_cat, code='5.1', name='Operating Expenses',
            defaults={'description': 'Operating expenses', 'is_active': True}
        )
        
        # Individual Accounts
        cash_acc, _ = Account.objects.get_or_create(
            company=company1, group=cash_group, code='1.1.001', name='Cash in Hand',
            defaults={'account_type': 'asset', 'is_group': False, 'is_active': True}
        )
        
        bank_acc, _ = Account.objects.get_or_create(
            company=company1, group=cash_group, code='1.1.002', name='Bank Account - Main',
            defaults={'account_type': 'asset', 'is_group': False, 'is_active': True}
        )
        
        ar_acc, _ = Account.objects.get_or_create(
            company=company1, group=ar_group, code='1.2.001', name='Trade Receivables',
            defaults={'account_type': 'asset', 'is_group': False, 'is_active': True}
        )
        
        inventory_acc, _ = Account.objects.get_or_create(
            company=company1, group=inventory_group, code='1.3.001', name='Finished Goods',
            defaults={'account_type': 'asset', 'is_group': False, 'is_active': True}
        )
        
        ap_acc, _ = Account.objects.get_or_create(
            company=company1, group=ap_group, code='2.1.001', name='Trade Payables',
            defaults={'account_type': 'liability', 'is_group': False, 'is_active': True}
        )
        
        sales_acc, _ = Account.objects.get_or_create(
            company=company1, group=sales_group, code='4.1.001', name='Product Sales',
            defaults={'account_type': 'income', 'is_group': False, 'is_active': True}
        )
        
        cogs_acc, _ = Account.objects.get_or_create(
            company=company1, group=expense_group, code='5.1.001', name='Cost of Goods Sold',
            defaults={'account_type': 'expense', 'is_group': False, 'is_active': True}
        )
        
        salary_acc, _ = Account.objects.get_or_create(
            company=company1, group=expense_group, code='5.1.002', name='Salaries & Wages',
            defaults={'account_type': 'expense', 'is_group': False, 'is_active': True}
        )
        
        # ===============================
        # 3. UNITS OF MEASURE
        # ===============================
        self.stdout.write('Creating units of measure...')
        
        # Base UOMs
        pieces_uom, _ = UnitOfMeasure.objects.get_or_create(
            company=company1, name='Pieces',
            defaults={'abbreviation': 'Pcs', 'uom_type': 'quantity', 'is_base_unit': True, 'conversion_factor': 1}
        )
        
        kg_uom, _ = UnitOfMeasure.objects.get_or_create(
            company=company1, name='Kilogram',
            defaults={'abbreviation': 'Kg', 'uom_type': 'weight', 'is_base_unit': True, 'conversion_factor': 1}
        )
        
        liter_uom, _ = UnitOfMeasure.objects.get_or_create(
            company=company1, name='Liter',
            defaults={'abbreviation': 'L', 'uom_type': 'volume', 'is_base_unit': True, 'conversion_factor': 1}
        )
        
        meter_uom, _ = UnitOfMeasure.objects.get_or_create(
            company=company1, name='Meter',
            defaults={'abbreviation': 'M', 'uom_type': 'length', 'is_base_unit': True, 'conversion_factor': 1}
        )
        
        # ===============================
        # 4. PRODUCT MANAGEMENT
        # ===============================
        self.stdout.write('Creating product categories and products...')
        
        # Product Categories
        electronics_cat, _ = ProductCategory.objects.get_or_create(
            company=company1, name='Electronics',
            defaults={'code': 'ELEC', 'description': 'Electronic products and components'}
        )
        
        furniture_cat, _ = ProductCategory.objects.get_or_create(
            company=company1, name='Furniture',
            defaults={'code': 'FURN', 'description': 'Office and home furniture'}
        )
        
        services_cat, _ = ProductCategory.objects.get_or_create(
            company=company1, name='Services',
            defaults={'code': 'SERV', 'description': 'Service offerings'}
        )
        
        # Product Attributes
        color_attr, _ = Attribute.objects.get_or_create(
            company=company1, name='Color',
            defaults={'data_type': 'text', 'is_required': False}
        )
        
        size_attr, _ = Attribute.objects.get_or_create(
            company=company1, name='Size',
            defaults={'data_type': 'text', 'is_required': False}
        )
        
        warranty_attr, _ = Attribute.objects.get_or_create(
            company=company1, name='Warranty Period',
            defaults={'data_type': 'number', 'is_required': False}
        )
        
        # Products
        laptop_product, _ = Product.objects.get_or_create(
            company=company1, sku='LAP-001',
            defaults={
                'name': 'Business Laptop',
                'description': 'High-performance business laptop with 16GB RAM',
                'product_type': 'product',
                'category': electronics_cat,
                'unit_of_measure': 'pcs',
                'cost_price': Decimal('800.00'),
                'selling_price': Decimal('1200.00'),
                'weight': Decimal('2.5'),
                'dimensions': '35x25x2 cm',
                'is_active': True,
                'is_saleable': True,
                'is_purchasable': True,
                'is_stockable': True,
                'minimum_stock': Decimal('5'),
                'maximum_stock': Decimal('50'),
                'reorder_level': Decimal('10'),
                'created_by': admin_user,
                'tracking_method': 'serial'
            }
        )
        
        desk_product, _ = Product.objects.get_or_create(
            company=company1, sku='DESK-001',
            defaults={
                'name': 'Executive Desk',
                'description': 'Premium executive office desk with drawers',
                'product_type': 'product',
                'category': furniture_cat,
                'unit_of_measure': 'pcs',
                'cost_price': Decimal('300.00'),
                'selling_price': Decimal('450.00'),
                'weight': Decimal('45.0'),
                'dimensions': '150x80x75 cm',
                'is_active': True,
                'is_saleable': True,
                'is_purchasable': True,
                'is_stockable': True,
                'minimum_stock': Decimal('2'),
                'maximum_stock': Decimal('20'),
                'reorder_level': Decimal('5'),
                'created_by': admin_user,
                'tracking_method': 'none'
            }
        )
        
        consultation_service, _ = Product.objects.get_or_create(
            company=company1, sku='SERV-001',
            defaults={
                'name': 'IT Consultation',
                'description': 'Professional IT consultation services',
                'product_type': 'service',
                'category': services_cat,
                'unit_of_measure': 'hour',
                'cost_price': Decimal('50.00'),
                'selling_price': Decimal('100.00'),
                'is_active': True,
                'is_saleable': True,
                'is_purchasable': False,
                'is_stockable': False,
                'created_by': admin_user,
                'tracking_method': 'none'
            }
        )
        
        # ===============================
        # 5. INVENTORY & WAREHOUSES
        # ===============================
        self.stdout.write('Creating warehouses and inventory...')
        
        # Warehouses
        main_warehouse, _ = Warehouse.objects.get_or_create(
            company=company1, name='Main Warehouse',
            defaults={
                'code': 'WH-001',
                'address': '789 Storage Street, Industrial Zone',
                'manager': inventory_user,
                'is_active': True
            }
        )
        
        secondary_warehouse, _ = Warehouse.objects.get_or_create(
            company=company1, name='Secondary Warehouse',
            defaults={
                'code': 'WH-002',
                'address': '456 Backup Lane, Storage District',
                'manager': inventory_user,
                'is_active': True
            }
        )
        
        # Stock Items
        laptop_stock, _ = StockItem.objects.get_or_create(
            company=company1, product=laptop_product, warehouse=main_warehouse,
            defaults={
                'quantity': Decimal('25'),
                'available_quantity': Decimal('20'),
                'reserved_quantity': Decimal('5'),
                'average_cost': Decimal('800.00'),
                'is_active': True,
                'account': inventory_acc
            }
        )
        
        desk_stock, _ = StockItem.objects.get_or_create(
            company=company1, product=desk_product, warehouse=main_warehouse,
            defaults={
                'quantity': Decimal('15'),
                'available_quantity': Decimal('13'),
                'reserved_quantity': Decimal('2'),
                'average_cost': Decimal('300.00'),
                'is_active': True,
                'account': inventory_acc
            }
        )
        
        # ===============================
        # 6. CRM & CUSTOMERS
        # ===============================
        self.stdout.write('Creating customers and partners...')
        
        # Partners (Base entities for customers and suppliers)
        tech_partner, _ = Partner.objects.get_or_create(
            company=company1, name='TechSolutions Inc.',
            defaults={
                'partner_type': 'company',
                'email': 'contact@techsolutions.com',
                'phone': '+1-555-0123',
                'street': '123 Tech Boulevard',
                'city': 'Silicon Valley',
                'state': 'CA',
                'zip_code': '94000',
                'is_customer': True,
                'is_supplier': False,
                'created_by': sales_user
            }
        )
        
        office_partner, _ = Partner.objects.get_or_create(
            company=company1, name='OfficeMax Corp.',
            defaults={
                'partner_type': 'company',
                'email': 'orders@officemax.com',
                'phone': '+1-555-0456',
                'street': '456 Business Ave',
                'city': 'Corporate City',
                'state': 'NY',
                'zip_code': '10001',
                'is_customer': True,
                'is_supplier': False,
                'created_by': sales_user
            }
        )
        
        supplier_partner, _ = Partner.objects.get_or_create(
            company=company1, name='Electronics Supply Co.',
            defaults={
                'partner_type': 'company',
                'email': 'sales@electronicsupply.com',
                'phone': '+1-555-0789',
                'street': '789 Supply Chain St',
                'city': 'Manufacturer District',
                'state': 'TX',
                'zip_code': '75001',
                'is_customer': False,
                'is_supplier': True,
                'created_by': purchase_user
            }
        )
        
        # Customers
        customer1, _ = Customer.objects.get_or_create(
            company=company1, name='TechSolutions Inc.',
            defaults={
                'customer_code': 'CUST-001',
                'email': 'contact@techsolutions.com',
                'phone': '+1-555-0123',
                'address': '123 Tech Boulevard, Silicon Valley, CA 94000',
                'created_by': sales_user,
                'account': ar_acc,
                'partner': tech_partner
            }
        )
        
        customer2, _ = Customer.objects.get_or_create(
            company=company1, name='OfficeMax Corp.',
            defaults={
                'customer_code': 'CUST-002',
                'email': 'orders@officemax.com',
                'phone': '+1-555-0456',
                'address': '456 Business Ave, Corporate City, NY 10001',
                'created_by': sales_user,
                'account': ar_acc,
                'partner': office_partner
            }
        )
        
        # ===============================
        # 7. SUPPLIERS & PURCHASE MODULE
        # ===============================
        self.stdout.write('Creating suppliers and purchase data...')
        
        # Suppliers
        supplier1, _ = Supplier.objects.get_or_create(
            company=company1, supplier_code='SUP-001',
            defaults={
                'name': 'Electronics Supply Co.',
                'email': 'sales@electronicsupply.com',
                'phone': '+1-555-0789',
                'address': '789 Supply Chain St, Manufacturer District, TX 75001',
                'contact_person': 'John Electronics',
                'payment_terms': 'net_30',
                'credit_limit': Decimal('100000.00'),
                'delivery_lead_time': 7,
                'quality_rating': Decimal('4.5'),
                'delivery_rating': Decimal('4.2'),
                'is_active': True,
                'created_by': purchase_user,
                'partner': supplier_partner
            }
        )
        
        supplier2, _ = Supplier.objects.get_or_create(
            company=company1, supplier_code='SUP-002',
            defaults={
                'name': 'Furniture Wholesale Ltd.',
                'email': 'sales@furniturewholesale.com',
                'phone': '+1-555-0234',
                'address': '234 Furniture Row, Wood City, NC 28001',
                'contact_person': 'Sarah Furniture',
                'payment_terms': 'net_45',
                'credit_limit': Decimal('75000.00'),
                'delivery_lead_time': 14,
                'quality_rating': Decimal('4.0'),
                'delivery_rating': Decimal('3.8'),
                'is_active': True,
                'created_by': purchase_user
            }
        )
        
        # Purchase Requisitions
        pr1, _ = PurchaseRequisition.objects.get_or_create(
            company=company1, pr_number='PR-2024-001',
            defaults={
                'department': 'IT',
                'request_date': date.today() - timedelta(days=30),
                'required_date': date.today() - timedelta(days=15),
                'purpose': 'Laptop procurement for new employees',
                'status': 'approved',
                'total_estimated_cost': Decimal('20000.00'),
                'requested_by': admin_user,
                'approved_by': purchase_user,
                'approved_at': timezone.now() - timedelta(days=25),
                'warehouse': main_warehouse
            }
        )
        
        # Purchase Requisition Items
        pr_item1, _ = PurchaseRequisitionItem.objects.get_or_create(
            purchase_requisition=pr1, product=laptop_product,
            defaults={
                'quantity': Decimal('25'),
                'unit_price': Decimal('800.00'),
                'total_amount': Decimal('20000.00'),
                'specifications': 'Business grade laptop with 16GB RAM, 512GB SSD',
                'preferred_supplier': supplier1
            }
        )
        
        # Request for Quotations
        rfq1, _ = RequestForQuotation.objects.get_or_create(
            company=company1, rfq_number='RFQ-2024-001',
            defaults={
                'issue_date': date.today() - timedelta(days=20),
                'response_deadline': date.today() - timedelta(days=10),
                'terms_and_conditions': 'Standard procurement terms apply',
                'payment_terms': 'Net 30 days',
                'delivery_terms': 'FOB destination',
                'status': 'closed',
                'created_by': purchase_user,
                'purchase_requisition': pr1,
                'warehouse': main_warehouse
            }
        )
        
        rfq1.suppliers.add(supplier1)
        
        # RFQ Items
        rfq_item1, _ = RFQItem.objects.get_or_create(
            rfq=rfq1, product=laptop_product,
            defaults={
                'quantity': Decimal('25'),
                'specifications': 'Business grade laptop with 16GB RAM, 512GB SSD',
                'minimum_qty_required': Decimal('20'),
                'maximum_qty_acceptable': Decimal('30'),
                'target_unit_price': Decimal('800.00'),
                'priority': 'high',
                'required_uom': pieces_uom
            }
        )
        
        # Supplier Quotations
        quotation1, _ = SupplierQuotation.objects.get_or_create(
            company=company1, supplier=supplier1, rfq=rfq1,
            defaults={
                'quotation_number': 'QUO-2024-001',
                'quotation_date': date.today() - timedelta(days=15),
                'valid_until': date.today() + timedelta(days=30),
                'payment_terms': 'net_30',
                'delivery_terms': 'FOB destination',
                'delivery_time_days': 7,
                'total_amount': Decimal('19500.00'),
                'discount_percentage': Decimal('2.5'),
                'discount_amount': Decimal('500.00'),
                'status': 'accepted'
            }
        )
        
        # Quotation Items
        quotation_item1, _ = SupplierQuotationItem.objects.get_or_create(
            quotation=quotation1, product=laptop_product,
            defaults={
                'quantity': Decimal('25'),
                'unit_price': Decimal('800.00'),
                'base_unit_price': Decimal('800.00'),
                'total_amount': Decimal('20000.00'),
                'delivery_time_days': 7,
                'minimum_order_qty': Decimal('20'),
                'rfq_item': rfq_item1,
                'quoted_uom': pieces_uom
            }
        )
        
        # Purchase Orders
        po1, _ = PurchaseOrder.objects.get_or_create(
            company=company1, po_number='PO-2024-001',
            defaults={
                'supplier': supplier1,
                'order_date': date.today() - timedelta(days=10),
                'expected_delivery_date': date.today() + timedelta(days=7),
                'terms_conditions': 'Standard purchase terms and conditions',
                'payment_terms': 'net_30',
                'delivery_terms': 'FOB destination',
                'subtotal': Decimal('20000.00'),
                'tax_amount': Decimal('1600.00'),
                'total_amount': Decimal('21600.00'),
                'status': 'approved',
                'created_by': purchase_user,
                'approved_by': purchase_user,
                'approved_at': timezone.now() - timedelta(days=8),
                'purchase_requisition': pr1,
                'supplier_quotation': quotation1,
                'warehouse': main_warehouse
            }
        )
        
        # Purchase Order Items
        po_item1, _ = PurchaseOrderItem.objects.get_or_create(
            purchase_order=po1, product=laptop_product,
            defaults={
                'quantity': Decimal('25'),
                'unit_price': Decimal('800.00'),
                'line_total': Decimal('20000.00'),
                'delivery_date': date.today() + timedelta(days=7),
                'quotation_item': quotation_item1,
                'uom': pieces_uom
            }
        )
        
        # ===============================
        # 8. GOODS RECEIPT & QUALITY CONTROL
        # ===============================
        self.stdout.write('Creating goods receipt and quality control data...')
        
        # Goods Receipt Notes
        grn1, _ = GoodsReceiptNote.objects.get_or_create(
            company=company1, grn_number='GRN-2024-001',
            defaults={
                'supplier': supplier1,
                'purchase_order': po1,
                'received_date': timezone.now() - timedelta(days=5),
                'received_by': inventory_user,
                'supplier_delivery_note': 'DN-2024-001',
                'transporter': 'FastDelivery Logistics',
                'vehicle_number': 'TRK-1234',
                'driver_name': 'Mike Driver',
                'driver_phone': '+1-555-9999',
                'gate_entry_number': 'GE-2024-001',
                'status': 'completed',
                'requires_inspection': True,
                'warehouse': main_warehouse
            }
        )
        
        # GRN Items
        grn_item1, _ = GRNItem.objects.get_or_create(
            grn=grn1, product=laptop_product,
            defaults={
                'po_item': po_item1,
                'ordered_qty': Decimal('25'),
                'received_qty': Decimal('25'),
                'accepted_qty': Decimal('23'),
                'rejected_qty': Decimal('2'),
                'quality_status': 'passed',
                'tracking_required': True,
                'tracking_type': 'serial',
                'warehouse': main_warehouse,
                'uom': pieces_uom,
                'inspector': inventory_user,
                'inspected_at': timezone.now() - timedelta(days=4)
            }
        )
        
        # Quality Inspections
        qi1, _ = QualityInspection.objects.get_or_create(
            company=company1, inspection_number='QI-2024-001',
            defaults={
                'grn': grn1,
                'inspection_type': 'incoming',
                'assigned_to': inventory_user,
                'assigned_by': purchase_user,
                'assigned_at': timezone.now() - timedelta(days=5),
                'due_date': date.today() - timedelta(days=3),
                'status': 'completed',
                'priority': 'high',
                'inspection_criteria': 'Visual inspection, functional testing, documentation verification',
                'sampling_method': 'random',
                'sample_size': 5,
                'overall_result': 'pass',
                'pass_percentage': Decimal('92.0'),
                'started_at': timezone.now() - timedelta(days=4),
                'completed_at': timezone.now() - timedelta(days=4),
                'recommendations': 'Minor packaging damage on 2 units, rest acceptable'
            }
        )
        
        # Bills/Invoices
        bill1, _ = Bill.objects.get_or_create(
            company=company1, bill_number='BILL-2024-001',
            defaults={
                'supplier': supplier1,
                'purchase_order': po1,
                'grn': grn1,
                'supplier_invoice_number': 'INV-ELEC-2024-001',
                'bill_date': date.today() - timedelta(days=3),
                'due_date': date.today() + timedelta(days=27),
                'subtotal': Decimal('20000.00'),
                'tax_amount': Decimal('1600.00'),
                'total_amount': Decimal('21600.00'),
                'paid_amount': Decimal('0.00'),
                'outstanding_amount': Decimal('21600.00'),
                'status': 'open',
                'three_way_match_status': True,
                'created_by': finance_user
            }
        )
        
        # ===============================
        # 9. SALES MODULE
        # ===============================
        self.stdout.write('Creating sales data...')
        
        # Sales Quotations
        sales_quotation1, _ = Quotation.objects.get_or_create(
            company=company1, customer=customer1,
            defaults={
                'date': date.today() - timedelta(days=20),
                'valid_until': date.today() + timedelta(days=10),
                'total': Decimal('2700.00'),
                'status': 'accepted',
                'created_by': sales_user
            }
        )
        
        # Sales Orders
        sales_order1, _ = SalesOrder.objects.get_or_create(
            company=company1, customer=customer1,
            defaults={
                'order_date': date.today() - timedelta(days=15),
                'delivery_date': date.today() + timedelta(days=5),
                'billing_address': customer1.address,
                'shipping_address': customer1.address,
                'total': Decimal('2700.00'),
                'status': 'confirmed',
                'created_by': sales_user,
                'quotation': sales_quotation1,
                'account': ar_acc
            }
        )
        
        # Sales Order Items
        so_item1, _ = SalesOrderItem.objects.get_or_create(
            sales_order=sales_order1, product=laptop_product,
            defaults={
                'quantity': Decimal('2'),
                'price': Decimal('1200.00'),
                'total': Decimal('2400.00')
            }
        )
        
        so_item2, _ = SalesOrderItem.objects.get_or_create(
            sales_order=sales_order1, product=consultation_service,
            defaults={
                'quantity': Decimal('3'),
                'price': Decimal('100.00'),
                'total': Decimal('300.00')
            }
        )
        
        # Sales Invoices
        invoice1, _ = Invoice.objects.get_or_create(
            company=company1, customer=customer1,
            defaults={
                'sales_order': sales_order1,
                'invoice_date': date.today() - timedelta(days=10),
                'due_date': date.today() + timedelta(days=20),
                'total': Decimal('2700.00'),
                'status': 'sent',
                'created_by': sales_user,
                'account': ar_acc
            }
        )
        
        # ===============================
        # 10. HR MODULE
        # ===============================
        self.stdout.write('Creating HR data...')
        
        # Employees
        employee1, _ = Employee.objects.get_or_create(
            company=company1, employee_id='EMP-001',
            defaults={
                'first_name': 'Alice',
                'last_name': 'Johnson',
                'email': 'alice.johnson@techcorp.com',
                'phone': '+1-555-1111',
                'department': 'Information Technology',
                'position': 'Senior Developer',
                'date_joined': date.today() - timedelta(days=365),
                'salary': Decimal('75000.00'),
                'is_active': True,
                'user': admin_user
            }
        )
        
        employee2, _ = Employee.objects.get_or_create(
            company=company1, employee_id='EMP-002',
            defaults={
                'first_name': 'Bob',
                'last_name': 'Smith',
                'email': 'bob.smith@techcorp.com',
                'phone': '+1-555-2222',
                'department': 'Sales & Marketing',
                'position': 'Sales Representative',
                'date_joined': date.today() - timedelta(days=200),
                'salary': Decimal('55000.00'),
                'is_active': True,
                'user': sales_user
            }
        )
        
        # ===============================
        # 11. MANUFACTURING MODULE
        # ===============================
        self.stdout.write('Creating manufacturing data...')
        
        # Bill of Materials
        laptop_bom, _ = BillOfMaterials.objects.get_or_create(
            company=company1, product=laptop_product,
            defaults={
                'name': 'Laptop Assembly BOM',
                'version': 'v1.0',
                'created_by': production_user
            }
        )
        
        # Work Orders
        work_order1, _ = WorkOrder.objects.get_or_create(
            company=company1, product=laptop_product,
            defaults={
                'bom': laptop_bom,
                'quantity': Decimal('10'),
                'status': 'in_progress',
                'scheduled_start': date.today() - timedelta(days=5),
                'scheduled_end': date.today() + timedelta(days=5),
                'actual_start': date.today() - timedelta(days=5),
                'created_by': production_user,
                'account': inventory_acc
            }
        )
        
        # ===============================
        # 12. PROJECT MANAGEMENT
        # ===============================
        self.stdout.write('Creating project management data...')
        
        # Projects
        project1, _ = Project.objects.get_or_create(
            company=company1, project_code='PROJ-2024-001',
            defaults={
                'name': 'ERP System Implementation',
                'description': 'Complete ERP system rollout and training',
                'start_date': date.today() - timedelta(days=90),
                'end_date': date.today() + timedelta(days=30),
                'budget': Decimal('250000.00'),
                'actual_cost': Decimal('180000.00'),
                'status': 'in_progress',
                'priority': 'high',
                'created_by': project_user,
                'project_manager': employee1,
                'client': tech_partner,
                'account': cash_acc
            }
        )
        
        # Tasks
        task1, _ = Task.objects.get_or_create(
            project=project1, name='System Analysis & Design',
            defaults={
                'description': 'Analyze current processes and design new system',
                'status': 'completed',
                'priority': 'high',
                'estimated_hours': Decimal('80'),
                'actual_hours': Decimal('75'),
                'due_date': date.today() - timedelta(days=60),
                'assigned_to_employee': employee1
            }
        )
        
        task2, _ = Task.objects.get_or_create(
            project=project1, name='Data Migration',
            defaults={
                'description': 'Migrate data from legacy systems',
                'status': 'in_progress',
                'priority': 'medium',
                'estimated_hours': Decimal('120'),
                'actual_hours': Decimal('90'),
                'due_date': date.today() + timedelta(days=15),
                'assigned_to_employee': employee2
            }
        )
        
        # Time Entries
        time_entry1, _ = TimeEntry.objects.get_or_create(
            task=task1, employee=employee1,
            defaults={
                'date': date.today() - timedelta(days=1),
                'hours': Decimal('8'),
                'notes': 'Completed system requirements documentation'
            }
        )
        
        # ===============================
        # 13. ACTIVITY LOGS
        # ===============================
        self.stdout.write('Creating activity logs...')
        
        ActivityLog.objects.get_or_create(
            user=admin_user,
            defaults={
                'action': 'login',
                'details': 'User logged into the system',
                'ip_address': '192.168.1.100'
            }
        )
        
        ActivityLog.objects.get_or_create(
            user=purchase_user,
            defaults={
                'action': 'create_purchase_order',
                'details': f'Created purchase order {po1.po_number}',
                'ip_address': '192.168.1.101'
            }
        )
        
        # Final success message
        self.stdout.write(
            self.style.SUCCESS(
                'Successfully seeded ERP database with comprehensive demo data!\n'
                'Created:\n'
                '- 2 Companies with full organizational structure\n'
                '- 8 User roles and 8 users\n'
                '- Complete Chart of Accounts (Categories, Groups, Accounts)\n'
                '- Product catalog with categories, attributes, and variants\n'
                '- Inventory management (warehouses, stock items)\n'
                '- Customer and supplier relationships\n'
                '- Complete purchase cycle (PR → RFQ → PO → GRN → Bill)\n'
                '- Sales quotations, orders, and invoices\n'
                '- HR data (departments, employees)\n'
                '- Manufacturing BOMs and work orders\n'
                '- Project management with tasks and time tracking\n'
                '- Quality control and inspection workflows\n'
                '- Activity logs and audit trails\n\n'
                'Login credentials:\n'
                '- Admin: admin@techcorp.com / admin123\n'
                '- Finance: finance@techcorp.com / finance123\n'
                '- Purchase: purchase@techcorp.com / purchase123\n'
                '- Sales: sales@techcorp.com / sales123\n'
                '- Inventory: inventory@techcorp.com / inventory123\n'
                '- HR: hr@techcorp.com / hr123\n'
                '- Production: production@techcorp.com / production123\n'
                '- Projects: projects@techcorp.com / projects123'
            )
        ) 