from django.urls import path
from .views import accounts_ui, accounts_add, accounts_edit, accounts_delete

urlpatterns = [
    path('accounts-ui/', accounts_ui, name='accounting_accounts_ui'),
    path('accounts-add/', accounts_add, name='accounting_accounts_add'),
    path('accounts-edit/<int:pk>/', accounts_edit, name='accounting_accounts_edit'),
    path('accounts-delete/<int:pk>/', accounts_delete, name='accounting_accounts_delete'),
] 