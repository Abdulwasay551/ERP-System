from django.core.management.base import BaseCommand
from django.db import transaction
from user_auth.models import Company, User
from accounting.models import (
    Account, JournalTemplate, JournalTemplateItem,
    AccountCategory, AccountGroup
)
from decimal import Decimal


class Command(BaseCommand):
    help = 'Create sample journal templates for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company-id',
            type=int,
            help='Company ID to create templates for',
            default=5
        )

    def handle(self, *args, **options):
        company_id = options['company_id']
        
        try:
            company = Company.objects.get(id=company_id)
            self.stdout.write(f"Creating sample journal templates for company: {company.name}")
        except Company.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Company with ID {company_id} does not exist')
            )
            return

        # Get or create a default user for templates
        user = User.objects.filter(company=company).first()
        if not user:
            self.stdout.write(
                self.style.WARNING('No users found for this company. Templates will be created without a creator.')
            )

        with transaction.atomic():
            self.create_sample_templates(company, user)

    def create_sample_templates(self, company, user):
        """Create sample journal entry templates"""
        
        # Get some common accounts (assuming they exist)
        try:
            cash_account = Account.objects.filter(
                company=company, 
                name__icontains='cash'
            ).first()
            
            ar_account = Account.objects.filter(
                company=company, 
                name__icontains='receivable'
            ).first()
            
            ap_account = Account.objects.filter(
                company=company, 
                name__icontains='payable'
            ).first()
            
            sales_account = Account.objects.filter(
                company=company, 
                type='income'
            ).first()
            
            expense_account = Account.objects.filter(
                company=company, 
                type='expense'
            ).first()
            
            if not any([cash_account, ar_account, ap_account, sales_account, expense_account]):
                self.stdout.write(
                    self.style.WARNING('No suitable accounts found. Please create basic accounts first.')
                )
                return
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error finding accounts: {e}')
            )
            return

        templates_data = []
        
        # Template 1: Sales Entry
        if ar_account and sales_account:
            templates_data.append({
                'name': 'Sales Invoice Entry',
                'description': 'Standard template for recording sales invoices',
                'items': [
                    {
                        'account': ar_account,
                        'description': 'Customer invoice',
                        'debit_amount': None,  # Variable
                        'credit_amount': Decimal('0'),
                        'is_amount_variable': True,
                        'order': 1
                    },
                    {
                        'account': sales_account,
                        'description': 'Sales revenue',
                        'debit_amount': Decimal('0'),
                        'credit_amount': None,  # Variable
                        'is_amount_variable': True,
                        'order': 2
                    }
                ]
            })

        # Template 2: Cash Receipt
        if cash_account and ar_account:
            templates_data.append({
                'name': 'Cash Receipt from Customer',
                'description': 'Template for recording cash receipts from customers',
                'items': [
                    {
                        'account': cash_account,
                        'description': 'Cash received',
                        'debit_amount': None,  # Variable
                        'credit_amount': Decimal('0'),
                        'is_amount_variable': True,
                        'order': 1
                    },
                    {
                        'account': ar_account,
                        'description': 'Payment on account',
                        'debit_amount': Decimal('0'),
                        'credit_amount': None,  # Variable
                        'is_amount_variable': True,
                        'order': 2
                    }
                ]
            })

        # Template 3: Purchase Entry
        if expense_account and ap_account:
            templates_data.append({
                'name': 'Purchase Entry',
                'description': 'Standard template for recording purchase transactions',
                'items': [
                    {
                        'account': expense_account,
                        'description': 'Purchase expense',
                        'debit_amount': None,  # Variable
                        'credit_amount': Decimal('0'),
                        'is_amount_variable': True,
                        'order': 1
                    },
                    {
                        'account': ap_account,
                        'description': 'Amount owed to supplier',
                        'debit_amount': Decimal('0'),
                        'credit_amount': None,  # Variable
                        'is_amount_variable': True,
                        'order': 2
                    }
                ]
            })

        # Template 4: Cash Payment
        if ap_account and cash_account:
            templates_data.append({
                'name': 'Cash Payment to Supplier',
                'description': 'Template for recording cash payments to suppliers',
                'items': [
                    {
                        'account': ap_account,
                        'description': 'Payment to supplier',
                        'debit_amount': None,  # Variable
                        'credit_amount': Decimal('0'),
                        'is_amount_variable': True,
                        'order': 1
                    },
                    {
                        'account': cash_account,
                        'description': 'Cash paid',
                        'debit_amount': Decimal('0'),
                        'credit_amount': None,  # Variable
                        'is_amount_variable': True,
                        'order': 2
                    }
                ]
            })

        # Template 5: Expense Payment
        if expense_account and cash_account:
            templates_data.append({
                'name': 'Office Expense Payment',
                'description': 'Template for recording direct office expense payments',
                'items': [
                    {
                        'account': expense_account,
                        'description': 'Office expenses',
                        'debit_amount': None,  # Variable
                        'credit_amount': Decimal('0'),
                        'is_amount_variable': True,
                        'order': 1
                    },
                    {
                        'account': cash_account,
                        'description': 'Cash paid for expenses',
                        'debit_amount': Decimal('0'),
                        'credit_amount': None,  # Variable
                        'is_amount_variable': True,
                        'order': 2
                    }
                ]
            })

        # Create the templates
        created_count = 0
        for template_data in templates_data:
            try:
                # Check if template already exists
                existing_template = JournalTemplate.objects.filter(
                    company=company,
                    name=template_data['name']
                ).first()
                
                if existing_template:
                    self.stdout.write(
                        self.style.WARNING(f'Template "{template_data["name"]}" already exists, skipping...')
                    )
                    continue

                # Create template
                template = JournalTemplate.objects.create(
                    company=company,
                    name=template_data['name'],
                    description=template_data['description'],
                    created_by=user,
                    is_active=True
                )

                # Create template items
                for item_data in template_data['items']:
                    JournalTemplateItem.objects.create(
                        template=template,
                        account=item_data['account'],
                        description=item_data['description'],
                        debit_amount=item_data['debit_amount'],
                        credit_amount=item_data['credit_amount'],
                        is_amount_variable=item_data['is_amount_variable'],
                        order=item_data['order']
                    )

                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created template: {template.name}')
                )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error creating template "{template_data["name"]}": {e}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} journal templates')
        )
