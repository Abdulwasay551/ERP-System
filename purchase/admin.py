from django.contrib import admin
from unfold.admin import ModelAdmin, StackedInline, TabularInline
from .models import (
    UnitOfMeasure, Supplier, TaxChargesTemplate, PurchaseRequisition, PurchaseRequisitionItem,
    RequestForQuotation, RFQItem, SupplierQuotation, SupplierQuotationItem,
    PurchaseOrder, PurchaseOrderItem, PurchaseOrderTaxCharge,
    GoodsReceiptNote, GRNItem, Bill, BillItem, PurchasePayment,
    PurchaseReturn, PurchaseReturnItem, PurchaseApproval
)

# Inline classes for related models
class PurchaseRequisitionItemInline(TabularInline):
    model = PurchaseRequisitionItem
    extra = 1
    fields = ('product', 'quantity', 'unit_price', 'preferred_supplier', 'specifications')

class RFQItemInline(TabularInline):
    model = RFQItem
    extra = 1
    fields = ('product', 'quantity', 'required_uom', 'specifications', 'priority')

class SupplierQuotationItemInline(TabularInline):
    model = SupplierQuotationItem
    extra = 1
    fields = ('product', 'quantity', 'quoted_uom', 'unit_price', 'item_discount_percentage', 'delivery_time_days')
    readonly_fields = ('base_unit_price', 'total_base_units', 'total_amount')

class PurchaseOrderItemInline(TabularInline):
    model = PurchaseOrderItem
    extra = 1
    fields = ('product', 'quantity', 'uom', 'unit_price', 'item_discount', 'received_quantity')
    readonly_fields = ('line_total',)

class PurchaseOrderTaxChargeInline(TabularInline):
    model = PurchaseOrderTaxCharge
    extra = 1
    fields = ('tax_template', 'amount')

class GRNItemInline(TabularInline):
    model = GRNItem
    extra = 1
    fields = ('po_item', 'uom', 'received_qty', 'accepted_qty', 'rejected_qty', 'quality_status', 'warehouse')
    readonly_fields = ('ordered_qty',)

class BillItemInline(TabularInline):
    model = BillItem
    extra = 1
    fields = ('product', 'quantity', 'unit_price', 'po_item', 'grn_item')
    readonly_fields = ('line_total',)

class PurchaseReturnItemInline(TabularInline):
    model = PurchaseReturnItem
    extra = 1
    fields = ('grn_item', 'return_quantity', 'unit_price', 'condition_at_return', 'replacement_requested', 'refund_requested')
    readonly_fields = ('line_total',)

# Main Admin Classes
@admin.register(UnitOfMeasure)
class UnitOfMeasureAdmin(ModelAdmin):
    list_display = ('name', 'abbreviation', 'uom_type', 'company', 'is_base_unit', 'conversion_factor', 'is_active')
    search_fields = ('name', 'abbreviation', 'uom_type')
    list_filter = ('company', 'uom_type', 'is_base_unit', 'is_active', 'created_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('company', 'name', 'abbreviation', 'uom_type')
        }),
        ('Conversion Settings', {
            'fields': ('is_base_unit', 'conversion_factor')
        }),
        ('Status', {
            'fields': ('is_active',)
        })
    )

@admin.register(Supplier)
class SupplierAdmin(ModelAdmin):
    list_display = ('name', 'supplier_code', 'company', 'email', 'phone', 'contact_person', 'payment_terms', 'is_active', 'created_at')
    search_fields = ('name', 'supplier_code', 'email', 'phone', 'address', 'contact_person', 'tax_number')
    list_filter = ('company', 'is_active', 'created_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'supplier_code', 'company', 'partner', 'contact_person', 'is_active')
        }),
        ('Contact Details', {
            'fields': ('email', 'phone', 'address')
        }),
        ('Business Details', {
            'fields': ('tax_number', 'bank_details', 'payment_terms', 'credit_limit', 'delivery_lead_time')
        }),
        ('Quality Ratings', {
            'fields': ('quality_rating', 'delivery_rating'),
            'classes': ('collapse',)
        }),
        ('Document Uploads', {
            'fields': ('registration_certificate', 'tax_certificate', 'quality_certificates', 'bank_documents', 'agreement_contract'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by',),
            'classes': ('collapse',)
        })
    )

