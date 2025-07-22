from django.urls import path
from .views import TaxPageView
from .views import QuotationPageView
from .views import SalesOrderPageView
from .views import products_ui, products_add, products_edit, products_delete

urlpatterns = [
    path('products-ui/', products_ui, name='sales_products_ui'),
    path('products-add/', products_add, name='sales_products_add'),
    path('products-edit/<int:pk>/', products_edit, name='sales_products_edit'),
    path('products-delete/<int:pk>/', products_delete, name='sales_products_delete'),
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