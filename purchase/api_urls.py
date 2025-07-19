from rest_framework.routers import DefaultRouter
from .api_views import SupplierViewSet, PurchaseOrderViewSet, PurchaseOrderItemViewSet, BillViewSet, PurchasePaymentViewSet

router = DefaultRouter()
router.register(r'suppliers', SupplierViewSet, basename='supplier')
router.register(r'purchaseorders', PurchaseOrderViewSet, basename='purchaseorder')
router.register(r'purchaseorderitems', PurchaseOrderItemViewSet, basename='purchaseorderitem')
router.register(r'bills', BillViewSet, basename='bill')
router.register(r'purchasepayments', PurchasePaymentViewSet, basename='purchasepayment')

urlpatterns = router.urls 