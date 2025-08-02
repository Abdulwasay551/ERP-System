from django.db import models
from user_auth.models import Company, User
from decimal import Decimal
from django.core.validators import MinValueValidator


class ProductCategory(models.Model):
    """Product Category for organizing products"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='product_categories')
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name_plural = "Product Categories"


class Product(models.Model):
    """Centralized Product model used across all ERP modules"""
    
    PRODUCT_TYPE_CHOICES = [
        ('product', 'Product'),
        ('service', 'Service'),
        ('raw_material', 'Raw Material'),
        ('component', 'Component'),
        ('consumable', 'Consumable'),
    ]
    
    UOM_CHOICES = [
        ('piece', 'Piece'),
        ('kg', 'Kilogram'),
        ('liter', 'Liter'),
        ('meter', 'Meter'),
        ('hour', 'Hour'),
        ('box', 'Box'),
        ('set', 'Set'),
        ('dozen', 'Dozen'),
    ]
    
    PRODUCT_TRACKING_CHOICES = [
        ('none', 'No Tracking'),
        ('batch', 'Batch/Lot Tracking'),
        ('serial', 'Serial Number'),
        ('imei', 'IMEI Number'),
        ('barcode', 'Barcode Tracking'),
        ('expiry', 'Expiry Date Tracking'),
    ]

    # Basic Information
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, unique=True, help_text="Stock Keeping Unit")
    barcode = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True)
    
    # Categorization
    category = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    product_type = models.CharField(max_length=50, choices=PRODUCT_TYPE_CHOICES, default='product')
    
    # Measurement
    unit_of_measure = models.CharField(max_length=50, choices=UOM_CHOICES, default='piece')
    weight = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, help_text="Weight in kg")
    dimensions = models.CharField(max_length=100, blank=True, help_text="L x W x H")
    
    # Pricing
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(Decimal('0.00'))])
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(Decimal('0.00'))])
    
    # Business Rules
    is_active = models.BooleanField(default=True)
    is_saleable = models.BooleanField(default=True, help_text="Can be sold to customers")
    is_purchasable = models.BooleanField(default=True, help_text="Can be purchased from suppliers")
    is_manufacturable = models.BooleanField(default=False, help_text="Can be manufactured")
    is_stockable = models.BooleanField(default=True, help_text="Tracked in inventory")
    is_variant = models.BooleanField(default=False, help_text="This product has variants")
    
    # Inventory Management
    valuation_method = models.CharField(max_length=20, choices=[
        ('fifo', 'First In First Out'),
        ('lifo', 'Last In First Out'),
        ('weighted_avg', 'Weighted Average'),
        ('standard', 'Standard Cost'),
        ('landed_cost', 'Landed Cost'),
    ], default='weighted_avg', help_text="Default valuation method for inventory")
    
    auto_reorder = models.BooleanField(default=False, help_text="Auto-create purchase requisitions")
    lead_time_days = models.IntegerField(default=0, help_text="Procurement lead time in days")
    safety_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Safety stock level")
    
    # Quality Control
    requires_quality_inspection = models.BooleanField(default=False, help_text="Requires QC before use")
    quality_parameters = models.TextField(blank=True, help_text="Quality check parameters")
    
    # Manufacturing (optional fields)
    bill_of_materials = models.JSONField(null=True, blank=True, help_text="BOM for manufacturing")
    manufacturing_type = models.CharField(max_length=30, choices=[
        ('make_to_stock', 'Make to Stock'),
        ('make_to_order', 'Make to Order'),
        ('engineer_to_order', 'Engineer to Order'),
    ], blank=True, null=True)
    
    # Default warehouse assignments (optional)
    default_purchase_warehouse = models.ForeignKey(
        'inventory.Warehouse', 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='default_purchase_products',
        help_text="Default warehouse for purchases"
    )
    default_sales_warehouse = models.ForeignKey(
        'inventory.Warehouse', 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='default_sales_products',
        help_text="Default warehouse for sales"
    )
    
    # Tracking Method
    tracking_method = models.CharField(
        max_length=20,
        choices=PRODUCT_TRACKING_CHOICES,
        default='none',
        help_text="How this product is tracked individually"
    )
    requires_individual_tracking = models.BooleanField(
        default=False,
        help_text="Whether each unit must be tracked individually (for serial/IMEI)"
    )
    requires_expiry_tracking = models.BooleanField(
        default=False,
        help_text="Whether this product has expiry dates that need tracking"
    )
    requires_batch_tracking = models.BooleanField(
        default=False,
        help_text="Whether this product should be tracked by batch/lot numbers"
    )
    shelf_life_days = models.IntegerField(
        null=True,
        blank=True,
        help_text="Shelf life in days (for expiry tracking)"
    )
    
    # Default Variant (for products with variants)
    default_variant = models.ForeignKey('ProductVariant', on_delete=models.SET_NULL, null=True, blank=True, related_name='default_for_product')
    
    # Inventory Control
    minimum_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    maximum_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reorder_level = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Additional Information
    notes = models.TextField(blank=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    
    # Audit fields
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_products')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_products')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.sku} - {self.name}"
    
    def is_trackable(self):
        """Check if this product requires any form of tracking"""
        return self.tracking_method != 'none'
    
    def requires_tracking_numbers(self):
        """Check if this product requires individual tracking numbers"""
        return self.tracking_method in ['serial', 'imei', 'barcode'] and self.requires_individual_tracking
    
    def get_tracking_field_name(self):
        """Get the field name for storing tracking numbers"""
        tracking_map = {
            'serial': 'serial_number',
            'imei': 'imei_number',
            'barcode': 'barcode',
            'batch': 'batch_number',
        }
        return tracking_map.get(self.tracking_method, None)
    
    def can_auto_generate_tracking(self):
        """Check if tracking numbers can be auto-generated for this product"""
        return self.tracking_method in ['barcode', 'batch'] and self.requires_individual_tracking
    
    def save(self, *args, **kwargs):
        # Auto-set tracking flags based on tracking method
        if self.tracking_method == 'expiry':
            self.requires_expiry_tracking = True
        elif self.tracking_method == 'batch':
            self.requires_batch_tracking = True
        elif self.tracking_method in ['serial', 'imei', 'barcode']:
            self.requires_individual_tracking = True
        
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['name']
        unique_together = ['company', 'sku']


class ProductVariant(models.Model):
    """Product variants for different sizes, colors, etc."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, unique=True)
    
    # Variant attributes
    color = models.CharField(max_length=50, blank=True)
    size = models.CharField(max_length=50, blank=True)
    material = models.CharField(max_length=100, blank=True)
    
    # Pricing override
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Stock override
    minimum_stock = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product.name} - {self.name}"

    class Meta:
        ordering = ['name']


