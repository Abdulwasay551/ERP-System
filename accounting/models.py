# ---
# Multi-level Chart of Accounts (COA) implementation as per coa_implementation_plan.md
# Includes AccountCategory, AccountGroup, and Account models for normalized, hierarchical COA
# ---
from django.db import models
from user_auth.models import Company, User
from purchase.models import Supplier  

# --- Chart of Accounts (COA) Hierarchy ---
# Top-level: AccountCategory (e.g., Asset, Liability)
# Mid-level: AccountGroup (e.g., Current Assets, Non-Current Assets)
# Leaf: Account (actual ledger, e.g., Cash, Inventory)

class AccountCategory(models.Model):
    """
    Top-level COA category (e.g., Asset, Liability, Equity, Income, Expense, Contra-accounts)
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='account_categories')
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('company', 'code')  # Enforce unique codes per company
        verbose_name_plural = 'Account Categories'

    def __str__(self):
        return f"{self.code} - {self.name}"

class AccountGroup(models.Model):
    """
    Mid-level COA group (e.g., Current Assets, Long-term Liabilities)
    Can be nested (parent-child) for up to 5 levels.
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='account_groups')
    category = models.ForeignKey(AccountCategory, on_delete=models.CASCADE, related_name='groups')
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('company', 'code')  # Enforce unique group codes per company
        verbose_name_plural = 'Account Groups'

    def __str__(self):
        return f"{self.code} - {self.name}"

class Account(models.Model):
    """
    Leaf-level COA account (actual ledger). Supports up to 5-level hierarchy via group/parent.
    """
    ACCOUNT_TYPES = [
        ('asset', 'Asset'),
        ('liability', 'Liability'),
        ('equity', 'Equity'),
        ('income', 'Income'),
        ('expense', 'Expense'),
        ('contra', 'Contra-Account'),
    ]
    BALANCE_SIDES = [
        ('debit', 'Debit'),
        ('credit', 'Credit'),
    ]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='accounts')
    group = models.ForeignKey(AccountGroup, on_delete=models.CASCADE, related_name='accounts')  
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)  # Account metadata/details
    type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)  # Main account type (Asset, Liability, etc.)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')  # For sub-ledger relationships (e.g., customer/vendor sub-accounts)
    is_group = models.BooleanField(default=False, help_text="If true, this is a grouping node, not a posting account.")  # Mark as grouping node (non-posting)
    is_default = models.BooleanField(default=False, help_text="System default account for mapping.")  # For system-wide default account mapping
    is_active = models.BooleanField(default=True)  # Enable/disable account
    balance_side = models.CharField(max_length=10, choices=BALANCE_SIDES, default='debit')  # Normal balance side (debit/credit)
    account_type = models.CharField(max_length=50, blank=True, help_text="Sub-classification, e.g., COGS, Admin Expense, Bank, Receivable, etc.")  # For COA sub-categories
    created_at = models.DateTimeField(auto_now_add=True)  # Audit/history tracking
    updated_at = models.DateTimeField(auto_now=True)  # Audit/history tracking

    class Meta:
        unique_together = ('company', 'code')  # Enforce unique account codes per company
        verbose_name_plural = 'Accounts'

    def __str__(self):
        return f"{self.code} - {self.name}"

# AccountCategory, AccountGroup, and Account form the hierarchical COA structure (category > group > account)


class Journal(models.Model):
    JOURNAL_TYPES = [
        ('general', 'General'),
        ('sales', 'Sales'),
        ('purchase', 'Purchase'),
        ('cash', 'Cash'),
        ('bank', 'Bank'),
    ]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='journals')
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=JOURNAL_TYPES, default='general')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class JournalEntry(models.Model):
    journal = models.ForeignKey(Journal, on_delete=models.CASCADE, related_name='entries')
    date = models.DateField()
    reference = models.CharField(max_length=100, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_journal_entries')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='journal_entries')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Entry #{self.id} - {self.journal.name}"

class JournalItem(models.Model):
    entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='items')
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='journal_items')
    debit = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.account.name}: D{self.debit} C{self.credit}"

