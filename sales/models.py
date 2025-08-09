from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
from django.db import transaction
from user_auth.models import Company, User
from crm.models import Customer
from accounting.models import Account
from products.models import Product  # Import centralized Product model

# Create your models here.

# Status choices for various models
QUOTATION_STATUS_CHOICES = [
    ('draft', 'Draft'),
    ('sent', 'Sent'),
    ('accepted', 'Accepted'),
    ('lost', 'Lost'),
    ('expired', 'Expired'),
]

SALES_ORDER_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('confirmed', 'Confirmed'),
    ('in_progress', 'In Progress'),
    ('delivered', 'Delivered'),
    ('invoiced', 'Invoiced'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled'),
]

DELIVERY_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('in_transit', 'In Transit'),
    ('delivered', 'Delivered'),
    ('returned', 'Returned'),
    ('cancelled', 'Cancelled'),
]

INVOICE_STATUS_CHOICES = [
    ('draft', 'Draft'),
    ('sent', 'Sent'),
    ('paid', 'Paid'),
    ('partially_paid', 'Partially Paid'),
    ('overdue', 'Overdue'),
    ('cancelled', 'Cancelled'),
]

PAYMENT_METHOD_CHOICES = [
    ('cash', 'Cash'),
    ('bank_transfer', 'Bank Transfer'),
    ('cheque', 'Cheque'),
    ('credit_card', 'Credit Card'),
    ('online', 'Online Payment'),
    ('other', 'Other'),
]

# Legacy Product model - keeping for backward compatibility but deprecated
class LegacyProduct(models.Model):
    """
    DEPRECATED: This model is kept for backward compatibility only.
    Use products.Product instead.
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='legacy_products')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    sku = models.CharField(max_length=100, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    is_service = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'sales_product'  # Keep the original table name


class Currency(models.Model):
    """Currency management for multi-currency support"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='currencies')
    code = models.CharField(max_length=3, help_text='ISO 4217 currency code (e.g., USD, EUR)')
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=10)
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=4, default=1.0000,
                                      help_text='Exchange rate relative to base currency')
    is_base_currency = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        unique_together = ['company', 'code']
        verbose_name_plural = 'Currencies'


