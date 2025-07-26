from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.analytics_dashboard, name='analytics_dashboard'),
    path('dashboard-ui/', views.dashboard_ui, name='analytics_dashboard_ui'),
    path('sales-reports-ui/', views.sales_reports_ui, name='analytics_sales_reports_ui'),
    path('financial-reports-ui/', views.financial_reports_ui, name='analytics_financial_reports_ui'),
    path('inventory-reports-ui/', views.inventory_reports_ui, name='analytics_inventory_reports_ui'),
]
