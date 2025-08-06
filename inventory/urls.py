from django.urls import path
from .views import (
    inventory_dashboard, stockitems_ui, stockitem_detail, stockitems_add, stockitems_edit, stockitems_delete,
    warehouses_ui, warehouse_add, warehouse_edit, warehouse_delete, warehouse_detail, stock_movement_add,
    movements_ui, alerts_ui, categories_ui, adjustments_ui, reports_ui,
    transfers_ui, lots_ui, locks_ui, physical_count_ui, warehouse_zones_api, warehouse_bins_api,
    lot_add, lot_details, lot_approve_quality, lot_quarantine, export_expiring_lots,
    locks_create, locks_unlock, locks_bulk_unlock, locks_details, locks_status, locks_export,
    create_adjustment_api, approve_adjustment_api, post_adjustment_api,
    adjustment_detail, adjustment_edit, category_create, category_update, category_delete, category_detail
)

app_name = 'inventory'


urlpatterns = [
    # Dashboard
    path('', inventory_dashboard, name='dashboard'),
    path('dashboard/', inventory_dashboard, name='inventory_dashboard'),
    path('dashboard-ui/', inventory_dashboard, name='inventory_dashboard_ui'),
    
    # Stock Items
    path('stockitems-ui/', stockitems_ui, name='inventory_stockitems_ui'),
    path('stockitem/<int:pk>/', stockitem_detail, name='inventory_stockitem_detail'),
    path('stockitems-add/', stockitems_add, name='inventory_stockitems_add'),
    path('stockitems-edit/<int:pk>/', stockitems_edit, name='inventory_stockitems_edit'),
    path('stockitems-delete/<int:pk>/', stockitems_delete, name='inventory_stockitems_delete'),
    
    # Warehouses
    path('warehouses-ui/', warehouses_ui, name='inventory_warehouses_ui'),
    path('warehouse/<int:pk>/', warehouse_detail, name='inventory_warehouse_detail'),
    path('warehouse-add/', warehouse_add, name='inventory_warehouse_add'),
    path('warehouse-edit/<int:pk>/', warehouse_edit, name='inventory_warehouse_edit'),
    path('warehouse-delete/<int:pk>/', warehouse_delete, name='inventory_warehouse_delete'),
    
    # Stock Movements
    path('movements-ui/', movements_ui, name='inventory_movements_ui'),
    path('stock-movement-add/', stock_movement_add, name='inventory_stock_movement_add'),
    
    # Stock Transfers
    path('transfers-ui/', transfers_ui, name='inventory_transfers_ui'),
    
    # Lot/Batch Tracking
    path('lots-ui/', lots_ui, name='inventory_lots_ui'),
    path('lots/add/', lot_add, name='lot_add'),
    path('lots/<int:lot_id>/details/', lot_details, name='lot_details'),
    path('lots/<int:lot_id>/approve-quality/', lot_approve_quality, name='lot_approve_quality'),
    path('lots/<int:lot_id>/quarantine/', lot_quarantine, name='lot_quarantine'),
    path('lots/export-expiring/', export_expiring_lots, name='export_expiring_lots'),
    
    # Inventory Locks
    path('locks-ui/', locks_ui, name='inventory_locks_ui'),
    path('locks/create/', locks_create, name='locks_create'),
    path('locks/<int:lock_id>/unlock/', locks_unlock, name='locks_unlock'),
    path('locks/bulk-unlock/', locks_bulk_unlock, name='locks_bulk_unlock'),
    path('locks/<int:lock_id>/details/', locks_details, name='locks_details'),
    path('locks/status/', locks_status, name='locks_status'),
    path('locks/export/', locks_export, name='locks_export'),
    
    # Physical Count
    path('physical-count-ui/', physical_count_ui, name='inventory_physical_count_ui'),
    path('adjustments/<int:adjustment_id>/', adjustment_detail, name='adjustment_detail'),
    path('adjustments/<int:adjustment_id>/edit/', adjustment_edit, name='adjustment_edit'),
    
    # Other UIs
    path('alerts-ui/', alerts_ui, name='inventory_alerts_ui'),
    path('categories-ui/', categories_ui, name='inventory_categories_ui'),
    path('adjustments-ui/', adjustments_ui, name='inventory_adjustments_ui'),
    path('reports-ui/', reports_ui, name='inventory_reports_ui'),
    
    # Category Management API endpoints
    path('categories/create/', category_create, name='category_create'),
    path('categories/<int:category_id>/update/', category_update, name='category_update'),
    path('categories/<int:category_id>/delete/', category_delete, name='category_delete'),
    path('categories/<int:category_id>/detail/', category_detail, name='category_detail'),
    
    # API endpoints for dynamic loading
    path('api/warehouse-zones/<int:warehouse_id>/', warehouse_zones_api, name='inventory_warehouse_zones_api'),
    path('api/warehouse-bins/<int:zone_id>/', warehouse_bins_api, name='inventory_warehouse_bins_api'),
    
    # Physical Count API endpoints
    path('api/adjustments/create/', create_adjustment_api, name='create_adjustment_api'),
    path('api/adjustments/<int:adjustment_id>/approve/', approve_adjustment_api, name='approve_adjustment_api'),
    path('api/adjustments/<int:adjustment_id>/post/', post_adjustment_api, name='post_adjustment_api'),
]