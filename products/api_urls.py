from rest_framework.routers import DefaultRouter
from .api_views import (
    ProductViewSet, ProductCategoryViewSet, ProductVariantViewSet,
    ProductTrackingViewSet, AttributeViewSet, AttributeValueViewSet,
    ProductAttributeViewSet
)

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'categories', ProductCategoryViewSet, basename='productcategory')
router.register(r'variants', ProductVariantViewSet, basename='productvariant')
router.register(r'tracking', ProductTrackingViewSet, basename='producttracking')
router.register(r'attributes', AttributeViewSet, basename='attribute')
router.register(r'attribute-values', AttributeValueViewSet, basename='attributevalue')
router.register(r'product-attributes', ProductAttributeViewSet, basename='productattribute')

urlpatterns = router.urls
