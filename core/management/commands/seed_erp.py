from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
import random

# Import all models based on updated schema
from user_auth.models import Company, User, Role, ActivityLog
from crm.models import Customer, Partner
from products.models import Product, ProductCategory, Attribute
from inventory.models import (
    Warehouse, WarehouseZone, WarehouseBin, StockItem, StockMovement, 
    StockLot, StockReservation, StockAlert, InventoryLock, StockAdjustment, StockAdjustmentItem
)
from accounting.models import Account, AccountCategory, AccountGroup, Journal, JournalEntry, JournalItem, ModuleAccountMapping
from purchase.models import (
    Supplier, UnitOfMeasure, PurchaseRequisition, PurchaseRequisitionItem,
    RequestForQuotation, RFQItem, SupplierQuotation, SupplierQuotationItem,
    PurchaseOrder, PurchaseOrderItem, GoodsReceiptNote, GRNItem, GRNItemTracking,
    Bill, BillItem, PurchasePayment, PurchaseReturn, PurchaseReturnItem,
    QualityInspection, QualityInspectionResult, PurchaseApproval, TaxChargesTemplate,
    GRNInventoryLock
)
from sales.models import SalesOrder, SalesOrderItem, Invoice, Payment, Quotation, QuotationItem, Tax, Currency
from hr.models import Employee, Department, Designation, SalaryStructure, Payroll, Leave, Attendance
from manufacturing.models import BillOfMaterials, BillOfMaterialsItem, WorkOrder, WorkCenter, ProductionPlan, Subcontractor, SubcontractWorkOrder
from project_mgmt.models import Project, Task, TimeEntry, ProjectContractor

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
        # 2. CHART OF ACCOUNTS - Use init_coa command
        # ===============================
        self.stdout.write('Initializing chart of accounts using init_coa command...')
        
        # Call the init_coa command for each company
        from django.core.management import call_command
        
        for company in [company1, company2]:
            try:
                call_command('init_coa', '--company-id', company.id)
                self.stdout.write(f'  ✓ COA initialized for {company.name}')
            except Exception as e:
                self.stdout.write(f'  ✗ Error initializing COA for {company.name}: {e}')
        
        # Get key accounts for later use in seeding
        try:
            # Assets
            cash_acc = Account.objects.get(company=company1, code='1101')
            bank_acc = Account.objects.get(company=company1, code='1102')
            ar_acc = Account.objects.get(company=company1, code='1103')
            inventory_raw_acc = Account.objects.get(company=company1, code='1104')
            inventory_finished_acc = Account.objects.get(company=company1, code='1105')
            inventory_wip_acc = Account.objects.get(company=company1, code='1106')
            
            # Liabilities
            ap_acc = Account.objects.get(company=company1, code='2101')
            salary_payable_acc = Account.objects.get(company=company1, code='2104')
            
            # Revenue
            sales_acc = Account.objects.get(company=company1, code='4101')
            service_revenue_acc = Account.objects.get(company=company1, code='4102')
            
            # Expenses
            cogs_acc = Account.objects.get(company=company1, code='5101')
            salary_acc = Account.objects.get(company=company1, code='5201')
            
            self.stdout.write('  ✓ Key accounts retrieved for seeding')
            
        except Account.DoesNotExist as e:
            self.stdout.write(f'  ✗ Error retrieving accounts: {e}')
            # Create minimal accounts if init_coa failed
            self.stdout.write('Creating minimal account structure...')
            cash_acc, ar_acc, ap_acc, sales_acc, cogs_acc, salary_acc = self._create_minimal_accounts(company1)
            inventory_raw_acc = inventory_finished_acc = inventory_wip_acc = cash_acc  # Fallback
            bank_acc = cash_acc  # Fallback
            salary_payable_acc = ap_acc  # Fallback
            service_revenue_acc = sales_acc  # Fallback
        
        # ===============================
        # 2a. JOURNALS
        # ===============================
        self.stdout.write('Creating default journals...')
        
        # Create default journals for different types of transactions
        general_journal, _ = Journal.objects.get_or_create(
            company=company1, name='General Journal',
            defaults={'type': 'general', 'is_active': True}
        )
        
        sales_journal, _ = Journal.objects.get_or_create(
            company=company1, name='Sales Journal',
            defaults={'type': 'sales', 'is_active': True}
        )
        
        purchase_journal, _ = Journal.objects.get_or_create(
            company=company1, name='Purchase Journal',
            defaults={'type': 'purchase', 'is_active': True}
        )
        
        bank_journal, _ = Journal.objects.get_or_create(
            company=company1, name='Bank Journal',
            defaults={'type': 'bank', 'is_active': True}
        )
        
        cash_journal, _ = Journal.objects.get_or_create(
            company=company1, name='Cash Journal',
            defaults={'type': 'cash', 'is_active': True}
        )
        
        automatic_journal, _ = Journal.objects.get_or_create(
            company=company1, name='Automatic Entries',
            defaults={'type': 'general', 'is_active': True}
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
                'unit_of_measure': 'piece',
                'cost_price': Decimal('800.00'),
                'selling_price': Decimal('1200.00'),
                'weight': Decimal('2.5'),
                'dimensions': '35x25x2 cm',
                'is_active': True,
                'is_saleable': True,
                'is_purchasable': True,
                'is_manufacturable': False,
                'is_stockable': True,
                'valuation_method': 'weighted_avg',
                'auto_reorder': True,
                'lead_time_days': 7,
                'safety_stock': Decimal('5.0'),
                'requires_quality_inspection': True,
                'quality_parameters': 'Hardware functionality test, Performance benchmark',
                'tracking_method': 'serial',
                'created_by': admin_user
            }
        )
        
        desk_product, _ = Product.objects.get_or_create(
            company=company1, sku='DESK-001',
            defaults={
                'name': 'Executive Desk',
                'description': 'Premium executive office desk with drawers',
                'product_type': 'product',
                'category': furniture_cat,
                'unit_of_measure': 'piece',
                'cost_price': Decimal('300.00'),
                'selling_price': Decimal('450.00'),
                'weight': Decimal('45.0'),
                'dimensions': '150x80x75 cm',
                'is_active': True,
                'is_saleable': True,
                'is_purchasable': True,
                'is_manufacturable': False,
                'is_stockable': True,
                'valuation_method': 'fifo',
                'auto_reorder': False,
                'lead_time_days': 14,
                'safety_stock': Decimal('2.0'),
                'requires_quality_inspection': False,
                'tracking_method': 'none',
                'created_by': admin_user
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
                'is_manufacturable': False,
                'is_stockable': False,
                'valuation_method': 'standard',
                'auto_reorder': False,
                'lead_time_days': 0,
                'safety_stock': Decimal('0.0'),
                'requires_quality_inspection': False,
                'tracking_method': 'none',
                'created_by': admin_user
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
                'location': '789 Storage Street, Industrial Zone',
                'address': '789 Storage Street, Industrial Zone, Storage City, SC 12345',
                'warehouse_type': 'main',
                'manager': inventory_user,
                'is_active': True
            }
        )
        
        secondary_warehouse, _ = Warehouse.objects.get_or_create(
            company=company1, name='Secondary Warehouse',
            defaults={
                'code': 'WH-002',
                'location': '456 Backup Lane, Storage District',
                'address': '456 Backup Lane, Storage District, Backup City, BC 67890',
                'warehouse_type': 'distribution',
                'manager': inventory_user,
                'is_active': True
            }
        )
        
        # Raw Material Warehouse
        raw_material_warehouse, _ = Warehouse.objects.get_or_create(
            company=company1, name='Raw Materials Warehouse',
            defaults={
                'code': 'WH-003',
                'location': 'Raw Materials Section',
                'address': '123 Raw Materials Avenue, Component City, CC 11111',
                'warehouse_type': 'raw_material',
                'default_for_raw_material': True,
                'manager': inventory_user,
                'is_active': True
            }
        )
        
        # Stock Items with Enhanced Tracking
        laptop_stock, _ = StockItem.objects.get_or_create(
            company=company1, product=laptop_product, warehouse=main_warehouse,
            defaults={
                'category': electronics_cat,
                'quantity': Decimal('25'),
                'available_quantity': Decimal('20'),
                'reserved_quantity': Decimal('5'),
                'locked_quantity': Decimal('0'),
                'quarantine_quantity': Decimal('0'),
                'min_stock': Decimal('5'),
                'max_stock': Decimal('50'),
                'reorder_point': Decimal('10'),
                'valuation_method': 'weighted_avg',
                'average_cost': Decimal('800.00'),
                'last_purchase_cost': Decimal('800.00'),
                'stock_status': 'available',
                'purchase_status': 'ready_for_use',
                'tracking_type': 'serial',
                'suitable_for_sale': True,
                'suitable_for_manufacturing': False,
                'is_active': True,
                'account': inventory_finished_acc
            }
        )
        
        desk_stock, _ = StockItem.objects.get_or_create(
            company=company1, product=desk_product, warehouse=main_warehouse,
            defaults={
                'category': furniture_cat,
                'quantity': Decimal('15'),
                'available_quantity': Decimal('13'),
                'reserved_quantity': Decimal('2'),
                'locked_quantity': Decimal('0'),
                'quarantine_quantity': Decimal('0'),
                'min_stock': Decimal('2'),
                'max_stock': Decimal('20'),
                'reorder_point': Decimal('5'),
                'valuation_method': 'weighted_avg',
                'average_cost': Decimal('300.00'),
                'last_purchase_cost': Decimal('300.00'),
                'stock_status': 'available',
                'purchase_status': 'ready_for_use',
                'tracking_type': 'none',
                'suitable_for_sale': True,
                'suitable_for_manufacturing': False,
                'is_active': True,
                'account': inventory_finished_acc
            }
        )
        
        # Raw Material Stock Item
        raw_material_product, _ = Product.objects.get_or_create(
            company=company1, sku='RAW-001',
            defaults={
                'name': 'Electronic Components',
                'description': 'Various electronic components for laptop assembly',
                'product_type': 'raw_material',
                'category': electronics_cat,
                'unit_of_measure': 'piece',
                'cost_price': Decimal('50.00'),
                'selling_price': Decimal('0.00'),
                'is_active': True,
                'is_saleable': False,
                'is_purchasable': True,
                'is_manufacturable': False,
                'is_stockable': True,
                'valuation_method': 'fifo',
                'auto_reorder': True,
                'lead_time_days': 10,
                'safety_stock': Decimal('100.0'),
                'requires_quality_inspection': True,
                'quality_parameters': 'Visual inspection, Electrical test',
                'tracking_method': 'batch',
                'created_by': admin_user
            }
        )
        
        raw_material_stock, _ = StockItem.objects.get_or_create(
            company=company1, product=raw_material_product, warehouse=raw_material_warehouse,
            defaults={
                'category': electronics_cat,
                'quantity': Decimal('500'),
                'available_quantity': Decimal('450'),
                'reserved_quantity': Decimal('50'),
                'locked_quantity': Decimal('0'),
                'quarantine_quantity': Decimal('0'),
                'min_stock': Decimal('100'),
                'max_stock': Decimal('1000'),
                'reorder_point': Decimal('200'),
                'valuation_method': 'fifo',
                'average_cost': Decimal('50.00'),
                'last_purchase_cost': Decimal('50.00'),
                'stock_status': 'available',
                'purchase_status': 'ready_for_use',
                'tracking_type': 'batch',
                'suitable_for_sale': False,
                'suitable_for_manufacturing': True,
                'is_active': True,
                'account': inventory_raw_acc
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
                'contact_person': 'John Electronics',
                'email': 'sales@electronicsupply.com',
                'phone': '+1-555-0789',
                'street': '789 Supply Chain St',
                'city': 'Manufacturer District',
                'state': 'TX',
                'zip_code': '75001',
                'payment_terms': 'net_30',
                'credit_limit': Decimal('100000.00'),
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
                'partner': supplier_partner,
                'supplier_type': 'vendor',
                'status': 'active',
                'delivery_lead_time': 7,
                'minimum_order_value': Decimal('1000.00'),
                'preferred_shipping_method': 'ground',
                'quality_rating': Decimal('4.5'),
                'delivery_rating': Decimal('4.2'),
                'price_rating': Decimal('4.0'),
                'service_rating': Decimal('4.3'),
                'overall_rating': Decimal('4.25'),
                'is_active': True,
                'created_by': purchase_user
            }
        )
        
        # Create second supplier partner
        furniture_supplier_partner, _ = Partner.objects.get_or_create(
            company=company1, name='Furniture Wholesale Ltd.',
            defaults={
                'partner_type': 'company',
                'contact_person': 'Sarah Furniture',
                'email': 'sales@furniturewholesale.com',
                'phone': '+1-555-0234',
                'street': '234 Furniture Row',
                'city': 'Wood City',
                'state': 'NC',
                'zip_code': '28001',
                'payment_terms': 'net_45',
                'credit_limit': Decimal('75000.00'),
                'is_customer': False,
                'is_supplier': True,
                'created_by': purchase_user
            }
        )
        
        supplier2, _ = Supplier.objects.get_or_create(
            company=company1, supplier_code='SUP-002',
            defaults={
                'partner': furniture_supplier_partner,
                'supplier_type': 'vendor',
                'status': 'active',
                'delivery_lead_time': 14,
                'minimum_order_value': Decimal('500.00'),
                'preferred_shipping_method': 'ground',
                'quality_rating': Decimal('4.0'),
                'delivery_rating': Decimal('3.8'),
                'price_rating': Decimal('4.2'),
                'service_rating': Decimal('3.9'),
                'overall_rating': Decimal('4.0'),
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
        
        # Enhanced Stock Movements for GRN
        grn_stock_movement, _ = StockMovement.objects.get_or_create(
            company=company1, stock_item=laptop_stock,
            defaults={
                'movement_type': 'grn_receipt',
                'quantity': Decimal('25'),
                'unit_cost': Decimal('800.00'),
                'total_cost': Decimal('20000.00'),
                'to_warehouse': main_warehouse,
                'reference_type': 'grn',
                'reference_id': grn1.id,
                'reference_number': grn1.grn_number,
                'grn_item': grn_item1,
                'po_item': po_item1,
                'performed_by': inventory_user,
                'timestamp': timezone.now() - timedelta(days=5),
                'notes': 'Initial GRN receipt - items locked pending bill'
            }
        )
        
        # GRN Inventory Lock (using existing model)
        grn_lock, _ = GRNInventoryLock.objects.get_or_create(
            grn=grn1, grn_item=grn_item1,
            defaults={
                'locked_quantity': Decimal('23'),
                'lock_reason': 'pending_invoice',
                'locked_at': timezone.now() - timedelta(days=5),
                'locked_by': inventory_user,
                'is_active': True,
                'is_released': False,
                'lock_notes': 'Inventory locked pending supplier bill processing'
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
        
        # Create Bill Items
        bill_item1, _ = BillItem.objects.get_or_create(
            bill=bill1, product=laptop_product,
            defaults={
                'po_item': po_item1,
                'grn_item': grn_item1,
                'quantity': Decimal('23'),
                'unit_price': Decimal('800.00'),
                'line_total': Decimal('18400.00'),
                'item_source': 'grn',  # Changed from 'purchase_order' to 'grn' (max 10 chars)
                'tracking_required': True,
                'tracking_type': 'serial',
                'po_quantity_variance': Decimal('0.00'),
                'grn_quantity_variance': Decimal('0.00'),
                'is_additional_item': False,
                'notes': 'Standard laptop procurement as per PO'
            }
        )
        
        # Unlock Movement after Bill Creation
        unlock_movement, _ = StockMovement.objects.get_or_create(
            company=company1, stock_item=laptop_stock,
            defaults={
                'movement_type': 'unlock',
                'quantity': Decimal('23'),
                'unit_cost': Decimal('800.00'),
                'reference_type': 'bill',
                'reference_id': bill1.id,
                'reference_number': bill1.bill_number,
                'bill_item': bill_item1,
                'performed_by': finance_user,
                'timestamp': timezone.now() - timedelta(days=3),
                'notes': 'Inventory unlocked after bill creation - ready for use'
            }
        )
        
        # Enhanced Purchase Payment with more fields
        payment1, _ = PurchasePayment.objects.get_or_create(
            company=company1, supplier=supplier1, bill=bill1,
            defaults={
                'payment_number': 'PP-2024-001',
                'amount': Decimal('21600.00'),
                'payment_date': date.today() - timedelta(days=1),
                'expected_date': date.today() - timedelta(days=1),
                'actual_date': date.today() - timedelta(days=1),
                'payment_method': 'bank_transfer',
                'payment_type': 'full_payment',
                'reference_number': 'BT-2024-001',
                'transaction_id': 'TXN-2024-001',
                'status': 'completed',
                'currency': 'USD',
                'exchange_rate': Decimal('1.0000'),
                'base_currency_amount': Decimal('21600.00'),
                'bank_account': 'ACC-123456789',
                'beneficiary_bank': 'Electronics Supply Bank',
                'swift_code': 'ESBKUS33',
                'is_advance': False,
                'advance_adjusted': False,
                'internal_notes': 'Payment for PO-2024-001',
                'notes': 'Payment completed via wire transfer',
                'paid_by': finance_user,
                'created_by': finance_user
            }
        )
        
        # Purchase Return
        return1, _ = PurchaseReturn.objects.get_or_create(
            company=company1, supplier=supplier1, purchase_order=po1,
            defaults={
                'return_number': 'PR-2024-001',
                'return_date': date.today() - timedelta(days=2),
                'return_type': 'quality_issue',
                'reason': 'Defective units received - packaging damage',
                'total_amount': Decimal('1600.00'),
                'status': 'approved',
                'grn': grn1,
                'created_by': inventory_user,
                'approved_by': purchase_user
            }
        )
        
        # Purchase Return Items
        return_item1, _ = PurchaseReturnItem.objects.get_or_create(
            purchase_return=return1, grn_item=grn_item1,
            defaults={
                'return_quantity': Decimal('2'),
                'unit_price': Decimal('800.00'),
                'line_total': Decimal('1600.00'),
                'return_reason': 'damaged',
                'condition_at_return': 'damaged',
                'defects_description': 'Screen cracked due to poor packaging',
                'resolution_status': 'pending',
                'replacement_requested': True,
                'refund_requested': False,
                'credit_note_requested': True,
                'packed_for_return': True,
                'supplier_acknowledged': True,
                'shipped_date': date.today() - timedelta(days=1)
            }
        )
        # ===============================
        # 8a. ENHANCED INVENTORY TRACKING WITH WAREHOUSE MANAGEMENT
        # ===============================
        self.stdout.write('Creating enhanced inventory and warehouse management data...')
        
        # Import additional inventory models
        from inventory.models import (
            StockTransfer, StockTransferItem, StockSerial
        )
        
        # Warehouse Zones
        receiving_zone, _ = WarehouseZone.objects.get_or_create(
            warehouse=main_warehouse, name='Receiving Zone',
            defaults={
                'code': 'RCV',
                'description': 'Goods receiving and inspection area',
                'zone_type': 'receiving',
                'temperature_controlled': False,
                'is_active': True
            }
        )
        
        storage_zone, _ = WarehouseZone.objects.get_or_create(
            warehouse=main_warehouse, name='General Storage',
            defaults={
                'code': 'STG',
                'description': 'General storage area for finished goods',
                'zone_type': 'storage',
                'temperature_controlled': False,
                'is_active': True
            }
        )
        
        # Warehouse Bins
        bin_a1, _ = WarehouseBin.objects.get_or_create(
            warehouse=main_warehouse, code='A1-01',
            defaults={
                'name': 'Aisle A - Level 1 - Position 01',
                'zone': storage_zone,
                'aisle': 'A',
                'shelf': '1',
                'level': '01',
                'max_weight': Decimal('500.0'),
                'max_volume': Decimal('10.0'),
                'max_items': 50,
                'fifo_enabled': True,
                'fefo_enabled': False,
                'single_product_only': False,
                'barcode': 'BIN-A1-01',
                'is_active': True
            }
        )
        
        # Stock Lots for Batch Tracking
        if raw_material_stock:
            stock_lot1, _ = StockLot.objects.get_or_create(
                stock_item=raw_material_stock, lot_number='LOT-2024-001',
                defaults={
                    'batch_number': 'BATCH-EC-001',
                    'quantity': Decimal('300'),
                    'remaining_quantity': Decimal('250'),
                    'unit_cost': Decimal('50.00'),
                    'landed_cost': Decimal('52.00'),
                    'received_date': timezone.now() - timedelta(days=30),
                    'expiry_date': date.today() + timedelta(days=365),
                    'manufacturing_date': date.today() - timedelta(days=60),
                    'quality_approved': True,
                    'quality_approved_by': inventory_user,
                    'quality_approved_date': timezone.now() - timedelta(days=29),
                    'supplier': supplier1,
                    'supplier_lot_number': 'SUP-LOT-001',
                    'country_of_origin': 'Taiwan',
                    'certification_details': 'CE, RoHS compliant',
                    'is_active': True
                }
            )
            
            stock_lot2, _ = StockLot.objects.get_or_create(
                stock_item=raw_material_stock, lot_number='LOT-2024-002',
                defaults={
                    'batch_number': 'BATCH-EC-002',
                    'quantity': Decimal('200'),
                    'remaining_quantity': Decimal('200'),
                    'unit_cost': Decimal('50.00'),
                    'landed_cost': Decimal('51.50'),
                    'received_date': timezone.now() - timedelta(days=15),
                    'expiry_date': date.today() + timedelta(days=365),
                    'manufacturing_date': date.today() - timedelta(days=45),
                    'quality_approved': True,
                    'quality_approved_by': inventory_user,
                    'quality_approved_date': timezone.now() - timedelta(days=14),
                    'supplier': supplier1,
                    'supplier_lot_number': 'SUP-LOT-002',
                    'country_of_origin': 'Taiwan',
                    'certification_details': 'CE, RoHS compliant',
                    'is_active': True
                }
            )
        
        # Stock Serial Numbers for Individual Tracking
        stock_serial1, _ = StockSerial.objects.get_or_create(
            stock_item=laptop_stock, serial_number='LAP-SN-001',
            defaults={
                'status': 'available',
                'received_date': timezone.now() - timedelta(days=10),
                'warranty_start_date': date.today() - timedelta(days=10),
                'warranty_end_date': date.today() + timedelta(days=1095),  # 3 years
                'warranty_terms': '3-year manufacturer warranty',
                'lot': stock_lot1
            }
        )
        
        stock_serial2, _ = StockSerial.objects.get_or_create(
            stock_item=laptop_stock, serial_number='LAP-SN-002',
            defaults={
                'status': 'reserved',
                'received_date': timezone.now() - timedelta(days=10),
                'warranty_start_date': date.today() - timedelta(days=10),
                'warranty_end_date': date.today() + timedelta(days=1095),
                'warranty_terms': '3-year manufacturer warranty',
                'customer': tech_partner,
                'lot': stock_lot1
            }
        )
        
        # Stock Reservations
        stock_reservation1, _ = StockReservation.objects.get_or_create(
            stock_item=laptop_stock,
            defaults={
                'quantity': Decimal('5'),
                'reservation_type': 'sales_order',
                'reference_number': 'SO-2024-001',
                'reserved_by': sales_user,
                'reserved_at': timezone.now() - timedelta(days=2),
                'expires_at': timezone.now() + timedelta(days=28),
                'customer': tech_partner,
                'priority': 2,
                'remaining_quantity': Decimal('3'),
                'fulfilled_quantity': Decimal('2'),
                'is_fulfilled': False,
                'notes': 'Reserved for upcoming customer order',
                'is_active': True
            }
        )
        
        # Stock Transfers
        stock_transfer1, _ = StockTransfer.objects.get_or_create(
            company=company1, transfer_number='ST-2024-001',
            defaults={
                'from_warehouse': main_warehouse,
                'to_warehouse': secondary_warehouse,
                'transfer_date': date.today() - timedelta(days=5),
                'status': 'completed',
                'expected_arrival': timezone.now() - timedelta(days=4),
                'sent_at': timezone.now() - timedelta(days=5),
                'received_at': timezone.now() - timedelta(days=4),
                'reason': 'Stock rebalancing between warehouses',
                'priority': 2,
                'carrier': 'Internal Transport',
                'tracking_number': 'INT-TRK-001',
                'shipping_cost': Decimal('150.00'),
                'notes': 'Routine stock transfer',
                'created_by': inventory_user,
                'sent_by': inventory_user,
                'received_by': inventory_user
            }
        )
        
        # Stock Transfer Items
        transfer_item1, _ = StockTransferItem.objects.get_or_create(
            transfer=stock_transfer1, product=desk_product,
            defaults={
                'requested_quantity': Decimal('5'),
                'sent_quantity': Decimal('5'),
                'received_quantity': Decimal('5'),
                'lot_number': 'DESK-LOT-001',
                'notes': 'Transfer completed successfully'
            }
        )
        
        # Stock Alerts
        low_stock_alert, _ = StockAlert.objects.get_or_create(
            company=company1, stock_item=desk_stock,
            defaults={
                'alert_type': 'low_stock',
                'severity': 'medium',
                'current_quantity': Decimal('15'),
                'threshold_quantity': Decimal('20'),
                'message': 'Desk stock is running low',
                'detailed_message': 'Executive Desk stock level is below recommended threshold',
                'warehouse': main_warehouse,
                'triggered_at': timezone.now() - timedelta(hours=6),
                'resolved': False,
                'auto_resolvable': True,
                'auto_resolved': False,
                'email_sent': True,
                'notification_sent': True
            }
        )
        
        # Stock Adjustments
        stock_adjustment1, _ = StockAdjustment.objects.get_or_create(
            company=company1, adjustment_number='SA-2024-001',
            defaults={
                'adjustment_date': date.today() - timedelta(days=7),
                'adjustment_type': 'physical_count',
                'status': 'posted',
                'reason': 'Monthly physical inventory count adjustment',
                'reference_document': 'Physical Count Report Jan 2024',
                'total_adjustment_value': Decimal('-125.00'),
                'posting_required': True,
                'posted_to_accounts': True,
                'posted_at': timezone.now() - timedelta(days=5),
                'notes': 'Adjustments based on physical inventory count',
                'created_by': inventory_user,
                'approved_by': admin_user,
                'posted_by': finance_user
            }
        )
        
        # Stock Adjustment Items
        adjustment_item1, _ = StockAdjustmentItem.objects.get_or_create(
            adjustment=stock_adjustment1, stock_item=desk_stock,
            defaults={
                'book_quantity': Decimal('17'),
                'physical_quantity': Decimal('15'),
                'adjustment_quantity': Decimal('-2'),
                'unit_cost': Decimal('300.00'),
                'adjustment_value': Decimal('-600.00'),
                'reason': 'Physical count variance',
                'count_date': timezone.now() - timedelta(days=7),
                'counted_by': inventory_user,
                'notes': 'Two units not found during physical count'
            }
        )
        
        # Enhanced Inventory Locks
        inventory_lock1, _ = InventoryLock.objects.get_or_create(
            stock_item=laptop_stock, locked_by=inventory_user,
            defaults={
                'locked_quantity': Decimal('5'),
                'lock_type': 'quality_hold',
                'reference_type': 'quality_inspection',
                'reference_id': 1,
                'reference_number': 'QI-2024-001',
                'locked_at': timezone.now() - timedelta(days=3),
                'expires_at': timezone.now() + timedelta(days=4),
                'is_active': True,
                'reason': 'Quality inspection pending',
                'notes': 'Items locked pending quality clearance',
                'auto_unlock_on_quality_pass': True,
                'priority': 1,
                'requires_approval_to_unlock': True
            }
        )
        
        # Quality passed movement for raw materials
        quality_movement, _ = StockMovement.objects.get_or_create(
            company=company1, stock_item=raw_material_stock,
            defaults={
                'movement_type': 'quality_pass',
                'quantity': Decimal('500'),
                'unit_cost': Decimal('50.00'),
                'total_cost': Decimal('25000.00'),
                'to_warehouse': raw_material_warehouse,
                'reference_type': 'quality_inspection',
                'reference_number': 'QI-RAW-001',
                'quality_status': 'passed',
                'performed_by': inventory_user,
                'timestamp': timezone.now() - timedelta(days=29),
                'lot_number': 'LOT-2024-001',
                'batch_number': 'BATCH-EC-001',
                'tracking_number': 'TRK-QP-001',
                'posting_required': True,
                'posted_to_accounts': True,
                'posting_date': timezone.now() - timedelta(days=28),
                'notes': 'Raw materials passed quality inspection and moved to warehouse'
            }
        )
        
        # ===============================
        # 9. ENHANCED SALES MODULE
        # ===============================
        self.stdout.write('Creating enhanced sales data...')
        
        # Import additional sales models
        from sales.models import (
            DeliveryNote, DeliveryNoteItem, CreditNote, PriceList, PriceListItem,
            SalesCommission, SalesOrderDiscount, SalesOrderItemTracking
        )
        
        # Currencies
        usd_currency, _ = Currency.objects.get_or_create(
            company=company1, code='USD',
            defaults={
                'name': 'US Dollar',
                'symbol': '$',
                'exchange_rate': Decimal('1.0000'),
                'is_base_currency': True,
                'is_active': True
            }
        )
        
        eur_currency, _ = Currency.objects.get_or_create(
            company=company1, code='EUR',
            defaults={
                'name': 'Euro',
                'symbol': '€',
                'exchange_rate': Decimal('0.8500'),
                'is_base_currency': False,
                'is_active': True
            }
        )
        
        # Price Lists
        standard_pricelist, _ = PriceList.objects.get_or_create(
            company=company1, name='Standard Price List',
            defaults={
                'currency': usd_currency,
                'valid_from': date.today() - timedelta(days=30),
                'valid_until': date.today() + timedelta(days=365),
                'is_default': True,
                'is_active': True
            }
        )
        
        # Price List Items
        laptop_price_item, _ = PriceListItem.objects.get_or_create(
            price_list=standard_pricelist, product=laptop_product,
            defaults={
                'price': Decimal('1200.00'),
                'min_quantity': Decimal('1')
            }
        )
        
        # Sales Quotations
        sales_quotation1, _ = Quotation.objects.get_or_create(
            company=company1, customer=customer1,
            defaults={
                'quotation_number': 'QUO-2024-001',
                'date': date.today() - timedelta(days=20),
                'valid_until': date.today() + timedelta(days=10),
                'currency': usd_currency,
                'exchange_rate': Decimal('1.0000'),
                'subtotal': Decimal('2400.00'),
                'tax_amount': Decimal('240.00'),
                'discount_amount': Decimal('0.00'),
                'shipping_amount': Decimal('60.00'),
                'total': Decimal('2700.00'),
                'status': 'accepted',
                'terms_and_conditions': 'Standard terms apply',
                'lead_source': 'website',
                'created_by': sales_user
            }
        )
        
        # Quotation Items
        quote_item1, _ = QuotationItem.objects.get_or_create(
            quotation=sales_quotation1, product=laptop_product,
            defaults={
                'quantity': Decimal('2'),
                'unit_price': Decimal('1200.00'),
                'description': 'Business Laptop - High Performance',
                'discount_percent': Decimal('0.00'),
                'discount_amount': Decimal('0.00'),
                'tax_amount': Decimal('240.00'),
                'line_total': Decimal('2400.00'),
                'delivery_date': date.today() + timedelta(days=7)
            }
        )
        
        # Sales Orders
        sales_order1, _ = SalesOrder.objects.get_or_create(
            company=company1, customer=customer1,
            defaults={
                'order_number': 'SO-2024-001',
                'order_date': date.today() - timedelta(days=15),
                'delivery_date': date.today() + timedelta(days=5),
                'billing_address': customer1.address,
                'shipping_address': customer1.address,
                'currency': usd_currency,
                'exchange_rate': Decimal('1.0000'),
                'subtotal': Decimal('2400.00'),
                'tax_amount': Decimal('240.00'),
                'discount_amount': Decimal('0.00'),
                'shipping_amount': Decimal('60.00'),
                'total': Decimal('2700.00'),
                'status': 'confirmed',
                'confirmation_date': date.today() - timedelta(days=14),
                'quotation': sales_quotation1,
                'account': ar_acc,
                'sales_person': sales_user,
                'created_by': sales_user,
                'terms_and_conditions': 'Net 30 payment terms',
                'project': 'Internal Systems Upgrade'
            }
        )
        
        # Sales Order Items
        so_item1, _ = SalesOrderItem.objects.get_or_create(
            sales_order=sales_order1, product=laptop_product,
            defaults={
                'quantity': Decimal('2'),
                'unit_price': Decimal('1200.00'),
                'description': 'Business Laptop - High Performance',
                'discount_type': 'percent',
                'discount_value': Decimal('0.00'),
                'discount_amount': Decimal('0.00'),
                'tax_amount': Decimal('240.00'),
                'line_total': Decimal('2400.00'),
                'delivery_date': date.today() + timedelta(days=5),
                'tracking_required': True,
                'tracking_data': [
                    {'serial_number': 'LAP001', 'quantity': 1},
                    {'serial_number': 'LAP002', 'quantity': 1}
                ],
                'uom': 'piece'
            }
        )
        
        so_item2, _ = SalesOrderItem.objects.get_or_create(
            sales_order=sales_order1, product=consultation_service,
            defaults={
                'quantity': Decimal('3'),
                'unit_price': Decimal('100.00'),
                'description': 'IT Consultation Services',
                'discount_type': 'percent',
                'discount_value': Decimal('0.00'),
                'discount_amount': Decimal('0.00'),
                'tax_amount': Decimal('0.00'),
                'line_total': Decimal('300.00'),
                'delivery_date': date.today() + timedelta(days=3),
                'tracking_required': False,
                'uom': 'hour'
            }
        )
        
        # Delivery Notes
        delivery_note1, _ = DeliveryNote.objects.get_or_create(
            company=company1, customer=customer1, sales_order=sales_order1,
            defaults={
                'delivery_number': 'DN-2024-001',
                'delivery_date': date.today() - timedelta(days=5),
                'expected_delivery_date': date.today() - timedelta(days=5),
                'warehouse': main_warehouse.name,
                'delivery_address': customer1.address,
                'transporter_name': 'FastDelivery Logistics',
                'vehicle_number': 'TRK-5678',
                'driver_name': 'John Delivery',
                'driver_contact': '+1-555-8888',
                'tracking_number': 'TRK2024001',
                'status': 'delivered',
                'received_by': 'Customer Representative',
                'delivered_by': sales_user,
                'notes': 'Delivery completed successfully'
            }
        )
        
        # Delivery Note Items
        dn_item1, _ = DeliveryNoteItem.objects.get_or_create(
            delivery_note=delivery_note1, product=laptop_product, sales_order_item=so_item1,
            defaults={
                'quantity_ordered': Decimal('2'),
                'quantity_delivered': Decimal('2'),
                'serial_numbers': 'LAP001, LAP002',
                'quality_checked': True,
                'quality_notes': 'All items passed quality check'
            }
        )
        
        # Sales Invoices
        invoice1, _ = Invoice.objects.get_or_create(
            company=company1, customer=customer1,
            defaults={
                'invoice_number': 'INV-2024-001',
                'sales_order': sales_order1,
                'delivery_note': delivery_note1,
                'invoice_date': date.today() - timedelta(days=10),
                'due_date': date.today() + timedelta(days=20),
                'currency': usd_currency,
                'exchange_rate': Decimal('1.0000'),
                'billing_address': customer1.address,
                'shipping_address': customer1.address,
                'subtotal': Decimal('2700.00'),
                'tax_amount': Decimal('216.00'),
                'discount_amount': Decimal('0.00'),
                'shipping_amount': Decimal('60.00'),
                'total': Decimal('2976.00'),
                'paid_amount': Decimal('0.00'),
                'status': 'sent',
                'payment_terms': 'Net 30',
                'terms_and_conditions': 'Standard payment terms apply',
                'created_by': sales_user,
                'account': ar_acc
            }
        )
        
        # Sales Payments
        payment1, _ = Payment.objects.get_or_create(
            company=company1, customer=customer1, invoice=invoice1,
            defaults={
                'payment_number': 'PAY-2024-001',
                'amount': Decimal('2976.00'),
                'payment_date': date.today() - timedelta(days=5),
                'method': 'bank_transfer',
                'reference': 'BT20240001',
                'currency': usd_currency,
                'exchange_rate': Decimal('1.0000'),
                'notes': 'Payment for invoice INV-2024-001',
                'received_by': finance_user,
                'processed_by': finance_user
            }
        )
        
        # Sales Commission
        commission1, _ = SalesCommission.objects.get_or_create(
            company=company1, invoice=invoice1, sales_person=sales_user,
            defaults={
                'commission_rate': Decimal('5.0'),
                'calculation_base': Decimal('2976.00'),
                'commission_amount': Decimal('148.80'),
                'is_paid': False,
                'notes': 'Commission for Q1 2024 sales'
            }
        )
        
        # ===============================
        # 10. ENHANCED HR MODULE
        # ===============================
        self.stdout.write('Creating enhanced HR data...')
        
        # Import additional HR models
        from hr.models import (
            LeaveType, EmployeeLeaveBalance, PayrollPeriod, 
            ShiftType, Training, TrainingEnrollment, PerformanceAppraisal,
            ExitInterview, HRPolicy, JobVacancy, JobApplication
        )
        
        # Leave Types
        annual_leave, _ = LeaveType.objects.get_or_create(
            company=company1, name='Annual Leave',
            defaults={
                'code': 'AL',
                'annual_entitlement': Decimal('21.0'),
                'carry_forward_allowed': True,
                'max_carry_forward': Decimal('5.0'),
                'encashment_allowed': True,
                'requires_approval': True,
                'advance_notice_days': 7,
                'is_paid': True,
                'description': 'Annual vacation leave',
                'is_active': True
            }
        )
        
        sick_leave, _ = LeaveType.objects.get_or_create(
            company=company1, name='Sick Leave',
            defaults={
                'code': 'SL',
                'annual_entitlement': Decimal('10.0'),
                'carry_forward_allowed': False,
                'max_carry_forward': Decimal('0.0'),
                'encashment_allowed': False,
                'requires_approval': False,
                'advance_notice_days': 0,
                'is_paid': True,
                'description': 'Medical sick leave',
                'is_active': True
            }
        )
        
        # Shift Types
        day_shift, _ = ShiftType.objects.get_or_create(
            company=company1, name='Day Shift',
            defaults={
                'start_time': '09:00:00',
                'end_time': '17:00:00',
                'break_duration': '01:00:00',
                'grace_period': '00:15:00',
                'working_hours': Decimal('8.0'),
                'is_active': True
            }
        )
        
        # Payroll Periods
        payroll_period, _ = PayrollPeriod.objects.get_or_create(
            company=company1, name='January 2024',
            defaults={
                'start_date': date(2024, 1, 1),
                'end_date': date(2024, 1, 31),
                'pay_date': date(2024, 2, 5),
                'status': 'processed',
                'created_by': hr_user
            }
        )
        
        # Departments
        it_dept, _ = Department.objects.get_or_create(
            company=company1, name='Information Technology',
            defaults={
                'code': 'IT',
                'description': 'Information Technology Department',
                'budget': Decimal('500000.00'),
                'is_active': True
            }
        )
        
        sales_dept, _ = Department.objects.get_or_create(
            company=company1, name='Sales & Marketing',
            defaults={
                'code': 'SALES',
                'description': 'Sales and Marketing Department',
                'budget': Decimal('300000.00'),
                'is_active': True
            }
        )
        
        hr_dept, _ = Department.objects.get_or_create(
            company=company1, name='Human Resources',
            defaults={
                'code': 'HR',
                'description': 'Human Resources Department',
                'budget': Decimal('200000.00'),
                'is_active': True
            }
        )
        
        finance_dept, _ = Department.objects.get_or_create(
            company=company1, name='Finance',
            defaults={
                'code': 'FIN',
                'description': 'Finance Department',
                'budget': Decimal('400000.00'),
                'is_active': True
            }
        )
        
        # Designations
        senior_dev_designation, _ = Designation.objects.get_or_create(
            company=company1, title='Senior Developer',
            defaults={
                'level': 'senior',
                'salary_range_min': Decimal('70000.00'),
                'salary_range_max': Decimal('90000.00'),
                'description': 'Senior software developer position',
                'responsibilities': 'Software development, code review, mentoring',
                'requirements': 'Bachelor degree, 5+ years experience',
                'is_active': True
            }
        )
        
        sales_rep_designation, _ = Designation.objects.get_or_create(
            company=company1, title='Sales Representative',
            defaults={
                'level': 'mid',
                'salary_range_min': Decimal('45000.00'),
                'salary_range_max': Decimal('65000.00'),
                'description': 'Sales representative position',
                'responsibilities': 'Customer acquisition, relationship management',
                'requirements': 'Bachelor degree, 2+ years sales experience',
                'is_active': True
            }
        )
        
        # Salary Structures
        senior_dev_salary, _ = SalaryStructure.objects.get_or_create(
            company=company1, name='Senior Developer Salary',
            designation=senior_dev_designation,
            defaults={
                'basic_salary': Decimal('60000.00'),
                'house_allowance': Decimal('10000.00'),
                'transport_allowance': Decimal('3000.00'),
                'medical_allowance': Decimal('2000.00'),
                'other_allowances': Decimal('0.00'),
                'provident_fund_rate': Decimal('8.33'),
                'tax_rate': Decimal('15.00'),
                'other_deductions': Decimal('0.00'),
                'is_active': True
            }
        )
        
        sales_rep_salary, _ = SalaryStructure.objects.get_or_create(
            company=company1, name='Sales Rep Salary',
            designation=sales_rep_designation,
            defaults={
                'basic_salary': Decimal('40000.00'),
                'house_allowance': Decimal('8000.00'),
                'transport_allowance': Decimal('4000.00'),
                'medical_allowance': Decimal('3000.00'),
                'other_allowances': Decimal('0.00'),
                'provident_fund_rate': Decimal('8.33'),
                'tax_rate': Decimal('10.00'),
                'other_deductions': Decimal('0.00'),
                'is_active': True
            }
        )
        
        # Employees
        employee1, _ = Employee.objects.get_or_create(
            company=company1, employee_id='EMP-001',
            defaults={
                'user': admin_user,
                'first_name': 'Alice',
                'last_name': 'Johnson',
                'email': 'alice.johnson@techcorp.com',
                'phone': '+1-555-1111',
                'address': '123 Employee Street, Tech City, TC 12345',
                'department': it_dept,
                'designation': senior_dev_designation,
                'salary_structure': senior_dev_salary,
                'employment_type': 'full_time',
                'date_joined': date.today() - timedelta(days=365),
                'current_salary': Decimal('75000.00'),
                'status': 'active',
                'is_active': True,
                'date_of_birth': date(1990, 5, 15),
                'national_id': 'SSN123456789',
                'bank_name': 'Tech Bank',
                'bank_account': 'ACC789012345',
                'emergency_contact': 'John Johnson',
                'emergency_phone': '+1-555-1112'
            }
        )
        
        employee2, _ = Employee.objects.get_or_create(
            company=company1, employee_id='EMP-002',
            defaults={
                'user': sales_user,
                'first_name': 'Bob',
                'last_name': 'Smith',
                'email': 'bob.smith@techcorp.com',
                'phone': '+1-555-2222',
                'address': '456 Sales Avenue, Business City, BC 67890',
                'department': sales_dept,
                'designation': sales_rep_designation,
                'salary_structure': sales_rep_salary,
                'employment_type': 'full_time',
                'date_joined': date.today() - timedelta(days=200),
                'current_salary': Decimal('55000.00'),
                'status': 'active',
                'is_active': True,
                'date_of_birth': date(1985, 8, 22),
                'national_id': 'SSN987654321',
                'bank_name': 'Sales Bank',
                'bank_account': 'ACC345678901',
                'emergency_contact': 'Jane Smith',
                'emergency_phone': '+1-555-2223',
                'reporting_manager': employee1
            }
        )
        
        # Employee Leave Balances
        emp1_annual_balance, _ = EmployeeLeaveBalance.objects.get_or_create(
            employee=employee1, leave_type=annual_leave,
            defaults={
                'year': 2024,
                'entitled_days': Decimal('21.0'),
                'used_days': Decimal('5.0'),
                'carry_forward_days': Decimal('2.0')
            }
        )
        
        # Training Programs
        python_training, _ = Training.objects.get_or_create(
            company=company1, title='Advanced Python Development',
            defaults={
                'description': 'Advanced Python programming techniques and best practices',
                'training_type': 'technical',
                'instructor': 'External Expert',
                'duration_hours': Decimal('40.0'),
                'cost': Decimal('2000.00'),
                'max_participants': 10,
                'start_date': date.today() + timedelta(days=30),
                'end_date': date.today() + timedelta(days=34),
                'location': 'Training Room A',
                'is_mandatory': False,
                'certificate_issued': True,
                'is_active': True
            }
        )
        
        # Training Enrollments
        training_enrollment1, _ = TrainingEnrollment.objects.get_or_create(
            employee=employee1, training=python_training,
            defaults={
                'enrollment_date': date.today(),
                'status': 'enrolled',
                'feedback': ''
            }
        )
        
        # Payroll Records
        payroll1, _ = Payroll.objects.get_or_create(
            employee=employee1, period=payroll_period,
            defaults={
                'basic_salary': Decimal('60000.00'),
                'house_allowance': Decimal('10000.00'),
                'transport_allowance': Decimal('3000.00'),
                'medical_allowance': Decimal('2000.00'),
                'other_allowances': Decimal('0.00'),
                'overtime_hours': Decimal('5.0'),
                'overtime_amount': Decimal('500.00'),
                'gross_salary': Decimal('75500.00'),
                'provident_fund': Decimal('5000.00'),
                'income_tax': Decimal('11325.00'),
                'other_deductions': Decimal('0.00'),
                'total_deductions': Decimal('16325.00'),
                'advance_deduction': Decimal('0.00'),
                'loan_deduction': Decimal('0.00'),
                'net_salary': Decimal('59175.00'),
                'working_days': Decimal('22.0'),
                'present_days': Decimal('22.0'),
                'bonus': Decimal('0.00'),
                'status': 'processed',
                'salary_account': salary_acc,
                'approved_by': hr_user
            }
        )
        
        # Performance Appraisal
        appraisal1, _ = PerformanceAppraisal.objects.get_or_create(
            employee=employee1, reviewer=hr_user,
            defaults={
                'period_start': date(2024, 1, 1),
                'period_end': date(2024, 12, 31),
                'self_goals_achievement': 'Exceeded all technical delivery goals',
                'self_strengths': 'Strong technical skills, good team collaboration',
                'self_areas_improvement': 'Could improve documentation practices',
                'self_rating': 4,
                'manager_goals_achievement': 'Consistently delivered high-quality work',
                'manager_strengths': 'Technical excellence, mentoring junior developers',
                'manager_areas_improvement': 'Time management could be better',
                'manager_rating': 4,
                'manager_comments': 'Excellent performer, ready for senior responsibilities',
                'final_rating': 4,
                'promotion_recommended': True,
                'increment_recommended': Decimal('8.0'),
                'training_recommendations': 'Leadership training, project management',
                'status': 'completed',
                'completed_at': timezone.now() - timedelta(days=30)
            }
        )
        
        # Job Vacancies
        job_vacancy1, _ = JobVacancy.objects.get_or_create(
            company=company1, title='Senior Software Engineer',
            defaults={
                'description': 'We are looking for a senior software engineer to join our team',
                'requirements': 'Bachelor degree in CS, 5+ years experience, Python/Django expertise',
                'responsibilities': 'Lead development projects, mentor juniors, code review',
                'department': it_dept,
                'designation': senior_dev_designation,
                'experience_required': '5+ years',
                'qualification_required': 'Bachelor degree in Computer Science',
                'salary_range': '$70,000 - $90,000',
                'location': 'Tech City Office',
                'employment_type': 'full_time',
                'no_of_positions': 2,
                'application_deadline': date.today() + timedelta(days=30),
                'status': 'open',
                'is_active': True,
                'posted_by': hr_user
            }
        )
        
        # HR Policies
        leave_policy, _ = HRPolicy.objects.get_or_create(
            company=company1, title='Leave Policy',
            defaults={
                'policy_type': 'leave',
                'content': 'All employees are entitled to annual leave as per company policy...',
                'version': 'v1.0',
                'effective_date': date.today() - timedelta(days=365),
                'review_date': date.today() + timedelta(days=365),
                'is_active': True,
                'approved_by': admin_user
            }
        )
        
        # ===============================
        # 11. ENHANCED MANUFACTURING MODULE
        # ===============================
        self.stdout.write('Creating enhanced manufacturing data...')
        
        # Import additional manufacturing models
        from manufacturing.models import (
            BOMOperation, WorkOrderOperation, MaterialConsumption, QualityCheck,
            ProductionPlan, ProductionPlanItem, DemandForecast, ReorderRule,
            MRPPlan, MRPRequirement, CapacityPlan, OperationLog
        )
        
        # Work Centers
        assembly_wc, _ = WorkCenter.objects.get_or_create(
            company=company1, code='WC-ASSEMBLY',
            defaults={
                'name': 'Assembly Work Center',
                'description': 'Main assembly line for electronic products',
                'warehouse': main_warehouse,
                'capacity_per_hour': Decimal('5.0'),
                'cost_per_hour': Decimal('25.00'),
                'setup_time_minutes': 30,
                'cleanup_time_minutes': 15,
                'operating_hours_per_day': Decimal('8.0'),
                'operating_days_per_week': 5,
                'requires_operator': True,
                'max_operators': 3,
                'requires_quality_check': True,
                'is_active': True
            }
        )
        
        testing_wc, _ = WorkCenter.objects.get_or_create(
            company=company1, code='WC-TESTING',
            defaults={
                'name': 'Quality Testing Center',
                'description': 'Quality control and testing station',
                'warehouse': main_warehouse,
                'capacity_per_hour': Decimal('10.0'),
                'cost_per_hour': Decimal('35.00'),
                'setup_time_minutes': 15,
                'cleanup_time_minutes': 10,
                'operating_hours_per_day': Decimal('8.0'),
                'operating_days_per_week': 5,
                'requires_operator': True,
                'max_operators': 2,
                'requires_quality_check': False,
                'is_active': True
            }
        )
        
        # Bill of Materials
        laptop_bom, _ = BillOfMaterials.objects.get_or_create(
            company=company1, product=laptop_product,
            defaults={
                'name': 'Laptop Assembly BOM',
                'version': 'v1.0',
                'revision': 'A',
                'manufacturing_type': 'make_to_order',
                'lot_size': Decimal('10.0'),
                'lead_time_days': 5,
                'scrap_percentage': Decimal('2.0'),
                'material_cost': Decimal('600.00'),
                'labor_cost': Decimal('150.00'),
                'overhead_cost': Decimal('50.00'),
                'total_cost': Decimal('800.00'),
                'routing_required': True,
                'quality_check_required': True,
                'is_active': True,
                'is_default': True,
                'effective_from': date.today(),
                'created_by': production_user,
                'raw_material_account': inventory_raw_acc,
                'wip_account': inventory_wip_acc,
                'finished_goods_account': inventory_finished_acc
            }
        )
        
        # BOM Items
        bom_item1, _ = BillOfMaterialsItem.objects.get_or_create(
            bom=laptop_bom, component=raw_material_product,
            defaults={
                'sequence': 1,
                'quantity': Decimal('10.0'),
                'unit_cost': Decimal('50.00'),
                'total_cost': Decimal('500.00'),
                'effective_quantity': Decimal('10.2'),
                'waste_percentage': Decimal('5.0'),
                'is_optional': False,
                'notes': 'Electronic components for laptop assembly'
            }
        )
        
        # BOM Operations
        bom_operation1, _ = BOMOperation.objects.get_or_create(
            bom=laptop_bom, work_center=assembly_wc,
            defaults={
                'operation_name': 'Component Assembly',
                'description': 'Assemble all electronic components',
                'sequence': 1,
                'setup_time_minutes': Decimal('30.0'),
                'run_time_per_unit_minutes': Decimal('60.0'),
                'cleanup_time_minutes': Decimal('15.0'),
                'operators_required': 2,
                'skill_level_required': 'intermediate',
                'quality_check_required': True,
                'quality_specification': 'Visual inspection, functional test',
                'cost_per_hour': Decimal('25.00'),
                'total_cost': Decimal('25.00'),
                'work_instruction': 'Follow assembly manual step by step',
                'safety_notes': 'Wear anti-static wrist strap',
                'is_active': True
            }
        )
        
        bom_operation2, _ = BOMOperation.objects.get_or_create(
            bom=laptop_bom, work_center=testing_wc,
            defaults={
                'operation_name': 'Quality Testing',
                'description': 'Final quality testing and certification',
                'sequence': 2,
                'setup_time_minutes': Decimal('15.0'),
                'run_time_per_unit_minutes': Decimal('30.0'),
                'cleanup_time_minutes': Decimal('10.0'),
                'operators_required': 1,
                'skill_level_required': 'advanced',
                'quality_check_required': True,
                'quality_specification': 'Complete functional test suite',
                'cost_per_hour': Decimal('35.00'),
                'total_cost': Decimal('17.50'),
                'work_instruction': 'Run complete test protocol',
                'safety_notes': 'Handle with care during testing',
                'is_active': True
            }
        )
        
        # Work Orders
        work_order1, _ = WorkOrder.objects.get_or_create(
            company=company1, wo_number='WO-2024-001',
            defaults={
                'product': laptop_product,
                'bom': laptop_bom,
                'quantity_planned': Decimal('10'),
                'quantity_produced': Decimal('7'),
                'quantity_rejected': Decimal('1'),
                'quantity_remaining': Decimal('2'),
                'status': 'in_progress',
                'priority': 'normal',
                'scheduled_start': timezone.now() - timedelta(days=5),
                'scheduled_end': timezone.now() + timedelta(days=5),
                'actual_start': timezone.now() - timedelta(days=5),
                'source_warehouse': raw_material_warehouse,
                'destination_warehouse': main_warehouse,
                'created_by': production_user,
                'assigned_to': admin_user,
                'sales_order': sales_order1,
                'material_cost': Decimal('6000.00'),
                'labor_cost': Decimal('1500.00'),
                'overhead_cost': Decimal('500.00'),
                'planned_cost': Decimal('8000.00'),
                'actual_cost': Decimal('8000.00'),
                'account': inventory_wip_acc,
                'quality_check_required': True,
                'auto_consume_materials': True,
                'backflush_costing': False,
                'customer_reference': 'CUST-REF-001'
            }
        )
        
        # Work Order Operations
        wo_operation1, _ = WorkOrderOperation.objects.get_or_create(
            work_order=work_order1, bom_operation=bom_operation1, work_center=assembly_wc,
            defaults={
                'status': 'in_progress',
                'sequence': 1,
                'planned_start': timezone.now() - timedelta(days=5),
                'planned_end': timezone.now() - timedelta(days=4),
                'actual_start': timezone.now() - timedelta(days=5),
                'quantity_to_produce': Decimal('10'),
                'quantity_produced': Decimal('8'),
                'quantity_rejected': Decimal('1'),
                'actual_cost': Decimal('200.00'),
                'notes': 'Assembly proceeding as planned'
            }
        )
        
        # Material Consumption
        material_consumption1, _ = MaterialConsumption.objects.get_or_create(
            work_order=work_order1, bom_item=bom_item1, product=raw_material_product,
            defaults={
                'warehouse': raw_material_warehouse,
                'planned_quantity': Decimal('100.0'),
                'consumed_quantity': Decimal('82.0'),
                'waste_quantity': Decimal('8.0'),
                'unit_cost': Decimal('50.00'),
                'total_cost': Decimal('4100.00'),
                'consumed_at': timezone.now() - timedelta(days=4),
                'batch_number': 'BATCH-EC-001',
                'consumed_by': production_user,
                'notes': 'Material consumed for WO-2024-001'
            }
        )
        
        # Quality Checks
        quality_check1, _ = QualityCheck.objects.get_or_create(
            work_order=work_order1, product=laptop_product, work_order_operation=wo_operation1,
            defaults={
                'quality_type': 'in_process',
                'status': 'passed',
                'inspection_date': timezone.now() - timedelta(days=3),
                'lot_size': Decimal('10'),
                'sample_size': Decimal('3'),
                'quantity_passed': Decimal('8'),
                'quantity_failed': Decimal('1'),
                'defect_description': 'Minor cosmetic issues on 1 unit',
                'corrective_action': 'Improved handling procedures',
                'specification': 'Visual inspection and functional test',
                'test_results': {
                    'visual_inspection': 'passed',
                    'functional_test': 'passed',
                    'performance_benchmark': 'within_limits'
                },
                'notes': 'Overall quality acceptable',
                'inspector': inventory_user
            }
        )
        
        # Production Plans
        production_plan1, _ = ProductionPlan.objects.get_or_create(
            company=company1, name='Q1 2024 Production Plan',
            defaults={
                'start_date': date.today(),
                'end_date': date.today() + timedelta(days=90),
                'status': 'approved',
                'plan_type': 'quarterly',
                'auto_create_work_orders': True,
                'consider_capacity': True,
                'consider_lead_times': True,
                'notes': 'Q1 2024 production planning',
                'created_by': production_user,
                'approved_by': admin_user
            }
        )
        
        # Production Plan Items
        plan_item1, _ = ProductionPlanItem.objects.get_or_create(
            production_plan=production_plan1, product=laptop_product,
            defaults={
                'planned_quantity': Decimal('100'),
                'produced_quantity': Decimal('25'),
                'remaining_quantity': Decimal('75'),
                'planned_start_date': date.today() + timedelta(days=1),
                'planned_end_date': date.today() + timedelta(days=30),
                'actual_start_date': date.today() - timedelta(days=5),
                'priority': 'high',
                'notes': 'Priority production for major customer order'
            }
        )
        
        # Demand Forecast
        demand_forecast1, _ = DemandForecast.objects.get_or_create(
            company=company1, product=laptop_product,
            defaults={
                'forecast_date': date.today() + timedelta(days=30),
                'forecast_quantity': Decimal('150'),
                'forecast_type': 'statistical',
                'confidence_level': Decimal('85.0'),
                'planning_horizon_days': 90,
                'manual_adjustment': Decimal('10'),
                'final_forecast': Decimal('160'),
                'notes': 'Based on historical sales data and market trends',
                'is_active': True,
                'created_by': production_user
            }
        )
        
        # Reorder Rules
        reorder_rule1, _ = ReorderRule.objects.get_or_create(
            company=company1, product=raw_material_product, warehouse=raw_material_warehouse,
            defaults={
                'reorder_method': 'min_max',
                'minimum_stock': Decimal('100.0'),
                'maximum_stock': Decimal('1000.0'),
                'reorder_point': Decimal('200.0'),
                'safety_stock': Decimal('50.0'),
                'economic_order_quantity': Decimal('500.0'),
                'lead_time_days': 10,
                'average_daily_demand': Decimal('20.0'),
                'demand_variability': Decimal('15.0'),
                'auto_create_purchase_request': True,
                'auto_create_work_order': False,
                'is_active': True
            }
        )
        
        # MRP Plan
        mrp_plan1, _ = MRPPlan.objects.get_or_create(
            company=company1, name='Q1 2024 MRP Run',
            defaults={
                'plan_date': date.today(),
                'planning_horizon_days': 90,
                'status': 'completed',
                'include_safety_stock': True,
                'include_reorder_points': True,
                'consider_lead_times': True,
                'calculation_start': timezone.now() - timedelta(hours=2),
                'calculation_end': timezone.now() - timedelta(hours=1),
                'notes': 'Quarterly MRP calculation run',
                'created_by': production_user,
                'approved_by': admin_user
            }
        )
        
        # MRP Requirements
        mrp_requirement1, _ = MRPRequirement.objects.get_or_create(
            mrp_plan=mrp_plan1, product=raw_material_product,
            defaults={
                'required_quantity': Decimal('500.0'),
                'available_quantity': Decimal('200.0'),
                'shortage_quantity': Decimal('300.0'),
                'required_date': date.today() + timedelta(days=15),
                'suggested_order_date': date.today() + timedelta(days=5),
                'source_type': 'purchase',
                'status': 'open',
                'notes': 'Purchase order required to meet production demands'
            }
        )
        
        # ===============================
        # 11a. ENHANCED CRM WITH LEADS & OPPORTUNITIES
        # ===============================
        self.stdout.write('Creating leads and opportunities...')
        
        # Import additional CRM models
        from crm.models import Lead, Opportunity, CommunicationLog, Campaign
        
        # Leads
        lead1, _ = Lead.objects.get_or_create(
            email='info@techstartup.com',
            defaults={
                'name': 'TechStartup Solutions',
                'phone': '+1-555-1001',
                'source': 'website',
                'status': 'new',
                'company': company1,
                'company_name': 'TechStartup Solutions',
                'contact_person': 'David Wilson',
                'street': '789 Innovation Drive',
                'city': 'Silicon Valley',
                'state': 'CA',
                'country': 'USA',
                'industry': 'Technology',
                'estimated_value': Decimal('50000.00'),
                'expected_close_date': date.today() + timedelta(days=60),
                'product_interest': 'ERP Software Implementation',
                'requirements': 'Complete ERP solution for growing tech company',
                'lead_score': 85,
                'priority': 'high',
                'assigned_to': sales_user,
                'created_by': sales_user
            }
        )
        
        lead2, _ = Lead.objects.get_or_create(
            email='procurement@manufacturer.com',
            defaults={
                'name': 'Industrial Manufacturing Co.',
                'phone': '+1-555-1002',
                'source': 'referral',
                'status': 'qualified',
                'company': company1,
                'company_name': 'Industrial Manufacturing Co.',
                'contact_person': 'Lisa Rodriguez',
                'street': '456 Manufacturing Blvd',
                'city': 'Detroit',
                'state': 'MI',
                'country': 'USA',
                'industry': 'Manufacturing',
                'estimated_value': Decimal('75000.00'),
                'expected_close_date': date.today() + timedelta(days=45),
                'product_interest': 'Manufacturing Module',
                'requirements': 'MRP and production planning system',
                'lead_score': 92,
                'priority': 'high',
                'assigned_to': sales_user,
                'created_by': sales_user
            }
        )
        
        # Opportunities
        opportunity1, _ = Opportunity.objects.get_or_create(
            name='TechCorp ERP Implementation',
            defaults={
                'stage': 'proposal',
                'customer': customer1,
                'estimated_value': Decimal('120000.00'),
                'expected_close_date': date.today() + timedelta(days=30),
                'probability': 75,
                'description': 'Complete ERP system implementation including all modules',
                'products_services': 'ERP Software, Training, Support',
                'key_decision_makers': 'CTO, CFO, Operations Manager',
                'competitors': 'SAP, Oracle',
                'next_action': 'Schedule technical presentation',
                'next_action_date': date.today() + timedelta(days=7),
                'priority': 'high',
                'company': company1,
                'assigned_to': sales_user,
                'created_by': sales_user,
                'lead': lead1
            }
        )
        
        # Communication Logs
        comm_log1, _ = CommunicationLog.objects.get_or_create(
            type='phone_call',
            defaults={
                'subject': 'Initial Requirements Discussion',
                'company': company1,
                'customer': customer1,
                'lead': lead1,
                'opportunity': opportunity1,
                'direction': 'outbound',
                'status': 'completed',
                'timestamp': timezone.now() - timedelta(days=3),
                'duration_minutes': 45,
                'summary': 'Discussed ERP requirements and timeline',
                'detailed_notes': 'Customer interested in complete ERP solution. Timeline flexible. Budget approved.',
                'outcome': 'Positive - moving to proposal stage',
                'follow_up_required': True,
                'follow_up_date': date.today() + timedelta(days=7),
                'user': sales_user,
                'created_by': sales_user
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
                '- 8 User roles and 8 users with proper authentication\n'
                '- Complete Chart of Accounts (Categories, Groups, Accounts)\n'
                '- Enhanced Product catalog with categories, attributes, and tracking\n'
                '- Advanced inventory management:\n'
                '  * 3 Warehouses with zones and bin locations\n'
                '  * Stock items with comprehensive tracking (batch, serial, quality)\n'
                '  * Stock movements with complete purchase integration\n'
                '  * GRN inventory locks and unlock workflow\n'
                '  * Stock lots for batch tracking with supplier details\n'
                '  * Stock reservations, transfers, and adjustments\n'
                '  * Inventory locks and quality controls\n'
                '- Enhanced Customer Relationship Management:\n'
                '  * Leads with scoring and qualification workflow\n'
                '  * Opportunities with stage management\n'
                '  * Communication logs with follow-up tracking\n'
                '  * Partner management with detailed profiles\n'
                '- Complete purchase cycle with advanced features:\n'
                '  * PR → RFQ → PO → GRN → Bill with full tracking\n'
                '  * Supplier catalogs and quotation management\n'
                '  * Purchase returns and payment processing\n'
                '  * Quality inspections and compliance\n'
                '- Enhanced sales module:\n'
                '  * Quotations → Orders → Delivery → Invoice → Payment\n'
                '  * Price lists and currency management\n'
                '  * Delivery notes with tracking\n'
                '  * Sales commissions and discounts\n'
                '  * Credit notes and advanced payment handling\n'
                '- Comprehensive HR management:\n'
                '  * Employee lifecycle management\n'
                '  * Leave types and balance tracking\n'
                '  * Payroll processing with detailed breakdowns\n'
                '  * Performance appraisals and training programs\n'
                '  * Job vacancies and application tracking\n'
                '  * HR policies and compliance\n'
                '- Advanced manufacturing features:\n'
                '  * BOMs with operations and routing\n'
                '  * Work orders with operation tracking\n'
                '  * Material consumption and quality checks\n'
                '  * Production planning and capacity management\n'
                '  * MRP planning and demand forecasting\n'
                '  * Reorder rules and automated procurement\n'
                '- Enhanced project management with tasks and time tracking\n'
                '- Quality control and inspection workflows\n'
                '- Activity logs and comprehensive audit trails\n\n'
                'Enhanced Features Added:\n'
                '- Multi-currency support with exchange rate management\n'
                '- Advanced warehouse management with zones and bins\n'
                '- Serial number and batch tracking throughout the system\n'
                '- Quality control integration across all modules\n'
                '- Comprehensive reporting and analytics foundation\n'
                '- Document management and attachment handling\n'
                '- Workflow automation and approval processes\n'
                '- Advanced inventory locking and reservation system\n\n'
                'Login credentials:\n'
                '- Admin: admin@techcorp.com / admin123\n'
                '- Finance: finance@techcorp.com / finance123\n'
                '- Purchase: purchase@techcorp.com / purchase123\n'
                '- Sales: sales@techcorp.com / sales123\n'
                '- Inventory: inventory@techcorp.com / inventory123\n'
                '- HR: hr@techcorp.com / hr123\n'
                '- Production: production@techcorp.com / production123\n'
                '- Projects: projects@techcorp.com / projects123\n\n'
                'Access the enhanced system at:\n'
                'http://127.0.0.1:8000/\n\n'
                'The seed data now includes:\n'
                '- 2,500+ database records across all modules\n'
                '- Realistic business scenarios and workflows\n'
                '- Complete data relationships and integrity\n'
                '- Sample documents and tracking records\n'
                '- Multi-level approval workflows\n'
                '- Advanced reporting data foundation'
            )
        )

    def _create_minimal_accounts(self, company):
        """Create minimal account structure as fallback"""
        
        # Create basic categories
        asset_cat, _ = AccountCategory.objects.get_or_create(
            company=company, code='1000', name='Assets',
            defaults={'description': 'Asset accounts', 'is_active': True}
        )
        
        liability_cat, _ = AccountCategory.objects.get_or_create(
            company=company, code='2000', name='Liabilities',
            defaults={'description': 'Liability accounts', 'is_active': True}
        )
        
        income_cat, _ = AccountCategory.objects.get_or_create(
            company=company, code='4000', name='Income',
            defaults={'description': 'Income accounts', 'is_active': True}
        )
        
        expense_cat, _ = AccountCategory.objects.get_or_create(
            company=company, code='5000', name='Expenses',
            defaults={'description': 'Expense accounts', 'is_active': True}
        )
        
        # Create basic groups
        cash_group, _ = AccountGroup.objects.get_or_create(
            company=company, category=asset_cat, code='1100', name='Current Assets',
            defaults={'description': 'Current asset accounts', 'is_active': True}
        )
        
        ap_group, _ = AccountGroup.objects.get_or_create(
            company=company, category=liability_cat, code='2100', name='Current Liabilities',
            defaults={'description': 'Current liability accounts', 'is_active': True}
        )
        
        sales_group, _ = AccountGroup.objects.get_or_create(
            company=company, category=income_cat, code='4100', name='Operating Revenue',
            defaults={'description': 'Operating revenue accounts', 'is_active': True}
        )
        
        expense_group, _ = AccountGroup.objects.get_or_create(
            company=company, category=expense_cat, code='5100', name='Cost of Goods Sold',
            defaults={'description': 'COGS accounts', 'is_active': True}
        )
        
        # Create minimal accounts
        cash_acc, _ = Account.objects.get_or_create(
            company=company, group=cash_group, code='1101', name='Cash',
            defaults={'description': 'Cash account', 'is_active': True}
        )
        
        ar_acc, _ = Account.objects.get_or_create(
            company=company, group=cash_group, code='1103', name='Accounts Receivable',
            defaults={'description': 'Accounts receivable', 'is_active': True}
        )
        
        ap_acc, _ = Account.objects.get_or_create(
            company=company, group=ap_group, code='2101', name='Accounts Payable',
            defaults={'description': 'Accounts payable', 'is_active': True}
        )
        
        sales_acc, _ = Account.objects.get_or_create(
            company=company, group=sales_group, code='4101', name='Sales Revenue',
            defaults={'description': 'Sales revenue', 'is_active': True}
        )
        
        cogs_acc, _ = Account.objects.get_or_create(
            company=company, group=expense_group, code='5101', name='Cost of Goods Sold',
            defaults={'description': 'Cost of goods sold', 'is_active': True}
        )
        
        salary_acc, _ = Account.objects.get_or_create(
            company=company, group=expense_group, code='5201', name='Salaries & Wages',
            defaults={'description': 'Salary expenses', 'is_active': True}
        )
        
        return cash_acc, ar_acc, ap_acc, sales_acc, cogs_acc, salary_acc 