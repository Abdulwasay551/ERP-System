from django.urls import path
from .api_views import dashboard_stats, profit_report, top_products, low_stock_items

urlpatterns = [
    path('dashboard/', dashboard_stats, name='analytics-dashboard'),
    path('profit-report/', profit_report, name='analytics-profit-report'),
    path('top-products/', top_products, name='analytics-top-products'),
    path('low-stock-items/', low_stock_items, name='analytics-low-stock-items'),
]
