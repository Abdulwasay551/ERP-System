from django.urls import path
from .views import (
    inventory_dashboard, stockitems_ui, stockitems_add, stockitems_edit, stockitems_delete,
    warehouses_ui, movements_ui, alerts_ui, categories_ui, adjustments_ui, reports_ui
)

urlpatterns = [
    path('dashboard/', inventory_dashboard, name='inventory_dashboard'),
    path('dashboard-ui/', inventory_dashboard, name='inventory_dashboard_ui'),
    path('stockitems-ui/', stockitems_ui, name='inventory_stockitems_ui'),
    path('stockitems-add/', stockitems_add, name='inventory_stockitems_add'),
    path('stockitems-edit/<int:pk>/', stockitems_edit, name='inventory_stockitems_edit'),
    path('stockitems-delete/<int:pk>/', stockitems_delete, name='inventory_stockitems_delete'),
    path('warehouses-ui/', warehouses_ui, name='inventory_warehouses_ui'),
    path('movements-ui/', movements_ui, name='inventory_movements_ui'),
    path('alerts-ui/', alerts_ui, name='inventory_alerts_ui'),
    path('categories-ui/', categories_ui, name='inventory_categories_ui'),
    path('adjustments-ui/', adjustments_ui, name='inventory_adjustments_ui'),
    path('reports-ui/', reports_ui, name='inventory_reports_ui'),
]