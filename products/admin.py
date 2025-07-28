from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from .models import (
    Product, ProductCategory, ProductVariant, ProductTracking, 
    Attribute, AttributeValue, ProductAttribute
)


@admin.register(ProductCategory)
class ProductCategoryAdmin(ModelAdmin):
    list_display = ('name', 'code', 'company', 'parent', 'is_active', 'created_at')
    search_fields = ('name', 'code', 'description')
    list_filter = ('company', 'is_active', 'parent')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'company', 'parent')
        }),
        ('Details', {
            'fields': ('description', 'is_active')
        })
    )


@admin.register(ProductVariant)
class ProductVariantAdmin(ModelAdmin):
    list_display = ('sku', 'product', 'name', 'color', 'size', 'selling_price', 'is_active')
    search_fields = ('name', 'sku', 'product__name', 'product__sku')
    list_filter = ('product__category', 'is_active', 'color', 'size')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('product', 'name', 'sku')
        }),
        ('Variant Attributes', {
            'fields': ('color', 'size', 'material')
        }),
        ('Pricing Override', {
            'fields': ('cost_price', 'selling_price'),
            'classes': ('collapse',)
        }),
        ('Stock Override', {
            'fields': ('minimum_stock',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        })
    )


# Inline classes
class ProductVariantInline(TabularInline):
    model = ProductVariant
    fields = ('name', 'sku', 'color', 'size', 'material', 'cost_price', 'selling_price', 'is_active')
    extra = 0


class ProductTrackingInline(TabularInline):
    model = ProductTracking
    fields = ('serial_number', 'imei_number', 'barcode', 'variant', 'status', 'quality_status')
    extra = 0
    readonly_fields = ('created_at',)


class ProductAttributeInline(TabularInline):
    model = ProductAttribute
    fields = ('attribute', 'value')
    extra = 0


class AttributeValueInline(TabularInline):
    model = AttributeValue
    fields = ('value', 'is_active')
    extra = 0


@admin.register(ProductTracking)
class ProductTrackingAdmin(ModelAdmin):
    list_display = ('product', 'get_tracking_identifier', 'variant', 'status', 'quality_status', 'created_at')
    search_fields = ('product__name', 'product__sku', 'serial_number', 'imei_number', 'barcode')
    list_filter = ('product__company', 'status', 'quality_status', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Product Information', {
            'fields': ('product', 'variant')
        }),
        ('Tracking Identifiers', {
            'fields': ('serial_number', 'imei_number', 'barcode'),
            'description': 'Only fill the field that matches your product\'s tracking method'
        }),
        ('Status', {
            'fields': ('status', 'quality_status')
        }),
        ('Additional Information', {
            'fields': ('purchase_date', 'warranty_expiry', 'notes'),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_tracking_identifier(self, obj):
        if obj.serial_number:
            return f"Serial: {obj.serial_number}"
        elif obj.imei_number:
            return f"IMEI: {obj.imei_number}"
        elif obj.barcode:
            return f"Barcode: {obj.barcode}"
        return "No identifier"
    get_tracking_identifier.short_description = "Tracking ID"


@admin.register(Attribute)
class AttributeAdmin(ModelAdmin):
    list_display = ('name', 'data_type', 'is_required', 'is_active', 'company', 'created_at')
    search_fields = ('name',)
    list_filter = ('company', 'data_type', 'is_required', 'is_active')
    inlines = [AttributeValueInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'company', 'data_type')
        }),
        ('Configuration', {
            'fields': ('is_required', 'is_active')
        })
    )


@admin.register(AttributeValue)
class AttributeValueAdmin(ModelAdmin):
    list_display = ('attribute', 'value', 'is_active', 'created_at')
    search_fields = ('attribute__name', 'value')
    list_filter = ('attribute__company', 'attribute', 'is_active')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('attribute', 'value')
        }),
        ('Status', {
            'fields': ('is_active',)
        })
    )


@admin.register(ProductAttribute)
class ProductAttributeAdmin(ModelAdmin):
    list_display = ('product', 'attribute', 'value', 'created_at')
    search_fields = ('product__name', 'product__sku', 'attribute__name', 'value')
    list_filter = ('product__company', 'attribute')
    
    fieldsets = (
        ('Assignment', {
            'fields': ('product', 'attribute', 'value')
        }),
    )


# Update the Product admin to include inlines
@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ('sku', 'name', 'category', 'product_type', 'tracking_method', 'selling_price', 'cost_price', 'is_active', 'flags_display')
    search_fields = ('name', 'sku', 'barcode', 'description')
    list_filter = ('company', 'category', 'product_type', 'tracking_method', 'is_active', 'is_saleable', 'is_purchasable', 'is_manufacturable', 'is_stockable', 'is_variant')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ProductVariantInline, ProductTrackingInline, ProductAttributeInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'sku', 'barcode', 'company', 'description', 'image')
        }),
        ('Categorization', {
            'fields': ('category', 'product_type')
        }),
        ('Measurement', {
            'fields': ('unit_of_measure', 'weight', 'dimensions')
        }),
        ('Pricing', {
            'fields': ('cost_price', 'selling_price')
        }),
        ('Business Rules', {
            'fields': ('is_active', 'is_saleable', 'is_purchasable', 'is_manufacturable', 'is_stockable', 'is_variant')
        }),
        ('Tracking', {
            'fields': ('tracking_method', 'default_variant'),
            'description': 'Configure how individual units of this product are tracked'
        }),
        ('Inventory Control', {
            'fields': ('minimum_stock', 'maximum_stock', 'reorder_level'),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('notes', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def flags_display(self, obj):
        flags = []
        if obj.is_saleable:
            flags.append('S')
        if obj.is_purchasable:
            flags.append('P')
        if obj.is_manufacturable:
            flags.append('M')
        if obj.is_stockable:
            flags.append('St')
        if obj.is_variant:
            flags.append('V')
        return ' | '.join(flags) if flags else '-'
    flags_display.short_description = "Flags"
