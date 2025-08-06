"""
Chart of Accounts (COA) Implementation & Initialization
This script creates the complete COA structure as per the ERP requirements.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from accounting.models import AccountCategory, AccountGroup, Account
from user_auth.models import Company


class Command(BaseCommand):
    help = 'Initialize comprehensive Chart of Accounts for ERP system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company-id',
            type=int,
            help='Company ID to create COA for (optional, creates for all if not specified)'
        )

    def handle(self, *args, **options):
        company_id = options.get('company_id')
        
        if company_id:
            companies = Company.objects.filter(id=company_id)
            if not companies.exists():
                self.stdout.write(
                    self.style.ERROR(f'Company with ID {company_id} not found')
                )
                return
        else:
            companies = Company.objects.all()

        for company in companies:
            self.stdout.write(f'Creating COA for {company.name}...')
            self.create_coa_for_company(company)
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created COA for {company.name}')
            )

    @transaction.atomic
    def create_coa_for_company(self, company):
        """Create complete COA structure for a company"""
        
        # 1. Create Account Categories
        categories = self.create_account_categories(company)
        
        # 2. Create Account Groups
        groups = self.create_account_groups(company, categories)
        
        # 3. Create Accounts
        self.create_accounts(company, groups)

    def create_account_categories(self, company):
        """Create top-level account categories"""
        categories_data = [
            {'code': '1', 'name': 'Assets', 'description': 'Resources owned by the business'},
            {'code': '2', 'name': 'Liabilities', 'description': 'Debts and obligations owed by the business'},
            {'code': '3', 'name': 'Equity', 'description': 'Owner\'s interest in the business'},
            {'code': '4', 'name': 'Income', 'description': 'Revenue and earnings from operations'},
            {'code': '5', 'name': 'Cost of Goods Sold', 'description': 'Direct costs of producing goods/services'},
            {'code': '6', 'name': 'Operating Expenses', 'description': 'Costs of running the business'},
            {'code': '7', 'name': 'Other Expenses', 'description': 'Non-operating expenses'},
            {'code': '8', 'name': 'Projects', 'description': 'Project-specific accounts (optional)'},
            {'code': '9', 'name': 'HR & Payroll', 'description': 'Human resources and payroll accounts'},
            {'code': '10', 'name': 'CRM Operations', 'description': 'Customer relationship management accounts'},
            {'code': '11', 'name': 'Internal Transfers', 'description': 'Internal adjustments and transfers'}
        ]
        
        categories = {}
        for cat_data in categories_data:
            category, created = AccountCategory.objects.get_or_create(
                company=company,
                code=cat_data['code'],
                defaults={
                    'name': cat_data['name'],
                    'description': cat_data['description']
                }
            )
            categories[cat_data['code']] = category
            if created:
                self.stdout.write(f'  Created category: {category}')
        
        return categories

    def create_account_groups(self, company, categories):
        """Create account groups for each category"""
        groups_data = [
            # 1. ASSETS
            {'code': '1.1', 'name': 'Current Assets', 'category': '1', 'parent': None},
            {'code': '1.1.1', 'name': 'Cash', 'category': '1', 'parent': '1.1'},
            {'code': '1.1.2', 'name': 'Bank Accounts', 'category': '1', 'parent': '1.1'},
            {'code': '1.1.3', 'name': 'Accounts Receivable', 'category': '1', 'parent': '1.1'},
            {'code': '1.1.4', 'name': 'Inventory', 'category': '1', 'parent': '1.1'},
            {'code': '1.1.5', 'name': 'Advances', 'category': '1', 'parent': '1.1'},
            {'code': '1.2', 'name': 'Non-Current Assets', 'category': '1', 'parent': None},
            {'code': '1.2.1', 'name': 'Fixed Assets', 'category': '1', 'parent': '1.2'},
            {'code': '1.2.2', 'name': 'Accumulated Depreciation', 'category': '1', 'parent': '1.2'},
            
            # 2. LIABILITIES
            {'code': '2.1', 'name': 'Current Liabilities', 'category': '2', 'parent': None},
            {'code': '2.1.1', 'name': 'Accounts Payable', 'category': '2', 'parent': '2.1'},
            {'code': '2.1.2', 'name': 'Accrued Expenses', 'category': '2', 'parent': '2.1'},
            {'code': '2.1.3', 'name': 'Tax Payable', 'category': '2', 'parent': '2.1'},
            {'code': '2.1.4', 'name': 'Short-Term Loans', 'category': '2', 'parent': '2.1'},
            {'code': '2.2', 'name': 'Long-Term Liabilities', 'category': '2', 'parent': None},
            {'code': '2.2.1', 'name': 'Long-Term Loans', 'category': '2', 'parent': '2.2'},
            {'code': '2.2.2', 'name': 'Lease Obligations', 'category': '2', 'parent': '2.2'},
            
            # 3. EQUITY
            {'code': '3.1', 'name': 'Capital Accounts', 'category': '3', 'parent': None},
            {'code': '3.2', 'name': 'Retained Earnings', 'category': '3', 'parent': None},
            {'code': '3.3', 'name': 'Reserves', 'category': '3', 'parent': None},
            {'code': '3.4', 'name': 'Drawings', 'category': '3', 'parent': None},
            
            # 4. INCOME
            {'code': '4.1', 'name': 'Sales Revenue', 'category': '4', 'parent': None},
            {'code': '4.2', 'name': 'Other Income', 'category': '4', 'parent': None},
            
            # 5. COST OF GOODS SOLD
            {'code': '5.1', 'name': 'Direct Material Costs', 'category': '5', 'parent': None},
            {'code': '5.2', 'name': 'Direct Labor', 'category': '5', 'parent': None},
            {'code': '5.3', 'name': 'Manufacturing Overhead', 'category': '5', 'parent': None},
            {'code': '5.4', 'name': 'Adjustments', 'category': '5', 'parent': None},
            
            # 6. OPERATING EXPENSES
            {'code': '6.1', 'name': 'Admin Expenses', 'category': '6', 'parent': None},
            {'code': '6.2', 'name': 'Selling & Distribution', 'category': '6', 'parent': None},
            {'code': '6.3', 'name': 'IT & Subscriptions', 'category': '6', 'parent': None},
            {'code': '6.4', 'name': 'Miscellaneous', 'category': '6', 'parent': None},
            
            # 7. OTHER EXPENSES
            {'code': '7.1', 'name': 'Financial Expenses', 'category': '7', 'parent': None},
            {'code': '7.2', 'name': 'Non-Operating Expenses', 'category': '7', 'parent': None},
        ]
        
        groups = {}
        # Create groups in two passes to handle parent relationships
        for group_data in groups_data:
            parent = groups.get(group_data['parent']) if group_data['parent'] else None
            
            group, created = AccountGroup.objects.get_or_create(
                company=company,
                code=group_data['code'],
                defaults={
                    'name': group_data['name'],
                    'category': categories[group_data['category']],
                    'parent': parent
                }
            )
            groups[group_data['code']] = group
            if created:
                self.stdout.write(f'    Created group: {group}')
        
        return groups

    def create_accounts(self, company, groups):
        """Create detailed accounts for each group"""
        accounts_data = [
            # 1.1.1 Cash Accounts
            {'code': '1.1.1.1', 'name': 'Petty Cash', 'group': '1.1.1', 'type': 'asset', 'balance_side': 'debit', 'account_type': 'cash'},
            {'code': '1.1.1.2', 'name': 'Cash on Hand', 'group': '1.1.1', 'type': 'asset', 'balance_side': 'debit', 'account_type': 'cash'},
            
            # 1.1.2 Bank Accounts
            {'code': '1.1.2.1', 'name': 'Bank - HBL', 'group': '1.1.2', 'type': 'asset', 'balance_side': 'debit', 'account_type': 'bank'},
            {'code': '1.1.2.2', 'name': 'Bank - UBL', 'group': '1.1.2', 'type': 'asset', 'balance_side': 'debit', 'account_type': 'bank'},
            {'code': '1.1.2.3', 'name': 'Bank - Meezan', 'group': '1.1.2', 'type': 'asset', 'balance_side': 'debit', 'account_type': 'bank'},
            
            # 1.1.3 Accounts Receivable
            {'code': '1.1.3.1', 'name': 'Customers - Local', 'group': '1.1.3', 'type': 'asset', 'balance_side': 'debit', 'account_type': 'receivable', 'is_default': True},
            {'code': '1.1.3.2', 'name': 'Customers - International', 'group': '1.1.3', 'type': 'asset', 'balance_side': 'debit', 'account_type': 'receivable'},
            
            # 1.1.4 Inventory Accounts
            {'code': '1.1.4.1', 'name': 'Raw Material Inventory', 'group': '1.1.4', 'type': 'asset', 'balance_side': 'debit', 'account_type': 'inventory', 'is_default': True},
            {'code': '1.1.4.2', 'name': 'WIP Inventory', 'group': '1.1.4', 'type': 'asset', 'balance_side': 'debit', 'account_type': 'inventory'},
            {'code': '1.1.4.3', 'name': 'Finished Goods Inventory', 'group': '1.1.4', 'type': 'asset', 'balance_side': 'debit', 'account_type': 'inventory'},
            {'code': '1.1.4.4', 'name': 'Scrap Inventory', 'group': '1.1.4', 'type': 'asset', 'balance_side': 'debit', 'account_type': 'inventory'},
            {'code': '1.1.4.5', 'name': 'Transit Inventory', 'group': '1.1.4', 'type': 'asset', 'balance_side': 'debit', 'account_type': 'inventory'},
            {'code': '1.1.4.6', 'name': 'Inventory Adjustment', 'group': '1.1.4', 'type': 'asset', 'balance_side': 'debit', 'account_type': 'inventory'},
            
            # 1.1.5 Advances
            {'code': '1.1.5.1', 'name': 'Advance to Employees', 'group': '1.1.5', 'type': 'asset', 'balance_side': 'debit', 'account_type': 'advance'},
            {'code': '1.1.5.2', 'name': 'Advance to Vendors', 'group': '1.1.5', 'type': 'asset', 'balance_side': 'debit', 'account_type': 'advance'},
            
            # 1.2.1 Fixed Assets
            {'code': '1.2.1.1', 'name': 'Machinery', 'group': '1.2.1', 'type': 'asset', 'balance_side': 'debit', 'account_type': 'fixed_asset'},
            {'code': '1.2.1.2', 'name': 'Vehicles', 'group': '1.2.1', 'type': 'asset', 'balance_side': 'debit', 'account_type': 'fixed_asset'},
            {'code': '1.2.1.3', 'name': 'Furniture & Fixtures', 'group': '1.2.1', 'type': 'asset', 'balance_side': 'debit', 'account_type': 'fixed_asset'},
            {'code': '1.2.1.4', 'name': 'Buildings', 'group': '1.2.1', 'type': 'asset', 'balance_side': 'debit', 'account_type': 'fixed_asset'},
            {'code': '1.2.1.5', 'name': 'Computers & Electronics', 'group': '1.2.1', 'type': 'asset', 'balance_side': 'debit', 'account_type': 'fixed_asset'},
            
            # 1.2.2 Accumulated Depreciation
            {'code': '1.2.2.1', 'name': 'Depreciation - Machinery', 'group': '1.2.2', 'type': 'contra', 'balance_side': 'credit', 'account_type': 'depreciation'},
            {'code': '1.2.2.2', 'name': 'Depreciation - Vehicles', 'group': '1.2.2', 'type': 'contra', 'balance_side': 'credit', 'account_type': 'depreciation'},
            {'code': '1.2.2.3', 'name': 'Depreciation - Others', 'group': '1.2.2', 'type': 'contra', 'balance_side': 'credit', 'account_type': 'depreciation'},
            
            # 2.1.1 Accounts Payable
            {'code': '2.1.1.1', 'name': 'Vendors - Local', 'group': '2.1.1', 'type': 'liability', 'balance_side': 'credit', 'account_type': 'payable', 'is_default': True},
            {'code': '2.1.1.2', 'name': 'Vendors - International', 'group': '2.1.1', 'type': 'liability', 'balance_side': 'credit', 'account_type': 'payable'},
            
            # 2.1.2 Accrued Expenses
            {'code': '2.1.2.1', 'name': 'Salaries Payable', 'group': '2.1.2', 'type': 'liability', 'balance_side': 'credit', 'account_type': 'accrued'},
            {'code': '2.1.2.2', 'name': 'Rent Payable', 'group': '2.1.2', 'type': 'liability', 'balance_side': 'credit', 'account_type': 'accrued'},
            {'code': '2.1.2.3', 'name': 'Utilities Payable', 'group': '2.1.2', 'type': 'liability', 'balance_side': 'credit', 'account_type': 'accrued'},
            
            # 2.1.3 Tax Payable
            {'code': '2.1.3.1', 'name': 'Sales Tax Payable', 'group': '2.1.3', 'type': 'liability', 'balance_side': 'credit', 'account_type': 'tax'},
            {'code': '2.1.3.2', 'name': 'Withholding Tax Payable', 'group': '2.1.3', 'type': 'liability', 'balance_side': 'credit', 'account_type': 'tax'},
            
            # 3.1 Capital Accounts
            {'code': '3.1.1', 'name': 'Owner\'s Capital', 'group': '3.1', 'type': 'equity', 'balance_side': 'credit', 'account_type': 'capital'},
            {'code': '3.1.2', 'name': 'Partner\'s Capital', 'group': '3.1', 'type': 'equity', 'balance_side': 'credit', 'account_type': 'capital'},
            
            # 4.1 Sales Revenue
            {'code': '4.1.1', 'name': 'Product Sales - Local', 'group': '4.1', 'type': 'income', 'balance_side': 'credit', 'account_type': 'sales', 'is_default': True},
            {'code': '4.1.2', 'name': 'Product Sales - Export', 'group': '4.1', 'type': 'income', 'balance_side': 'credit', 'account_type': 'sales'},
            {'code': '4.1.3', 'name': 'Service Revenue', 'group': '4.1', 'type': 'income', 'balance_side': 'credit', 'account_type': 'sales'},
            {'code': '4.1.4', 'name': 'POS Sales', 'group': '4.1', 'type': 'income', 'balance_side': 'credit', 'account_type': 'sales'},
            
            # 4.2 Other Income
            {'code': '4.2.1', 'name': 'Rental Income', 'group': '4.2', 'type': 'income', 'balance_side': 'credit', 'account_type': 'other_income'},
            {'code': '4.2.2', 'name': 'Commission Income', 'group': '4.2', 'type': 'income', 'balance_side': 'credit', 'account_type': 'other_income'},
            {'code': '4.2.3', 'name': 'Discount Received', 'group': '4.2', 'type': 'income', 'balance_side': 'credit', 'account_type': 'other_income'},
            {'code': '4.2.4', 'name': 'Interest Income', 'group': '4.2', 'type': 'income', 'balance_side': 'credit', 'account_type': 'other_income'},
            
            # 5.1 Direct Material Costs
            {'code': '5.1.1', 'name': 'Raw Material - Local', 'group': '5.1', 'type': 'expense', 'balance_side': 'debit', 'account_type': 'cogs', 'is_default': True},
            {'code': '5.1.2', 'name': 'Raw Material - Imported', 'group': '5.1', 'type': 'expense', 'balance_side': 'debit', 'account_type': 'cogs'},
            {'code': '5.1.3', 'name': 'Freight & Insurance', 'group': '5.1', 'type': 'expense', 'balance_side': 'debit', 'account_type': 'cogs'},
            
            # 5.2 Direct Labor
            {'code': '5.2.1', 'name': 'Wages - Production', 'group': '5.2', 'type': 'expense', 'balance_side': 'debit', 'account_type': 'cogs'},
            {'code': '5.2.2', 'name': 'Supervisor Salaries', 'group': '5.2', 'type': 'expense', 'balance_side': 'debit', 'account_type': 'cogs'},
            
            # 5.3 Manufacturing Overhead
            {'code': '5.3.1', 'name': 'Power & Fuel', 'group': '5.3', 'type': 'expense', 'balance_side': 'debit', 'account_type': 'cogs'},
            {'code': '5.3.2', 'name': 'Factory Rent', 'group': '5.3', 'type': 'expense', 'balance_side': 'debit', 'account_type': 'cogs'},
            {'code': '5.3.3', 'name': 'Depreciation - Factory Equipment', 'group': '5.3', 'type': 'expense', 'balance_side': 'debit', 'account_type': 'cogs'},
            
            # 6.1 Admin Expenses
            {'code': '6.1.1', 'name': 'Salaries - Admin', 'group': '6.1', 'type': 'expense', 'balance_side': 'debit', 'account_type': 'admin'},
            {'code': '6.1.2', 'name': 'Rent - Office', 'group': '6.1', 'type': 'expense', 'balance_side': 'debit', 'account_type': 'admin'},
            {'code': '6.1.3', 'name': 'Utilities - Office', 'group': '6.1', 'type': 'expense', 'balance_side': 'debit', 'account_type': 'admin'},
            {'code': '6.1.4', 'name': 'Office Supplies', 'group': '6.1', 'type': 'expense', 'balance_side': 'debit', 'account_type': 'admin'},
            {'code': '6.1.5', 'name': 'Insurance', 'group': '6.1', 'type': 'expense', 'balance_side': 'debit', 'account_type': 'admin'},
            
            # 6.2 Selling & Distribution
            {'code': '6.2.1', 'name': 'Marketing Expense', 'group': '6.2', 'type': 'expense', 'balance_side': 'debit', 'account_type': 'selling'},
            {'code': '6.2.2', 'name': 'Sales Commission', 'group': '6.2', 'type': 'expense', 'balance_side': 'debit', 'account_type': 'selling'},
            {'code': '6.2.3', 'name': 'Travel Expense', 'group': '6.2', 'type': 'expense', 'balance_side': 'debit', 'account_type': 'selling'},
            {'code': '6.2.4', 'name': 'Transportation & Logistics', 'group': '6.2', 'type': 'expense', 'balance_side': 'debit', 'account_type': 'selling'},
        ]
        
        for account_data in accounts_data:
            account, created = Account.objects.get_or_create(
                company=company,
                code=account_data['code'],
                defaults={
                    'name': account_data['name'],
                    'group': groups[account_data['group']],
                    'type': account_data['type'],
                    'balance_side': account_data['balance_side'],
                    'account_type': account_data['account_type'],
                    'is_default': account_data.get('is_default', False)
                }
            )
            if created:
                self.stdout.write(f'      Created account: {account}')
