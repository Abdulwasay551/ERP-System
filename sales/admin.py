from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Product, Tax, Quotation, SalesOrder, SalesOrderItem, Invoice, Payment

@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ('name', 'company', 'sku', 'price', 'is_service', 'is_active', 'created_at')
    search_fields = ('name', 'sku', 'description')
    list_filter = ('company', 'is_service', 'is_active')

@admin.register(Tax)
class TaxAdmin(ModelAdmin):
    list_display = ('name', 'company', 'rate', 'is_active')
    search_fields = ('name',)
    list_filter = ('company', 'is_active')

@admin.register(Quotation)
class QuotationAdmin(ModelAdmin):
    list_display = ('id', 'company', 'customer', 'date', 'valid_until', 'total', 'status', 'created_by')
    search_fields = ('id', 'customer__name', 'status')
    list_filter = ('company', 'status')

@admin.register(SalesOrder)
class SalesOrderAdmin(ModelAdmin):
    list_display = ('id', 'company', 'customer', 'order_date', 'delivery_date', 'total', 'status', 'created_by', 'account')
    search_fields = ('id', 'customer__name', 'status', 'account__code', 'account__name')
    list_filter = ('company', 'status', 'account')

@admin.register(SalesOrderItem)
class SalesOrderItemAdmin(ModelAdmin):
    list_display = ('sales_order', 'product', 'quantity', 'price', 'tax', 'total')
    search_fields = ('sales_order__id', 'product__name')
    list_filter = ('product',)

@admin.register(Invoice)
class InvoiceAdmin(ModelAdmin):
    list_display = ('id', 'company', 'customer', 'invoice_date', 'due_date', 'total', 'status', 'created_by', 'account')
    search_fields = ('id', 'customer__name', 'status', 'account__code', 'account__name')
    list_filter = ('company', 'status', 'account')

@admin.register(Payment)
class PaymentAdmin(ModelAdmin):
    list_display = ('id', 'company', 'invoice', 'amount', 'payment_date', 'method', 'received_by', 'account')
    search_fields = ('id', 'invoice__id', 'method', 'reference', 'account__code', 'account__name')
    list_filter = ('company', 'method', 'account')
