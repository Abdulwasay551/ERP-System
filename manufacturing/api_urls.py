from rest_framework.routers import DefaultRouter
from .api_views import (
    WorkCenterViewSet, BillOfMaterialsViewSet, BillOfMaterialsItemViewSet,
    BOMOperationViewSet, WorkOrderViewSet, WorkOrderOperationViewSet,
    OperationLogViewSet, QualityCheckViewSet, MaterialConsumptionViewSet,
    MRPPlanViewSet, MRPRequirementViewSet, ProductionPlanViewSet,
    ProductionPlanItemViewSet, JobCardViewSet, SubcontractorViewSet,
    SubcontractWorkOrderViewSet, DemandForecastViewSet, SupplierLeadTimeViewSet,
    MRPRunLogViewSet, ReorderRuleViewSet, CapacityPlanViewSet
)

router = DefaultRouter()

# Core manufacturing resources
router.register(r'work-centers', WorkCenterViewSet, basename='workcenter')
router.register(r'boms', BillOfMaterialsViewSet, basename='billofmaterials')
router.register(r'bom-items', BillOfMaterialsItemViewSet, basename='billofmaterialsitem')
router.register(r'bom-operations', BOMOperationViewSet, basename='bomoperation')

# Work orders and operations
router.register(r'work-orders', WorkOrderViewSet, basename='workorder')
router.register(r'work-order-operations', WorkOrderOperationViewSet, basename='workorderoperation')
router.register(r'operation-logs', OperationLogViewSet, basename='operationlog')

# Quality and materials
router.register(r'quality-checks', QualityCheckViewSet, basename='qualitycheck')
router.register(r'material-consumption', MaterialConsumptionViewSet, basename='materialconsumption')

# MRP and Planning
router.register(r'mrp-plans', MRPPlanViewSet, basename='mrpplan')
router.register(r'mrp-requirements', MRPRequirementViewSet, basename='mrprequirement')
router.register(r'mrp-run-logs', MRPRunLogViewSet, basename='mrprunlog')
router.register(r'production-plans', ProductionPlanViewSet, basename='productionplan')
router.register(r'production-plan-items', ProductionPlanItemViewSet, basename='productionplanitem')

# Demand and Supply Planning
router.register(r'demand-forecasts', DemandForecastViewSet, basename='demandforecast')
router.register(r'supplier-lead-times', SupplierLeadTimeViewSet, basename='supplierleadtime')
router.register(r'reorder-rules', ReorderRuleViewSet, basename='reorderrule')

# Capacity Planning
router.register(r'capacity-plans', CapacityPlanViewSet, basename='capacityplan')

# Job management
router.register(r'job-cards', JobCardViewSet, basename='jobcard')

# Subcontracting
router.register(r'subcontractors', SubcontractorViewSet, basename='subcontractor')
router.register(r'subcontract-work-orders', SubcontractWorkOrderViewSet, basename='subcontractworkorder')

# Import additional API views
from django.urls import path
from .api_views import (
    bulk_create_purchase_orders, get_mrp_requirement_details,
    create_purchase_order_from_requirement, export_supply_demand_excel,
    save_mrp_settings, create_reorder_purchase_order, export_mrp_report
)

urlpatterns = router.urls + [
    # MRP specific endpoints
    path('bulk-create-pos/', bulk_create_purchase_orders, name='bulk_create_pos'),
    path('mrp-requirements/<int:requirement_id>/', get_mrp_requirement_details, name='mrp_requirement_details'),
    path('mrp-requirements/<int:requirement_id>/create-po/', create_purchase_order_from_requirement, name='create_po_from_requirement'),
    path('mrp-settings/', save_mrp_settings, name='save_mrp_settings'),
    path('create-reorder-po/<int:product_id>/', create_reorder_purchase_order, name='create_reorder_po'),
    
    # Export endpoints
    path('export-supply-demand-excel/', export_supply_demand_excel, name='export_supply_demand_excel'),
    path('export-mrp-report/', export_mrp_report, name='export_mrp_report'),
] 