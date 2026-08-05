from rest_framework.routers import DefaultRouter
from django.urls import path
from .api_views import (
    ProductViewSet, TaxViewSet, QuotationViewSet, SalesOrderViewSet, SalesOrderItemViewSet,
    InvoiceViewSet, PaymentViewSet, CreditNoteViewSet, pos_search, pos_checkout, process_sales_return
)

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'taxes', TaxViewSet, basename='tax')
router.register(r'quotations', QuotationViewSet, basename='quotation')
router.register(r'salesorders', SalesOrderViewSet, basename='salesorder')
router.register(r'salesorderitems', SalesOrderItemViewSet, basename='salesorderitem')
router.register(r'invoices', InvoiceViewSet, basename='invoice')
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'returns', CreditNoteViewSet, basename='creditnote')

urlpatterns = [
    # Must come before router.urls - otherwise the CreditNoteViewSet detail route
    # (returns/(?P<pk>...)/) greedily matches "process" as a pk.
    path('returns/process/', process_sales_return, name='sales-return-process'),
    path('pos/search/', pos_search, name='pos-search'),
    path('pos/checkout/', pos_checkout, name='pos-checkout'),
] + router.urls