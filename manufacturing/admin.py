from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from .models import (
    WorkCenter, BillOfMaterials, BillOfMaterialsItem, BOMOperation, 
    WorkOrder, WorkOrderOperation, OperationLog, QualityCheck,
    MaterialConsumption, MRPPlan, MRPRequirement, ProductionPlan, 
    ProductionPlanItem, JobCard, Subcontractor, SubcontractWorkOrder,
    DemandForecast, SupplierLeadTime, MRPRunLog, ReorderRule, CapacityPlan
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


@admin.register(DemandForecast)
class DemandForecastAdmin(ModelAdmin):
    list_display = ('product', 'forecast_date', 'forecast_quantity', 'final_forecast', 'forecast_type', 'confidence_level', 'is_active')
    search_fields = ('product__name', 'product__sku')
    list_filter = ('company', 'forecast_type', 'forecast_date', 'is_active')
    date_hierarchy = 'forecast_date'
    readonly_fields = ('final_forecast',)
    fieldsets = (
        ('Basic Information', {
            'fields': ('company', 'product', 'forecast_date')
        }),
        ('Forecast Details', {
            'fields': ('forecast_quantity', 'manual_adjustment', 'final_forecast', 'forecast_type', 'confidence_level')
        }),
        ('Settings', {
            'fields': ('planning_horizon_days', 'is_active')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        })
    )


@admin.register(SupplierLeadTime)
class SupplierLeadTimeAdmin(ModelAdmin):
    list_display = ('supplier', 'product', 'lead_time_days', 'on_time_delivery_rate', 'quality_rating', 'price_per_unit', 'is_preferred', 'is_active')
    search_fields = ('supplier__name', 'product__name', 'product__sku')
    list_filter = ('company', 'is_preferred', 'is_active', 'supplier')
    fieldsets = (
        ('Basic Information', {
            'fields': ('company', 'supplier', 'product')
        }),
        ('Lead Time Details', {
            'fields': ('lead_time_days', 'min_lead_time_days', 'max_lead_time_days')
        }),
        ('Performance Metrics', {
            'fields': ('on_time_delivery_rate', 'quality_rating', 'actual_deliveries', 'late_deliveries')
        }),
        ('Pricing & Terms', {
            'fields': ('price_per_unit', 'minimum_order_quantity')
        }),
        ('Status & Validity', {
            'fields': ('is_preferred', 'is_active', 'valid_from', 'valid_to')
        })
    )


@admin.register(MRPRunLog)
class MRPRunLogAdmin(ModelAdmin):
    list_display = ('run_timestamp', 'company', 'mrp_plan', 'trigger_source', 'status', 'execution_time_seconds', 'requirements_generated')
    search_fields = ('company__name', 'mrp_plan__name')
    list_filter = ('company', 'trigger_source', 'status', 'run_timestamp')
    date_hierarchy = 'run_timestamp'
    readonly_fields = ('run_timestamp', 'execution_time_seconds', 'configuration_snapshot')
    fieldsets = (
        ('Basic Information', {
            'fields': ('company', 'mrp_plan', 'run_timestamp', 'trigger_source')
        }),
        ('Results', {
            'fields': ('status', 'execution_time_seconds', 'requirements_generated', 'purchase_requests_created')
        }),
        ('Error Details', {
            'fields': ('error_message', 'warnings'),
            'classes': ('collapse',)
        }),
        ('Configuration', {
            'fields': ('configuration_snapshot',),
            'classes': ('collapse',)
        })
    )


@admin.register(ReorderRule)
class ReorderRuleAdmin(ModelAdmin):
    list_display = ('product', 'warehouse', 'reorder_method', 'reorder_point', 'minimum_stock', 'maximum_stock', 'auto_create_purchase_request', 'is_active')
    search_fields = ('product__name', 'product__sku', 'warehouse__name')
    list_filter = ('company', 'warehouse', 'reorder_method', 'auto_create_purchase_request', 'is_active')
    fieldsets = (
        ('Basic Information', {
            'fields': ('company', 'product', 'warehouse', 'reorder_method')
        }),
        ('Stock Levels', {
            'fields': ('minimum_stock', 'maximum_stock', 'reorder_point', 'safety_stock', 'economic_order_quantity')
        }),
        ('Demand & Lead Time', {
            'fields': ('lead_time_days', 'average_daily_demand', 'demand_variability')
        }),
        ('Automation', {
            'fields': ('auto_create_purchase_request', 'auto_create_work_order')
        }),
        ('Status', {
            'fields': ('is_active', 'last_triggered')
        })
    )


@admin.register(CapacityPlan)
class CapacityPlanAdmin(ModelAdmin):
    list_display = ('work_center', 'plan_date', 'available_hours', 'planned_hours', 'utilization_percentage', 'is_overloaded')
    search_fields = ('work_center__name', 'work_center__code')
    list_filter = ('company', 'work_center', 'plan_date', 'is_overloaded')
    date_hierarchy = 'plan_date'
    readonly_fields = ('utilization_percentage', 'is_overloaded')
    fieldsets = (
        ('Basic Information', {
            'fields': ('company', 'work_center', 'plan_date', 'planning_horizon_days')
        }),
        ('Capacity Details', {
            'fields': ('available_hours', 'planned_hours', 'actual_hours')
        }),
        ('Metrics', {
            'fields': ('utilization_percentage', 'efficiency_percentage', 'is_overloaded')
        }),
        ('Issues', {
            'fields': ('capacity_issues',),
            'classes': ('collapse',)
        })
    )
