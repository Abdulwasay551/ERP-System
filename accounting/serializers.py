from rest_framework import serializers
from .models import (
    Account, Journal, JournalEntry, JournalItem, AccountPayable, AccountReceivable, BankAccount, BankReconciliation, TaxConfig, Currency, FinancialStatement, AccountingAuditLog, RecurringJournal
)

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = '__all__'

class JournalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Journal
        fields = '__all__'

class JournalEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = JournalEntry
        fields = '__all__'

class JournalItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = JournalItem
        fields = '__all__'

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