from rest_framework.routers import DefaultRouter
from .api_views import ProductViewSet, TaxViewSet, QuotationViewSet, SalesOrderViewSet, SalesOrderItemViewSet, InvoiceViewSet, PaymentViewSet

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'taxes', TaxViewSet, basename='tax')
router.register(r'quotations', QuotationViewSet, basename='quotation')
router.register(r'salesorders', SalesOrderViewSet, basename='salesorder')
router.register(r'salesorderitems', SalesOrderItemViewSet, basename='salesorderitem')
router.register(r'invoices', InvoiceViewSet, basename='invoice')
router.register(r'payments', PaymentViewSet, basename='payment')

urlpatterns = router.urls 