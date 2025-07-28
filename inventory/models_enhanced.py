from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.utils import timezone
from user_auth.models import Company, User
from products.models import Product, ProductCategory  # Import centralized models
from accounting.models import Account

# ProductCategory is now centralized in products app

class Warehouse(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='warehouses')
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, blank=True, help_text="Warehouse code")
    location = models.CharField(max_length=255, blank=True)
    address = models.TextField(blank=True)
    warehouse_type = models.CharField(max_length=50, choices=[
        ('main', 'Main Warehouse'),
        ('distribution', 'Distribution Center'),
        ('receiving', 'Receiving Dock'),
        ('quality', 'Quality Control'),
        ('quarantine', 'Quarantine Area'),
        ('returns', 'Returns Processing'),
    ], default='main')
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_warehouses')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ['company', 'code']
        ordering = ['name']


class StockItem(models.Model):
    """Enhanced stock item with tracking and valuation"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='stock_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_items')
    category = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_items')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='stock_items')
    
    # Quantity tracking
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    available_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Available for sale/use")
    reserved_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Reserved for orders")
    locked_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Locked pending invoice")
    quarantine_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="In quarantine")
    
    # Stock levels
    min_stock = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    max_stock = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reorder_point = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Valuation - Multiple methods
    valuation_method = models.CharField(max_length=20, choices=[
        ('fifo', 'First In First Out'),
        ('lifo', 'Last In First Out'),
        ('weighted_avg', 'Weighted Average'),
        ('standard', 'Standard Cost'),
    ], default='weighted_avg')
    
    # Cost tracking
    average_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    last_purchase_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_cost_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Location tracking
    location = models.CharField(max_length=255, blank=True, help_text="Specific location within warehouse")
    bin_location = models.CharField(max_length=100, blank=True)
    
    # Status and tracking
    is_active = models.BooleanField(default=True)
    is_tracked = models.BooleanField(default=False, help_text="Whether items are individually tracked")
    tracking_type = models.CharField(max_length=20, choices=[
        ('none', 'No Tracking'),
        ('batch', 'Batch Tracking'),
        ('serial', 'Serial Number'),
        ('expiry', 'Expiry Date Tracking'),
    ], default='none')
    
    # Dates
    last_movement_date = models.DateTimeField(null=True, blank=True)
    last_stock_take_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_items')

    def save(self, *args, **kwargs):
        # Calculate available quantity
        self.available_quantity = max(0, self.quantity - self.reserved_quantity - self.locked_quantity - self.quarantine_quantity)
        # Calculate total cost value
        self.total_cost_value = self.quantity * self.average_cost
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
        elif self.valuation_method == 'fifo':
            # For FIFO, we'll use the new cost as current cost
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

    def get_stock_status(self):
        """Get human-readable stock status"""
        if self.is_out_of_stock():
            return 'Out of Stock'
        elif self.is_low_stock():
            return 'Low Stock'
        elif self.quantity >= self.max_stock:
            return 'Overstock'
        else:
            return 'Normal'


class StockMovement(models.Model):
    """Enhanced stock movement with GRN integration"""
    MOVEMENT_TYPE_CHOICES = [
        ('grn_receipt', 'GRN Receipt'),
        ('quality_pass', 'Quality Passed'),
        ('quality_fail', 'Quality Failed'),
        ('purchase_return', 'Purchase Return'),
        ('sale', 'Sale'),
        ('transfer_in', 'Transfer In'),
        ('transfer_out', 'Transfer Out'),
        ('adjustment_in', 'Adjustment In'),
        ('adjustment_out', 'Adjustment Out'),
        ('production_in', 'Production In'),
        ('production_out', 'Production Out'),
        ('quarantine_in', 'Quarantine In'),
        ('quarantine_out', 'Quarantine Out'),
        ('lock', 'Lock Inventory'),
        ('unlock', 'Unlock Inventory'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='stock_movements')
    stock_item = models.ForeignKey(StockItem, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=50, choices=MOVEMENT_TYPE_CHOICES, default='grn_receipt')
    
    # Quantity and cost
    quantity = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Warehouse tracking
    from_warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True, related_name='outgoing_movements')
    to_warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True, related_name='incoming_movements')
    
    # Reference documents
    reference_type = models.CharField(max_length=50, choices=[
        ('grn', 'Goods Receipt Note'),
        ('purchase_return', 'Purchase Return'),
        ('quality_inspection', 'Quality Inspection'),
        ('sales_order', 'Sales Order'),
        ('transfer', 'Stock Transfer'),
        ('adjustment', 'Stock Adjustment'),
        ('production', 'Production Order'),
    ], blank=True)
    reference_id = models.PositiveIntegerField(null=True, blank=True, help_text="ID of the reference document")
    reference_number = models.CharField(max_length=100, blank=True, help_text="Document number for reference")
    
    # Tracking and quality
    tracking_number = models.CharField(max_length=100, blank=True, help_text="Item tracking number if applicable")
    quality_status = models.CharField(max_length=50, choices=[
        ('pending', 'Pending Inspection'),
        ('passed', 'Quality Passed'),
        ('failed', 'Quality Failed'),
        ('quarantined', 'Quarantined'),
    ], blank=True)
    
    # Batch and expiry tracking
    batch_number = models.CharField(max_length=100, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    
    # User and timing
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_movements')
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    # Accounting integration
    cogs_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_movements_cogs')
    inventory_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_movements_inventory')

    def save(self, *args, **kwargs):
        # Calculate total cost
        self.total_cost = self.quantity * self.unit_cost
        super().save(*args, **kwargs)
        
        # Update stock item quantities based on movement type
        self.update_stock_quantities()

    def update_stock_quantities(self):
        """Update stock item quantities based on movement type"""
        stock_item = self.stock_item
        
        if self.movement_type in ['grn_receipt', 'quality_pass', 'transfer_in', 'adjustment_in', 'production_in', 'quarantine_out']:
            # Increase quantity
            if self.movement_type == 'grn_receipt':
                # GRN receipt goes to locked quantity initially
                stock_item.locked_quantity += self.quantity
            elif self.movement_type == 'quality_pass':
                # Quality passed items become available (unlock from locked)
                stock_item.locked_quantity = max(0, stock_item.locked_quantity - self.quantity)
                stock_item.quantity += self.quantity
            elif self.movement_type == 'quarantine_out':
                # Items leaving quarantine
                stock_item.quarantine_quantity = max(0, stock_item.quarantine_quantity - self.quantity)
                stock_item.quantity += self.quantity
            else:
                stock_item.quantity += self.quantity
                
        elif self.movement_type in ['sale', 'transfer_out', 'adjustment_out', 'production_out', 'purchase_return', 'quarantine_in']:
            # Decrease quantity
            if self.movement_type == 'quarantine_in':
                # Items going to quarantine
                stock_item.quantity = max(0, stock_item.quantity - self.quantity)
                stock_item.quarantine_quantity += self.quantity
            elif self.movement_type == 'purchase_return':
                # Return decreases locked quantity
                stock_item.locked_quantity = max(0, stock_item.locked_quantity - self.quantity)
            else:
                stock_item.quantity = max(0, stock_item.quantity - self.quantity)
        
        elif self.movement_type == 'lock':
            # Lock inventory (move from available to locked)
            available = stock_item.quantity - stock_item.reserved_quantity - stock_item.locked_quantity - stock_item.quarantine_quantity
            lock_qty = min(self.quantity, available)
            stock_item.locked_quantity += lock_qty
            
        elif self.movement_type == 'unlock':
            # Unlock inventory
            stock_item.locked_quantity = max(0, stock_item.locked_quantity - self.quantity)
        
        # Update average cost for incoming items
        if self.movement_type in ['grn_receipt', 'quality_pass', 'transfer_in'] and self.unit_cost > 0:
            stock_item.update_average_cost(self.quantity, self.unit_cost)
        
        stock_item.last_movement_date = timezone.now()
        stock_item.save()

    def __str__(self):
        return f"{self.get_movement_type_display()} {self.quantity} of {self.stock_item.product.name}"

    class Meta:
        ordering = ['-timestamp']


class StockLot(models.Model):
    """Track individual lots/batches for FIFO/LIFO and expiry management"""
    stock_item = models.ForeignKey(StockItem, on_delete=models.CASCADE, related_name='lots')
    lot_number = models.CharField(max_length=100)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    remaining_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Dates
    received_date = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateField(null=True, blank=True)
    manufacturing_date = models.DateField(null=True, blank=True)
    
    # Reference to source
    grn_item = models.ForeignKey('purchase.GRNItem', on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_lots')
    
    # Status
    is_active = models.BooleanField(default=True)
    is_expired = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        # Check if expired
        if self.expiry_date and self.expiry_date <= timezone.now().date():
            self.is_expired = True
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Lot {self.lot_number} - {self.stock_item.product.name}"

    class Meta:
        unique_together = ['stock_item', 'lot_number']
        ordering = ['received_date']


class StockReservation(models.Model):
    """Reserve stock for specific orders or purposes"""
    stock_item = models.ForeignKey(StockItem, on_delete=models.CASCADE, related_name='reservations')
    quantity = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    
    # Reservation details
    reservation_type = models.CharField(max_length=50, choices=[
        ('sales_order', 'Sales Order'),
        ('production_order', 'Production Order'),
        ('transfer_order', 'Transfer Order'),
        ('quality_hold', 'Quality Hold'),
        ('manual', 'Manual Reservation'),
    ])
    reference_id = models.PositiveIntegerField(null=True, blank=True)
    reference_number = models.CharField(max_length=100, blank=True)
    
    # Timing
    reserved_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stock_reservations')
    reserved_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Reserved {self.quantity} of {self.stock_item.product.name}"

    class Meta:
        ordering = ['-reserved_at']


class StockAlert(models.Model):
    """Enhanced stock alerts with more types"""
    ALERT_TYPE_CHOICES = [
        ('low_stock', 'Low Stock'),
        ('out_of_stock', 'Out of Stock'),
        ('overstock', 'Overstock'),
        ('expired', 'Expired Items'),
        ('expiring_soon', 'Expiring Soon'),
        ('quality_failed', 'Quality Failed'),
        ('locked_too_long', 'Locked Too Long'),
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
    message = models.TextField(blank=True)
    
    # Status
    triggered_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_alerts')
    
    # Notification tracking
    notification_sent = models.BooleanField(default=False)
    email_sent = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.get_alert_type_display()} for {self.stock_item.product.name} @ {self.stock_item.warehouse.name}"

    class Meta:
        ordering = ['-triggered_at']


class InventoryLock(models.Model):
    """Track inventory locks for various business processes"""
    stock_item = models.ForeignKey(StockItem, on_delete=models.CASCADE, related_name='inventory_locks')
    locked_quantity = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    
    # Lock details
    lock_type = models.CharField(max_length=50, choices=[
        ('grn_pending_invoice', 'GRN Pending Invoice'),
        ('quality_inspection', 'Quality Inspection'),
        ('sales_order', 'Sales Order'),
        ('quality_failed', 'Quality Failed'),
        ('return_processing', 'Return Processing'),
        ('manual', 'Manual Lock'),
    ])
    
    # Reference
    reference_type = models.CharField(max_length=50, blank=True)
    reference_id = models.PositiveIntegerField(null=True, blank=True)
    reference_number = models.CharField(max_length=100, blank=True)
    
    # Timing
    locked_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inventory_locks')
    locked_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    # Unlock details
    unlocked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='unlocked_inventory_locks')
    unlocked_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Lock {self.locked_quantity} of {self.stock_item.product.name} - {self.get_lock_type_display()}"

    class Meta:
        ordering = ['-locked_at']
