from rest_framework import viewsets, permissions
from .models import (
    Account, Journal, JournalEntry, JournalItem, AccountPayable, AccountReceivable, BankAccount, BankReconciliation, TaxConfig, Currency, FinancialStatement, AccountingAuditLog, RecurringJournal
)
from .serializers import (
    AccountSerializer, JournalSerializer, JournalEntrySerializer, JournalItemSerializer, AccountPayableSerializer, AccountReceivableSerializer, BankAccountSerializer, BankReconciliationSerializer, TaxConfigSerializer, CurrencySerializer, FinancialStatementSerializer, AccountingAuditLogSerializer, RecurringJournalSerializer
)

class AccountViewSet(viewsets.ModelViewSet):
    serializer_class = AccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Account.objects.filter(company=self.request.user.company)

class JournalViewSet(viewsets.ModelViewSet):
    serializer_class = JournalSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Journal.objects.filter(company=self.request.user.company)

class JournalEntryViewSet(viewsets.ModelViewSet):
    serializer_class = JournalEntrySerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return JournalEntry.objects.filter(company=self.request.user.company)

class JournalItemViewSet(viewsets.ModelViewSet):
    serializer_class = JournalItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return JournalItem.objects.filter(entry__company=self.request.user.company)

class AccountPayableViewSet(viewsets.ModelViewSet):
    serializer_class = AccountPayableSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return AccountPayable.objects.filter(company=self.request.user.company)

class AccountReceivableViewSet(viewsets.ModelViewSet):
    serializer_class = AccountReceivableSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return AccountReceivable.objects.filter(company=self.request.user.company)

class BankAccountViewSet(viewsets.ModelViewSet):
    serializer_class = BankAccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return BankAccount.objects.filter(company=self.request.user.company)

class BankReconciliationViewSet(viewsets.ModelViewSet):
    serializer_class = BankReconciliationSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return BankReconciliation.objects.filter(company=self.request.user.company)

class TaxConfigViewSet(viewsets.ModelViewSet):
    serializer_class = TaxConfigSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return TaxConfig.objects.filter(company=self.request.user.company)

class CurrencyViewSet(viewsets.ModelViewSet):
    serializer_class = CurrencySerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Currency.objects.all()

class FinancialStatementViewSet(viewsets.ModelViewSet):
    serializer_class = FinancialStatementSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return FinancialStatement.objects.filter(company=self.request.user.company)

class AccountingAuditLogViewSet(viewsets.ModelViewSet):
    serializer_class = AccountingAuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = AccountingAuditLog.objects.all()

class RecurringJournalViewSet(viewsets.ModelViewSet):
    serializer_class = RecurringJournalSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return RecurringJournal.objects.filter(journal__company=self.request.user.company) 