class PriceList(models.Model):
    """Price lists for customer groups or regions"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='price_lists')
    name = models.CharField(max_length=100)
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='price_lists')
    valid_from = models.DateField(default=timezone.now)
    valid_until = models.DateField(null=True, blank=True)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.currency.code})"


class PriceListItem(models.Model):
    """Individual product prices in a price list"""
    price_list = models.ForeignKey(PriceList, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    min_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product.name} - {self.price} ({self.price_list.name})"

    class Meta:
        unique_together = ['price_list', 'product', 'min_quantity']


class Tax(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='taxes')
    name = models.CharField(max_length=100)
    rate = models.DecimalField(max_digits=5, decimal_places=2, help_text='Percent (e.g. 18.00)')
    is_inclusive = models.BooleanField(default=False, help_text='Is tax included in price?')
    is_active = models.BooleanField(default=True)
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True,
                               help_text='Tax account for accounting entries')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.rate}%)"

class Quotation(models.Model):
    """Sales Quotation model with enhanced fields"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='quotations')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='quotations')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_quotations')
    quotation_number = models.CharField(max_length=50, unique=True, blank=True)
    date = models.DateField(default=timezone.now)
    valid_until = models.DateField(null=True, blank=True)
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='quotations',null=True,blank=True)
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=4, default=1.0000)
    
    # Amounts
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    status = models.CharField(max_length=20, choices=QUOTATION_STATUS_CHOICES, default='draft')
    terms_and_conditions = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    # Lead tracking
    lead_source = models.CharField(max_length=100, blank=True)
    campaign = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.quotation_number:
            # Generate quotation number
            last_quotation = Quotation.objects.filter(company=self.company).order_by('-id').first()
            if last_quotation and last_quotation.quotation_number:
                try:
                    last_num = int(last_quotation.quotation_number.split('-')[-1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = 1
            else:
                new_num = 1
            self.quotation_number = f"QUO-{new_num:06d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quotation_number} - {self.customer.name}"

    class Meta:
        ordering = ['-created_at']

class QuotationItem(models.Model):
    """Enhanced Quotation line items"""
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    description = models.TextField(blank=True, help_text='Override product description if needed')
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0, 
                                          validators=[MinValueValidator(0), MaxValueValidator(100)])
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax = models.ForeignKey(Tax, on_delete=models.SET_NULL, null=True, blank=True)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Additional fields
    delivery_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Calculate line total
        subtotal = self.quantity * self.unit_price
        subtotal_after_discount = subtotal - self.discount_amount
        if self.tax:
            self.tax_amount = subtotal_after_discount * (self.tax.rate / 100)
        self.line_total = subtotal_after_discount + self.tax_amount
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

class SalesOrder(models.Model):
    """Enhanced Sales Order model"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='sales_orders')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='sales_orders')
    quotation = models.ForeignKey(Quotation, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales_orders')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_sales_orders')
    
    # Order details
    order_number = models.CharField(max_length=50, unique=True, blank=True)
    order_date = models.DateField(default=timezone.now)
    delivery_date = models.DateField(null=True, blank=True)
    confirmation_date = models.DateField(null=True, blank=True)
    
    # Addresses
    billing_address = models.TextField(blank=True)
    shipping_address = models.TextField(blank=True)
    
    # Currency and amounts
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='sales_orders',null=True,blank=True)
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=4, default=1.0000)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    status = models.CharField(max_length=20, choices=SALES_ORDER_STATUS_CHOICES, default='pending')
    
    # Additional options
    partial_delivery_allowed = models.BooleanField(default=True)
    project = models.CharField(max_length=100, blank=True, help_text='Linked project or campaign')
    sales_person = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='assigned_sales_orders')
    
    terms_and_conditions = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales_orders')

    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate order number
            last_order = SalesOrder.objects.filter(company=self.company).order_by('-id').first()
            if last_order and last_order.order_number:
                try:
                    last_num = int(last_order.order_number.split('-')[-1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = 1
            else:
                new_num = 1
            self.order_number = f"SO-{new_num:06d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order_number} - {self.customer.name}"

    class Meta:
        ordering = ['-created_at']

class SalesOrderItem(models.Model):
    """Enhanced Sales Order line items with tracking and UOM support"""
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    description = models.TextField(blank=True, help_text='Override product description if needed')
    
    # Quantity and UOM
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    uom = models.CharField(max_length=20, default='Pcs', help_text='Unit of Measure')
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Enhanced discount management
    discount_type = models.CharField(max_length=10, choices=[
        ('percent', 'Percentage'),
        ('amount', 'Amount'),
    ], default='percent')
    discount_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Tax
    tax = models.ForeignKey(Tax, on_delete=models.SET_NULL, null=True, blank=True)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Tracking Management
    tracking_data = models.JSONField(default=list, blank=True, help_text='Tracking numbers, serial numbers, batch info')
    tracking_required = models.BooleanField(default=False)
    tracking_complete = models.BooleanField(default=False)
    
    # Delivery tracking
    delivered_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_date = models.DateField(null=True, blank=True)
    
    # Manufacturing integration
    is_make_to_order = models.BooleanField(default=False)
    production_order = models.CharField(max_length=100, blank=True)
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Update UOM from product if not set
        if not self.uom and self.product:
            self.uom = getattr(self.product, 'uom', 'Pcs')
        
        # Check if tracking is required
        if self.product and hasattr(self.product, 'has_tracking'):
            self.tracking_required = self.product.has_tracking
        
        # Calculate discount amount based on type
        if self.discount_type == 'percent':
            subtotal = self.quantity * self.unit_price
            self.discount_amount = subtotal * (self.discount_value / 100)
        else:  # amount
            self.discount_amount = self.discount_value
        
        # Calculate line total
        subtotal = self.quantity * self.unit_price
        subtotal_after_discount = subtotal - self.discount_amount
        if self.tax:
            self.tax_amount = subtotal_after_discount * (self.tax.rate / 100)
        self.line_total = subtotal_after_discount + self.tax_amount
        
        # Validate tracking completeness
        if self.tracking_required and self.tracking_data:
            total_tracked_qty = sum(float(item.get('quantity', 0)) for item in self.tracking_data)
            self.tracking_complete = total_tracked_qty >= float(self.quantity)
        
        super().save(*args, **kwargs)

    @property
    def pending_quantity(self):
        """Quantity yet to be delivered"""
        return self.quantity - self.delivered_quantity
    
    def get_tracking_summary(self):
        """Get summary of tracking information"""
        if not self.tracking_data:
            return "No tracking data"
        
        summary = []
        for item in self.tracking_data:
            tracking_type = item.get('type', 'serial')
            number = item.get('number', '')
            quantity = item.get('quantity', 0)
            
            if tracking_type == 'serial':
                summary.append(f"S/N: {number}")
            elif tracking_type == 'batch':
                summary.append(f"Batch: {number} (Qty: {quantity})")
        
        return "; ".join(summary)
    
    def validate_tracking_quantity(self):
        """Validate that tracked quantity matches line quantity"""
        if not self.tracking_required:
            return True
        
        if not self.tracking_data:
            return False
        
        total_tracked = sum(float(item.get('quantity', 0)) for item in self.tracking_data)
        return total_tracked >= float(self.quantity)

    def __str__(self):
        return f"{self.product.name} x {self.quantity} {self.uom}"


class DeliveryNote(models.Model):
    """Delivery Note for tracking deliveries"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='delivery_notes')
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='delivery_notes')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='delivery_notes')
    
    # Delivery details
    delivery_number = models.CharField(max_length=50, unique=True, blank=True)
    delivery_date = models.DateField(default=timezone.now)
    expected_delivery_date = models.DateField(null=True, blank=True)
    
    # Warehouse and logistics
    warehouse = models.CharField(max_length=100, blank=True, help_text='Source warehouse')
    delivery_address = models.TextField()
    
    # Transporter information
    transporter_name = models.CharField(max_length=100, blank=True)
    vehicle_number = models.CharField(max_length=50, blank=True)
    driver_name = models.CharField(max_length=100, blank=True)
    driver_contact = models.CharField(max_length=20, blank=True)
    tracking_number = models.CharField(max_length=100, blank=True)
    
    status = models.CharField(max_length=20, choices=DELIVERY_STATUS_CHOICES, default='pending')
    
    # Additional fields
    delivered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='delivered_orders')
    received_by = models.CharField(max_length=100, blank=True, help_text='Customer representative who received')
    signature = models.ImageField(upload_to='delivery_signatures/', blank=True, null=True)
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.delivery_number:
            # Generate delivery number
            last_delivery = DeliveryNote.objects.filter(company=self.company).order_by('-id').first()
            if last_delivery and last_delivery.delivery_number:
                try:
                    last_num = int(last_delivery.delivery_number.split('-')[-1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = 1
            else:
                new_num = 1
            self.delivery_number = f"DN-{new_num:06d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.delivery_number} - {self.customer.name}"

    class Meta:
        ordering = ['-created_at']


class DeliveryNoteItem(models.Model):
    """Items in a delivery note"""
    delivery_note = models.ForeignKey(DeliveryNote, on_delete=models.CASCADE, related_name='items')
    sales_order_item = models.ForeignKey(SalesOrderItem, on_delete=models.CASCADE, related_name='delivery_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    
    quantity_ordered = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_delivered = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    
    # Batch/Serial tracking
    batch_numbers = models.TextField(blank=True, help_text='Comma-separated batch numbers')
    serial_numbers = models.TextField(blank=True, help_text='Comma-separated serial numbers')
    
    # Quality check
    quality_checked = models.BooleanField(default=False)
    quality_notes = models.TextField(blank=True)
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - {self.quantity_delivered}/{self.quantity_ordered}"

class Invoice(models.Model):
    """Enhanced Sales Invoice model with optional sales order"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='invoices')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='invoices')
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    delivery_note = models.ForeignKey(DeliveryNote, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_invoices')
    
    # Invoice details
    invoice_number = models.CharField(max_length=50, unique=True, blank=True)
    invoice_date = models.DateField(default=timezone.now)
    due_date = models.DateField(null=True, blank=True)
    
    # Currency and amounts
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='invoices',null=True, blank=True)
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=4, default=1.0000)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    status = models.CharField(max_length=20, choices=INVOICE_STATUS_CHOICES, default='draft')
    
    # Payment terms
    payment_terms = models.CharField(max_length=100, blank=True, help_text='e.g., Net 30, COD')
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Addresses
    billing_address = models.TextField(blank=True)
    shipping_address = models.TextField(blank=True)
    
    # File management
    pdf_file = models.FileField(upload_to='invoices/', blank=True, null=True)
    
    notes = models.TextField(blank=True)
    terms_and_conditions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_status = None
        
        if not is_new:
            old_status = Invoice.objects.get(pk=self.pk).status
            
        if not self.invoice_number:
            # Generate invoice number
            last_invoice = Invoice.objects.filter(company=self.company).order_by('-id').first()
            if last_invoice and last_invoice.invoice_number:
                try:
                    last_num = int(last_invoice.invoice_number.split('-')[-1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = 1
            else:
                new_num = 1
            self.invoice_number = f"INV-{new_num:06d}"
        
        super().save(*args, **kwargs)
        
        # Process inventory reduction when invoice is confirmed (status changed from draft to sent/paid)
        if old_status == 'draft' and self.status in ['sent', 'paid']:
            self.process_inventory_reduction()
    
    def can_create_items_from_sales_order(self):
        """Check if we can create invoice items from sales order"""
        return self.sales_order is not None and not self.items.exists()
    
    def create_items_from_sales_order(self):
        """Create invoice items from sales order items"""
        if not self.can_create_items_from_sales_order():
            return False
        
        for so_item in self.sales_order.items.all():
            # Check if product is sellable and available
            if not self.is_product_sellable(so_item.product):
                continue
                
            InvoiceItem.objects.create(
                invoice=self,
                product=so_item.product,
                description=so_item.description,
                quantity=so_item.quantity,
                uom=so_item.uom,
                unit_price=so_item.unit_price,
                discount_type=so_item.discount_type,
                discount_value=so_item.discount_value,
                tax=so_item.tax,
                tracking_data=so_item.tracking_data,
                tracking_required=so_item.tracking_required
            )
        
        return True
    
    def is_product_sellable(self, product):
        """Check if product can be sold (not locked and marked as sellable)"""
        from inventory.models import StockItem
        
        # Check if product is marked as sellable
        if hasattr(product, 'is_sellable') and not product.is_sellable:
            return False
        
        # Check if there's available stock (not locked)
        available_stock = StockItem.objects.filter(
            company=self.company,
            product=product,
            stock_status='available',
            quantity__gt=0
        ).aggregate(
            total_available=models.Sum('available_quantity')
        )['total_available'] or 0
        
        return available_stock > 0
    
    def get_available_products(self):
        """Get all products that can be sold"""
        from inventory.models import StockItem
        
        # Get products that are sellable and have available stock
        available_product_ids = StockItem.objects.filter(
            company=self.company,
            stock_status='available',
            quantity__gt=0
        ).values_list('product_id', flat=True).distinct()
        
        sellable_products = Product.objects.filter(
            company=self.company,
            is_active=True,
            id__in=available_product_ids
        )
        
        # Filter by is_sellable if the field exists
        if hasattr(Product, 'is_sellable'):
            sellable_products = sellable_products.filter(is_sellable=True)
        
        return sellable_products
    
    def process_inventory_reduction(self):
        """Reduce inventory and create stock movements when invoice is confirmed"""
        from inventory.models import StockItem, StockMovement
        
        with transaction.atomic():
            for item in self.items.all():
                # Find stock items for this product
                stock_items = StockItem.objects.filter(
                    company=self.company,
                    product=item.product,
                    quantity__gt=0,
                    stock_status='available'
                ).order_by('created_at')  # FIFO approach
                
                remaining_quantity = item.quantity
                
                for stock_item in stock_items:
                    if remaining_quantity <= 0:
                        break
                    
                    # Calculate quantity to reduce from this stock item
                    quantity_to_reduce = min(remaining_quantity, stock_item.available_quantity)
                    
                    if quantity_to_reduce > 0:
                        # Update stock quantities
                        stock_item.quantity -= quantity_to_reduce
                        stock_item.available_quantity -= quantity_to_reduce
                        stock_item.save()
                        
                        # Create stock movement record
                        StockMovement.objects.create(
                            company=self.company,
                            stock_item=stock_item,
                            movement_type='sale',
                            quantity=quantity_to_reduce,
                            unit_cost=stock_item.average_cost,
                            total_cost=quantity_to_reduce * stock_item.average_cost,
                            from_warehouse=stock_item.warehouse,
                            reference_number=self.invoice_number,
                            reference_type='invoice',
                            reference_id=self.id,
                            notes=f'Sale to {self.customer.name} - Invoice {self.invoice_number}',
                            performed_by=self.created_by
                        )
                        
                        # Create tracking records if product has tracking
                        if item.product.tracking_method != 'none':
                            self.create_tracking_movements(item, stock_item, quantity_to_reduce)
                        
                        remaining_quantity -= quantity_to_reduce
                
                # If there's still remaining quantity, create backorder or alert
                if remaining_quantity > 0:
                    self.create_stock_shortage_alert(item, remaining_quantity)
    
    def create_tracking_movements(self, invoice_item, stock_item, quantity):
        """Create tracking movements for products with tracking requirements"""
        from inventory.models import StockSerial, StockLot
        
        if invoice_item.product.tracking_method in ['serial', 'imei']:
            # For serial/IMEI tracking, move individual items
            serial_items = StockSerial.objects.filter(
                stock_item=stock_item,
                status='in_stock'
            )[:int(quantity)]
            
            for serial_item in serial_items:
                serial_item.status = 'sold'
                serial_item.customer = self.customer.partner if hasattr(self.customer, 'partner') else None
                serial_item.sold_date = timezone.now()
                serial_item.save()
        
        elif invoice_item.product.tracking_method in ['batch', 'expiry']:
            # For batch/expiry tracking, update lot quantities
            lot_items = StockLot.objects.filter(
                stock_item=stock_item,
                remaining_quantity__gt=0
            ).order_by('expiry_date')  # FEFO for expiry tracking
            
            remaining_qty = quantity
            for lot_item in lot_items:
                if remaining_qty <= 0:
                    break
                
                qty_from_lot = min(remaining_qty, lot_item.remaining_quantity)
                lot_item.remaining_quantity -= qty_from_lot
                lot_item.save()
                
                remaining_qty -= qty_from_lot
    
    def create_stock_shortage_alert(self, invoice_item, shortage_quantity):
        """Create alert for stock shortage"""
        from inventory.models import StockAlert
        
    def reverse_inventory_movements(self):
        """Reverse inventory movements when invoice is cancelled or returned"""
        from inventory.models import StockItem, StockMovement, StockSerial, StockLot
        
        with transaction.atomic():
            # Find all stock movements related to this invoice
            movements = StockMovement.objects.filter(
                company=self.company,
                reference_type='invoice',
                reference_id=self.id,
                movement_type='sale'
            )
            
            for movement in movements:
                # Restore stock quantities
                stock_item = movement.stock_item
                stock_item.quantity += movement.quantity
                stock_item.available_quantity += movement.quantity
                stock_item.save()
                
                # Create reverse movement
                StockMovement.objects.create(
                    company=self.company,
                    stock_item=stock_item,
                    movement_type='sales_return',
                    quantity=movement.quantity,
                    unit_cost=movement.unit_cost,
                    total_cost=movement.total_cost,
                    to_warehouse=stock_item.warehouse,
                    reference_number=f"{self.invoice_number}-REV",
                    reference_type='invoice',
                    reference_id=self.id,
                    notes=f'Reversal of sale - Invoice {self.invoice_number} cancelled/returned',
                    performed_by=self.created_by
                )
                
                # Restore serial/lot tracking
                if stock_item.product.tracking_method in ['serial', 'imei']:
                    StockSerial.objects.filter(
                        customer=self.customer.partner if hasattr(self.customer, 'partner') else None,
                        stock_item=stock_item,
                        status='sold'
                    ).update(
                        status='in_stock',
                        customer=None,
                        sold_date=None
                    )
                
                elif stock_item.product.tracking_method in ['batch', 'expiry']:
                    # For lots, we can't easily restore the exact quantities without additional tracking
                    # This would need more sophisticated lot tracking implementation
                    pass

    @property
    def outstanding_amount(self):
        """Amount still due"""
        return self.total - self.paid_amount

    @property
    def is_overdue(self):
        """Check if invoice is overdue"""
        if self.due_date and self.status in ['sent', 'partially_paid']:
            return timezone.now().date() > self.due_date
        return False

    def __str__(self):
        return f"{self.invoice_number} - {self.customer.name}"

    class Meta:
        ordering = ['-created_at']


class InvoiceItem(models.Model):
    """Enhanced Items in an invoice with tracking and UOM support"""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    description = models.TextField(blank=True, help_text='Override product description if needed')
    
    # Quantity and UOM
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    uom = models.CharField(max_length=20, default='Pcs', help_text='Unit of Measure')
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Enhanced discount management
    discount_type = models.CharField(max_length=10, choices=[
        ('percent', 'Percentage'),
        ('amount', 'Amount'),
    ], default='percent')
    discount_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Tax
    tax = models.ForeignKey(Tax, on_delete=models.SET_NULL, null=True, blank=True)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Tracking Management
    tracking_data = models.JSONField(default=list, blank=True, help_text='Tracking numbers, serial numbers, batch info')
    tracking_required = models.BooleanField(default=False)
    tracking_complete = models.BooleanField(default=False)
    
    # Quality and delivery
    quality_notes = models.TextField(blank=True)
    delivery_notes = models.TextField(blank=True)
    
    # Linked to delivery
    delivery_note_item = models.ForeignKey(DeliveryNoteItem, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Update UOM from product if not set
        if not self.uom and self.product:
            self.uom = getattr(self.product, 'uom', 'Pcs')
        
        # Check if tracking is required
        if self.product and hasattr(self.product, 'has_tracking'):
            self.tracking_required = self.product.has_tracking
        
        # Calculate discount amount based on type
        if self.discount_type == 'percent':
            subtotal = self.quantity * self.unit_price
            self.discount_amount = subtotal * (self.discount_value / 100)
        else:  # amount
            self.discount_amount = self.discount_value
        
        # Calculate line total
        subtotal = self.quantity * self.unit_price
        subtotal_after_discount = subtotal - self.discount_amount
        if self.tax:
            self.tax_amount = subtotal_after_discount * (self.tax.rate / 100)
        self.line_total = subtotal_after_discount + self.tax_amount
        
        # Validate tracking completeness
        if self.tracking_required and self.tracking_data:
            total_tracked_qty = sum(float(item.get('quantity', 0)) for item in self.tracking_data)
            self.tracking_complete = total_tracked_qty >= float(self.quantity)
        
        super().save(*args, **kwargs)
    
    def get_tracking_summary(self):
        """Get summary of tracking information"""
        if not self.tracking_data:
            return "No tracking data"
        
        summary = []
        for item in self.tracking_data:
            tracking_type = item.get('type', 'serial')
            number = item.get('number', '')
            quantity = item.get('quantity', 0)
            
            if tracking_type == 'serial':
                summary.append(f"S/N: {number}")
            elif tracking_type == 'batch':
                summary.append(f"Batch: {number} (Qty: {quantity})")
        
        return "; ".join(summary)
    
    def validate_tracking_quantity(self):
        """Validate that tracked quantity matches line quantity"""
        if not self.tracking_required:
            return True
        
        if not self.tracking_data:
            return False
        
        total_tracked = sum(float(item.get('quantity', 0)) for item in self.tracking_data)
        return total_tracked >= float(self.quantity)

    def __str__(self):
        return f"{self.product.name} x {self.quantity} {self.uom}"

class Payment(models.Model):
    """Enhanced Customer Payment model"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='payments')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='payments',null=True, blank=True)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments', null=True, blank=True)
    
    # Payment details
    payment_number = models.CharField(max_length=50, unique=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    payment_date = models.DateField(default=timezone.now)
    
    # Payment method details
    method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cash')
    reference = models.CharField(max_length=100, blank=True, help_text='Check number, transaction ID, etc.')
    bank_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='payments', help_text='Bank account where payment was received')
    
    # Currency support
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='payments',null=True, blank=True)
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=4, default=1.0000)
    
    # Processing details
    received_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_payments')
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_payments')
    
    # Payment processing
    is_advance_payment = models.BooleanField(default=False, help_text='Payment received before invoice')
    is_write_off = models.BooleanField(default=False, help_text='Write-off due to uncollectible amount')
    write_off_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='write_off_payments')
    
    # Additional fields
    notes = models.TextField(blank=True)
    attachment = models.FileField(upload_to='payment_attachments/', blank=True, null=True,
                                help_text='Receipt, check image, etc.')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.payment_number:
            # Generate payment number
            last_payment = Payment.objects.filter(company=self.company).order_by('-id').first()
            if last_payment and last_payment.payment_number:
                try:
                    last_num = int(last_payment.payment_number.split('-')[-1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = 1
            else:
                new_num = 1
            self.payment_number = f"PAY-{new_num:06d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.payment_number} - {self.amount} ({self.customer.name})"

    class Meta:
        ordering = ['-created_at']


class SalesCommission(models.Model):
    """Sales commission tracking"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='sales_commissions')
    sales_person = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sales_commissions')
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='commissions')
    
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, help_text='Commission percentage')
    commission_amount = models.DecimalField(max_digits=12, decimal_places=2)
    calculation_base = models.DecimalField(max_digits=12, decimal_places=2, help_text='Amount on which commission is calculated')
    
    # Status
    is_paid = models.BooleanField(default=False)
    paid_date = models.DateField(null=True, blank=True)
    paid_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='paid_commissions')
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Commission for {self.sales_person.email} - {self.commission_amount}"


class CreditNote(models.Model):
    """Credit notes for returns and adjustments"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='credit_notes')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='credit_notes')
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True, related_name='credit_notes')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_credit_notes')
    
    credit_number = models.CharField(max_length=50, unique=True, blank=True)
    credit_date = models.DateField(default=timezone.now)
    
    # Amounts
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='credit_notes')
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=4, default=1.0000)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Reason for credit
    reason = models.CharField(max_length=20, choices=[
        ('return', 'Product Return'),
        ('damage', 'Damaged Goods'),
        ('discount', 'Additional Discount'),
        ('error', 'Billing Error'),
        ('other', 'Other'),
    ], default='return')
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.credit_number:
            # Generate credit number
            last_credit = CreditNote.objects.filter(company=self.company).order_by('-id').first()
            if last_credit and last_credit.credit_number:
                try:
                    last_num = int(last_credit.credit_number.split('-')[-1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = 1
            else:
                new_num = 1
            self.credit_number = f"CN-{new_num:06d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.credit_number} - {self.customer.name}"


class SalesOrderItemTracking(models.Model):
    """Enhanced tracking for sales order items - supports all tracking methods"""
    sales_order_item = models.ForeignKey(SalesOrderItem, on_delete=models.CASCADE, related_name='tracking_items')
    
    # Core tracking fields
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1.0,
                                 help_text='Quantity for this tracking entry')
    
    # Serial/IMEI tracking
    serial_number = models.CharField(max_length=255, blank=True,
                                   help_text='Serial number for individual tracking')
    imei_number = models.CharField(max_length=20, blank=True,
                                 help_text='IMEI number for mobile devices')
    
    # Batch/Lot tracking
    batch_number = models.CharField(max_length=100, blank=True,
                                  help_text='Batch or lot number')
    production_date = models.DateField(null=True, blank=True,
                                     help_text='Production/manufacture date')
    expiry_date = models.DateField(null=True, blank=True,
                                 help_text='Expiry date for perishable items')
    
    # Barcode tracking
    barcode = models.CharField(max_length=255, blank=True,
                             help_text='Product barcode/QR code')
    
    # Status and location
    status = models.CharField(max_length=20, choices=[
        ('reserved', 'Reserved'),
        ('picked', 'Picked'),
        ('packed', 'Packed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('returned', 'Returned'),
    ], default='reserved')
    
    warehouse_location = models.CharField(max_length=100, blank=True,
                                        help_text='Specific warehouse location/bin')
    
    # Delivery tracking
    delivery_note = models.ForeignKey(DeliveryNote, on_delete=models.SET_NULL, 
                                    null=True, blank=True, related_name='tracked_items')
    delivered_date = models.DateTimeField(null=True, blank=True)
    
    # Quality and condition
    quality_status = models.CharField(max_length=20, choices=[
        ('good', 'Good'),
        ('damaged', 'Damaged'), 
        ('defective', 'Defective'),
        ('expired', 'Expired'),
        ('returned', 'Returned'),
    ], default='good')
    
    notes = models.TextField(blank=True, help_text='Additional tracking notes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        tracking_info = []
        if self.serial_number:
            tracking_info.append(f"SN: {self.serial_number}")
        if self.imei_number:
            tracking_info.append(f"IMEI: {self.imei_number}")
        if self.batch_number:
            tracking_info.append(f"Batch: {self.batch_number}")
        if self.barcode:
            tracking_info.append(f"Barcode: {self.barcode}")
        
        tracking_str = " | ".join(tracking_info) if tracking_info else f"Qty: {self.quantity}"
        return f"{self.sales_order_item.product.name} - {tracking_str}"
    
    class Meta:
        verbose_name = 'Sales Order Item Tracking'
        verbose_name_plural = 'Sales Order Item Tracking'
        indexes = [
            models.Index(fields=['serial_number']),
            models.Index(fields=['imei_number']),
            models.Index(fields=['batch_number']),
            models.Index(fields=['barcode']),
        ]


class SalesOrderDiscount(models.Model):
    """Enhanced discount support for sales orders"""
    sales_order = models.OneToOneField(SalesOrder, on_delete=models.CASCADE, related_name='discount_details')
    
    # Discount type and amounts
    discount_type = models.CharField(max_length=20, choices=[
        ('percentage', 'Percentage'),
        ('fixed_amount', 'Fixed Amount'),
        ('bulk_discount', 'Bulk Discount'),
        ('customer_discount', 'Customer Discount'),
        ('promotion', 'Promotional Discount'),
    ], default='percentage')
    
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                                            validators=[MinValueValidator(0), MaxValueValidator(100)],
                                            help_text='Discount percentage (0-100)')
    
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                        help_text='Fixed discount amount')
    
    # Conditional discounts
    minimum_quantity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                         help_text='Minimum quantity for discount')
    minimum_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True,
                                       help_text='Minimum order amount for discount')
    
    # Validity
    valid_from = models.DateField(null=True, blank=True)
    valid_until = models.DateField(null=True, blank=True)
    
    # Approval and authorization
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='approved_discounts')
    approval_reason = models.TextField(blank=True)
    
    # Customer-specific
    customer_tier = models.CharField(max_length=50, blank=True,
                                   help_text='Customer tier/category for discount')
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def calculate_discount_amount(self, base_amount):
        """Calculate actual discount amount based on type and base amount"""
        if self.discount_type == 'percentage':
            return base_amount * (self.discount_percentage / 100)
        elif self.discount_type == 'fixed_amount':
            return min(self.discount_amount, base_amount)
        return 0
    
    def __str__(self):
        if self.discount_type == 'percentage':
            return f"{self.discount_percentage}% discount"
        else:
            return f"${self.discount_amount} fixed discount"
    
    class Meta:
        verbose_name = 'Sales Order Discount'
        verbose_name_plural = 'Sales Order Discounts'
