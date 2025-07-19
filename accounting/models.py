from django.db import models
from user_auth.models import Company, User
from crm.models import Customer
from purchase.models import Supplier

class Account(models.Model):
    ACCOUNT_TYPES = [
        ('asset', 'Asset'),
        ('liability', 'Liability'),
        ('equity', 'Equity'),
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='accounts')
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    is_group = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

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

class AccountPayable(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='payables')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='payables')
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
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='receivables')
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
