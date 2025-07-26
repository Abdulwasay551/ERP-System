from django.urls import path
from .views import (
    ProductPageView, TaxPageView, QuotationPageView, SalesOrderPageView, InvoicePageView,
    products_ui, products_add, products_edit, products_delete,
    taxes_add, taxes_edit, taxes_delete,
    quotations_add, quotations_edit, quotations_delete,
    salesorders_add, salesorders_edit, salesorders_delete,
    quotation_items_add, quotation_items_edit, quotation_items_delete,
    salesorder_items_add, salesorder_items_edit, salesorder_items_delete
)

urlpatterns = [
    # Product URLs
    path('products/', ProductPageView.as_view(), name='sales_products'),
    path('products-ui/', products_ui, name='sales_products_ui'),
    path('products-add/', products_add, name='sales_products_add'),
    path('products-edit/<int:pk>/', products_edit, name='sales_products_edit'),
    path('products-delete/<int:pk>/', products_delete, name='sales_products_delete'),
    
    # Tax URLs
    path('taxes/', TaxPageView.as_view(), name='sales_taxes'),
    path('taxes-add/', taxes_add, name='sales_taxes_add'),
    path('taxes-edit/<int:pk>/', taxes_edit, name='sales_taxes_edit'),
    path('taxes-delete/<int:pk>/', taxes_delete, name='sales_taxes_delete'),
    
    # Quotation URLs
    path('quotations/', QuotationPageView.as_view(), name='sales_quotations'),
    path('quotations-add/', quotations_add, name='sales_quotations_add'),
    path('quotations-edit/<int:pk>/', quotations_edit, name='sales_quotations_edit'),
    path('quotations-delete/<int:pk>/', quotations_delete, name='sales_quotations_delete'),
    
    # Quotation Line Items URLs
    path('quotations/<int:quotation_id>/items-add/', quotation_items_add, name='sales_quotation_items_add'),
    path('quotations/<int:quotation_id>/items-edit/<int:item_id>/', quotation_items_edit, name='sales_quotation_items_edit'),
    path('quotations/<int:quotation_id>/items-delete/<int:item_id>/', quotation_items_delete, name='sales_quotation_items_delete'),
    
    # Sales Order URLs
    path('salesorders/', SalesOrderPageView.as_view(), name='sales_orders'),
    path('salesorders-add/', salesorders_add, name='sales_orders_add'),
    path('salesorders-edit/<int:pk>/', salesorders_edit, name='sales_orders_edit'),
    path('salesorders-delete/<int:pk>/', salesorders_delete, name='sales_orders_delete'),
    
    # Sales Order Line Items URLs
    path('salesorders/<int:salesorder_id>/items-add/', salesorder_items_add, name='sales_order_items_add'),
    path('salesorders/<int:salesorder_id>/items-edit/<int:item_id>/', salesorder_items_edit, name='sales_order_items_edit'),
    path('salesorders/<int:salesorder_id>/items-delete/<int:item_id>/', salesorder_items_delete, name='sales_order_items_delete'),
    
    # Invoice URLs
    path('invoices/', InvoicePageView.as_view(), name='sales_invoices'),
]