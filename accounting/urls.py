from django.urls import path
from .views import (
    accounts_ui, accounts_add, accounts_edit, accounts_delete,
    journals_ui, ledger_ui, trial_balance_ui, reports_ui
)

urlpatterns = [
    path('accounts-ui/', accounts_ui, name='accounting_accounts_ui'),
    path('accounts-add/', accounts_add, name='accounting_accounts_add'),
    path('accounts-edit/<int:pk>/', accounts_edit, name='accounting_accounts_edit'),
    path('accounts-delete/<int:pk>/', accounts_delete, name='accounting_accounts_delete'),
    path('journals-ui/', journals_ui, name='accounting_journals_ui'),
    path('ledger-ui/', ledger_ui, name='accounting_ledger_ui'),
    path('trial-balance-ui/', trial_balance_ui, name='accounting_trial_balance_ui'),
    path('reports-ui/', reports_ui, name='accounting_reports_ui'),
]