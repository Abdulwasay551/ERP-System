from rest_framework.routers import DefaultRouter
from .api_views import BillOfMaterialsViewSet, BillOfMaterialsItemViewSet, WorkOrderViewSet, ProductionPlanViewSet, SubcontractorViewSet, SubcontractWorkOrderViewSet

router = DefaultRouter()
router.register(r'boms', BillOfMaterialsViewSet, basename='billofmaterials')
router.register(r'bomitems', BillOfMaterialsItemViewSet, basename='billofmaterialsitem')
router.register(r'workorders', WorkOrderViewSet, basename='workorder')
router.register(r'productionplans', ProductionPlanViewSet, basename='productionplan')
router.register(r'subcontractors', SubcontractorViewSet, basename='subcontractor')
router.register(r'subcontract-workorders', SubcontractWorkOrderViewSet, basename='subcontractworkorder')

urlpatterns = router.urls 