class JournalTemplate(models.Model):
    """Template for creating journal entries with predefined accounts and structure"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='journal_templates')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ['company', 'name']

class JournalTemplateItem(models.Model):
    """Individual line items for journal templates"""
    template = models.ForeignKey(JournalTemplate, on_delete=models.CASCADE, related_name='items')
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    description = models.CharField(max_length=255, blank=True)
    debit_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0, blank=True, null=True)
    credit_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0, blank=True, null=True)
    is_amount_variable = models.BooleanField(default=True, help_text="Allow amount to be changed when applying template")
    order = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.template.name} - {self.account.name}"

    class Meta:
        ordering = ['order']

class AccountPayable(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='payables')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='payables',null=True,blank=True)  
    invoice = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    due_date = models.DateField()
    status = models.CharField(max_length=50, default='Unpaid')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"AP #{self.id} - {self.supplier.name}"

class AccountReceivable(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='receivables')
    customer = models.ForeignKey('crm.Customer', on_delete=models.CASCADE, related_name='receivables',null=True,blank=True) 
    invoice = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    due_date = models.DateField()
    status = models.CharField(max_length=50, default='Unpaid')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"AR #{self.id} - {self.customer.name}"

class BankAccount(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='bank_accounts')
    name = models.CharField(max_length=255)
    number = models.CharField(max_length=100, blank=True)
    balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class BankReconciliation(models.Model):
    bank_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='reconciliations')
    period_start = models.DateField()
    period_end = models.DateField()
    status = models.CharField(max_length=50, default='Open')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='bank_reconciliations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Reconciliation {self.bank_account.name} ({self.period_start} - {self.period_end})"

class TaxConfig(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='tax_configs')
    name = models.CharField(max_length=100)
    rate = models.DecimalField(max_digits=5, decimal_places=2)
    type = models.CharField(max_length=50, default='VAT')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.rate}%)"

class Currency(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=50)
    symbol = models.CharField(max_length=10, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

class FinancialStatement(models.Model):
    STATEMENT_TYPES = [
        ('pnl', 'Profit & Loss'),
        ('balance', 'Balance Sheet'),
        ('trial', 'Trial Balance'),
        ('cashflow', 'Cash Flow'),
    ]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='financial_statements')
    type = models.CharField(max_length=20, choices=STATEMENT_TYPES)
    period_start = models.DateField()
    period_end = models.DateField()
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_type_display()} ({self.period_start} - {self.period_end})"

class AccountingAuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=255)
    model = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user} - {self.action} {self.model} #{self.object_id}"

class RecurringJournal(models.Model):
    journal = models.ForeignKey(Journal, on_delete=models.CASCADE, related_name='recurring_journals')
    schedule = models.CharField(max_length=100)
    next_run = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Recurring {self.journal.name} ({self.schedule})"


# Module Integration Models
# These models handle automatic journal entry creation when transactions occur in other modules

class ModuleAccountMapping(models.Model):
    """
    Maps specific transaction types to Chart of Accounts
    This allows configuration of which accounts to use for different module operations
    """
    TRANSACTION_TYPES = [
        # Sales Module
        ('sales_invoice', 'Sales Invoice'),
        ('sales_return', 'Sales Return'),
        ('sales_discount', 'Sales Discount'),
        
        # Purchase Module
        ('purchase_invoice', 'Purchase Invoice'),
        ('purchase_return', 'Purchase Return'),
        ('purchase_discount', 'Purchase Discount'),
        
        # Inventory Module
        ('inventory_receipt', 'Inventory Receipt'),
        ('inventory_issue', 'Inventory Issue'),
        ('inventory_adjustment', 'Inventory Adjustment'),
        ('inventory_transfer', 'Inventory Transfer'),
        
        # Manufacturing Module
        ('material_issue', 'Material Issue to Production'),
        ('production_completion', 'Production Completion'),
        ('work_order_cost', 'Work Order Cost'),
        ('manufacturing_overhead', 'Manufacturing Overhead'),
        
        # HR Module
        ('payroll_salary', 'Payroll Salary'),
        ('payroll_bonus', 'Payroll Bonus'),
        ('employee_advance', 'Employee Advance'),
        ('employee_expense', 'Employee Expense'),
        
        # CRM Module
        ('customer_invoice', 'Customer Invoice'),
        ('customer_payment', 'Customer Payment'),
        
        # Project Module
        ('project_expense', 'Project Expense'),
        ('project_billing', 'Project Billing'),
        
        # General
        ('bank_transfer', 'Bank Transfer'),
        ('cash_receipt', 'Cash Receipt'),
        ('cash_payment', 'Cash Payment'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='module_account_mappings')
    transaction_type = models.CharField(max_length=50, choices=TRANSACTION_TYPES)
    debit_account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='debit_mappings')
    credit_account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='credit_mappings')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['company', 'transaction_type']
        verbose_name = 'Module Account Mapping'
        verbose_name_plural = 'Module Account Mappings'
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.company.name}"


class AutoJournalEntry(models.Model):
    """
    Tracks automatically created journal entries from other modules
    This provides audit trail and traceability
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='auto_journal_entries')
    journal_entry = models.OneToOneField(JournalEntry, on_delete=models.CASCADE, related_name='auto_entry')
    source_module = models.CharField(max_length=50)
    source_model = models.CharField(max_length=100)
    source_object_id = models.CharField(max_length=100)
    transaction_type = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Auto Journal Entry'
        verbose_name_plural = 'Auto Journal Entries'
        indexes = [
            models.Index(fields=['source_module', 'source_model', 'source_object_id']),
            models.Index(fields=['transaction_type']),
        ]
    
    def __str__(self):
        return f"Auto JE #{self.journal_entry.id} from {self.source_module}.{self.source_model}"


# Additional models for new features

