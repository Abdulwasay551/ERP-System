from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from .models import (
    WorkCenter, BillOfMaterials, BillOfMaterialsItem, BOMOperation, 
    WorkOrder, WorkOrderOperation, OperationLog, QualityCheck,
    MaterialConsumption, MRPPlan, MRPRequirement, ProductionPlan, 
    ProductionPlanItem, JobCard, Subcontractor, SubcontractWorkOrder
)


class BillOfMaterialsItemInline(TabularInline):
    model = BillOfMaterialsItem
    extra = 1
    fields = ['component', 'quantity', 'unit_cost', 'waste_percentage', 'is_optional', 'sequence']


class BOMOperationInline(TabularInline):
    model = BOMOperation
    extra = 1
    fields = ['work_center', 'operation_name', 'sequence', 'setup_time_minutes', 'run_time_per_unit_minutes', 'operators_required']


class WorkOrderOperationInline(TabularInline):
    model = WorkOrderOperation
    extra = 0
    fields = ['bom_operation', 'status', 'sequence', 'quantity_to_produce', 'quantity_produced', 'quantity_rejected']
    readonly_fields = ['bom_operation', 'sequence']


class MaterialConsumptionInline(TabularInline):
    model = MaterialConsumption
    extra = 0
    fields = ['product', 'warehouse', 'planned_quantity', 'consumed_quantity', 'waste_quantity', 'unit_cost']


class QualityCheckInline(TabularInline):
    model = QualityCheck
    extra = 0
    fields = ['quality_type', 'status', 'inspector', 'sample_size', 'quantity_passed', 'quantity_failed']


@admin.register(WorkCenter)
class WorkCenterAdmin(ModelAdmin):
    list_display = ('code', 'name', 'company', 'warehouse', 'capacity_per_hour', 'cost_per_hour', 'is_active')
    search_fields = ('code', 'name', 'description')
    list_filter = ('company', 'warehouse', 'is_active', 'requires_operator', 'requires_quality_check')
    fieldsets = (
        ('Basic Information', {
            'fields': ('company', 'name', 'code', 'description', 'warehouse')
        }),
        ('Capacity & Costing', {
            'fields': ('capacity_per_hour', 'cost_per_hour', 'setup_time_minutes', 'cleanup_time_minutes')
        }),
        ('Operating Schedule', {
            'fields': ('operating_hours_per_day', 'operating_days_per_week')
        }),
        ('Requirements', {
            'fields': ('requires_operator', 'max_operators', 'requires_quality_check')
        }),
        ('Status', {
            'fields': ('is_active',)
        })
    )


@admin.register(BillOfMaterials)
class BillOfMaterialsAdmin(ModelAdmin):
    list_display = ('name', 'product', 'version', 'manufacturing_type', 'is_active', 'is_default', 'total_cost', 'created_by')
    search_fields = ('name', 'product__name', 'version')
    list_filter = ('company', 'manufacturing_type', 'is_active', 'is_default', 'phantom_bom', 'quality_check_required')
    inlines = [BillOfMaterialsItemInline, BOMOperationInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('company', 'product', 'name', 'version', 'revision', 'manufacturing_type')
        }),
        ('Production Details', {
            'fields': ('lot_size', 'lead_time_days', 'scrap_percentage', 'routing_required', 'phantom_bom')
        }),
        ('Quality', {
            'fields': ('quality_check_required', 'quality_specification')
        }),
        ('Costing', {
            'fields': ('material_cost', 'labor_cost', 'overhead_cost', 'total_cost')
        }),
        ('Lifecycle', {
            'fields': ('is_active', 'is_default', 'effective_from', 'effective_to')
        }),
        ('Accounting', {
            'fields': ('raw_material_account', 'wip_account', 'finished_goods_account', 'overhead_account')
        })
    )
    readonly_fields = ('material_cost', 'labor_cost', 'total_cost')


@admin.register(BillOfMaterialsItem)
class BillOfMaterialsItemAdmin(ModelAdmin):
    list_display = ('bom', 'component', 'quantity', 'effective_quantity', 'unit_cost', 'total_cost', 'is_optional')
    search_fields = ('bom__name', 'component__name')
    list_filter = ('bom__company', 'is_optional', 'preferred_supplier')
    readonly_fields = ('effective_quantity', 'total_cost')


@admin.register(BOMOperation)
class BOMOperationAdmin(ModelAdmin):
    list_display = ('bom', 'operation_name', 'work_center', 'sequence', 'setup_time_minutes', 'run_time_per_unit_minutes', 'cost_per_hour')
    search_fields = ('bom__name', 'operation_name', 'work_center__name')
    list_filter = ('work_center', 'quality_check_required', 'is_active')
    ordering = ['bom', 'sequence']


