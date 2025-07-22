from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Supplier, PurchaseOrder, PurchaseOrderItem, Bill, PurchasePayment

@admin.register(Supplier)
class SupplierAdmin(ModelAdmin):
    list_display = ('name', 'company', 'email', 'phone', 'contact_person', 'is_active', 'created_by', 'created_at')
    search_fields = ('name', 'email', 'phone', 'address', 'contact_person')
    list_filter = ('company', 'is_active')

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(ModelAdmin):
    list_display = ('id', 'company', 'supplier', 'order_date', 'expected_date', 'total', 'status', 'created_by', 'account')
    search_fields = ('id', 'supplier__name', 'status', 'account__code', 'account__name')
    list_filter = ('company', 'status', 'account')

@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(ModelAdmin):
    list_display = ('purchase_order', 'product', 'quantity', 'price', 'total')
    search_fields = ('purchase_order__id', 'product__name')
    list_filter = ('product',)

@admin.register(Bill)
class BillAdmin(ModelAdmin):
    list_display = ('id', 'company', 'supplier', 'bill_date', 'due_date', 'total', 'status', 'created_by', 'account')
    search_fields = ('id', 'supplier__name', 'status', 'account__code', 'account__name')
    list_filter = ('company', 'status', 'account')

@admin.register(PurchasePayment)
class PurchasePaymentAdmin(ModelAdmin):
    list_display = ('id', 'company', 'bill', 'amount', 'payment_date', 'method', 'paid_by', 'account')
    search_fields = ('id', 'bill__id', 'method', 'reference', 'account__code', 'account__name')
    list_filter = ('company', 'method', 'account')
