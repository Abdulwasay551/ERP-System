from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import (
    Currency, PriceList, PriceListItem, Tax, Quotation, QuotationItem, 
    SalesOrder, SalesOrderItem, DeliveryNote, DeliveryNoteItem, 
    Invoice, InvoiceItem, Payment, SalesCommission, CreditNote
)

@admin.register(Currency)
class CurrencyAdmin(ModelAdmin):
    list_display = ('code', 'name', 'symbol', 'company', 'exchange_rate', 'is_base_currency', 'is_active')
    search_fields = ('code', 'name')
    list_filter = ('company', 'is_base_currency', 'is_active')
    ordering = ('code',)

@admin.register(PriceList)
class PriceListAdmin(ModelAdmin):
    list_display = ('name', 'company', 'currency', 'valid_from', 'valid_until', 'is_default', 'is_active')
    search_fields = ('name',)
    list_filter = ('company', 'currency', 'is_default', 'is_active')
    date_hierarchy = 'valid_from'

@admin.register(PriceListItem)
class PriceListItemAdmin(ModelAdmin):
    list_display = ('price_list', 'product', 'price', 'min_quantity')
    search_fields = ('price_list__name', 'product__name')
    list_filter = ('price_list',)

@admin.register(Tax)
class TaxAdmin(ModelAdmin):
    list_display = ('name', 'company', 'rate', 'is_inclusive', 'is_active', 'account')
    search_fields = ('name',)
    list_filter = ('company', 'is_inclusive', 'is_active')

@admin.register(Quotation)
class QuotationAdmin(ModelAdmin):
    list_display = ('quotation_number', 'company', 'customer', 'date', 'valid_until', 
                   'total', 'status', 'created_by')
    search_fields = ('quotation_number', 'customer__name', 'status')
    list_filter = ('company', 'status', 'currency')
    date_hierarchy = 'date'
    readonly_fields = ('quotation_number',)

@admin.register(QuotationItem)
class QuotationItemAdmin(ModelAdmin):
    list_display = ('quotation', 'product', 'quantity', 'unit_price', 'tax', 'line_total')
    search_fields = ('quotation__quotation_number', 'product__name')
    list_filter = ('product', 'tax')

@admin.register(SalesOrder)
class SalesOrderAdmin(ModelAdmin):
    list_display = ('order_number', 'company', 'customer', 'order_date', 'delivery_date', 
                   'total', 'status', 'created_by', 'account')
    search_fields = ('order_number', 'customer__name', 'status', 'account__code', 'account__name')
    list_filter = ('company', 'status', 'account', 'currency')
    date_hierarchy = 'order_date'
    readonly_fields = ('order_number',)

@admin.register(SalesOrderItem)
class SalesOrderItemAdmin(ModelAdmin):
    list_display = ('sales_order', 'product', 'quantity', 'unit_price', 'tax', 'line_total', 
                   'delivered_quantity', 'pending_quantity')
    search_fields = ('sales_order__order_number', 'product__name')
    list_filter = ('product', 'tax', 'is_make_to_order')
    
    def pending_quantity(self, obj):
        return obj.pending_quantity
    pending_quantity.short_description = 'Pending Qty'

@admin.register(DeliveryNote)
class DeliveryNoteAdmin(ModelAdmin):
    list_display = ('delivery_number', 'company', 'customer', 'sales_order', 'delivery_date', 
                   'status', 'delivered_by')
    search_fields = ('delivery_number', 'customer__name', 'sales_order__order_number')
    list_filter = ('company', 'status', 'warehouse')
    date_hierarchy = 'delivery_date'
    readonly_fields = ('delivery_number',)

@admin.register(DeliveryNoteItem)
class DeliveryNoteItemAdmin(ModelAdmin):
    list_display = ('delivery_note', 'product', 'quantity_ordered', 'quantity_delivered', 
                   'quality_checked')
    search_fields = ('delivery_note__delivery_number', 'product__name')
    list_filter = ('product', 'quality_checked')

@admin.register(Invoice)
class InvoiceAdmin(ModelAdmin):
    list_display = ('invoice_number', 'company', 'customer', 'invoice_date', 'due_date', 
                   'total', 'paid_amount', 'outstanding_amount', 'status', 'created_by', 'account')
    search_fields = ('invoice_number', 'customer__name', 'status', 'account__code', 'account__name')
    list_filter = ('company', 'status', 'account', 'currency')
    date_hierarchy = 'invoice_date'
    readonly_fields = ('invoice_number', 'outstanding_amount', 'is_overdue')
    
    def outstanding_amount(self, obj):
        return obj.outstanding_amount
    outstanding_amount.short_description = 'Outstanding'

@admin.register(InvoiceItem)
class InvoiceItemAdmin(ModelAdmin):
    list_display = ('invoice', 'product', 'quantity', 'unit_price', 'tax', 'line_total')
    search_fields = ('invoice__invoice_number', 'product__name')
    list_filter = ('product', 'tax')

@admin.register(Payment)
class PaymentAdmin(ModelAdmin):
    list_display = ('payment_number', 'company', 'customer', 'invoice', 'amount', 
                   'payment_date', 'method', 'received_by', 'bank_account')
    search_fields = ('payment_number', 'customer__name', 'invoice__invoice_number', 
                    'method', 'reference', 'bank_account__code', 'bank_account__name')
    list_filter = ('company', 'method', 'bank_account', 'is_advance_payment', 'is_write_off')
    date_hierarchy = 'payment_date'
    readonly_fields = ('payment_number',)

@admin.register(SalesCommission)
class SalesCommissionAdmin(ModelAdmin):
    list_display = ('sales_person', 'invoice', 'commission_rate', 'commission_amount', 
                   'calculation_base', 'is_paid', 'paid_date')
    search_fields = ('sales_person__email', 'invoice__invoice_number')
    list_filter = ('company', 'sales_person', 'is_paid')
    date_hierarchy = 'created_at'

@admin.register(CreditNote)
class CreditNoteAdmin(ModelAdmin):
    list_display = ('credit_number', 'company', 'customer', 'invoice', 'credit_date', 
                   'total', 'reason')
    search_fields = ('credit_number', 'customer__name', 'invoice__invoice_number')
    list_filter = ('company', 'reason', 'currency')
    date_hierarchy = 'credit_date'
    readonly_fields = ('credit_number',)