@admin.register(WorkOrder)
class WorkOrderAdmin(ModelAdmin):
    list_display = ('wo_number', 'product', 'quantity_planned', 'quantity_produced', 'status', 'priority', 'scheduled_start', 'get_progress')
    search_fields = ('wo_number', 'product__name', 'customer_reference')
    list_filter = ('company', 'status', 'priority', 'quality_check_required', 'auto_consume_materials')
    inlines = [WorkOrderOperationInline, MaterialConsumptionInline, QualityCheckInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('company', 'bom', 'product', 'wo_number', 'sales_order', 'customer_reference')
        }),
        ('Production Details', {
            'fields': ('quantity_planned', 'quantity_produced', 'quantity_rejected', 'quantity_remaining')
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority', 'quality_check_required', 'quality_approved')
        }),
        ('Scheduling', {
            'fields': ('scheduled_start', 'scheduled_end', 'actual_start', 'actual_end')
        }),
        ('Warehouses', {
            'fields': ('source_warehouse', 'destination_warehouse')
        }),
        ('Costing', {
            'fields': ('planned_cost', 'actual_cost', 'material_cost', 'labor_cost', 'overhead_cost')
        }),
        ('Automation', {
            'fields': ('auto_consume_materials', 'backflush_costing')
        }),
        ('Assignment', {
            'fields': ('created_by', 'assigned_to')
        })
    )
    readonly_fields = ('quantity_remaining', 'wo_number')
    
    def get_progress(self, obj):
        return f"{obj.get_progress_percentage()}%"
    get_progress.short_description = "Progress"


@admin.register(WorkOrderOperation)
class WorkOrderOperationAdmin(ModelAdmin):
    list_display = ('work_order', 'bom_operation', 'work_center', 'status', 'sequence', 'quantity_produced', 'actual_cost')
    search_fields = ('work_order__wo_number', 'bom_operation__operation_name', 'work_center__name')
    list_filter = ('status', 'work_center')
    ordering = ['work_order', 'sequence']


@admin.register(OperationLog)
class OperationLogAdmin(ModelAdmin):
    list_display = ('work_order_operation', 'operator', 'log_type', 'timestamp', 'quantity_produced', 'quality_passed')
    search_fields = ('work_order_operation__work_order__wo_number', 'operator__username', 'downtime_reason')
    list_filter = ('log_type', 'quality_passed', 'timestamp')
    ordering = ['-timestamp']


@admin.register(QualityCheck)
class QualityCheckAdmin(ModelAdmin):
    list_display = ('work_order', 'product', 'quality_type', 'status', 'inspector', 'inspection_date', 'quantity_passed', 'quantity_failed')
    search_fields = ('work_order__wo_number', 'product__name', 'inspector__username')
    list_filter = ('quality_type', 'status', 'inspection_date')
    ordering = ['-inspection_date']


@admin.register(MaterialConsumption)
class MaterialConsumptionAdmin(ModelAdmin):
    list_display = ('work_order', 'product', 'warehouse', 'planned_quantity', 'consumed_quantity', 'waste_quantity', 'total_cost')
    search_fields = ('work_order__wo_number', 'product__name', 'batch_number')
    list_filter = ('warehouse', 'consumed_at')
    readonly_fields = ('total_cost',)


@admin.register(MRPPlan)
class MRPPlanAdmin(ModelAdmin):
    list_display = ('name', 'company', 'plan_date', 'status', 'planning_horizon_days', 'created_by')
    search_fields = ('name',)
    list_filter = ('company', 'status', 'plan_date')
    fieldsets = (
        ('Basic Information', {
            'fields': ('company', 'name', 'plan_date', 'planning_horizon_days', 'status')
        }),
        ('Planning Parameters', {
            'fields': ('include_safety_stock', 'include_reorder_points', 'consider_lead_times')
        }),
        ('Execution Tracking', {
            'fields': ('created_by', 'approved_by', 'calculation_start', 'calculation_end')
        })
    )


@admin.register(MRPRequirement)
class MRPRequirementAdmin(ModelAdmin):
    list_display = ('mrp_plan', 'product', 'required_quantity', 'available_quantity', 'shortage_quantity', 'required_date', 'source_type', 'status')
    search_fields = ('mrp_plan__name', 'product__name')
    list_filter = ('source_type', 'status', 'required_date')
    ordering = ['required_date']


@admin.register(ProductionPlan)
class ProductionPlanAdmin(ModelAdmin):
    list_display = ('name', 'company', 'plan_type', 'start_date', 'end_date', 'status', 'created_by')
    search_fields = ('name',)
    list_filter = ('company', 'plan_type', 'status')


@admin.register(ProductionPlanItem)
class ProductionPlanItemAdmin(ModelAdmin):
    list_display = ('production_plan', 'product', 'planned_quantity', 'produced_quantity', 'remaining_quantity', 'priority', 'planned_start_date')
    search_fields = ('production_plan__name', 'product__name')
    list_filter = ('priority', 'planned_start_date')
    readonly_fields = ('remaining_quantity',)


@admin.register(JobCard)
class JobCardAdmin(ModelAdmin):
    list_display = ('card_number', 'work_order', 'work_center', 'operation', 'status', 'issued_to', 'target_quantity', 'actual_quantity')
    search_fields = ('card_number', 'work_order__wo_number', 'work_center__name')
    list_filter = ('status', 'work_center', 'issued_at')
    readonly_fields = ('card_number',)


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
    search_fields = ('work_order__wo_number', 'subcontractor__partner__name', 'product__name')
    list_filter = ('subcontractor', 'status')
    readonly_fields = ('total_cost',)
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
