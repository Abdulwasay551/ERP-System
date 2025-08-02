from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.utils import timezone
from user_auth.models import Company, User
from products.models import Product, ProductCategory  # Import centralized models
from accounting.models import Account

# ProductCategory is now centralized in products app

class Warehouse(models.Model):
    """Enhanced Warehouse model with flexible hierarchical structure"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='warehouses')
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, blank=True, help_text="Warehouse code (e.g., KHI-RAW-01)")
    location = models.CharField(max_length=255, blank=True)
    address = models.TextField(blank=True)
    
    # Enhanced warehouse types (flexible)
    warehouse_type = models.CharField(max_length=50, choices=[
        ('raw_material', 'Raw Material'),
        ('work_in_progress', 'Work-in-Progress (WIP)'),
        ('finished_goods', 'Finished Goods'),
        ('scrap', 'Scrap'),
        ('transit', 'Transit'),
        ('quarantine', 'Quarantine'),
        ('returns', 'Returns'),
        ('virtual', 'Virtual'),
        ('main', 'Main Warehouse'),
        ('distribution', 'Distribution Center'),
        ('receiving', 'Receiving Dock'),
        ('quality', 'Quality Control'),
    ], default='main')
    
    # Hierarchical structure (optional)
    parent_warehouse = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='sub_warehouses')
    
    # Location tracking (optional - all null=True, blank=True)
    location_type = models.CharField(max_length=20, choices=[
        ('physical', 'Physical'),
        ('virtual', 'Virtual'),
    ], default='physical', null=True, blank=True)
    
    # Coordinates (optional)
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    
    # Default settings (optional)
    default_for_raw_material = models.BooleanField(default=False, null=True, blank=True)
    default_for_finished_goods = models.BooleanField(default=False, null=True, blank=True)
    default_for_wip = models.BooleanField(default=False, null=True, blank=True)
    
    # Capacity and constraints (optional)
    max_capacity_weight = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Maximum weight capacity")
    max_capacity_volume = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Maximum volume capacity")
    temperature_controlled = models.BooleanField(default=False, null=True, blank=True)
    min_temperature = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    max_temperature = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Access and security (optional)
    restricted_access = models.BooleanField(default=False, null=True, blank=True)
    requires_approval = models.BooleanField(default=False, null=True, blank=True)
    
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_warehouses')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ['company', 'code']
        ordering = ['name']


class WarehouseZone(models.Model):
    """Optional warehouse zones for advanced location tracking"""
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='zones')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)
    
    # Zone characteristics (optional)
    zone_type = models.CharField(max_length=50, choices=[
        ('storage', 'Storage'),
        ('picking', 'Picking'),
        ('packing', 'Packing'),
        ('receiving', 'Receiving'),
        ('shipping', 'Shipping'),
        ('quality', 'Quality Control'),
        ('cold_storage', 'Cold Storage'),
        ('hazmat', 'Hazardous Materials'),
    ], null=True, blank=True)
    
    temperature_controlled = models.BooleanField(default=False, null=True, blank=True)
    min_temperature = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    max_temperature = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.warehouse.name} - {self.name}"
    
    class Meta:
        unique_together = ['warehouse', 'code']
        ordering = ['warehouse__name', 'name']


class WarehouseBin(models.Model):
    """Optional bin-level tracking for precise inventory location"""
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='bins')
    zone = models.ForeignKey(WarehouseZone, on_delete=models.CASCADE, null=True, blank=True, related_name='bins')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=30, blank=True)
    
    # Bin location details (optional)
    aisle = models.CharField(max_length=20, null=True, blank=True)
    shelf = models.CharField(max_length=20, null=True, blank=True)
    level = models.CharField(max_length=20, null=True, blank=True)
    
    # Capacity constraints (optional)
    max_weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_volume = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_items = models.PositiveIntegerField(null=True, blank=True)
    
    # Storage rules (optional)
    fifo_enabled = models.BooleanField(default=False, null=True, blank=True)
    fefo_enabled = models.BooleanField(default=False, null=True, blank=True)
    single_product_only = models.BooleanField(default=False, null=True, blank=True)
    
    # Restrictions (optional)
    restricted_products = models.ManyToManyField(Product, blank=True, help_text="Products restricted from this bin")
    allowed_categories = models.ManyToManyField(ProductCategory, blank=True, help_text="Only these categories allowed")
    
    # Barcode/QR (optional)
    barcode = models.CharField(max_length=100, null=True, blank=True)
    qr_code = models.CharField(max_length=255, null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        location = f"{self.warehouse.name}"
        if self.zone:
            location += f" - {self.zone.name}"
        location += f" - {self.name}"
        return location
    
    class Meta:
        unique_together = ['warehouse', 'code']
        ordering = ['warehouse__name', 'zone__name', 'name']


class StockItem(models.Model):
    """Enhanced stock item with comprehensive tracking and flexible features"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='stock_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_items')
    category = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_items')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='stock_items')
    
    # Optional precise location tracking
    zone = models.ForeignKey(WarehouseZone, on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_items')
    bin_location = models.ForeignKey(WarehouseBin, on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_items')
    specific_location = models.CharField(max_length=255, blank=True, help_text="Specific location within warehouse/bin")
    
    # Quantity tracking
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    available_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Available for sale/use")
    reserved_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Reserved for orders")
    locked_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Locked pending invoice")
    quarantine_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="In quarantine")
    
    # Enhanced status tracking
    stock_status = models.CharField(max_length=50, choices=[
        ('available', 'Available'),
        ('locked', 'Locked (Pending Invoice)'),
        ('quarantine', 'In Quarantine'),
        ('quality_check', 'Quality Check Required'),
        ('reserved', 'Reserved'),
        ('blocked', 'Blocked'),
        ('expired', 'Expired'),
    ], default='available')
    
    # Integration with Purchase app - status based on GRN/Bill cycle
    purchase_status = models.CharField(max_length=50, choices=[
        ('not_received', 'Not Received'),
        ('received_unbilled', 'Received but Unbilled'),
        ('received_billed', 'Received and Billed'),
        ('ready_for_use', 'Ready for Usage'),
    ], default='not_received', null=True, blank=True)
    
    # Stock levels
    min_stock = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    max_stock = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reorder_point = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    safety_stock = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=True, blank=True)
    reorder_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=True, blank=True)
    
    # Valuation - Multiple methods (flexible)
    valuation_method = models.CharField(max_length=20, choices=[
        ('fifo', 'First In First Out'),
        ('lifo', 'Last In First Out'),
        ('weighted_avg', 'Weighted Average'),
        ('moving_avg', 'Moving Average'),
        ('standard', 'Standard Cost'),
        ('landed_cost', 'Landed Cost'),
    ], default='weighted_avg')
    
    # Cost tracking
    average_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    last_purchase_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    standard_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=True, blank=True)
    landed_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=True, blank=True)
    total_cost_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Advanced tracking (optional)
    is_tracked = models.BooleanField(default=False, help_text="Whether items are individually tracked")
    tracking_type = models.CharField(max_length=20, choices=[
        ('none', 'No Tracking'),
        ('batch', 'Batch Tracking'),
        ('serial', 'Serial Number'),
        ('expiry', 'Expiry Date Tracking'),
        ('lot', 'Lot Tracking'),
    ], default='none')
    
    # Quality and compliance (optional)
    requires_quality_check = models.BooleanField(default=False, null=True, blank=True)
    quality_approved = models.BooleanField(default=False, null=True, blank=True)
    quality_approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='quality_approved_items')
    quality_approved_at = models.DateTimeField(null=True, blank=True)
    
    # Expiry and shelf life (optional)
    has_expiry = models.BooleanField(default=False, null=True, blank=True)
    shelf_life_days = models.PositiveIntegerField(null=True, blank=True, help_text="Shelf life in days")
    expiry_alert_days = models.PositiveIntegerField(null=True, blank=True, help_text="Days before expiry to alert")
    
    # Manufacturing and usage tracking (optional)
    suitable_for_sale = models.BooleanField(default=True, null=True, blank=True, help_text="Product can be sold")
    suitable_for_manufacturing = models.BooleanField(default=True, null=True, blank=True, help_text="Can be used in manufacturing")
    consumable_item = models.BooleanField(default=False, null=True, blank=True, help_text="Consumable/office supplies")
    
    # Lead time and procurement (optional)
    lead_time_days = models.PositiveIntegerField(null=True, blank=True, help_text="Lead time for procurement")
    preferred_supplier = models.ForeignKey('purchase.Supplier', on_delete=models.SET_NULL, null=True, blank=True, related_name='preferred_items')
    
    # Physical characteristics (optional)
    weight_per_unit = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    volume_per_unit = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    dimensions_length = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    dimensions_width = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    dimensions_height = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Barcoding and identification (optional)
    barcode = models.CharField(max_length=100, null=True, blank=True)
    qr_code = models.CharField(max_length=255, null=True, blank=True)
    rfid_tag = models.CharField(max_length=100, null=True, blank=True)
    
    # Restrictions and rules (optional)
    restricted_access = models.BooleanField(default=False, null=True, blank=True)
    requires_approval_for_issue = models.BooleanField(default=False, null=True, blank=True)
    temperature_sensitive = models.BooleanField(default=False, null=True, blank=True)
    hazardous_material = models.BooleanField(default=False, null=True, blank=True)
    
    # Status and activity
    is_active = models.BooleanField(default=True)
    is_discontinued = models.BooleanField(default=False, null=True, blank=True)
    discontinue_date = models.DateField(null=True, blank=True)
    
    # Dates
    last_movement_date = models.DateTimeField(null=True, blank=True)
    last_stock_take_date = models.DateField(null=True, blank=True)
    last_received_date = models.DateTimeField(null=True, blank=True)
    last_issued_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Accounting integration
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_items')

    def save(self, *args, **kwargs):
        # Calculate available quantity
        self.available_quantity = max(0, self.quantity - self.reserved_quantity - self.locked_quantity - self.quarantine_quantity)
        # Calculate total cost value
        self.total_cost_value = self.quantity * self.average_cost
        
        # Set category from product if not set
        if not self.category and self.product.category:
            self.category = self.product.category
            
        # Update purchase status based on stock status
        if self.stock_status == 'available' and self.purchase_status == 'received_billed':
            self.purchase_status = 'ready_for_use'
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} @ {self.warehouse.name}"

    class Meta:
        unique_together = ['product', 'warehouse']
        ordering = ['product__name', 'warehouse__name']

    def update_average_cost(self, new_quantity, new_cost):
        """Update average cost using weighted average method"""
        if self.valuation_method == 'weighted_avg':
            total_value = (self.quantity * self.average_cost) + (new_quantity * new_cost)
            total_quantity = self.quantity + new_quantity
            if total_quantity > 0:
                self.average_cost = total_value / total_quantity
        elif self.valuation_method == 'moving_avg':
            # Moving average updates continuously
            if self.quantity > 0:
                total_value = (self.quantity * self.average_cost) + (new_quantity * new_cost)
                total_quantity = self.quantity + new_quantity
                self.average_cost = total_value / total_quantity if total_quantity > 0 else new_cost
            else:
                self.average_cost = new_cost
        elif self.valuation_method == 'fifo':
            # For FIFO, we'll use the new cost as current cost
            self.average_cost = new_cost
        elif self.valuation_method == 'standard':
            # Standard cost doesn't change with new purchases
            if self.standard_cost:
                self.average_cost = self.standard_cost
        elif self.valuation_method == 'landed_cost':
            # Use landed cost if available
            if self.landed_cost:
                self.average_cost = self.landed_cost
            else:
                self.average_cost = new_cost
                
        # Update last purchase cost
        self.last_purchase_cost = new_cost
        self.save()

    def is_low_stock(self):
        """Check if stock is below minimum level"""
        return self.available_quantity <= self.min_stock

    def is_out_of_stock(self):
        """Check if completely out of stock"""
        return self.quantity <= 0
        
    def is_overstock(self):
        """Check if stock is above maximum level"""
        if self.max_stock > 0:
            return self.quantity >= self.max_stock
        return False

    def get_stock_status_display(self):
        """Get human-readable stock status with context"""
        if self.is_out_of_stock():
            return 'Out of Stock'
        elif self.is_low_stock():
            return 'Low Stock'
        elif self.is_overstock():
            return 'Overstock'
        elif self.locked_quantity > 0:
            return f'Partially Locked ({self.locked_quantity})'
        elif self.quarantine_quantity > 0:
            return f'Partially Quarantined ({self.quarantine_quantity})'
        elif self.reserved_quantity > 0:
            return f'Partially Reserved ({self.reserved_quantity})'
        else:
            return 'Normal'
            
    def get_purchase_status_display_detailed(self):
        """Get detailed purchase status for inventory tracking"""
        status_map = {
            'not_received': 'Not Received',
            'received_unbilled': 'Received - Pending Bill',
            'received_billed': 'Received & Billed',
            'ready_for_use': 'Ready for Usage'
        }
        return status_map.get(self.purchase_status, 'Unknown')
        
    def can_be_sold(self):
        """Check if item can be sold based on various criteria"""
        return (
            self.suitable_for_sale and 
            self.available_quantity > 0 and
            self.stock_status == 'available' and
            not self.is_discontinued and
            (not self.requires_quality_check or self.quality_approved)
        )
        
    def can_be_manufactured(self):
        """Check if item can be used in manufacturing"""
        return (
            self.suitable_for_manufacturing and 
            self.available_quantity > 0 and
            self.stock_status == 'available' and
            not self.is_discontinued
        )
        
    def get_total_committed_quantity(self):
        """Get total quantity committed (reserved + locked + quarantine)"""
        return self.reserved_quantity + self.locked_quantity + self.quarantine_quantity
        
    def get_location_display(self):
        """Get full location hierarchy"""
        location = f"{self.warehouse.name}"
        if self.zone:
            location += f" > {self.zone.name}"
        if self.bin_location:
            location += f" > {self.bin_location.name}"
        if self.specific_location:
            location += f" > {self.specific_location}"
        return location
        
    def days_since_last_movement(self):
        """Calculate days since last movement"""
        if self.last_movement_date:
            return (timezone.now() - self.last_movement_date).days
        return None
        
    def is_fast_moving(self, days=30):
        """Check if item has moved recently (fast moving)"""
        if self.last_movement_date:
            return (timezone.now() - self.last_movement_date).days <= days
        return False
        
    def is_slow_moving(self, days=90):
        """Check if item hasn't moved for a while (slow moving)"""
        if self.last_movement_date:
            return (timezone.now() - self.last_movement_date).days > days
        return True  # If never moved, consider slow moving