class AccountTemplate(models.Model):
    """Predefined chart of accounts templates for different business types"""
    TEMPLATE_CATEGORIES = [
        ('retail', 'Retail Business'),
        ('manufacturing', 'Manufacturing'),
        ('service', 'Service Business'),
        ('consulting', 'Consulting'),
        ('restaurant', 'Restaurant/Food Service'),
        ('healthcare', 'Healthcare'),
        ('construction', 'Construction'),
        ('nonprofit', 'Non-Profit'),
        ('ecommerce', 'E-Commerce'),
        ('custom', 'Custom Template'),
    ]
    
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=TEMPLATE_CATEGORIES)
    description = models.TextField()
    is_system = models.BooleanField(default=True, help_text="System template vs custom template")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Account Template'
        verbose_name_plural = 'Account Templates'
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"
    
    @property
    def account_count(self):
        return self.template_accounts.count()
    
    @property
    def group_count(self):
        return self.template_groups.count()


class AccountTemplateGroup(models.Model):
    """Account groups within a template"""
    template = models.ForeignKey(AccountTemplate, on_delete=models.CASCADE, related_name='template_groups')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    category_name = models.CharField(max_length=50)  # Asset, Liability, etc.
    parent_code = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)
    
    class Meta:
        unique_together = ('template', 'code')
    
    def __str__(self):
        return f"{self.template.name} - {self.name}"


class AccountTemplateAccount(models.Model):
    """Accounts within a template"""
    template = models.ForeignKey(AccountTemplate, on_delete=models.CASCADE, related_name='template_accounts')
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=20)
    account_type = models.CharField(max_length=20, choices=Account.ACCOUNT_TYPES)
    balance_side = models.CharField(max_length=10, choices=Account.BALANCE_SIDES)
    group_code = models.CharField(max_length=20, blank=True)
    parent_code = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('template', 'code')
    
    def __str__(self):
        return f"{self.template.name} - {self.code} {self.name}"


class AccountReconciliation(models.Model):
    """Bank reconciliation records"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='reconciliations')
    reconciliation_date = models.DateField()
    statement_date = models.DateField()
    statement_balance = models.DecimalField(max_digits=15, decimal_places=2)
    book_balance = models.DecimalField(max_digits=15, decimal_places=2)
    difference = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Account Reconciliation'
        verbose_name_plural = 'Account Reconciliations'
    
    def __str__(self):
        return f"Reconciliation for {self.account.name} - {self.statement_date}"
    
    def save(self, *args, **kwargs):
        self.difference = self.statement_balance - self.book_balance
        super().save(*args, **kwargs)


class ImportExportOperation(models.Model):
    """Track import/export operations"""
    OPERATION_TYPES = [
        ('import', 'Import'),
        ('export', 'Export'),
    ]
    
    DATA_TYPES = [
        ('accounts', 'Accounts'),
        ('groups', 'Account Groups'),
        ('chart', 'Chart of Accounts'),
        ('template', 'Account Template'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    operation_type = models.CharField(max_length=10, choices=OPERATION_TYPES)
    data_type = models.CharField(max_length=20, choices=DATA_TYPES)
    file_name = models.CharField(max_length=255, blank=True)
    file_format = models.CharField(max_length=10, blank=True)  # csv, excel, json
    record_count = models.IntegerField(default=0)
    success_count = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_log = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Import/Export Operation'
        verbose_name_plural = 'Import/Export Operations'
    
    def __str__(self):
        return f"{self.get_operation_type_display()} {self.get_data_type_display()} - {self.created_at.strftime('%Y-%m-%d')}"


class COASettings(models.Model):
    """Chart of Accounts configuration settings"""
    CODE_FORMATS = [
        ('numeric', 'Numeric'),
        ('alphanumeric', 'Alphanumeric'),
        ('hierarchical', 'Hierarchical'),
        ('custom', 'Custom'),
    ]
    
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name='coa_settings')
    
    # Code settings
    code_format = models.CharField(max_length=20, choices=CODE_FORMATS, default='numeric')
    code_length = models.CharField(max_length=10, default='4')
    custom_pattern = models.CharField(max_length=50, blank=True)
    auto_generate_codes = models.BooleanField(default=True)
    strict_code_validation = models.BooleanField(default=True)
    
    # Display settings
    default_view = models.CharField(max_length=20, default='list')
    accounts_per_page = models.CharField(max_length=10, default='50')
    show_account_codes = models.BooleanField(default=True)
    show_balances = models.BooleanField(default=True)
    color_coding = models.BooleanField(default=True)
    hierarchical_indent = models.BooleanField(default=True)
    
    # Security settings
    require_approval_new_accounts = models.BooleanField(default=False)
    restrict_account_deletion = models.BooleanField(default=True)
    log_account_changes = models.BooleanField(default=True)
    log_balance_changes = models.BooleanField(default=True)
    
    # Integration settings
    auto_sales_entries = models.BooleanField(default=True)
    auto_purchase_entries = models.BooleanField(default=True)
    auto_inventory_entries = models.BooleanField(default=True)
    default_sales_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='default_for_sales')
    default_purchase_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='default_for_purchase')
    default_inventory_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='default_for_inventory')
    
    # Backup settings
    auto_backup_enabled = models.BooleanField(default=False)
    backup_frequency = models.CharField(max_length=20, default='weekly')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'COA Settings'
        verbose_name_plural = 'COA Settings'
    
    def __str__(self):
        return f"COA Settings for {self.company.name}"