@admin.register(TaxChargesTemplate)
class TaxChargesTemplateAdmin(ModelAdmin):
    list_display = ('name', 'charge_type', 'rate', 'is_percentage', 'company', 'is_active', 'created_at')
    search_fields = ('name', 'charge_type')
    list_filter = ('company', 'charge_type', 'is_percentage', 'is_active', 'created_at')

@admin.register(PurchaseRequisition)
class PurchaseRequisitionAdmin(ModelAdmin):
    list_display = ('pr_number', 'company', 'requested_by', 'department', 'warehouse', 'request_date', 'required_date', 'status', 'total_estimated_cost')
    search_fields = ('pr_number', 'department', 'purpose', 'requested_by__email')
    list_filter = ('company', 'status', 'request_date', 'required_date', 'created_at')
    inlines = [PurchaseRequisitionItemInline]
    fieldsets = (
        ('Request Information', {
            'fields': ('pr_number', 'company', 'requested_by', 'department', 'warehouse', 'required_date')
        }),
        ('Details', {
            'fields': ('purpose', 'total_estimated_cost')
        }),
        ('Document Uploads', {
            'fields': ('requisition_document', 'technical_specifications', 'budget_approval'),
            'classes': ('collapse',)
        }),
        ('Approval', {
            'fields': ('status', 'approved_by', 'approved_at', 'rejected_reason'),
            'classes': ('collapse',)
        })
    )

