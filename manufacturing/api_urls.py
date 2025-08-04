from rest_framework.routers import DefaultRouter
from .api_views import (
    WorkCenterViewSet, BillOfMaterialsViewSet, BillOfMaterialsItemViewSet,
    BOMOperationViewSet, WorkOrderViewSet, WorkOrderOperationViewSet,
    OperationLogViewSet, QualityCheckViewSet, MaterialConsumptionViewSet,
    MRPPlanViewSet, MRPRequirementViewSet, ProductionPlanViewSet,
    ProductionPlanItemViewSet, JobCardViewSet, SubcontractorViewSet,
    SubcontractWorkOrderViewSet
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

# Planning
router.register(r'mrp-plans', MRPPlanViewSet, basename='mrpplan')
router.register(r'mrp-requirements', MRPRequirementViewSet, basename='mrprequirement')
router.register(r'production-plans', ProductionPlanViewSet, basename='productionplan')
router.register(r'production-plan-items', ProductionPlanItemViewSet, basename='productionplanitem')

# Job management
router.register(r'job-cards', JobCardViewSet, basename='jobcard')

# Subcontracting
router.register(r'subcontractors', SubcontractorViewSet, basename='subcontractor')
router.register(r'subcontract-work-orders', SubcontractWorkOrderViewSet, basename='subcontractworkorder')

urlpatterns = router.urls 