class ProductTracking(models.Model):
    """Individual tracking for products with serial numbers, IMEI, barcodes, or batch tracking"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='tracking_units')
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Tracking identifiers (only one should be used based on product.tracking_method)
    serial_number = models.CharField(max_length=100, blank=True, null=True, unique=True)
    imei_number = models.CharField(max_length=100, blank=True, null=True, unique=True)
    barcode = models.CharField(max_length=100, blank=True, null=True)
    batch_number = models.CharField(max_length=100, blank=True, null=True)
    
    # Batch and expiry information
    manufacturing_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    supplier_batch_reference = models.CharField(max_length=100, blank=True, help_text="Supplier's batch reference")
    
    # Status tracking
    status = models.CharField(max_length=20, choices=[
        ('available', 'Available'),
        ('sold', 'Sold'),
        ('returned', 'Returned'),
        ('damaged', 'Damaged'),
        ('expired', 'Expired'),
        ('quarantined', 'Quarantined'),
    ], default='available')
    
    # Current location and inventory
    current_warehouse = models.ForeignKey(
        'inventory.Warehouse', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Current warehouse location"
    )
    location_notes = models.CharField(max_length=255, blank=True, help_text="Specific location within warehouse")
    
    # Quality information
    quality_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending Inspection'),
        ('passed', 'Quality Passed'),
        ('failed', 'Quality Failed'),
        ('quarantined', 'Quarantined'),
    ], default='pending')
    
    # Purchase information
    grn_item = models.ForeignKey(
        'purchase.GRNItem', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='product_tracking_units',
        help_text="GRN item this tracking unit came from"
    )
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    purchase_date = models.DateField(null=True, blank=True)
    supplier = models.ForeignKey(
        'purchase.Supplier', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    
    # Warranty and service
    warranty_expiry = models.DateField(null=True, blank=True)
    service_history = models.TextField(blank=True, help_text="Service and maintenance history")
    
    # Additional tracking info
    notes = models.TextField(blank=True)
    custom_fields = models.JSONField(default=dict, blank=True, help_text="Additional custom tracking fields")
    
    # Audit fields
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_tracking_units')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['serial_number']),
            models.Index(fields=['imei_number']),
            models.Index(fields=['barcode']),
            models.Index(fields=['batch_number']),
            models.Index(fields=['status']),
            models.Index(fields=['expiry_date']),
        ]

    def __str__(self):
        tracking_value = self.get_tracking_value()
        if tracking_value:
            return f"{self.product.name} - {self.product.get_tracking_method_display()}: {tracking_value}"
        return f"{self.product.name} - Tracking Unit #{self.id}"
    
    def get_tracking_value(self):
        """Get the tracking value based on product's tracking method"""
        tracking_map = {
            'serial': self.serial_number,
            'imei': self.imei_number,
            'barcode': self.barcode,
            'batch': self.batch_number,
        }
        return tracking_map.get(self.product.tracking_method)
    
    def set_tracking_value(self, value):
        """Set the tracking value based on product's tracking method"""
        if self.product.tracking_method == 'serial':
            self.serial_number = value
        elif self.product.tracking_method == 'imei':
            self.imei_number = value
        elif self.product.tracking_method == 'barcode':
            self.barcode = value
        elif self.product.tracking_method == 'batch':
            self.batch_number = value
    
    def is_expired(self):
        """Check if this tracking unit has expired"""
        if self.expiry_date:
            from django.utils import timezone
            return self.expiry_date <= timezone.now().date()
        return False
    
    def days_to_expiry(self):
        """Get number of days until expiry"""
        if self.expiry_date:
            from django.utils import timezone
            delta = self.expiry_date - timezone.now().date()
            return delta.days
        return None
    
    def is_warranty_valid(self):
        """Check if warranty is still valid"""
        if self.warranty_expiry:
            from django.utils import timezone
            return self.warranty_expiry >= timezone.now().date()
        return False

    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Validate tracking method matches product's tracking method
        tracking_fields = {
            'serial': self.serial_number,
            'imei': self.imei_number,
            'barcode': self.barcode,
            'batch': self.batch_number,
        }
        
        # Check if the correct field is filled based on product tracking method
        if self.product.tracking_method != 'none' and self.product.tracking_method != 'expiry':
            expected_field = tracking_fields.get(self.product.tracking_method)
            if not expected_field:
                raise ValidationError(f"This product requires {self.product.get_tracking_method_display()} tracking.")
        
        # Ensure only one tracking field is filled
        filled_fields = [field for field in tracking_fields.values() if field]
        if len(filled_fields) > 1:
            raise ValidationError("Only one tracking identifier should be provided.")
        
        if self.product.tracking_method == 'none' and filled_fields:
            raise ValidationError("This product does not use individual tracking.")
        
        # Validate expiry date for products that require expiry tracking
        if self.product.requires_expiry_tracking and not self.expiry_date:
            raise ValidationError("This product requires expiry date tracking.")
        
        # Auto-calculate expiry date based on shelf life
        if (self.product.shelf_life_days and self.manufacturing_date and 
            not self.expiry_date):
            from datetime import timedelta
            self.expiry_date = self.manufacturing_date + timedelta(days=self.product.shelf_life_days)


class Attribute(models.Model):
    """Dynamic attributes for products (e.g., Color, Size, Material)"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='product_attributes')
    name = models.CharField(max_length=100)
    data_type = models.CharField(max_length=20, choices=[
        ('text', 'Text'),
        ('number', 'Number'),
        ('boolean', 'Yes/No'),
        ('choice', 'Multiple Choice'),
    ], default='text')
    is_required = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ['company', 'name']
        ordering = ['name']


class AttributeValue(models.Model):
    """Possible values for choice-type attributes"""
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name='values')
    value = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"

    class Meta:
        unique_together = ['attribute', 'value']
        ordering = ['value']


class ProductAttribute(models.Model):
    """Link products to their attribute values"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_attributes')
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    value = models.CharField(max_length=255)  # Stores the actual value
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - {self.attribute.name}: {self.value}"

    class Meta:
        unique_together = ['product', 'attribute']
