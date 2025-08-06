"""
Service to initialize default account mappings for all modules
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from accounting.models import Account
from accounting.integration import ModuleAccountMapping
from user_auth.models import Company


class Command(BaseCommand):
    help = 'Initialize default account mappings for module integration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company-id',
            type=int,
            help='Company ID to create mappings for (optional, creates for all if not specified)'
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
            self.stdout.write(f'Creating account mappings for {company.name}...')
            self.create_mappings_for_company(company)
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created account mappings for {company.name}')
            )

    @transaction.atomic
    def create_mappings_for_company(self, company):
        """Create default account mappings for a company"""
        
        # Get default accounts by account_type
        try:
            accounts = {
                'receivable': Account.objects.get(company=company, account_type='receivable', is_default=True),
                'payable': Account.objects.get(company=company, account_type='payable', is_default=True),
                'sales': Account.objects.get(company=company, account_type='sales', is_default=True),
                'cogs': Account.objects.get(company=company, account_type='cogs', is_default=True),
                'inventory': Account.objects.get(company=company, account_type='inventory', is_default=True),
                'cash': Account.objects.filter(company=company, account_type='cash').first(),
                'bank': Account.objects.filter(company=company, account_type='bank').first(),
                'salary_payable': Account.objects.filter(company=company, name__icontains='Salaries Payable').first(),
                'salary_expense': Account.objects.filter(company=company, name__icontains='Salaries').first(),
                'wip': Account.objects.filter(company=company, name__icontains='WIP').first(),
                'finished_goods': Account.objects.filter(company=company, name__icontains='Finished Goods').first(),
            }
        except Account.DoesNotExist as e:
            self.stdout.write(
                self.style.ERROR(f'Missing required account for {company.name}: {e}')
            )
            return

        # Define account mappings
        mappings_data = [
            # Sales Module Mappings
            {
                'transaction_type': 'sales_invoice',
                'debit_account': accounts['receivable'],
                'credit_account': accounts['sales'],
            },
            {
                'transaction_type': 'sales_return',
                'debit_account': accounts['sales'],
                'credit_account': accounts['receivable'],
            },
            
            # Purchase Module Mappings
            {
                'transaction_type': 'purchase_invoice',
                'debit_account': accounts['inventory'],
                'credit_account': accounts['payable'],
            },
            {
                'transaction_type': 'purchase_return',
                'debit_account': accounts['payable'],
                'credit_account': accounts['inventory'],
            },
            
            # Inventory Module Mappings
            {
                'transaction_type': 'inventory_receipt',
                'debit_account': accounts['inventory'],
                'credit_account': accounts['payable'],  # or GRN suspense
            },
            {
                'transaction_type': 'inventory_issue',
                'debit_account': accounts['cogs'],
                'credit_account': accounts['inventory'],
            },
            
            # Manufacturing Module Mappings
            {
                'transaction_type': 'material_issue',
                'debit_account': accounts['wip'] if accounts['wip'] else accounts['inventory'],
                'credit_account': accounts['inventory'],
            },
            {
                'transaction_type': 'production_completion',
                'debit_account': accounts['finished_goods'] if accounts['finished_goods'] else accounts['inventory'],
                'credit_account': accounts['wip'] if accounts['wip'] else accounts['inventory'],
            },
            
            # HR Module Mappings
            {
                'transaction_type': 'payroll_salary',
                'debit_account': accounts['salary_expense'] if accounts['salary_expense'] else accounts['receivable'],
                'credit_account': accounts['salary_payable'] if accounts['salary_payable'] else accounts['payable'],
            },
            {
                'transaction_type': 'employee_advance',
                'debit_account': accounts['receivable'],  # Employee advance is receivable
                'credit_account': accounts['cash'] if accounts['cash'] else accounts['bank'],
            },
            
            # CRM Module Mappings
            {
                'transaction_type': 'customer_invoice',
                'debit_account': accounts['receivable'],
                'credit_account': accounts['sales'],
            },
            {
                'transaction_type': 'customer_payment',
                'debit_account': accounts['cash'] if accounts['cash'] else accounts['bank'],
                'credit_account': accounts['receivable'],
            },
            
            # General Cash/Bank Mappings
            {
                'transaction_type': 'bank_payment',
                'debit_account': accounts['payable'],  # Default, should be configured per case
                'credit_account': accounts['bank'] if accounts['bank'] else accounts['cash'],
            },
            {
                'transaction_type': 'bank_receipt',
                'debit_account': accounts['bank'] if accounts['bank'] else accounts['cash'],
                'credit_account': accounts['receivable'],  # Default, should be configured per case
            },
            {
                'transaction_type': 'cash_payment',
                'debit_account': accounts['payable'],  # Default, should be configured per case
                'credit_account': accounts['cash'] if accounts['cash'] else accounts['bank'],
            },
            {
                'transaction_type': 'cash_receipt',
                'debit_account': accounts['cash'] if accounts['cash'] else accounts['bank'],
                'credit_account': accounts['receivable'],  # Default, should be configured per case
            },
        ]
        
        # Create mappings
        for mapping_data in mappings_data:
            if mapping_data['debit_account'] and mapping_data['credit_account']:
                mapping, created = ModuleAccountMapping.objects.get_or_create(
                    company=company,
                    transaction_type=mapping_data['transaction_type'],
                    defaults={
                        'debit_account': mapping_data['debit_account'],
                        'credit_account': mapping_data['credit_account'],
                    }
                )
                if created:
                    self.stdout.write(f'  Created mapping: {mapping}')
                else:
                    self.stdout.write(f'  Mapping already exists: {mapping}')
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'  Skipped {mapping_data["transaction_type"]} - missing required accounts'
                    )
                )
