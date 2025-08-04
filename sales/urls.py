from django.urls import path
from . import views
from .views import (
    sales_dashboard, ProductPageView, CustomerPageView, TaxPageView, SalesReportPageView, QuotationPageView, SalesOrderPageView, InvoicePageView,
    DeliveryNotePageView, PaymentPageView, CurrencyListView, PriceListView, SalesCommissionListView, CreditNoteListView,
    products_ui, products_add, products_edit, products_delete,
    customers_add, customers_edit, customers_delete, customers_detail,
    taxes_add, taxes_edit, taxes_delete, taxes_detail,
    quotations_add, quotations_edit, quotations_delete, quotation_detail, quotation_form_view,
    quotation_confirm, quotation_send,
    salesorders_add, salesorders_edit, salesorders_delete, salesorders_confirm, sales_order_detail,
    invoices_add, invoices_edit, invoices_delete, invoices_send, invoices_mark_paid, invoice_detail,
    quotation_items_add, quotation_items_edit, quotation_items_delete,
    salesorder_items_add, salesorder_items_edit, salesorder_items_delete,
    delivery_note_detail, delivery_notes_create, delivery_notes_export,
    payment_detail, payment_receipt, payments_create, payments_edit, payments_export,
    currencies_create, currency_detail, currencies_update, currencies_delete,
    pricelists_create, pricelist_detail, pricelists_update, pricelists_delete,
    commissions_create, commissions_update, commission_detail, commissions_delete, commissions_mark_paid,
    creditnotes_create, creditnotes_update, creditnote_detail, creditnotes_delete
)

app_name = 'sales'

