from rest_framework import serializers
from .models import (
    Account, AccountCategory, AccountGroup, Journal, JournalEntry, JournalItem, 
    AccountPayable, AccountReceivable, BankAccount, BankReconciliation, TaxConfig, 
    Currency, FinancialStatement, AccountingAuditLog, RecurringJournal
)
from .integration import ModuleAccountMapping, AutoJournalEntry


class AccountCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountCategory
        fields = '__all__'


class AccountGroupSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    
    class Meta:
        model = AccountGroup
        fields = ['id', 'company', 'category', 'category_name', 'code', 'name', 'parent', 'parent_name', 'description', 'is_active']


class AccountSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source='group.name', read_only=True)
    category_name = serializers.CharField(source='group.category.name', read_only=True)
    balance = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    
    class Meta:
        model = Account
        fields = ['id', 'company', 'group', 'group_name', 'category_name', 'code', 'name', 'description', 
                 'type', 'parent', 'is_group', 'is_default', 'is_active', 'balance_side', 'account_type', 
                 'balance', 'created_at', 'updated_at']


class JournalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Journal
        fields = '__all__'


class JournalItemSerializer(serializers.ModelSerializer):
    account_name = serializers.CharField(source='account.name', read_only=True)
    account_code = serializers.CharField(source='account.code', read_only=True)
    
    class Meta:
        model = JournalItem
        fields = ['id', 'entry', 'account', 'account_name', 'account_code', 'debit', 'credit', 'description']


class JournalEntrySerializer(serializers.ModelSerializer):
    items = JournalItemSerializer(many=True, read_only=True)
    journal_name = serializers.CharField(source='journal.name', read_only=True)
    total_debit = serializers.SerializerMethodField()
    total_credit = serializers.SerializerMethodField()
    is_balanced = serializers.SerializerMethodField()
    
    class Meta:
        model = JournalEntry
        fields = ['id', 'journal', 'journal_name', 'date', 'reference', 'created_by', 'company', 
                 'items', 'total_debit', 'total_credit', 'is_balanced', 'created_at', 'updated_at']
    
    def get_total_debit(self, obj):
        return sum(item.debit for item in obj.items.all())
    
    def get_total_credit(self, obj):
        return sum(item.credit for item in obj.items.all())
    
    def get_is_balanced(self, obj):
        total_debit = sum(item.debit for item in obj.items.all())
        total_credit = sum(item.credit for item in obj.items.all())
        return total_debit == total_credit


class ModuleAccountMappingSerializer(serializers.ModelSerializer):
    debit_account_name = serializers.CharField(source='debit_account.name', read_only=True)
    credit_account_name = serializers.CharField(source='credit_account.name', read_only=True)
    
    class Meta:
        model = ModuleAccountMapping
        fields = ['id', 'company', 'transaction_type', 'debit_account', 'debit_account_name', 
                 'credit_account', 'credit_account_name', 'is_active', 'created_at', 'updated_at']


class AutoJournalEntrySerializer(serializers.ModelSerializer):
    journal_entry_reference = serializers.CharField(source='journal_entry.reference', read_only=True)
    
    class Meta:
        model = AutoJournalEntry
        fields = ['id', 'company', 'journal_entry', 'journal_entry_reference', 'source_module', 
                 'source_model', 'source_object_id', 'transaction_type', 'amount', 'description', 
                 'is_reversed', 'created_at']

class AccountPayableSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountPayable
        fields = '__all__'

class AccountReceivableSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountReceivable
        fields = '__all__'

class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = '__all__'

class BankReconciliationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankReconciliation
        fields = '__all__'

class TaxConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxConfig
        fields = '__all__'

class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = '__all__'

class FinancialStatementSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialStatement
        fields = '__all__'

class AccountingAuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountingAuditLog
        fields = '__all__'

class RecurringJournalSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecurringJournal
        fields = '__all__' 