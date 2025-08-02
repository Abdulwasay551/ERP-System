from rest_framework.routers import DefaultRouter
from django.urls import path
from .api_views import ProductCategoryViewSet, StockItemViewSet, StockMovementViewSet, WarehouseViewSet, StockAlertViewSet, quick_restock, alerts_export

router = DefaultRouter()
router.register(r'productcategories', ProductCategoryViewSet, basename='productcategory')
router.register(r'warehouses', WarehouseViewSet, basename='warehouse')
router.register(r'stockitems', StockItemViewSet, basename='stockitem')
router.register(r'stockmovements', StockMovementViewSet, basename='stockmovement')
router.register(r'stockalerts', StockAlertViewSet, basename='stockalert')

urlpatterns = router.urls + [
    path('quick-restock/<int:item_id>/', quick_restock, name='quick-restock'),
    path('alerts/export/', alerts_export, name='alerts-export'),
] 