@admin.register(RequestForQuotation)
class RequestForQuotationAdmin(ModelAdmin):
    list_display = ('rfq_number', 'company', 'purchase_requisition', 'warehouse', 'issue_date', 'response_deadline', 'status', 'created_by')
    search_fields = ('rfq_number', 'purchase_requisition__pr_number', 'created_by__email')
    list_filter = ('company', 'status', 'issue_date', 'response_deadline', 'created_at')
    filter_horizontal = ('suppliers',)
    inlines = [RFQItemInline]
    fieldsets = (
        ('RFQ Information', {
            'fields': ('rfq_number', 'company', 'purchase_requisition', 'warehouse', 'response_deadline')
        }),
        ('Terms & Conditions', {
            'fields': ('payment_terms', 'delivery_terms', 'description', 'terms_and_conditions')
        }),
        ('Suppliers', {
            'fields': ('suppliers',)
        }),
        ('Document Uploads', {
            'fields': ('rfq_document', 'technical_specifications', 'drawing_attachments'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('status', 'created_by')
        })
    )

@admin.register(SupplierQuotation)
class SupplierQuotationAdmin(ModelAdmin):
    list_display = ('quotation_number', 'supplier', 'rfq', 'quotation_date', 'valid_until', 'total_amount', 'status', 'delivery_time_days')
    search_fields = ('quotation_number', 'supplier__name', 'rfq__rfq_number')
    list_filter = ('company', 'status', 'quotation_date', 'valid_until', 'created_at')
    inlines = [SupplierQuotationItemInline]
    fieldsets = (
        ('Quotation Information', {
            'fields': ('quotation_number', 'company', 'rfq', 'supplier', 'quotation_date', 'valid_until')
        }),
        ('Terms & Pricing', {
            'fields': ('payment_terms', 'delivery_terms', 'delivery_time_days', 'discount_type', 'discount_percentage', 'discount_amount')
        }),
        ('Document Uploads', {
            'fields': ('quotation_document', 'price_list', 'technical_brochure', 'certificate_documents'),
            'classes': ('collapse',)
        }),
        ('Total & Status', {
            'fields': ('total_amount', 'status', 'notes')
        })
    )

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(ModelAdmin):
    list_display = ('po_number', 'company', 'supplier', 'warehouse', 'order_date', 'expected_delivery_date', 'total_amount', 'status', 'created_by')
    search_fields = ('po_number', 'supplier__name', 'status', 'purchase_requisition__pr_number')
    list_filter = ('company', 'status', 'order_date', 'expected_delivery_date', 'created_at')
    inlines = [PurchaseOrderItemInline, PurchaseOrderTaxChargeInline]
    fieldsets = (
        ('Order Information', {
            'fields': ('po_number', 'company', 'supplier', 'purchase_requisition', 'supplier_quotation', 'warehouse')
        }),
        ('Delivery & Terms', {
            'fields': ('expected_delivery_date', 'delivery_terms', 'payment_terms', 'purchase_limit')
        }),
        ('Discount & Financial', {
            'fields': ('discount_type', 'discount_value', 'subtotal', 'discount_amount', 'tax_amount', 'total_amount', 'account'),
            'classes': ('collapse',)
        }),
        ('Document Uploads', {
            'fields': ('purchase_order_document', 'supplier_agreement', 'technical_drawings', 'amendment_documents'),
            'classes': ('collapse',)
        }),
        ('Status & Approval', {
            'fields': ('status', 'approved_by', 'approved_at', 'notes', 'terms_conditions')
        })
    )

@admin.register(GoodsReceiptNote)
class GoodsReceiptNoteAdmin(ModelAdmin):
    list_display = ('grn_number', 'company', 'purchase_order', 'supplier', 'received_by', 'received_date', 'status')
    search_fields = ('grn_number', 'purchase_order__po_number', 'supplier__name', 'supplier_delivery_note', 'vehicle_number')
    list_filter = ('company', 'status', 'received_date', 'created_at')
    inlines = [GRNItemInline]
    fieldsets = (
        ('Receipt Information', {
            'fields': ('grn_number', 'company', 'purchase_order', 'supplier', 'received_by', 'inspected_by')
        }),
        ('Delivery Details', {
            'fields': ('supplier_delivery_note', 'transporter', 'vehicle_number', 'gate_entry_number')
        }),
        ('Document Uploads', {
            'fields': ('delivery_challan', 'packing_list', 'quality_certificates', 'inspection_report', 'photos_received_goods'),
            'classes': ('collapse',)
        }),
        ('Financial & Status', {
            'fields': ('total_received_value', 'status', 'notes')
        })
    )

@admin.register(Bill)
class BillAdmin(ModelAdmin):
    list_display = ('bill_number', 'company', 'supplier', 'bill_date', 'due_date', 'total_amount', 'paid_amount', 'outstanding_amount', 'status', 'three_way_match_status')
    search_fields = ('bill_number', 'supplier__name', 'supplier_invoice_number', 'purchase_order__po_number')
    list_filter = ('company', 'status', 'bill_date', 'due_date', 'three_way_match_status', 'created_at')
    inlines = [BillItemInline]
    fieldsets = (
        ('Bill Information', {
            'fields': ('bill_number', 'company', 'supplier', 'supplier_invoice_number', 'purchase_order', 'grn', 'created_by')
        }),
        ('Dates', {
            'fields': ('bill_date', 'due_date')
        }),
        ('Financial', {
            'fields': ('subtotal', 'tax_amount', 'total_amount', 'paid_amount', 'outstanding_amount', 'account'),
            'classes': ('collapse',)
        }),
        ('Document Uploads', {
            'fields': ('supplier_invoice', 'tax_invoice', 'supporting_documents', 'approval_documents'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('status', 'three_way_match_status', 'notes')
        })
    )

@admin.register(PurchasePayment)
class PurchasePaymentAdmin(ModelAdmin):
    list_display = ('payment_number', 'company', 'bill', 'supplier', 'amount', 'payment_date', 'payment_method', 'paid_by')
    search_fields = ('payment_number', 'bill__bill_number', 'supplier__name', 'reference_number')
    list_filter = ('company', 'payment_method', 'payment_date', 'created_at')
    fieldsets = (
        ('Payment Information', {
            'fields': ('payment_number', 'company', 'bill', 'supplier', 'amount', 'payment_date')
        }),
        ('Payment Details', {
            'fields': ('payment_method', 'reference_number', 'bank_account', 'paid_by')
        }),
        ('Document Uploads', {
            'fields': ('payment_receipt', 'bank_statement', 'check_copy', 'wire_transfer_advice'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes',)
        })
    )

@admin.register(PurchaseReturn)
class PurchaseReturnAdmin(ModelAdmin):
    list_display = ('return_number', 'company', 'supplier', 'purchase_order', 'return_date', 'return_type', 'total_amount', 'status')
    search_fields = ('return_number', 'supplier__name', 'purchase_order__po_number', 'reason')
    list_filter = ('company', 'return_type', 'status', 'return_date', 'created_at')
    inlines = [PurchaseReturnItemInline]
    fieldsets = (
        ('Return Information', {
            'fields': ('return_number', 'company', 'supplier', 'purchase_order', 'grn')
        }),
        ('Return Details', {
            'fields': ('return_type', 'reason', 'total_amount')
        }),
        ('Document Uploads', {
            'fields': ('return_authorization', 'quality_report', 'photos_returned_items', 'supplier_acknowledgment'),
            'classes': ('collapse',)
        }),
        ('Approval', {
            'fields': ('status', 'created_by', 'approved_by')
        })
    )

@admin.register(PurchaseApproval)
class PurchaseApprovalAdmin(ModelAdmin):
    list_display = ('document_type', 'document_id', 'requested_by', 'approver', 'amount', 'status', 'approved_at')
    search_fields = ('document_type', 'document_id', 'requested_by__email', 'approver__email')
    list_filter = ('company', 'document_type', 'status', 'approved_at', 'created_at')
    fieldsets = (
        ('Approval Request', {
            'fields': ('company', 'document_type', 'document_id', 'requested_by', 'amount')
        }),
        ('Approval Details', {
            'fields': ('approver', 'status', 'comments', 'approved_at')
        })
    )

# Register the item models as standalone admins
@admin.register(PurchaseRequisitionItem)
class PurchaseRequisitionItemAdmin(ModelAdmin):
    list_display = ('purchase_requisition', 'product', 'quantity', 'unit_price', 'total_amount')
    search_fields = ('purchase_requisition__pr_number', 'product__name')
    list_filter = ('product',)

@admin.register(RFQItem)
class RFQItemAdmin(ModelAdmin):
    list_display = ('rfq', 'product', 'quantity', 'required_uom', 'priority', 'minimum_qty_required')
    search_fields = ('rfq__rfq_number', 'product__name')
    list_filter = ('product', 'priority', 'required_uom')

@admin.register(SupplierQuotationItem)
class SupplierQuotationItemAdmin(ModelAdmin):
    list_display = ('quotation', 'product', 'quantity', 'quoted_uom', 'unit_price', 'base_unit_price', 'delivery_time_days')
    search_fields = ('quotation__quotation_number', 'product__name')
    list_filter = ('product', 'quoted_uom')
    readonly_fields = ('base_unit_price', 'total_base_units', 'total_amount')

@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(ModelAdmin):
    list_display = ('purchase_order', 'product', 'quantity', 'uom', 'unit_price', 'line_total', 'received_quantity')
    search_fields = ('purchase_order__po_number', 'product__name')
    list_filter = ('product', 'uom')
    readonly_fields = ('line_total',)

@admin.register(PurchaseOrderTaxCharge)
class PurchaseOrderTaxChargeAdmin(ModelAdmin):
    list_display = ('purchase_order', 'tax_template', 'amount')
    search_fields = ('purchase_order__po_number', 'tax_template__name')
    list_filter = ('tax_template',)

@admin.register(GRNItem)
class GRNItemAdmin(ModelAdmin):
    list_display = ('grn', 'po_item', 'uom', 'ordered_qty', 'received_qty', 'accepted_qty', 'rejected_qty', 'quality_status')
    search_fields = ('grn__grn_number', 'po_item__product__name')
    list_filter = ('quality_status', 'po_item__product', 'uom')
    readonly_fields = ('ordered_qty',)

@admin.register(BillItem)
class BillItemAdmin(ModelAdmin):
    list_display = ('bill', 'product', 'quantity', 'unit_price', 'line_total')
    search_fields = ('bill__bill_number', 'product__name')
    list_filter = ('product',)

@admin.register(PurchaseReturnItem)
class PurchaseReturnItemAdmin(ModelAdmin):
    list_display = ('purchase_return', 'grn_item', 'return_quantity', 'unit_price', 'line_total', 'condition_at_return')
    search_fields = ('purchase_return__return_number', 'grn_item__product__name')
    list_filter = ('grn_item__product', 'return_reason', 'resolution_status')
