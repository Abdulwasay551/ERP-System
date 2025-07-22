from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import ProductCategory, StockItem, StockMovement, Warehouse, StockAlert

@admin.register(ProductCategory)
class ProductCategoryAdmin(ModelAdmin):
    list_display = ('name', 'company', 'parent', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    list_filter = ('company', 'is_active')

@admin.register(Warehouse)
class WarehouseAdmin(ModelAdmin):
    list_display = ('name', 'company', 'location', 'is_active', 'created_at')
    search_fields = ('name', 'location')
    list_filter = ('company', 'is_active')

@admin.register(StockItem)
class StockItemAdmin(ModelAdmin):
    list_display = ('product', 'company', 'category', 'warehouse', 'quantity', 'min_stock', 'max_stock', 'is_active', 'account')
    search_fields = ('product__name', 'warehouse__name', 'account__code', 'account__name')
    list_filter = ('company', 'warehouse', 'is_active', 'account')

@admin.register(StockMovement)
class StockMovementAdmin(ModelAdmin):
    list_display = ('stock_item', 'company', 'movement_type', 'quantity', 'from_warehouse', 'to_warehouse', 'performed_by', 'timestamp', 'cogs_account')
    search_fields = ('stock_item__product__name', 'reference', 'cogs_account__code', 'cogs_account__name')
    list_filter = ('company', 'movement_type', 'cogs_account')

@admin.register(StockAlert)
class StockAlertAdmin(ModelAdmin):
    list_display = ('stock_item', 'company', 'alert_type', 'triggered_at', 'resolved', 'resolved_at')
    search_fields = ('stock_item__product__name',)
    list_filter = ('company', 'alert_type', 'resolved')
