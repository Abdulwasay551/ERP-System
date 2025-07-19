from rest_framework.routers import DefaultRouter
from .api_views import (
    AccountViewSet, JournalViewSet, JournalEntryViewSet, JournalItemViewSet, AccountPayableViewSet, AccountReceivableViewSet, BankAccountViewSet, BankReconciliationViewSet, TaxConfigViewSet, CurrencyViewSet, FinancialStatementViewSet, AccountingAuditLogViewSet, RecurringJournalViewSet
)

router = DefaultRouter()
router.register(r'accounts', AccountViewSet, basename='account')
router.register(r'journals', JournalViewSet, basename='journal')
router.register(r'journalentries', JournalEntryViewSet, basename='journalentry')
router.register(r'journalitems', JournalItemViewSet, basename='journalitem')
router.register(r'payables', AccountPayableViewSet, basename='accountpayable')
router.register(r'receivables', AccountReceivableViewSet, basename='accountreceivable')
router.register(r'bankaccounts', BankAccountViewSet, basename='bankaccount')
router.register(r'bankreconciliations', BankReconciliationViewSet, basename='bankreconciliation')
router.register(r'taxconfigs', TaxConfigViewSet, basename='taxconfig')
router.register(r'currencies', CurrencyViewSet, basename='currency')
router.register(r'financialstatements', FinancialStatementViewSet, basename='financialstatement')
router.register(r'auditlogs', AccountingAuditLogViewSet, basename='accountingauditlog')
router.register(r'recurringjournals', RecurringJournalViewSet, basename='recurringjournal')

urlpatterns = router.urls 