class StockMovement(models.Model):
    """Enhanced stock movement with comprehensive tracking and GRN integration"""
    MOVEMENT_TYPE_CHOICES = [
        # Purchase cycle movements
        ('grn_receipt', 'GRN Receipt'),
        ('grn_return', 'GRN Return'),
        ('purchase_return', 'Purchase Return'),
        
        # Quality movements
        ('quality_pass', 'Quality Passed'),
        ('quality_fail', 'Quality Failed'),
        ('quarantine_in', 'Quarantine In'),
        ('quarantine_out', 'Quarantine Out'),
        
        # Sales movements
        ('sale', 'Sale'),
        ('sales_return', 'Sales Return'),
        ('customer_return', 'Customer Return'),
        
        # Internal movements
        ('transfer_in', 'Transfer In'),
        ('transfer_out', 'Transfer Out'),
        ('inter_warehouse_transfer', 'Inter-Warehouse Transfer'),
        
        # Manufacturing movements
        ('production_in', 'Production In'),
        ('production_out', 'Production Out'),
        ('material_issue', 'Material Issue'),
        ('material_return', 'Material Return'),
        
        # Adjustments
        ('adjustment_in', 'Adjustment In'),
        ('adjustment_out', 'Adjustment Out'),
        ('physical_verification', 'Physical Verification'),
        ('stock_correction', 'Stock Correction'),
        
        # Status changes
        ('lock', 'Lock Inventory'),
        ('unlock', 'Unlock Inventory'),
        ('reserve', 'Reserve Stock'),
        ('unreserve', 'Unreserve Stock'),
        
        # Special movements
        ('opening_stock', 'Opening Stock'),
        ('closing_stock', 'Closing Stock'),
        ('scrap', 'Scrap/Write-off'),
        ('expiry', 'Expiry Write-off'),
        ('damage', 'Damage Write-off'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='stock_movements')
    stock_item = models.ForeignKey(StockItem, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=50, choices=MOVEMENT_TYPE_CHOICES, default='grn_receipt')
    
    # Quantity and cost
    quantity = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Landed cost components (optional)
    freight_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=True, blank=True)
    tax_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=True, blank=True)
    duty_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=True, blank=True)
    other_charges = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=True, blank=True)
    
    # Warehouse tracking
    from_warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True, related_name='outgoing_movements')
    to_warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True, related_name='incoming_movements')
    
    # Bin-level tracking (optional)
    from_bin = models.ForeignKey(WarehouseBin, on_delete=models.SET_NULL, null=True, blank=True, related_name='outgoing_movements')
    to_bin = models.ForeignKey(WarehouseBin, on_delete=models.SET_NULL, null=True, blank=True, related_name='incoming_movements')
    
    # Reference documents
    reference_type = models.CharField(max_length=50, choices=[
        ('grn', 'Goods Receipt Note'),
        ('purchase_return', 'Purchase Return'),
        ('quality_inspection', 'Quality Inspection'),
        ('sales_order', 'Sales Order'),
        ('delivery_note', 'Delivery Note'),
        ('transfer_order', 'Transfer Order'),
        ('production_order', 'Production Order'),
        ('work_order', 'Work Order'),
        ('stock_adjustment', 'Stock Adjustment'),
        ('physical_count', 'Physical Count'),
        ('bill', 'Purchase Bill'),
        ('invoice', 'Sales Invoice'),
    ], blank=True)
    reference_id = models.PositiveIntegerField(null=True, blank=True, help_text="ID of the reference document")
    reference_number = models.CharField(max_length=100, blank=True, help_text="Document number for reference")
    
    # Tracking and quality (optional)
    tracking_number = models.CharField(max_length=100, blank=True, help_text="Item tracking number if applicable")
    quality_status = models.CharField(max_length=50, choices=[
        ('pending', 'Pending Inspection'),
        ('passed', 'Quality Passed'),
        ('failed', 'Quality Failed'),
        ('quarantined', 'Quarantined'),
        ('approved', 'Approved for Use'),
        ('rejected', 'Rejected'),
    ], blank=True)
    
    # Batch and expiry tracking (optional)
    batch_number = models.CharField(max_length=100, blank=True)
    lot_number = models.CharField(max_length=100, blank=True)
    serial_number = models.CharField(max_length=100, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    manufacturing_date = models.DateField(null=True, blank=True)
    
    # Purchase integration fields
    # Purchase integration fields (optional foreign keys)
    grn_item = models.ForeignKey('purchase.GRNItem', on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_movements')
    bill_item = models.ForeignKey('purchase.BillItem', on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_movements')
    po_item = models.ForeignKey('purchase.PurchaseOrderItem', on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_movements')
    
    # Approval workflow (optional)
    requires_approval = models.BooleanField(default=False, null=True, blank=True)
    approved = models.BooleanField(default=False, null=True, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_movements')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # User and timing
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_movements')
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    # Status tracking
    is_reversed = models.BooleanField(default=False, help_text="Whether this movement has been reversed")
    reversed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reversed_movements')
    reversed_at = models.DateTimeField(null=True, blank=True)
    reversal_reason = models.TextField(blank=True)
    
    # Accounting integration
    cogs_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_movements_cogs')
    inventory_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_movements_inventory')
    posting_required = models.BooleanField(default=True, help_text="Whether this movement requires accounting posting")
    posted_to_accounts = models.BooleanField(default=False, help_text="Whether posted to accounting")
    posting_date = models.DateTimeField(null=True, blank=True)
    def save(self, *args, **kwargs):
        # Calculate total cost including landed cost components
        self.total_cost = self.quantity * self.unit_cost
        if self.freight_cost:
            self.total_cost += self.freight_cost
        if self.tax_cost:
            self.total_cost += self.tax_cost
        if self.duty_cost:
            self.total_cost += self.duty_cost
        if self.other_charges:
            self.total_cost += self.other_charges
            
        super().save(*args, **kwargs)
        
        # Update stock item quantities based on movement type
        if not self.is_reversed:
            self.update_stock_quantities()

    def update_stock_quantities(self):
        """Update stock item quantities based on movement type"""
        stock_item = self.stock_item
        
        # Incoming movements (increase stock)
        if self.movement_type in [
            'grn_receipt', 'quality_pass', 'transfer_in', 'adjustment_in', 
            'production_in', 'quarantine_out', 'sales_return', 'customer_return',
            'material_return', 'opening_stock', 'inter_warehouse_transfer'
        ]:
            if self.movement_type == 'grn_receipt':
                # GRN receipt goes to locked quantity initially (pending bill)
                stock_item.locked_quantity += self.quantity
                stock_item.purchase_status = 'received_unbilled'
            elif self.movement_type == 'quality_pass':
                # Quality passed items become available (unlock from locked or quarantine)
                if stock_item.locked_quantity >= self.quantity:
                    stock_item.locked_quantity = max(0, stock_item.locked_quantity - self.quantity)
                elif stock_item.quarantine_quantity >= self.quantity:
                    stock_item.quarantine_quantity = max(0, stock_item.quarantine_quantity - self.quantity)
                stock_item.quantity += self.quantity
                stock_item.stock_status = 'available'
                stock_item.quality_approved = True
                stock_item.quality_approved_at = timezone.now()
            elif self.movement_type == 'quarantine_out':
                # Items leaving quarantine
                stock_item.quarantine_quantity = max(0, stock_item.quarantine_quantity - self.quantity)
                stock_item.quantity += self.quantity
            elif self.movement_type == 'inter_warehouse_transfer' and self.to_warehouse == stock_item.warehouse:
                # Transfer into this warehouse
                stock_item.quantity += self.quantity
            else:
                stock_item.quantity += self.quantity
                
        # Outgoing movements (decrease stock)
        elif self.movement_type in [
            'sale', 'transfer_out', 'adjustment_out', 'production_out', 
            'purchase_return', 'grn_return', 'quarantine_in', 'material_issue',
            'scrap', 'expiry', 'damage', 'inter_warehouse_transfer'
        ]:
            if self.movement_type == 'quarantine_in':
                # Items going to quarantine
                stock_item.quantity = max(0, stock_item.quantity - self.quantity)
                stock_item.quarantine_quantity += self.quantity
                stock_item.stock_status = 'quarantine'
            elif self.movement_type in ['purchase_return', 'grn_return']:
                # Return decreases locked quantity first, then regular quantity
                if stock_item.locked_quantity >= self.quantity:
                    stock_item.locked_quantity = max(0, stock_item.locked_quantity - self.quantity)
                else:
                    remaining = self.quantity - stock_item.locked_quantity
                    stock_item.locked_quantity = 0
                    stock_item.quantity = max(0, stock_item.quantity - remaining)
            elif self.movement_type == 'inter_warehouse_transfer' and self.from_warehouse == stock_item.warehouse:
                # Transfer out of this warehouse
                stock_item.quantity = max(0, stock_item.quantity - self.quantity)
            else:
                stock_item.quantity = max(0, stock_item.quantity - self.quantity)
        
        # Status change movements
        elif self.movement_type == 'lock':
            # Lock inventory (move from available to locked)
            available = stock_item.quantity - stock_item.reserved_quantity - stock_item.locked_quantity - stock_item.quarantine_quantity
            lock_qty = min(self.quantity, available)
            stock_item.locked_quantity += lock_qty
            stock_item.stock_status = 'locked'
            
        elif self.movement_type == 'unlock':
            # Unlock inventory (move from locked to available)
            stock_item.locked_quantity = max(0, stock_item.locked_quantity - self.quantity)
            if stock_item.locked_quantity == 0:
                stock_item.stock_status = 'available'
                stock_item.purchase_status = 'ready_for_use'
                
        elif self.movement_type == 'reserve':
            # Reserve stock
            available = stock_item.quantity - stock_item.reserved_quantity - stock_item.locked_quantity - stock_item.quarantine_quantity
            reserve_qty = min(self.quantity, available)
            stock_item.reserved_quantity += reserve_qty
            
        elif self.movement_type == 'unreserve':
            # Unreserve stock
            stock_item.reserved_quantity = max(0, stock_item.reserved_quantity - self.quantity)
        
        # Update average cost for incoming items with cost
        if self.movement_type in ['grn_receipt', 'quality_pass', 'transfer_in', 'production_in'] and self.unit_cost > 0:
            # Calculate landed cost per unit
            landed_cost_per_unit = self.unit_cost
            if self.quantity > 0:
                additional_costs = (self.freight_cost or 0) + (self.tax_cost or 0) + (self.duty_cost or 0) + (self.other_charges or 0)
                landed_cost_per_unit += additional_costs / self.quantity
                
            stock_item.update_average_cost(self.quantity, landed_cost_per_unit)
            stock_item.landed_cost = landed_cost_per_unit
        
        # Update timestamps
        stock_item.last_movement_date = timezone.now()
        if self.movement_type in ['grn_receipt', 'quality_pass', 'transfer_in', 'production_in']:
            stock_item.last_received_date = timezone.now()
        elif self.movement_type in ['sale', 'transfer_out', 'production_out', 'material_issue']:
            stock_item.last_issued_date = timezone.now()
        
        stock_item.save()

    def reverse_movement(self, user, reason=""):
        """Reverse this stock movement"""
        if self.is_reversed:
            return False, "Movement is already reversed"
            
        # Create reverse movement
        reverse_movement = StockMovement.objects.create(
            company=self.company,
            stock_item=self.stock_item,
            movement_type=f"reverse_{self.movement_type}",
            quantity=self.quantity,
            unit_cost=self.unit_cost,
            from_warehouse=self.to_warehouse,
            to_warehouse=self.from_warehouse,
            from_bin=self.to_bin,
            to_bin=self.from_bin,
            reference_type='reversal',
            reference_id=self.id,
            reference_number=f"REV-{self.reference_number or self.id}",
            notes=f"Reversal of movement {self.id}. Reason: {reason}",
            performed_by=user,
        )
        
        # Mark this movement as reversed
        self.is_reversed = True
        self.reversed_by = user
        self.reversed_at = timezone.now()
        self.reversal_reason = reason
        self.save()
        
        # Apply reverse quantities to stock item
        self._apply_reverse_quantities()
        
        return True, f"Movement reversed successfully. Reverse movement ID: {reverse_movement.id}"
    
    def _apply_reverse_quantities(self):
        """Apply reverse quantities to undo the original movement effect"""
        stock_item = self.stock_item
        
        # This is essentially the opposite of update_stock_quantities
        if self.movement_type in ['grn_receipt']:
            stock_item.locked_quantity = max(0, stock_item.locked_quantity - self.quantity)
        elif self.movement_type in ['quality_pass']:
            stock_item.quantity = max(0, stock_item.quantity - self.quantity)
        elif self.movement_type in ['sale', 'transfer_out', 'material_issue']:
            stock_item.quantity += self.quantity
        # Add more reverse logic as needed
        
        stock_item.save()

    def get_landed_cost_per_unit(self):
        """Calculate landed cost per unit including all charges"""
        if self.quantity <= 0:
            return self.unit_cost
            
        additional_costs = (self.freight_cost or 0) + (self.tax_cost or 0) + (self.duty_cost or 0) + (self.other_charges or 0)
        return self.unit_cost + (additional_costs / self.quantity)

    def __str__(self):
        return f"{self.get_movement_type_display()} {self.quantity} of {self.stock_item.product.name}"

    class Meta:
        ordering = ['-timestamp']


class StockLot(models.Model):
    """Enhanced lot/batch tracking for FIFO/LIFO and expiry management"""
    stock_item = models.ForeignKey(StockItem, on_delete=models.CASCADE, related_name='lots')
    lot_number = models.CharField(max_length=100)
    batch_number = models.CharField(max_length=100, blank=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    remaining_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    landed_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=True, blank=True)
    
    # Dates
    received_date = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateField(null=True, blank=True)
    manufacturing_date = models.DateField(null=True, blank=True)
    best_before_date = models.DateField(null=True, blank=True)
    
    # Quality and compliance (optional)
    quality_certificate = models.CharField(max_length=100, null=True, blank=True)
    quality_approved = models.BooleanField(default=False, null=True, blank=True)
    quality_approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_lots')
    quality_approved_date = models.DateTimeField(null=True, blank=True)
    
    # Source tracking
    grn_item = models.ForeignKey('purchase.GRNItem', on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_lots')
    supplier = models.ForeignKey('purchase.Supplier', on_delete=models.SET_NULL, null=True, blank=True, related_name='supplied_lots')
    
    # Compliance and traceability (optional)
    supplier_lot_number = models.CharField(max_length=100, null=True, blank=True)
    country_of_origin = models.CharField(max_length=50, null=True, blank=True)
    certification_details = models.TextField(blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_expired = models.BooleanField(default=False)
    is_quarantined = models.BooleanField(default=False, null=True, blank=True)
    quarantine_reason = models.TextField(blank=True, null=True)
    
    def save(self, *args, **kwargs):
        # Check if expired
        if self.expiry_date and self.expiry_date <= timezone.now().date():
            self.is_expired = True
        # Set initial remaining quantity
        if not self.pk and self.remaining_quantity == 0:
            self.remaining_quantity = self.quantity
        super().save(*args, **kwargs)
        
    def is_expiring_soon(self, days=30):
        """Check if lot is expiring within given days"""
        if self.expiry_date:
            return (self.expiry_date - timezone.now().date()).days <= days
        return False

    @property
    def used_quantity(self):
        """Calculate the used quantity"""
        return self.quantity - self.remaining_quantity

    def __str__(self):
        return f"Lot {self.lot_number} - {self.stock_item.product.name}"

    class Meta:
        unique_together = ['stock_item', 'lot_number']
        ordering = ['received_date']


class StockSerial(models.Model):
    """Individual serial number tracking"""
    stock_item = models.ForeignKey(StockItem, on_delete=models.CASCADE, related_name='serials')
    lot = models.ForeignKey(StockLot, on_delete=models.CASCADE, null=True, blank=True, related_name='serials')
    serial_number = models.CharField(max_length=100, unique=True)
    
    # Status
    status = models.CharField(max_length=30, choices=[
        ('in_stock', 'In Stock'),
        ('sold', 'Sold'),
        ('reserved', 'Reserved'),
        ('quarantined', 'Quarantined'),
        ('damaged', 'Damaged'),
        ('returned', 'Returned'),
    ], default='in_stock')
    
    # Tracking
    received_date = models.DateTimeField(auto_now_add=True)
    sold_date = models.DateTimeField(null=True, blank=True)
    customer = models.ForeignKey('crm.Partner', on_delete=models.SET_NULL, null=True, blank=True, related_name='purchased_serials')
    
    # Warranty (optional)
    warranty_start_date = models.DateField(null=True, blank=True)
    warranty_end_date = models.DateField(null=True, blank=True)
    warranty_terms = models.TextField(blank=True)
    
    def __str__(self):
        return f"SN: {self.serial_number} - {self.stock_item.product.name}"
    
    class Meta:
        ordering = ['received_date']


class StockReservation(models.Model):
    """Enhanced stock reservation with flexible purposes"""
    stock_item = models.ForeignKey(StockItem, on_delete=models.CASCADE, related_name='reservations')
    quantity = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    
    # Reservation details
    reservation_type = models.CharField(max_length=50, choices=[
        ('sales_order', 'Sales Order'),
        ('production_order', 'Production Order'),
        ('transfer_order', 'Transfer Order'),
        ('work_order', 'Work Order'),
        ('quality_hold', 'Quality Hold'),
        ('project', 'Project'),
        ('maintenance', 'Maintenance'),
        ('manual', 'Manual Reservation'),
        ('customer_specific', 'Customer Specific'),
    ])
    reference_id = models.PositiveIntegerField(null=True, blank=True)
    reference_number = models.CharField(max_length=100, blank=True)
    
    # Customer/Project details (optional)
    customer = models.ForeignKey('crm.Partner', on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_reservations')
    project = models.ForeignKey('project_mgmt.Project', on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_reservations')
    
    # Timing
    reserved_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stock_reservations')
    reserved_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Fulfillment tracking
    fulfilled_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    remaining_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_fulfilled = models.BooleanField(default=False)
    priority = models.IntegerField(default=5, help_text="1=Highest, 10=Lowest")
    notes = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        # Calculate remaining quantity
        self.remaining_quantity = max(0, self.quantity - self.fulfilled_quantity)
        # Check if fulfilled
        self.is_fulfilled = self.fulfilled_quantity >= self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Reserved {self.quantity} of {self.stock_item.product.name} for {self.get_reservation_type_display()}"

    class Meta:
        ordering = ['priority', '-reserved_at']


class StockAlert(models.Model):
    """Comprehensive stock alert system"""
    ALERT_TYPE_CHOICES = [
        ('low_stock', 'Low Stock'),
        ('out_of_stock', 'Out of Stock'),
        ('overstock', 'Overstock'),
        ('negative_stock', 'Negative Stock'),
        ('expired', 'Expired Items'),
        ('expiring_soon', 'Expiring Soon'),
        ('quality_failed', 'Quality Failed'),
        ('locked_too_long', 'Locked Too Long'),
        ('slow_moving', 'Slow Moving'),
        ('dead_stock', 'Dead Stock'),
        ('reorder_required', 'Reorder Required'),
        ('quality_pending', 'Quality Check Pending'),
        ('quarantine_extended', 'Extended Quarantine'),
        ('cost_variance', 'Cost Variance'),
        ('unauthorized_movement', 'Unauthorized Movement'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='stock_alerts')
    stock_item = models.ForeignKey(StockItem, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=50, choices=ALERT_TYPE_CHOICES, default='low_stock')
    severity = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], default='medium')
    
    # Alert details
    current_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    threshold_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    variance_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=True, blank=True)
    message = models.TextField(blank=True)
    detailed_message = models.TextField(blank=True)
    
    # Context (optional)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True, related_name='alerts')
    lot = models.ForeignKey(StockLot, on_delete=models.SET_NULL, null=True, blank=True, related_name='alerts')
    
    # Status
    triggered_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_alerts')
    resolution_notes = models.TextField(blank=True)
    
    # Notification tracking
    notification_sent = models.BooleanField(default=False)
    email_sent = models.BooleanField(default=False)
    sms_sent = models.BooleanField(default=False, null=True, blank=True)
    
    # Auto-resolution
    auto_resolvable = models.BooleanField(default=False)
    auto_resolved = models.BooleanField(default=False)
    
    def resolve_alert(self, user, notes=""):
        """Manually resolve the alert"""
        self.resolved = True
        self.resolved_at = timezone.now()
        self.resolved_by = user
        self.resolution_notes = notes
        self.save()
    
    def get_age_in_hours(self):
        """Get alert age in hours"""
        return (timezone.now() - self.triggered_at).total_seconds() / 3600

    def __str__(self):
        return f"{self.get_alert_type_display()} ({self.get_severity_display()}) for {self.stock_item.product.name}"

    class Meta:
        ordering = ['-triggered_at']


class InventoryLock(models.Model):
    """Enhanced inventory lock tracking for business processes"""
    stock_item = models.ForeignKey(StockItem, on_delete=models.CASCADE, related_name='inventory_locks')
    locked_quantity = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    
    # Lock details
    lock_type = models.CharField(max_length=50, choices=[
        ('grn_pending_invoice', 'GRN Pending Invoice'),
        ('grn_pending_bill', 'GRN Pending Bill'),
        ('quality_inspection', 'Quality Inspection'),
        ('quality_failed', 'Quality Failed'),
        ('sales_order', 'Sales Order'),
        ('production_order', 'Production Order'),
        ('return_processing', 'Return Processing'),
        ('audit_hold', 'Audit Hold'),
        ('legal_hold', 'Legal Hold'),
        ('customs_clearance', 'Customs Clearance'),
        ('manual', 'Manual Lock'),
        ('system_auto', 'System Auto Lock'),
    ])
    
    # Reference
    reference_type = models.CharField(max_length=50, choices=[
        ('grn', 'Goods Receipt Note'),
        ('bill', 'Purchase Bill'),
        ('quality_check', 'Quality Check'),
        ('sales_order', 'Sales Order'),
        ('production_order', 'Production Order'),
        ('return', 'Return Document'),
        ('audit', 'Audit Document'),
        ('legal', 'Legal Document'),
        ('customs', 'Customs Document'),
    ], blank=True)
    reference_id = models.PositiveIntegerField(null=True, blank=True)
    reference_number = models.CharField(max_length=100, blank=True)
    
    # Timing
    locked_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inventory_locks')
    locked_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Business rules
    auto_unlock_on_bill = models.BooleanField(default=False, help_text="Auto unlock when bill is created")
    auto_unlock_on_quality_pass = models.BooleanField(default=False, help_text="Auto unlock on quality approval")
    requires_approval_to_unlock = models.BooleanField(default=False)
    
    # Status
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=5, help_text="1=Highest, 10=Lowest")
    reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    # Unlock details
    unlocked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='unlocked_inventory_locks')
    unlocked_at = models.DateTimeField(null=True, blank=True)
    unlock_reason = models.TextField(blank=True)
    
    # Approval for unlock (optional)
    unlock_approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_unlocks')
    unlock_approved_at = models.DateTimeField(null=True, blank=True)
    
    def unlock(self, user, reason="", approved_by=None):
        """Unlock the inventory"""
        if self.requires_approval_to_unlock and not approved_by:
            return False, "Approval required to unlock this inventory"
            
        self.is_active = False
        self.unlocked_by = user
        self.unlocked_at = timezone.now()
        self.unlock_reason = reason
        
        if approved_by:
            self.unlock_approved_by = approved_by
            self.unlock_approved_at = timezone.now()
            
        self.save()
        
        # Update stock item locked quantity
        self.stock_item.locked_quantity = max(0, self.stock_item.locked_quantity - self.locked_quantity)
        self.stock_item.save()
        
        return True, "Inventory unlocked successfully"
    
    def is_expired(self):
        """Check if lock has expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

    def __str__(self):
        return f"Lock {self.locked_quantity} of {self.stock_item.product.name} - {self.get_lock_type_display()}"

    class Meta:
        ordering = ['priority', '-locked_at']


class StockAdjustment(models.Model):
    """Stock adjustment/reconciliation with comprehensive tracking"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='stock_adjustments')
    adjustment_number = models.CharField(max_length=100, unique=True)
    adjustment_date = models.DateField(default=timezone.now)
    
    # Adjustment type
    adjustment_type = models.CharField(max_length=50, choices=[
        ('physical_count', 'Physical Count'),
        ('cycle_count', 'Cycle Count'),
        ('annual_audit', 'Annual Audit'),
        ('damage_write_off', 'Damage Write-off'),
        ('expiry_write_off', 'Expiry Write-off'),
        ('theft_loss', 'Theft/Loss'),
        ('system_correction', 'System Correction'),
        ('opening_balance', 'Opening Balance'),
        ('revaluation', 'Revaluation'),
        ('other', 'Other'),
    ])
    
    # Status
    status = models.CharField(max_length=30, choices=[
        ('draft', 'Draft'),
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('posted', 'Posted'),
        ('cancelled', 'Cancelled'),
    ], default='draft')
    
    # Workflow
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_adjustments')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_adjustments')
    posted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='posted_adjustments')
    
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    posted_at = models.DateTimeField(null=True, blank=True)
    
    # Details
    reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    reference_document = models.CharField(max_length=100, blank=True)
    
    # Accounting
    total_adjustment_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    posting_required = models.BooleanField(default=True)
    posted_to_accounts = models.BooleanField(default=False)
    
    def approve(self, user):
        """Approve the adjustment"""
        if self.status == 'draft':
            self.status = 'approved'
            self.approved_by = user
            self.approved_at = timezone.now()
            self.save()
            return True, "Adjustment approved successfully"
        return False, f"Cannot approve adjustment in {self.status} status"
    
    def post(self, user):
        """Post the adjustment and create stock movements"""
        if self.status == 'approved':
            # Create stock movements for each adjustment item
            for item in self.items.all():
                item.create_stock_movement()
            
            self.status = 'posted'
            self.posted_by = user
            self.posted_at = timezone.now()
            self.posted_to_accounts = True
            self.save()
            return True, "Adjustment posted successfully"
        return False, f"Cannot post adjustment in {self.status} status"

    def __str__(self):
        return f"{self.adjustment_number} - {self.get_adjustment_type_display()}"

    class Meta:
        ordering = ['-created_at']


class StockAdjustmentItem(models.Model):
    """Individual items in a stock adjustment"""
    adjustment = models.ForeignKey(StockAdjustment, on_delete=models.CASCADE, related_name='items')
    stock_item = models.ForeignKey(StockItem, on_delete=models.CASCADE, related_name='adjustment_items')
    
    # Quantities
    book_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="System quantity")
    physical_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Actual counted quantity")
    adjustment_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Difference")
    
    # Valuation
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    adjustment_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Tracking details (optional)
    lot_number = models.CharField(max_length=100, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    # Counting details
    counted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='counted_items')
    count_date = models.DateTimeField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        # Calculate adjustment quantity and value
        self.adjustment_quantity = self.physical_quantity - self.book_quantity
        self.adjustment_value = self.adjustment_quantity * self.unit_cost
        super().save(*args, **kwargs)
    
    def create_stock_movement(self):
        """Create corresponding stock movement"""
        if self.adjustment_quantity == 0:
            return None
            
        movement_type = 'adjustment_in' if self.adjustment_quantity > 0 else 'adjustment_out'
        
        movement = StockMovement.objects.create(
            company=self.adjustment.company,
            stock_item=self.stock_item,
            movement_type=movement_type,
            quantity=abs(self.adjustment_quantity),
            unit_cost=self.unit_cost,
            reference_type='stock_adjustment',
            reference_id=self.adjustment.id,
            reference_number=self.adjustment.adjustment_number,
            notes=f"Adjustment: {self.reason}",
            performed_by=self.adjustment.posted_by,
        )
        
        return movement

    def __str__(self):
        return f"{self.stock_item.product.name} - Adj: {self.adjustment_quantity}"

    class Meta:
        ordering = ['stock_item__product__name']


class StockTransfer(models.Model):
    """Inter-warehouse stock transfers"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='stock_transfers')
    transfer_number = models.CharField(max_length=100, unique=True)
    transfer_date = models.DateField(default=timezone.now)
    
    # Warehouses
    from_warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='outgoing_transfers')
    to_warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='incoming_transfers')
    
    # Status
    status = models.CharField(max_length=30, choices=[
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('in_transit', 'In Transit'),
        ('received', 'Received'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], default='draft')
    
    # Workflow
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_transfers')
    sent_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_transfers')
    received_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_transfers')
    
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    received_at = models.DateTimeField(null=True, blank=True)
    expected_arrival = models.DateTimeField(null=True, blank=True)
    
    # Details
    reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    priority = models.IntegerField(default=5, help_text="1=Highest, 10=Lowest")
    
    # Logistics (optional)
    carrier = models.CharField(max_length=100, blank=True)
    tracking_number = models.CharField(max_length=100, blank=True)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True, blank=True)

    def send_transfer(self, user):
        """Send the transfer"""
        if self.status == 'draft':
            self.status = 'in_transit'
            self.sent_by = user
            self.sent_at = timezone.now()
            self.save()
            
            # Create outgoing stock movements
            for item in self.items.all():
                item.create_outgoing_movement()
            
            return True, "Transfer sent successfully"
        return False, f"Cannot send transfer in {self.status} status"
    
    def receive_transfer(self, user):
        """Receive the transfer"""
        if self.status == 'in_transit':
            self.status = 'completed'
            self.received_by = user
            self.received_at = timezone.now()
            self.save()
            
            # Create incoming stock movements
            for item in self.items.all():
                item.create_incoming_movement()
            
            return True, "Transfer received successfully"
        return False, f"Cannot receive transfer in {self.status} status"

    def __str__(self):
        return f"{self.transfer_number}: {self.from_warehouse.name} → {self.to_warehouse.name}"

    class Meta:
        ordering = ['-created_at']


class StockTransferItem(models.Model):
    """Items in a stock transfer"""
    transfer = models.ForeignKey(StockTransfer, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    
    # Quantities
    requested_quantity = models.DecimalField(max_digits=12, decimal_places=2)
    sent_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    received_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Tracking (optional)
    lot_number = models.CharField(max_length=100, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    def create_outgoing_movement(self):
        """Create outgoing stock movement"""
        from_stock = StockItem.objects.get(
            product=self.product,
            warehouse=self.transfer.from_warehouse,
            company=self.transfer.company
        )
        
        movement = StockMovement.objects.create(
            company=self.transfer.company,
            stock_item=from_stock,
            movement_type='transfer_out',
            quantity=self.sent_quantity,
            from_warehouse=self.transfer.from_warehouse,
            to_warehouse=self.transfer.to_warehouse,
            reference_type='transfer_order',
            reference_id=self.transfer.id,
            reference_number=self.transfer.transfer_number,
            performed_by=self.transfer.sent_by,
        )
        return movement
    
    def create_incoming_movement(self):
        """Create incoming stock movement"""
        to_stock, created = StockItem.objects.get_or_create(
            product=self.product,
            warehouse=self.transfer.to_warehouse,
            company=self.transfer.company,
            defaults={
                'category': self.product.category,
                'valuation_method': 'weighted_avg',
            }
        )
        
        movement = StockMovement.objects.create(
            company=self.transfer.company,
            stock_item=to_stock,
            movement_type='transfer_in',
            quantity=self.received_quantity,
            from_warehouse=self.transfer.from_warehouse,
            to_warehouse=self.transfer.to_warehouse,
            reference_type='transfer_order',
            reference_id=self.transfer.id,
            reference_number=self.transfer.transfer_number,
            performed_by=self.transfer.received_by,
        )
        return movement

    def __str__(self):
        return f"{self.product.name} - Qty: {self.requested_quantity}"

    class Meta:
        ordering = ['product__name']
