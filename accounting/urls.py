from django.urls import path, include
from .views import (
    accounting_dashboard, accounts_ui, accounts_add, accounts_edit, accounts_delete,
    journals_ui, journal_create, ledger_ui, trial_balance_ui, reports_ui, analytics_ui,
    balance_sheet_ui, profit_loss_ui, cash_flow_ui, bank_reconciliation_ui,
    module_mappings_ui, settings_ui, account_categories_ui, account_groups_ui
)
from . import api_urls

app_name = 'accounting'

urlpatterns = [
    # Dashboard
    path('', accounting_dashboard, name='dashboard'),
    path('dashboard/', accounting_dashboard, name='dashboard'),
    
    # Chart of Accounts
    path('chart-of-accounts/', accounts_ui, name='chart_of_accounts'),
    path('accounts/', accounts_ui, name='accounts'),
    path('accounts/add/', accounts_add, name='account_create'),
    path('accounts/<int:pk>/edit/', accounts_edit, name='account_edit'),
    path('accounts/<int:pk>/delete/', accounts_delete, name='account_delete'),
    path('categories/', account_categories_ui, name='account_categories'),
    path('groups/', account_groups_ui, name='account_groups'),
    
    # Journal Entries
    path('journal-entries/', journals_ui, name='journal_entries'),
    path('journal-entries/create/', journal_create, name='journal_entry_create'),
    path('journal/', journals_ui, name='journal'),
    path('auto-entries/', journals_ui, name='auto_entries'),
    
    # General Ledger
    path('general-ledger/', ledger_ui, name='general_ledger'),
    path('ledger/', ledger_ui, name='ledger'),
    
    # Financial Reports
    path('trial-balance/', trial_balance_ui, name='trial_balance'),
    path('profit-loss/', profit_loss_ui, name='profit_loss'),
    path('balance-sheet/', balance_sheet_ui, name='balance_sheet'),
    path('cash-flow/', cash_flow_ui, name='cash_flow'),
    path('financial-statements/', reports_ui, name='financial_statements'),
    path('reports/', reports_ui, name='reports'),
    
    # Bank Reconciliation
    path('bank-reconciliation/', bank_reconciliation_ui, name='bank_reconciliation'),
    
    # Analytics
    path('analytics/', analytics_ui, name='analytics'),
    
    # Module Integration
    path('module-mappings/', module_mappings_ui, name='module_mappings'),
    
    # Settings
    path('settings/', settings_ui, name='settings'),
    
    # API URLs
    path('api/', include(api_urls)),
]