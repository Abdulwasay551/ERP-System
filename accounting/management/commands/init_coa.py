"""
Management command to initialize the Chart of Accounts with default structure
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from user_auth.models import Company
from accounting.models import AccountCategory, AccountGroup, Account, ModuleAccountMapping


class Command(BaseCommand):
    help = 'Initialize Chart of Accounts with default structure'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company-id',
            type=int,
            help='Company ID to initialize COA for (optional, will create for all companies if not specified)',
        )

    def handle(self, *args, **options):
        company_id = options.get('company_id')
        
        if company_id:
            try:
                companies = [Company.objects.get(id=company_id)]
            except Company.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Company with ID {company_id} does not exist')
                )
                return
        else:
            companies = Company.objects.all()

        if not companies:
            self.stdout.write(
                self.style.ERROR('No companies found. Please create a company first.')
            )
            return

        for company in companies:
            self.stdout.write(f'Initializing COA for company: {company.name}')
            with transaction.atomic():
                self.create_default_coa(company)
                self.create_default_mappings(company)
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully initialized COA for {company.name}')
            )

    def create_default_coa(self, company):
        """Create default Chart of Accounts structure"""
        
        # Create Account Categories
        categories_data = [
            ('1000', 'Assets', 'Resources owned by the company'),
            ('2000', 'Liabilities', 'Obligations owed by the company'),
            ('3000', 'Equity', 'Owner\'s interest in the company'),
            ('4000', 'Income', 'Revenue and earnings'),
            ('5000', 'Expenses', 'Costs of doing business'),
        ]
        
        categories = {}
        for code, name, description in categories_data:
            category, created = AccountCategory.objects.get_or_create(
                company=company,
                code=code,
                defaults={
                    'name': name,
                    'description': description,
                    'is_active': True
                }
            )
            categories[code] = category
            if created:
                self.stdout.write(f'  Created category: {code} - {name}')

        # Create Account Groups
        groups_data = [
            # Assets
            ('1100', 'Current Assets', '1000', 'Assets expected to be converted to cash within one year'),
            ('1200', 'Fixed Assets', '1000', 'Long-term assets used in operations'),
            ('1300', 'Other Assets', '1000', 'Miscellaneous assets'),
            
            # Liabilities
            ('2100', 'Current Liabilities', '2000', 'Obligations due within one year'),
            ('2200', 'Long-term Liabilities', '2000', 'Obligations due after one year'),
            
            # Equity
            ('3100', 'Owner\'s Equity', '3000', 'Owner\'s investment and retained earnings'),
            
            # Income
            ('4100', 'Operating Revenue', '4000', 'Revenue from primary business operations'),
            ('4200', 'Other Income', '4000', 'Non-operating income'),
            
            # Expenses
            ('5100', 'Cost of Goods Sold', '5000', 'Direct costs of producing goods'),
            ('5200', 'Operating Expenses', '5000', 'General business operating costs'),
            ('5300', 'Other Expenses', '5000', 'Non-operating expenses'),
        ]
        
        groups = {}
        for code, name, category_code, description in groups_data:
            group, created = AccountGroup.objects.get_or_create(
                company=company,
                code=code,
                defaults={
                    'name': name,
                    'category': categories[category_code],
                    'description': description,
                    'is_active': True
                }
            )
            groups[code] = group
            if created:
                self.stdout.write(f'    Created group: {code} - {name}')

        # Create Default Accounts
        accounts_data = [
            # Current Assets
            ('1101', 'Cash', '1100', 'Cash on hand and in bank'),
            ('1102', 'Bank Account', '1100', 'Checking and savings accounts'),
            ('1103', 'Accounts Receivable', '1100', 'Money owed by customers'),
            ('1104', 'Inventory - Raw Materials', '1100', 'Raw materials in stock'),
            ('1105', 'Inventory - Finished Goods', '1100', 'Finished products in stock'),
            ('1106', 'Inventory - Work in Progress', '1100', 'Goods in production'),
            ('1107', 'Prepaid Expenses', '1100', 'Expenses paid in advance'),
            
            # Fixed Assets
            ('1201', 'Equipment', '1200', 'Machinery and equipment'),
            ('1202', 'Accumulated Depreciation - Equipment', '1200', 'Depreciation of equipment'),
            ('1203', 'Buildings', '1200', 'Real estate and buildings'),
            ('1204', 'Accumulated Depreciation - Buildings', '1200', 'Depreciation of buildings'),
            
            # Current Liabilities
            ('2101', 'Accounts Payable', '2100', 'Money owed to suppliers'),
            ('2102', 'Accrued Expenses', '2100', 'Expenses incurred but not yet paid'),
            ('2103', 'Tax Payable', '2100', 'Taxes owed'),
            ('2104', 'Salary Payable', '2100', 'Salaries owed to employees'),
            ('2105', 'Short-term Loans', '2100', 'Loans due within one year'),
            
            # Long-term Liabilities
            ('2201', 'Long-term Loans', '2200', 'Loans due after one year'),
            ('2202', 'Mortgage Payable', '2200', 'Real estate mortgages'),
            
            # Equity
            ('3101', 'Owner\'s Capital', '3100', 'Owner\'s initial investment'),
            ('3102', 'Retained Earnings', '3100', 'Accumulated profits'),
            ('3103', 'Current Year Earnings', '3100', 'Current year profit/loss'),
            
            # Revenue
            ('4101', 'Sales Revenue', '4100', 'Revenue from product sales'),
            ('4102', 'Service Revenue', '4100', 'Revenue from services'),
            ('4201', 'Interest Income', '4200', 'Interest earned on investments'),
            ('4202', 'Other Income', '4200', 'Miscellaneous income'),
            
            # Expenses
            ('5101', 'Cost of Goods Sold', '5100', 'Direct cost of products sold'),
            ('5102', 'Material Costs', '5100', 'Cost of raw materials'),
            ('5103', 'Labor Costs', '5100', 'Direct labor costs'),
            ('5104', 'Manufacturing Overhead', '5100', 'Indirect manufacturing costs'),
            
            ('5201', 'Salaries and Wages', '5200', 'Employee compensation'),
            ('5202', 'Rent Expense', '5200', 'Office and facility rent'),
            ('5203', 'Utilities Expense', '5200', 'Electricity, water, gas'),
            ('5204', 'Office Supplies', '5200', 'Office materials and supplies'),
            ('5205', 'Marketing Expense', '5200', 'Advertising and promotion'),
            ('5206', 'Travel Expense', '5200', 'Business travel costs'),
            ('5207', 'Insurance Expense', '5200', 'Business insurance premiums'),
            ('5208', 'Depreciation Expense', '5200', 'Asset depreciation'),
            
            ('5301', 'Interest Expense', '5300', 'Interest on loans and debt'),
            ('5302', 'Bank Charges', '5300', 'Banking fees and charges'),
            ('5303', 'Tax Expense', '5300', 'Income and other taxes'),
        ]
        
        accounts = {}
        for code, name, group_code, description in accounts_data:
            account, created = Account.objects.get_or_create(
                company=company,
                code=code,
                defaults={
                    'name': name,
                    'group': groups[group_code],
                    'description': description,
                    'is_active': True
                }
            )
            accounts[code] = account
            if created:
                self.stdout.write(f'      Created account: {code} - {name}')
        
        return accounts

    def create_default_mappings(self, company):
        """Create default module account mappings"""
        
        # Get required accounts
        try:
            accounts_receivable = Account.objects.get(company=company, code='1103')
            sales_revenue = Account.objects.get(company=company, code='4101')
            cogs = Account.objects.get(company=company, code='5101')
            inventory_finished = Account.objects.get(company=company, code='1105')
            inventory_raw = Account.objects.get(company=company, code='1104')
            inventory_wip = Account.objects.get(company=company, code='1106')
            accounts_payable = Account.objects.get(company=company, code='2101')
            salary_expense = Account.objects.get(company=company, code='5201')
            salary_payable = Account.objects.get(company=company, code='2104')
            cash = Account.objects.get(company=company, code='1101')
            bank = Account.objects.get(company=company, code='1102')
        except Account.DoesNotExist as e:
            self.stdout.write(
                self.style.ERROR(f'Required account not found: {e}')
            )
            return

        # Create mappings
        mappings_data = [
            # Sales Module
            ('sales_invoice', accounts_receivable, sales_revenue),
            
            # Purchase Module  
            ('purchase_invoice', inventory_raw, accounts_payable),
            
            # Inventory Module
            ('inventory_receipt', inventory_raw, accounts_payable),
            ('inventory_issue', cogs, inventory_finished),
            ('inventory_adjustment', inventory_raw, cogs),
            
            # Manufacturing Module
            ('material_issue', inventory_wip, inventory_raw),
            ('production_completion', inventory_finished, inventory_wip),
            ('manufacturing_overhead', inventory_wip, accounts_payable),
            
            # HR Module
            ('payroll_salary', salary_expense, salary_payable),
            
            # General
            ('cash_receipt', cash, accounts_receivable),
            ('cash_payment', accounts_payable, cash),
            ('bank_transfer', bank, cash),
        ]
        
        for transaction_type, debit_account, credit_account in mappings_data:
            mapping, created = ModuleAccountMapping.objects.get_or_create(
                company=company,
                transaction_type=transaction_type,
                defaults={
                    'debit_account': debit_account,
                    'credit_account': credit_account,
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f'  Created mapping: {transaction_type} - Dr: {debit_account.code} Cr: {credit_account.code}')

        self.stdout.write(f'Created {len(mappings_data)} default account mappings')
