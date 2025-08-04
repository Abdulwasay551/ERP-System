from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('api/dashboard/', views.analytics_dashboard, name='analytics_dashboard'),
    path('dashboard/', views.dashboard_ui, name='dashboard_ui'),
    path('sales-reports/', views.sales_reports_ui, name='sales_reports_ui'),
    path('sales-reports/', views.sales_reports_ui, name='sales_reports'),  # Added for sidebar consistency
    path('financial-reports/', views.financial_reports_ui, name='financial_reports_ui'),
    path('inventory-reports/', views.inventory_reports_ui, name='inventory_reports_ui'),
    
    # Alternative URL patterns for compatibility
    path('dashboard-ui/', views.dashboard_ui, name='analytics_dashboard_ui'),
    path('sales-reports-ui/', views.sales_reports_ui, name='analytics_sales_reports_ui'),
    path('financial-reports-ui/', views.financial_reports_ui, name='analytics_financial_reports_ui'),
    path('inventory-reports-ui/', views.inventory_reports_ui, name='analytics_inventory_reports_ui'),
]
