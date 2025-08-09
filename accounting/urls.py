from django.urls import path, include
from .views import (
    accounting_dashboard, accounts_ui, accounts_add, accounts_edit, accounts_delete, accounts_detail,
    journals_ui, dynamic_journals, journal_templates_management, journal_create, ledger_ui, trial_balance_ui, reports_ui, analytics_ui,
    balance_sheet_ui, profit_loss_ui, cash_flow_ui, bank_reconciliation_ui, financial_reports_ui,
    module_mappings_ui, settings_ui, account_categories_ui, account_groups_ui,
    chart_of_accounts_ui, account_group_create, account_group_edit, account_group_delete,
    account_types_ui, account_templates_ui, account_analysis_ui, account_reconciliation_ui,
    account_import_export_ui, coa_settings_ui,
    template_create, template_apply, reconciliation_create, reconciliation_detail,
    settings_update, import_accounts, export_accounts,
    api_chart_of_accounts, api_journal_entries, api_create_journal_entry,
    api_journal_entry_detail, api_update_journal_entry, api_delete_journal_entry,
    api_post_journal_entry, api_journal_templates, api_apply_journal_template,
    api_create_journal_template, api_journal_template_detail, api_update_journal_template,
    api_delete_journal_template, api_financial_reports, api_reconciliations, api_create_reconciliation
)
from . import api_urls

app_name = 'accounting'

urlpatterns = [
    # Dashboard
    path('', accounting_dashboard, name='dashboard'),
    path('dashboard/', accounting_dashboard, name='dashboard'),
    
    # Chart of Accounts
    path('chart-of-accounts/', chart_of_accounts_ui, name='chart_of_accounts'),
    path('accounts/', accounts_ui, name='accounts'),
    path('accounts/add/', accounts_add, name='account_create'),
    path('accounts/<int:pk>/', accounts_detail, name='account_detail'),
    path('accounts/<int:pk>/edit/', accounts_edit, name='account_edit'),
    path('accounts/<int:pk>/delete/', accounts_delete, name='account_delete'),
    path('categories/', account_categories_ui, name='account_categories'),
    path('groups/', account_groups_ui, name='account_groups'),
    path('groups/add/', account_group_create, name='account_group_create'),
    path('groups/<int:pk>/edit/', account_group_edit, name='account_group_edit'),
    path('groups/<int:pk>/delete/', account_group_delete, name='account_group_delete'),
    
    # Account Types
    path('types/', account_types_ui, name='account_types'),
    
    # Account Templates
    path('templates/', account_templates_ui, name='account_templates'),
    path('templates/create/', template_create, name='template_create'),
    path('templates/<int:template_id>/apply/', template_apply, name='template_apply'),
    
    # Account Tools
    path('analysis/', account_analysis_ui, name='account_analysis'),
    path('reconciliation/', account_reconciliation_ui, name='account_reconciliation'),
    path('reconciliation/create/', reconciliation_create, name='reconciliation_create'),
    path('reconciliation/<int:reconciliation_id>/', reconciliation_detail, name='reconciliation_detail'),
    path('import-export/', account_import_export_ui, name='account_import_export'),
    path('import-export/template/', template_create, name='template_import_export'),
    path('import-accounts/', import_accounts, name='import_accounts'),
    path('export-accounts/', export_accounts, name='export_accounts'),
    path('import-export/template/', export_accounts, {'template_only': True}, name='export_template'),
    path('coa-settings/', coa_settings_ui, name='coa_settings'),
    path('coa-settings/update/', settings_update, name='settings_update'),
    
    # Journal Entries
    path('journal-entries/', journals_ui, name='journal_entries'),
    path('dynamic-journal-entries/', dynamic_journals, name='dynamic_journal_entries'),
    path('journal-templates/', journal_templates_management, name='journal_templates'),
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
    path('financial-reports/', financial_reports_ui, name='financial_reports'),
    
    # Bank Reconciliation
    path('bank-reconciliation/', bank_reconciliation_ui, name='bank_reconciliation'),
    
    # Analytics
    path('analytics/', analytics_ui, name='analytics'),
    
    # Module Integration
    path('module-mappings/', module_mappings_ui, name='module_mappings'),
    
    # Settings
    path('settings/', settings_ui, name='settings'),
    
    # Custom API endpoints for frontend integration
    path('api/chart-of-accounts/', api_chart_of_accounts, name='api_chart_of_accounts'),
    path('api/journal-entries/', api_journal_entries, name='api_journal_entries'),
    path('api/journal-entries/create/', api_create_journal_entry, name='api_create_journal_entry'),
    path('api/journal-entries/<int:entry_id>/', api_journal_entry_detail, name='api_journal_entry_detail'),
    path('api/journal-entries/<int:entry_id>/update/', api_update_journal_entry, name='api_update_journal_entry'),
    path('api/journal-entries/<int:entry_id>/delete/', api_delete_journal_entry, name='api_delete_journal_entry'),
    path('api/journal-entries/<int:entry_id>/post/', api_post_journal_entry, name='api_post_journal_entry'),
    path('api/journal-templates/', api_journal_templates, name='api_journal_templates'),
    path('api/journal-templates/create/', api_create_journal_template, name='api_create_journal_template'),
    path('api/journal-templates/<int:template_id>/', api_journal_template_detail, name='api_journal_template_detail'),
    path('api/journal-templates/<int:template_id>/update/', api_update_journal_template, name='api_update_journal_template'),
    path('api/journal-templates/<int:template_id>/delete/', api_delete_journal_template, name='api_delete_journal_template'),
    path('api/journal-templates/apply/', api_apply_journal_template, name='api_apply_journal_template'),
    path('api/financial-reports/', api_financial_reports, name='api_financial_reports'),
    path('api/reconciliations/', api_reconciliations, name='api_reconciliations'),
    path('api/reconciliations/create/', api_create_reconciliation, name='api_create_reconciliation'),
    
    # API URLs
    path('api/', include(api_urls)),
]