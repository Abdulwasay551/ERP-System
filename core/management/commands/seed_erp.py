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
                'has_expiry': False,
                'shelf_life_days': 0,
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
                'has_expiry': False,
                'shelf_life_days': 0,
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
                'has_expiry': False,
                'shelf_life_days': 0,
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
                'has_expiry': False,
                'shelf_life_days': 0,
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
        
        # Update GRN Lock status (simulate bill processing)
        if grn_lock:
            grn_lock.is_active = False
            grn_lock.is_released = True
            grn_lock.released_at = timezone.now() - timedelta(days=3)
            grn_lock.released_by = finance_user
            grn_lock.released_for_bill = bill1
            grn_lock.release_notes = 'Bill processed and approved'
            grn_lock.save()
            
        # ===============================
        # 8a. ADDITIONAL INVENTORY TRACKING
        # ===============================
        self.stdout.write('Creating additional inventory tracking data...')
        
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
                    'quality_approved': True,
                    'quality_approved_by': inventory_user,
                    'quality_approved_date': timezone.now() - timedelta(days=29),
                    'supplier': supplier1,
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
                    'quality_approved': True,
                    'quality_approved_by': inventory_user,
                    'quality_approved_date': timezone.now() - timedelta(days=14),
                    'supplier': supplier1,
                    'is_active': True
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
                'expires_at': timezone.now() + timedelta(days=30),
                'priority': 2,
                'notes': 'Reserved for upcoming customer order',
                'is_active': True
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
                'resolved': False
            }
        )
        
        # Quality passed movement for raw materials
        quality_movement, _ = StockMovement.objects.get_or_create(
            company=company1, stock_item=raw_material_stock,
            defaults={
                'movement_type': 'quality_pass',
                'quantity': Decimal('500'),
                'unit_cost': Decimal('50.00'),
                'to_warehouse': raw_material_warehouse,
                'reference_type': 'quality_inspection',
                'reference_number': 'QI-RAW-001',
                'quality_status': 'passed',
                'performed_by': inventory_user,
                'timestamp': timezone.now() - timedelta(days=29),
                'notes': 'Raw materials passed quality inspection and moved to warehouse'
            }
        )
        
        # ===============================
        # 9. SALES MODULE
        # ===============================
        self.stdout.write('Creating sales data...')
        
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
                'unit_price': Decimal('1200.00'),
                'discount_type': 'percent',
                'discount_value': Decimal('0.00'),
                'discount_amount': Decimal('0.00'),
                'line_total': Decimal('2400.00')
            }
        )
        
        so_item2, _ = SalesOrderItem.objects.get_or_create(
            sales_order=sales_order1, product=consultation_service,
            defaults={
                'quantity': Decimal('3'),
                'unit_price': Decimal('100.00'),
                'discount_type': 'percent',
                'discount_value': Decimal('0.00'),
                'discount_amount': Decimal('0.00'),
                'line_total': Decimal('300.00')
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
                'department': it_dept,
                'designation': senior_dev_designation,
                'salary_structure': senior_dev_salary,
                'employment_type': 'full_time',
                'date_joined': date.today() - timedelta(days=365),
                'current_salary': Decimal('75000.00'),
                'status': 'active',
                'is_active': True
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
                'department': sales_dept,
                'designation': sales_rep_designation,
                'salary_structure': sales_rep_salary,
                'employment_type': 'full_time',
                'date_joined': date.today() - timedelta(days=200),
                'current_salary': Decimal('55000.00'),
                'status': 'active',
                'is_active': True
            }
        )
        
        # ===============================
        # 11. MANUFACTURING MODULE
        # ===============================
        self.stdout.write('Creating manufacturing data...')
        
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
                'quantity': Decimal('10.0'),
                'unit_cost': Decimal('50.00'),
                'waste_percentage': Decimal('5.0'),
                'sequence': 1,
                'notes': 'Electronic components for laptop assembly'
            }
        )
        
        # Work Orders
        work_order1, _ = WorkOrder.objects.get_or_create(
            company=company1, product=laptop_product,
            defaults={
                'wo_number': 'WO-2024-001',
                'bom': laptop_bom,
                'quantity_planned': Decimal('10'),
                'quantity_produced': Decimal('7'),
                'quantity_rejected': Decimal('1'),
                'status': 'in_progress',
                'priority': 'normal',
                'scheduled_start': timezone.now() - timedelta(days=5),
                'scheduled_end': timezone.now() + timedelta(days=5),
                'actual_start': timezone.now() - timedelta(days=5),
                'source_warehouse': raw_material_warehouse,
                'destination_warehouse': main_warehouse,
                'created_by': production_user,
                'assigned_to': admin_user,
                'sales_order': None,
                'material_cost': Decimal('6000.00'),
                'labor_cost': Decimal('1500.00'),
                'overhead_cost': Decimal('500.00'),
                'planned_cost': Decimal('8000.00'),
                'actual_cost': Decimal('8000.00'),
                'account': inventory_wip_acc
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
                '- Enhanced inventory management:\n'
                '  * 3 Warehouses with different types (main, distribution, raw materials)\n'
                '  * Stock items with advanced tracking (batch, serial, quality status)\n'
                '  * Stock movements with purchase integration\n'
                '  * GRN inventory locks and unlock workflow\n'
                '  * Stock lots for batch tracking\n'
                '  * Stock reservations and alerts\n'
                '- Customer and supplier relationships\n'
                '- Complete purchase cycle (PR → RFQ → PO → GRN → Bill) with inventory integration\n'
                '- Sales quotations, orders, and invoices\n'
                '- HR data (departments, employees)\n'
                '- Manufacturing BOMs and work orders\n'
                '- Project management with tasks and time tracking\n'
                '- Quality control and inspection workflows\n'
                '- Activity logs and audit trails\n\n'
                'Enhanced Inventory Features:\n'
                '- Purchase status tracking (received_unbilled → received_billed → ready_for_use)\n'
                '- Inventory locking system for GRN → Bill workflow\n'
                '- Quality control integration with stock movements\n'
                '- Batch and lot tracking for raw materials\n'
                '- Stock reservations for sales orders\n'
                '- Automated stock alerts for low inventory\n'
                '- Multi-warehouse support with warehouse types\n\n'
                'Login credentials:\n'
                '- Admin: admin@techcorp.com / admin123\n'
                '- Finance: finance@techcorp.com / finance123\n'
                '- Purchase: purchase@techcorp.com / purchase123\n'
                '- Sales: sales@techcorp.com / sales123\n'
                '- Inventory: inventory@techcorp.com / inventory123\n'
                '- HR: hr@techcorp.com / hr123\n'
                '- Production: production@techcorp.com / production123\n'
                '- Projects: projects@techcorp.com / projects123\n\n'
                'Access the enhanced inventory dashboard at:\n'
                'http://127.0.0.1:8000/inventory/dashboard/'
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