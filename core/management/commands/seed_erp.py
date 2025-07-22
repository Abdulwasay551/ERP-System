from django.core.management.base import BaseCommand
from user_auth.models import Company, User, Role
from crm.models import Customer
from sales.models import Product, SalesOrder
from inventory.models import StockItem, Warehouse, ProductCategory
from accounting.models import Account, AccountCategory, AccountGroup
from purchase.models import Supplier, PurchaseOrder, Bill
from hr.models import Employee, Payroll
from manufacturing.models import BillOfMaterials, WorkOrder
from project_mgmt.models import Project, Task
from django.contrib.auth.hashers import make_password
from datetime import date

class Command(BaseCommand):
    help = 'Seed the ERP database with demo data.'

    def handle(self, *args, **kwargs):
        # Company
        company, _ = Company.objects.get_or_create(name='DemoCorp', defaults={'is_active': True})
        # Roles
        admin_role, _ = Role.objects.get_or_create(name='Admin', defaults={'department': 'IT', 'level': 1})
        sales_role, _ = Role.objects.get_or_create(name='Sales Manager', defaults={'department': 'Sales', 'level': 2})
        hr_role, _ = Role.objects.get_or_create(name='HR Manager', defaults={'department': 'HR', 'level': 2})
        # Users
        admin, _ = User.objects.get_or_create(email='admin@demo.com', defaults={
            'first_name': 'Admin', 'last_name': 'User', 'company': company, 'role': admin_role, 'is_staff': True, 'is_superuser': True, 'is_active': True, 'password': make_password('admin123')
        })
        sales_user, _ = User.objects.get_or_create(email='sales@demo.com', defaults={
            'first_name': 'Sally', 'last_name': 'Sales', 'company': company, 'role': sales_role, 'is_active': True, 'password': make_password('sales123')
        })
        hr_user, _ = User.objects.get_or_create(email='hr@demo.com', defaults={
            'first_name': 'Henry', 'last_name': 'HR', 'company': company, 'role': hr_role, 'is_active': True, 'password': make_password('hr123')
        })
        # COA
        asset_cat, _ = AccountCategory.objects.get_or_create(company=company, code='1', name='Asset')
        liab_cat, _ = AccountCategory.objects.get_or_create(company=company, code='2', name='Liability')
        equity_cat, _ = AccountCategory.objects.get_or_create(company=company, code='3', name='Equity')
        income_cat, _ = AccountCategory.objects.get_or_create(company=company, code='4', name='Income')
        expense_cat, _ = AccountCategory.objects.get_or_create(company=company, code='5', name='Expense')
        cash_group, _ = AccountGroup.objects.get_or_create(company=company, category=asset_cat, code='1.1', name='Cash & Bank')
        ar_group, _ = AccountGroup.objects.get_or_create(company=company, category=asset_cat, code='1.2', name='Accounts Receivable')
        ap_group, _ = AccountGroup.objects.get_or_create(company=company, category=liab_cat, code='2.1', name='Accounts Payable')
        sales_group, _ = AccountGroup.objects.get_or_create(company=company, category=income_cat, code='4.1', name='Sales Revenue')
        salary_exp_group, _ = AccountGroup.objects.get_or_create(company=company, category=expense_cat, code='5.1', name='Salaries')
        cash_acc, _ = Account.objects.get_or_create(company=company, group=cash_group, code='1.1.1', name='Cash', type='asset', is_group=False, is_active=True)
        ar_acc, _ = Account.objects.get_or_create(company=company, group=ar_group, code='1.2.1', name='Accounts Receivable', type='asset', is_group=False, is_active=True)
        ap_acc, _ = Account.objects.get_or_create(company=company, group=ap_group, code='2.1.1', name='Accounts Payable', type='liability', is_group=False, is_active=True)
        sales_acc, _ = Account.objects.get_or_create(company=company, group=sales_group, code='4.1.1', name='Sales Revenue', type='income', is_group=False, is_active=True)
        salary_exp_acc, _ = Account.objects.get_or_create(company=company, group=salary_exp_group, code='5.1.1', name='Salaries Expense', type='expense', is_group=False, is_active=True)
        # Customers
        cust1, _ = Customer.objects.get_or_create(company=company, name='Acme Corp', defaults={'email': 'acme@example.com', 'created_by': admin, 'account': ar_acc})
        cust2, _ = Customer.objects.get_or_create(company=company, name='Beta LLC', defaults={'email': 'beta@example.com', 'created_by': admin, 'account': ar_acc})
        # Products
        prod1, _ = Product.objects.get_or_create(company=company, name='Widget', defaults={'price': 100, 'is_active': True})
        prod2, _ = Product.objects.get_or_create(company=company, name='Gadget', defaults={'price': 200, 'is_active': True})
        # Sales Orders
        so1, _ = SalesOrder.objects.get_or_create(company=company, customer=cust1, defaults={'total': 100, 'created_by': sales_user, 'account': ar_acc})
        so2, _ = SalesOrder.objects.get_or_create(company=company, customer=cust2, defaults={'total': 200, 'created_by': sales_user, 'account': ar_acc})
        # Inventory
        cat, _ = ProductCategory.objects.get_or_create(company=company, name='General')
        wh, _ = Warehouse.objects.get_or_create(company=company, name='Main Warehouse')
        stock1, _ = StockItem.objects.get_or_create(company=company, product=prod1, warehouse=wh, category=cat, defaults={'quantity': 50, 'is_active': True, 'account': cash_acc})
        stock2, _ = StockItem.objects.get_or_create(company=company, product=prod2, warehouse=wh, category=cat, defaults={'quantity': 30, 'is_active': True, 'account': cash_acc})
        # Suppliers & Purchase
        supp1, _ = Supplier.objects.get_or_create(company=company, name='SupplyCo', defaults={'email': 'supply@example.com', 'created_by': admin})
        po1, _ = PurchaseOrder.objects.get_or_create(company=company, supplier=supp1, defaults={'total': 150, 'created_by': admin, 'account': ap_acc})
        bill1, _ = Bill.objects.get_or_create(company=company, supplier=supp1, purchase_order=po1, defaults={'total': 150, 'created_by': admin, 'account': ap_acc})
        # HR
        emp1, _ = Employee.objects.get_or_create(company=company, first_name='Alice', last_name='Anderson', defaults={'email': 'alice@demo.com'})
        emp2, _ = Employee.objects.get_or_create(company=company, first_name='Bob', last_name='Brown', defaults={'email': 'bob@demo.com'})
        payroll1, _ = Payroll.objects.get_or_create(employee=emp1, period_start=date(2023,1,1), period_end=date(2023,1,31), defaults={'basic_salary': 3000, 'deductions': 200, 'bonuses': 100, 'net_salary': 2900, 'status': 'Paid'})
        # Manufacturing
        bom1, _ = BillOfMaterials.objects.get_or_create(company=company, product=prod1, name='Widget BOM', defaults={'version': 'v1', 'created_by': admin})
        wo1, _ = WorkOrder.objects.get_or_create(company=company, bom=bom1, product=prod1, defaults={'quantity': 10, 'status': 'Completed', 'created_by': admin})
        # Project Management
        proj1, _ = Project.objects.get_or_create(company=company, name='ERP Launch', defaults={'description': 'ERP rollout project', 'created_by': admin})
        task1, _ = Task.objects.get_or_create(project=proj1, name='Setup Server', defaults={'assigned_to': emp1, 'status': 'Done'})
        task2, _ = Task.objects.get_or_create(project=proj1, name='Data Migration', defaults={'assigned_to': emp2, 'status': 'In Progress'})
        self.stdout.write(self.style.SUCCESS('Seeded ERP database with demo data for all modules.')) 