from rest_framework.routers import DefaultRouter
from .api_views import ProductCategoryViewSet, StockItemViewSet, StockMovementViewSet, WarehouseViewSet, StockAlertViewSet

router = DefaultRouter()
router.register(r'productcategories', ProductCategoryViewSet, basename='productcategory')
router.register(r'warehouses', WarehouseViewSet, basename='warehouse')
router.register(r'stockitems', StockItemViewSet, basename='stockitem')
router.register(r'stockmovements', StockMovementViewSet, basename='stockmovement')
router.register(r'stockalerts', StockAlertViewSet, basename='stockalert')

urlpatterns = router.urls 