from django.urls import path
from .views import ProductPageView
from .views import TaxPageView
from .views import QuotationPageView
from .views import SalesOrderPageView

urlpatterns = [
    path('products-ui/', ProductPageView.as_view(), name='product_page'),
]

urlpatterns += [
    path('taxes-ui/', TaxPageView.as_view(), name='tax_page'),
]

urlpatterns += [
    path('quotations-ui/', QuotationPageView.as_view(), name='quotation_page'),
]

urlpatterns += [
    path('salesorders-ui/', SalesOrderPageView.as_view(), name='salesorder_page'),
] 