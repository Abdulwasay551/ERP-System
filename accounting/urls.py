from django.urls import path
from .views import accounts_ui

urlpatterns = [
    path('accounts-ui/', accounts_ui, name='accounting_accounts_ui'),
] 