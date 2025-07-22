from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import (
    Account, Journal, JournalEntry, JournalItem, AccountPayable, AccountReceivable, BankAccount, BankReconciliation, TaxConfig, Currency, FinancialStatement, AccountingAuditLog, RecurringJournal, AccountCategory, AccountGroup
)

@admin.register(AccountCategory)
class AccountCategoryAdmin(ModelAdmin):
    list_display = ('code', 'name', 'company', 'is_active')
    search_fields = ('code', 'name')
    list_filter = ('company', 'is_active')

@admin.register(AccountGroup)
class AccountGroupAdmin(ModelAdmin):
    list_display = ('code', 'name', 'company', 'category', 'parent', 'is_active')
    search_fields = ('code', 'name')
    list_filter = ('company', 'category', 'is_active')

@admin.register(Account)
class AccountAdmin(ModelAdmin):
    list_display = ('code', 'name', 'type', 'company', 'parent', 'is_group', 'is_active')
    search_fields = ('code', 'name')
    list_filter = ('company', 'type', 'is_group', 'is_active')

@admin.register(Journal)
class JournalAdmin(ModelAdmin):
    list_display = ('name', 'type', 'company', 'is_active')
    search_fields = ('name',)
    list_filter = ('company', 'type', 'is_active')

@admin.register(JournalEntry)
class JournalEntryAdmin(ModelAdmin):
    list_display = ('id', 'journal', 'date', 'reference', 'company', 'created_by', 'created_at')
    search_fields = ('id', 'reference', 'journal__name')
    list_filter = ('company', 'journal')

@admin.register(JournalItem)
class JournalItemAdmin(ModelAdmin):
    list_display = ('entry', 'account', 'debit', 'credit', 'description')
    search_fields = ('entry__id', 'account__name', 'description')
    list_filter = ('account',)

@admin.register(AccountPayable)
class AccountPayableAdmin(ModelAdmin):
    list_display = ('id', 'company', 'supplier', 'invoice', 'amount', 'due_date', 'status')
    search_fields = ('id', 'supplier__name', 'invoice', 'status')
    list_filter = ('company', 'status')

@admin.register(AccountReceivable)
class AccountReceivableAdmin(ModelAdmin):
    list_display = ('id', 'company', 'customer', 'invoice', 'amount', 'due_date', 'status')
    search_fields = ('id', 'customer__name', 'invoice', 'status')
    list_filter = ('company', 'status')

@admin.register(BankAccount)
class BankAccountAdmin(ModelAdmin):
    list_display = ('name', 'company', 'number', 'balance', 'is_active')
    search_fields = ('name', 'number')
    list_filter = ('company', 'is_active')

@admin.register(BankReconciliation)
class BankReconciliationAdmin(ModelAdmin):
    list_display = ('bank_account', 'company', 'period_start', 'period_end', 'status')
    search_fields = ('bank_account__name',)
    list_filter = ('company', 'status')

@admin.register(TaxConfig)
class TaxConfigAdmin(ModelAdmin):
    list_display = ('name', 'company', 'rate', 'type', 'is_active')
    search_fields = ('name', 'type')
    list_filter = ('company', 'type', 'is_active')

@admin.register(Currency)
class CurrencyAdmin(ModelAdmin):
    list_display = ('code', 'name', 'symbol', 'is_active')
    search_fields = ('code', 'name')
    list_filter = ('is_active',)

@admin.register(FinancialStatement)
class FinancialStatementAdmin(ModelAdmin):
    list_display = ('type', 'company', 'period_start', 'period_end', 'generated_at')
    search_fields = ('type',)
    list_filter = ('company', 'type')

@admin.register(AccountingAuditLog)
class AccountingAuditLogAdmin(ModelAdmin):
    list_display = ('user', 'action', 'model', 'object_id', 'timestamp')
    search_fields = ('user__email', 'action', 'model', 'object_id', 'details')
    list_filter = ('model', 'action')

@admin.register(RecurringJournal)
class RecurringJournalAdmin(ModelAdmin):
    list_display = ('journal', 'schedule', 'next_run', 'is_active')
    search_fields = ('journal__name', 'schedule')
    list_filter = ('is_active',)
