from django.urls import path
from .views import (
    manufacturing_dashboard, boms_ui, work_orders_ui, work_order_detail,
    start_work_order, complete_work_order, quality_checks_ui, production_plans_ui,
    mrp_ui, work_centers_ui, create_work_order_from_sales, consume_materials,
    manufacturing_reports, boms_add, boms_edit, boms_delete, workorders_ui,
    production_ui, quality_ui, material_tracking_ui, job_cards_ui, 
    subcontracting_ui, reports_ui, settings_ui, work_center_create,
    work_center_detail, work_center_edit, work_center_manage, work_order_create,
    work_order_edit, production_plan_create, production_plan_edit, production_plan_detail
)

app_name = 'manufacturing'

urlpatterns = [
    # Dashboard
    path('', manufacturing_dashboard, name='dashboard'),
    path('dashboard/', manufacturing_dashboard, name='dashboard'),
    
    # BOMs
    path('boms/', boms_ui, name='boms_ui'),
    path('boms/add/', boms_add, name='bom_create'),
    path('boms/<int:pk>/edit/', boms_edit, name='bom_edit'),
    path('boms/<int:pk>/delete/', boms_delete, name='bom_delete'),
    
    # Work Orders
    path('work-orders/', work_orders_ui, name='work_orders_ui'),
    path('work-orders/create/', work_order_create, name='work_order_create'),
    path('work-orders/<int:wo_id>/', work_order_detail, name='work_order_detail'),
    path('work-orders/<int:wo_id>/edit/', work_order_edit, name='work_order_edit'),
    path('work-orders/<int:wo_id>/start/', start_work_order, name='start_work_order'),
    path('work-orders/<int:wo_id>/complete/', complete_work_order, name='complete_work_order'),
    
    # Quality Checks
    path('quality-checks/', quality_checks_ui, name='quality_checks_ui'),
    
    # Production Plans
    path('production-plans/', production_plans_ui, name='production_plans_ui'),
    path('production-plans/create/', production_plan_create, name='production_plan_create'),
    path('production-plans/<int:plan_id>/edit/', production_plan_edit, name='production_plan_edit'),
    path('production-plans/<int:plan_id>/', production_plan_detail, name='production_plan_detail'),
    
    # MRP
    path('mrp/', mrp_ui, name='mrp_ui'),
    
    # Work Centers
    path('work-centers/', work_centers_ui, name='work_centers_ui'),
    path('work-centers/create/', work_center_create, name='work_center_create'),
    path('work-centers/<int:pk>/', work_center_detail, name='work_center_detail'),
    path('work-centers/<int:pk>/edit/', work_center_edit, name='work_center_edit'),
    path('work-centers/<int:pk>/manage/', work_center_manage, name='work_center_manage'),
    
    # Material Tracking
    path('material-tracking/', material_tracking_ui, name='material_tracking_ui'),
    
    # Job Cards
    path('job-cards/', job_cards_ui, name='job_cards_ui'),
    
    # Subcontracting
    path('subcontracting/', subcontracting_ui, name='subcontracting_ui'),
    
    # Reports
    path('reports/', reports_ui, name='reports_ui'),
    
    # Settings
    path('settings/', settings_ui, name='settings_ui'),
    
    # API endpoints
    path('api/work-orders/from-sales/', create_work_order_from_sales, name='create_work_order_from_sales'),
    path('api/work-orders/<int:wo_id>/consume-materials/', consume_materials, name='consume_materials'),
    path('api/reports/', manufacturing_reports, name='manufacturing_reports'),
    
    # Legacy URLs for backward compatibility
    path('dashboard-ui/', manufacturing_dashboard, name='manufacturing_dashboard_ui'),
    path('boms-ui/', boms_ui, name='manufacturing_boms_ui'),
    path('workorders-ui/', workorders_ui, name='manufacturing_workorders_ui'),
    path('production-ui/', production_ui, name='manufacturing_production_ui'),
    path('quality-ui/', quality_ui, name='manufacturing_quality_ui'),
]