from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import BillOfMaterials, BillOfMaterialsItem, WorkOrder, ProductionPlan, Subcontractor, SubcontractWorkOrder

@admin.register(BillOfMaterials)
class BillOfMaterialsAdmin(ModelAdmin):
    list_display = ('name', 'company', 'product', 'version', 'created_by', 'created_at', 'raw_material_account', 'wip_account', 'finished_goods_account', 'overhead_account')
    search_fields = ('name', 'product__name', 'version', 'raw_material_account__code', 'wip_account__code', 'finished_goods_account__code', 'overhead_account__code')
    list_filter = ('company', 'product', 'raw_material_account', 'wip_account', 'finished_goods_account', 'overhead_account')

@admin.register(BillOfMaterialsItem)
class BillOfMaterialsItemAdmin(ModelAdmin):
    list_display = ('bom', 'component', 'quantity')
    search_fields = ('bom__name', 'component__name')
    list_filter = ('bom', 'component')

@admin.register(WorkOrder)
class WorkOrderAdmin(ModelAdmin):
    list_display = ('id', 'company', 'product', 'quantity', 'status', 'scheduled_start', 'scheduled_end', 'actual_start', 'actual_end', 'created_by', 'account')
    search_fields = ('id', 'product__name', 'status', 'account__code', 'account__name')
    list_filter = ('company', 'status', 'account')

@admin.register(ProductionPlan)
class ProductionPlanAdmin(ModelAdmin):
    list_display = ('name', 'company', 'start_date', 'end_date', 'status', 'created_by')
    search_fields = ('name', 'status')
    list_filter = ('company', 'status')

@admin.register(Subcontractor)
class SubcontractorAdmin(ModelAdmin):
    list_display = ('partner', 'company', 'specialization', 'capacity', 'quality_rating', 'delivery_rating', 'lead_time_days', 'is_active')
    search_fields = ('partner__name', 'specialization', 'capacity')
    list_filter = ('company', 'is_active')
    fieldsets = (
        ('Basic Information', {
            'fields': ('partner', 'company', 'specialization', 'capacity')
        }),
        ('Performance Metrics', {
            'fields': ('quality_rating', 'delivery_rating', 'lead_time_days')
        }),
        ('Status', {
            'fields': ('is_active',)
        })
    )

@admin.register(SubcontractWorkOrder)
class SubcontractWorkOrderAdmin(ModelAdmin):
    list_display = ('work_order', 'subcontractor', 'product', 'quantity', 'unit_cost', 'total_cost', 'status', 'start_date', 'due_date')
    search_fields = ('work_order__id', 'subcontractor__partner__name', 'product__name')
    list_filter = ('subcontractor', 'status')
    fieldsets = (
        ('Work Order Details', {
            'fields': ('work_order', 'subcontractor', 'product', 'quantity')
        }),
        ('Costing', {
            'fields': ('unit_cost', 'total_cost')
        }),
        ('Timeline', {
            'fields': ('start_date', 'due_date', 'status')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        })
    )