urlpatterns = [
    # Dashboard
    path('', sales_dashboard, name='dashboard'),
    path('dashboard/', sales_dashboard, name='sales_dashboard'),
    
    # Currency URLs  
    path('currencies/', CurrencyListView.as_view(), name='currencies'),
    path('currencies/create/', currencies_create, name='currencies_create'),
    path('currencies/<int:pk>/', currency_detail, name='currencies_detail'),
    path('currencies/<int:pk>/update/', currencies_update, name='currencies_update'),
    path('currencies/<int:pk>/delete/', currencies_delete, name='currencies_delete'),
    
    # Product URLs
    path('products/', ProductPageView.as_view(), name='sales_products'),
    path('products/add/', products_add, name='products_add'),
    path('products/<int:pk>/edit/', products_edit, name='products_edit'),
    path('products/<int:pk>/delete/', products_delete, name='products_delete'),
    
    # Customer URLs (Sales Integration)
    path('customers/', CustomerPageView.as_view(), name='sales_customers'),
    path('customers/add/', customers_add, name='customers_add'),
    path('customers/<int:pk>/', customers_detail, name='customers_detail'),
    path('customers/<int:pk>/edit/', customers_edit, name='customers_edit'),
    path('customers/<int:pk>/delete/', customers_delete, name='customers_delete'),
    
    # Tax URLs
    path('taxes/', TaxPageView.as_view(), name='taxes'),
    path('taxes/add/', taxes_add, name='taxes_add'),
    path('taxes/<int:pk>/', taxes_detail, name='taxes_detail'),
    path('taxes/<int:pk>/edit/', taxes_edit, name='taxes_edit'),
    path('taxes/<int:pk>/delete/', taxes_delete, name='taxes_delete'),
    
    # Sales Reports URLs
    path('reports/', SalesReportPageView.as_view(), name='sales_reports'),
    
    # Quotation URLs
    path('quotations/', QuotationPageView.as_view(), name='quotations'),
    path('quotations/add/', quotation_form_view, name='quotations_add'),
    path('quotations/<int:pk>/', quotation_detail, name='quotations_detail'),
    path('quotations/<int:pk>/edit/', quotation_form_view, name='quotations_edit'),
    path('quotations/<int:pk>/delete/', quotations_delete, name='quotations_delete'),
    path('quotations/<int:pk>/confirm/', quotation_confirm, name='quotations_confirm'),
    path('quotations/<int:pk>/send/', quotation_send, name='quotations_send'),
    
    # Quotation Line Items URLs
    path('quotations/<int:quotation_id>/items/add/', quotation_items_add, name='quotation_items_add'),
    path('quotations/<int:quotation_id>/items/<int:item_id>/edit/', quotation_items_edit, name='quotation_items_edit'),
    path('quotations/<int:quotation_id>/items/<int:item_id>/delete/', quotation_items_delete, name='quotation_items_delete'),
    
    # Sales Order URLs
    path('sales-orders/', SalesOrderPageView.as_view(), name='sales_orders'),
    path('sales-orders/create/', views.salesorder_form, name='salesorder_create'),
    path('sales-orders/add/', salesorders_add, name='sales_orders_add'),
    path('sales-orders/<int:pk>/', sales_order_detail, name='sales_orders_detail'),
    path('sales-orders/<int:pk>/edit/', views.salesorder_form, name='salesorder_edit_form'),
    path('sales-orders/<int:pk>/update/', salesorders_edit, name='sales_orders_edit'),
    path('sales-orders/<int:pk>/delete/', salesorders_delete, name='sales_orders_delete'),
    path('sales-orders/<int:pk>/confirm/', salesorders_confirm, name='sales_orders_confirm'),
    
    # Sales Order Line Items URLs
    path('sales-orders/<int:salesorder_id>/items/add/', salesorder_items_add, name='sales_order_items_add'),
    path('sales-orders/<int:salesorder_id>/items/<int:item_id>/edit/', salesorder_items_edit, name='sales_order_items_edit'),
    path('sales-orders/<int:salesorder_id>/items/<int:item_id>/delete/', salesorder_items_delete, name='sales_order_items_delete'),
    
    # Invoice URLs
    path('invoices/', InvoicePageView.as_view(), name='invoices'),
    path('invoices/create/', views.invoice_form, name='invoices_create'),
    path('invoices/add/', invoices_add, name='invoices_add'),
    path('invoices/<int:pk>/', invoice_detail, name='invoice_detail'),
    path('invoices/<int:pk>/edit/', views.invoice_form, name='invoices_edit_form'),
    path('invoices/<int:pk>/update/', invoices_edit, name='invoices_edit'),
    path('invoices/<int:pk>/delete/', invoices_delete, name='invoices_delete'),
    path('invoices/<int:pk>/send/', invoices_send, name='invoices_send'),
    path('invoices/<int:pk>/mark-paid/', invoices_mark_paid, name='invoices_mark_paid'),
    
    # Delivery Note URLs
    path('delivery-notes/', DeliveryNotePageView.as_view(), name='delivery_notes'),
    path('delivery-notes/add/', DeliveryNotePageView.as_view(), name='delivery_notes_add'),
    path('delivery-notes/<int:pk>/', delivery_note_detail, name='delivery_notes_detail'),
    path('delivery-notes/create/', delivery_notes_create, name='delivery_notes_create'),
    path('delivery-notes/export/', delivery_notes_export, name='delivery_notes_export'),
    
    # Payment URLs
    path('payments/', PaymentPageView.as_view(), name='payments'),
    path('payments/add/', PaymentPageView.as_view(), name='payments_add'),
    path('payments/<int:pk>/', payment_detail, name='payments_detail'),
    path('payments/<int:pk>/receipt/', payment_receipt, name='payments_receipt'),
    path('payments/<int:pk>/edit/', payments_edit, name='payments_edit'),
    path('payments/create/', payments_create, name='payments_create'),
    path('payments/export/', payments_export, name='payments_export'),
    
    # Price List URLs
    path('price-lists/', PriceListView.as_view(), name='price_lists'),
    path('price-lists/create/', pricelists_create, name='pricelists_create'),
    path('price-lists/<int:pk>/', pricelist_detail, name='pricelists_detail'),
    path('price-lists/<int:pk>/update/', pricelists_update, name='pricelists_update'),
    path('price-lists/<int:pk>/delete/', pricelists_delete, name='pricelists_delete'),
    
    # Sales Commission URLs
    path('commissions/', SalesCommissionListView.as_view(), name='commissions'),
    path('commissions/create/', views.commissions_create, name='commissions_create'),
    path('commissions/<int:pk>/update/', views.commissions_update, name='commissions_update'),
    path('commissions/<int:pk>/detail/', views.commission_detail, name='commission_detail'),
    path('commissions/<int:pk>/delete/', views.commissions_delete, name='commissions_delete'),
    path('commissions/<int:pk>/mark-paid/', views.commissions_mark_paid, name='commissions_mark_paid'),
    
    # Credit Note URLs
    path('credit-notes/', CreditNoteListView.as_view(), name='credit_notes'),
    path('credit-notes/create/', views.creditnotes_create, name='creditnotes_create'),
    path('credit-notes/<int:pk>/update/', views.creditnotes_update, name='creditnotes_update'),
    path('credit-notes/<int:pk>/detail/', views.creditnote_detail, name='creditnote_detail'),
    path('credit-notes/<int:pk>/delete/', views.creditnotes_delete, name='creditnotes_delete'),
]