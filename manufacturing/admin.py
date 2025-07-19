from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import BillOfMaterials, BillOfMaterialsItem, WorkOrder, ProductionPlan

@admin.register(BillOfMaterials)
class BillOfMaterialsAdmin(ModelAdmin):
    list_display = ('name', 'company', 'product', 'version', 'created_by', 'created_at')
    search_fields = ('name', 'product__name', 'version')
    list_filter = ('company', 'product')

@admin.register(BillOfMaterialsItem)
class BillOfMaterialsItemAdmin(ModelAdmin):
    list_display = ('bom', 'component', 'quantity')
    search_fields = ('bom__name', 'component__name')
    list_filter = ('bom', 'component')

@admin.register(WorkOrder)
class WorkOrderAdmin(ModelAdmin):
    list_display = ('id', 'company', 'product', 'quantity', 'status', 'scheduled_start', 'scheduled_end', 'actual_start', 'actual_end', 'created_by')
    search_fields = ('id', 'product__name', 'status')
    list_filter = ('company', 'status')

@admin.register(ProductionPlan)
class ProductionPlanAdmin(ModelAdmin):
    list_display = ('name', 'company', 'start_date', 'end_date', 'status', 'created_by')
    search_fields = ('name', 'status')
    list_filter = ('company', 'status')
