from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import BillOfMaterials, BillOfMaterialsItem, WorkOrder, ProductionPlan

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
