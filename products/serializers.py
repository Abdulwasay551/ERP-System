from rest_framework import serializers
from .models import Product, ProductCategory, ProductVariant, ProductTracking, Attribute, AttributeValue, ProductAttribute


class ProductCategorySerializer(serializers.ModelSerializer):
    subcategories_count = serializers.SerializerMethodField()
    products_count = serializers.SerializerMethodField()
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    
    class Meta:
        model = ProductCategory
        fields = '__all__'
        read_only_fields = ['company', 'created_at', 'updated_at']

    def get_subcategories_count(self, obj):
        return obj.subcategories.count()

    def get_products_count(self, obj):
        return obj.products.count()


class ProductVariantSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    effective_cost_price = serializers.SerializerMethodField()
    effective_selling_price = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductVariant
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def get_effective_cost_price(self, obj):
        """Get cost price from variant or fall back to product"""
        return obj.cost_price or obj.product.cost_price

    def get_effective_selling_price(self, obj):
        """Get selling price from variant or fall back to product"""
        return obj.selling_price or obj.product.selling_price


class ProductTrackingSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    variant_name = serializers.CharField(source='variant.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    tracking_identifier = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductTracking
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'updated_at']

    def get_tracking_identifier(self, obj):
        """Get the relevant tracking identifier based on product tracking method"""
        if obj.serial_number:
            return {'type': 'serial', 'value': obj.serial_number}
        elif obj.imei_number:
            return {'type': 'imei', 'value': obj.imei_number}
        elif obj.barcode:
            return {'type': 'barcode', 'value': obj.barcode}
        return None

    def validate(self, data):
        """Validate tracking data based on product's tracking method"""
        product = data.get('product')
        if not product:
            raise serializers.ValidationError("Product is required")
        
        tracking_method = product.tracking_method
        
        # Check if tracking method matches provided data
        if tracking_method == 'serial' and not data.get('serial_number'):
            raise serializers.ValidationError("Serial number is required for this product")
        elif tracking_method == 'imei' and not data.get('imei_number'):
            raise serializers.ValidationError("IMEI number is required for this product")
        elif tracking_method == 'barcode' and not data.get('barcode'):
            raise serializers.ValidationError("Barcode is required for this product")
        elif tracking_method == 'none':
            raise serializers.ValidationError("This product does not support individual tracking")
        
        return data


class AttributeSerializer(serializers.ModelSerializer):
    values_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Attribute
        fields = '__all__'
        read_only_fields = ['company', 'created_at']

    def get_values_count(self, obj):
        return obj.values.filter(is_active=True).count()


class AttributeValueSerializer(serializers.ModelSerializer):
    attribute_name = serializers.CharField(source='attribute.name', read_only=True)
    
    class Meta:
        model = AttributeValue
        fields = '__all__'
        read_only_fields = ['created_at']


class ProductAttributeSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    attribute_name = serializers.CharField(source='attribute.name', read_only=True)
    attribute_type = serializers.CharField(source='attribute.data_type', read_only=True)
    
    class Meta:
        model = ProductAttribute
        fields = '__all__'
        read_only_fields = ['created_at']


class ProductListSerializer(serializers.ModelSerializer):
    """Serializer for product list view - optimized for performance"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    variants_count = serializers.SerializerMethodField()
    tracking_units_count = serializers.SerializerMethodField()
    flags = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'sku', 'name', 'category_name', 'product_type', 'unit_of_measure',
            'selling_price', 'cost_price', 'tracking_method', 'variants_count',
            'tracking_units_count', 'flags', 'is_active', 'created_at'
        ]

    def get_variants_count(self, obj):
        return obj.variants.count()

    def get_tracking_units_count(self, obj):
        return obj.tracking_units.filter(is_active=True).count()

    def get_flags(self, obj):
        """Return business rule flags as a list"""
        flags = []
        if obj.is_saleable:
            flags.append('saleable')
        if obj.is_purchasable:
            flags.append('purchasable')
        if obj.is_manufacturable:
            flags.append('manufacturable')
        if obj.is_stockable:
            flags.append('stockable')
        if obj.is_variant:
            flags.append('has_variants')
        return flags


class ProductDetailSerializer(serializers.ModelSerializer):
    """Serializer for product detail view - includes all related data"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.get_full_name', read_only=True)
    default_variant_name = serializers.CharField(source='default_variant.name', read_only=True)
    
    variants = ProductVariantSerializer(many=True, read_only=True)
    tracking_units = ProductTrackingSerializer(many=True, read_only=True)
    product_attributes = ProductAttributeSerializer(many=True, read_only=True)
    
    flags = serializers.SerializerMethodField()
    tracking_method_display = serializers.CharField(source='get_tracking_method_display', read_only=True)
    product_type_display = serializers.CharField(source='get_product_type_display', read_only=True)
    unit_of_measure_display = serializers.CharField(source='get_unit_of_measure_display', read_only=True)
    
    class Meta:
        model = Product
        fields = '__all__'

    def get_flags(self, obj):
        """Return business rule flags as a dictionary"""
        return {
            'is_saleable': obj.is_saleable,
            'is_purchasable': obj.is_purchasable,
            'is_manufacturable': obj.is_manufacturable,
            'is_stockable': obj.is_stockable,
            'is_variant': obj.is_variant,
        }


class ProductSerializer(serializers.ModelSerializer):
    """Standard product serializer for create/update operations"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    tracking_method_display = serializers.CharField(source='get_tracking_method_display', read_only=True)
    product_type_display = serializers.CharField(source='get_product_type_display', read_only=True)
    
    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['company', 'created_by', 'updated_by', 'created_at', 'updated_at']

    def validate_sku(self, value):
        """Validate SKU uniqueness within company"""
        company = self.context['request'].user.company
        queryset = Product.objects.filter(company=company, sku=value)
        
        # Exclude current instance during update
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise serializers.ValidationError("A product with this SKU already exists in your company.")
        
        return value

    def validate(self, data):
        """Cross-field validation"""
        # Validate pricing
        cost_price = data.get('cost_price', 0)
        selling_price = data.get('selling_price', 0)
        
        if cost_price < 0:
            raise serializers.ValidationError("Cost price cannot be negative.")
        
        if selling_price < 0:
            raise serializers.ValidationError("Selling price cannot be negative.")
        
        # Validate stock levels
        minimum_stock = data.get('minimum_stock', 0)
        maximum_stock = data.get('maximum_stock', 0)
        reorder_level = data.get('reorder_level', 0)
        
        if minimum_stock < 0:
            raise serializers.ValidationError("Minimum stock cannot be negative.")
        
        if maximum_stock > 0 and maximum_stock < minimum_stock:
            raise serializers.ValidationError("Maximum stock cannot be less than minimum stock.")
        
        if reorder_level < 0:
            raise serializers.ValidationError("Reorder level cannot be negative.")
        
        return data
