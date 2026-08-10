from django.db import models
from django.db.models import Sum
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
from django.db import transaction
from user_auth.models import Company, User
from crm.models import Customer
from accounting.models import Account
from products.models import Product  # Import centralized Product model
from core.models import SoftDeleteMixin
from core.numbering import next_number

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
            self.quotation_number = next_number(
                self.company, 'quotation', 'QUO', 6, Quotation, 'quotation_number', 'objects',
            )
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
            self.order_number = next_number(
                self.company, 'sales_order', 'SO', 6, SalesOrder, 'order_number', 'objects',
            )
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
        discount_value = Decimal(str(self.discount_value or 0))
        if self.discount_type == 'percent':
            subtotal = self.quantity * self.unit_price
            self.discount_amount = subtotal * (discount_value / Decimal('100'))
        else:  # amount
            self.discount_amount = discount_value
        
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
            self.delivery_number = next_number(
                self.company, 'delivery_note', 'DN', 6, DeliveryNote, 'delivery_number', 'objects',
            )
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

class Invoice(SoftDeleteMixin, models.Model):
    """Enhanced Sales Invoice model with optional sales order"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='invoices')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='invoices')
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    delivery_note = models.ForeignKey(DeliveryNote, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_invoices')
    
    # Invoice details
    invoice_number = models.CharField(max_length=50, unique=True, blank=True)
    invoice_date = models.DateField(default=timezone.localdate)
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
            # all_objects, not the soft-delete filtered default manager: restore() flips
            # is_deleted=False on this same Python instance then calls save(), which lands
            # here while the DB row is still is_deleted=True - Invoice.objects.get() would
            # 404 on its own row and crash every restore of a soft-deleted invoice.
            old_status = Invoice.all_objects.get(pk=self.pk).status
            
        if not self.invoice_number:
            # next_number()'s shared counter serializes concurrent invoice-number
            # generation so two simultaneous POS checkouts can't collide on the same
            # generated number, and (via lease_range() sharing the same counter) so a
            # desktop app spending a leased offline batch can't collide with a number the
            # cloud generates directly at the same time either.
            self.invoice_number = next_number(
                self.company, 'invoice', 'INV', 6, Invoice, 'invoice_number', 'all_objects',
            )

        super().save(*args, **kwargs)

        # Process inventory reduction when invoice is confirmed (status changed from draft
        # to sent/paid/partially_paid - goods physically leave the store even on a partial
        # payment, e.g. a POS credit sale, so partially_paid must trigger this too).
        if old_status == 'draft' and self.status in ['sent', 'paid', 'partially_paid']:
            self.process_inventory_reduction()
            self.update_customer_ledger_debit()

    def update_customer_ledger_debit(self):
        """Debit the customer ledger for this invoice's total (liability recorded on confirm)."""
        from crm.models import CustomerLedger  # Avoid circular import

        description = f'Invoice {self.invoice_number}'
        ledger_entry, created = CustomerLedger.objects.get_or_create(
            company=self.company,
            customer=self.customer,
            reference_type='invoice',
            reference_id=self.id,
            defaults={
                'transaction_date': self.invoice_date,
                'description': description,
                'debit_amount': self.total,
                'credit_amount': 0,
                'created_by': self.created_by,
            }
        )
        if not created:
            # Deliberately not update_or_create() - its update path only writes fields
            # listed in defaults, so the balance recalculated in CustomerLedger.save()
            # would be silently dropped. A full .save() is required to persist it.
            ledger_entry.transaction_date = self.invoice_date
            ledger_entry.description = description
            ledger_entry.debit_amount = self.total
            ledger_entry.credit_amount = 0
            ledger_entry.save()
    
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
                        # NOTE: don't mutate/save stock_item's quantity here -
                        # StockMovement.save() (movement_type='sale') already applies this
                        # exact reduction via update_stock_quantities(). Doing both was a
                        # real bug: every sale silently deducted stock TWICE.

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
        from inventory.models import StockLot
        from products.models import ProductTracking

        if invoice_item.product.tracking_method in ['serial', 'imei']:
            # For serial/IMEI tracking, sell individual ProductTracking units.
            # ProductTracking is the canonical source of truth for individually-tracked
            # units - it's the model actually populated by GRN/Bill receiving.
            if invoice_item.tracking_unit_id:
                # Explicit selection (e.g. POS: cashier scanned this exact IMEI) - sell
                # that unit specifically rather than letting FIFO pick a different one.
                tracked_units = ProductTracking.objects.filter(
                    pk=invoice_item.tracking_unit_id,
                    product=invoice_item.product,
                    status='available'
                )
            else:
                tracked_units = ProductTracking.objects.filter(
                    product=invoice_item.product,
                    current_warehouse=stock_item.warehouse,
                    status='available'
                ).order_by('created_at')[:int(quantity)]

            customer_partner = self.customer.partner if hasattr(self.customer, 'partner') else None
            for unit in tracked_units:
                unit.status = 'sold'
                unit.sold_to_customer = customer_partner
                unit.sold_date = timezone.now()
                unit.sold_invoice = self
                unit.save()

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
        from inventory.models import StockItem, StockMovement
        from products.models import ProductTracking
        
        with transaction.atomic():
            # Find all stock movements related to this invoice
            movements = StockMovement.objects.filter(
                company=self.company,
                reference_type='invoice',
                reference_id=self.id,
                movement_type='sale'
            )
            
            for movement in movements:
                # NOTE: don't mutate/save stock_item's quantity here - StockMovement.save()
                # (movement_type='sales_return') already restores it via
                # update_stock_quantities(). See the matching note in
                # process_inventory_reduction() for why doing both double-counts.
                stock_item = movement.stock_item

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
                
                # Restore serial/IMEI tracking units sold from this invoice
                if stock_item.product.tracking_method in ['serial', 'imei']:
                    ProductTracking.objects.filter(
                        sold_invoice=self,
                        product=stock_item.product,
                        status='sold'
                    ).update(
                        status='available',
                        sold_to_customer=None,
                        sold_date=None,
                        sold_invoice=None
                    )
                
                elif stock_item.product.tracking_method in ['batch', 'expiry']:
                    # For lots, we can't easily restore the exact quantities without additional tracking
                    # This would need more sophisticated lot tracking implementation
                    pass

    def soft_delete(self, user):
        """Same ledger-mirror-cleanup pattern as Payment.soft_delete: the CustomerLedger
        debit entry isn't touched by save() on a plain field-update save (it's only
        (re)written on the draft->confirmed status transition), so remove it explicitly.
        Deliberately NOT reversing stock/tracking movements here - reverse_inventory_
        movements() isn't written to be safely re-appliable on a later restore (no
        idempotency guard against double-counting), so an invoice's stock effect is left
        as-is by delete/restore; only its ledger/financial visibility changes. Revisit if
        stock accuracy after a delete turns out to matter in practice.
        """
        super().soft_delete(user)
        from crm.models import CustomerLedger
        CustomerLedger.objects.filter(
            company=self.company, customer=self.customer, reference_type='invoice', reference_id=self.id,
        ).delete()

    def restore(self):
        super().restore()
        if self.status != 'draft':
            self.update_customer_ledger_debit()

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
    tracking_unit = models.ForeignKey(
        'products.ProductTracking', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='invoice_items',
        help_text="Specific IMEI/serial unit sold on this line (POS explicit selection) - "
                  "when set, this exact unit is sold instead of FIFO-picking any available unit."
    )
    description = models.TextField(blank=True, help_text='Override product description if needed')

    # Quantity and UOM
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    uom = models.CharField(max_length=20, default='Pcs', help_text='Unit of Measure')
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)

    # Enhanced discount management - discount_type/discount_value are the legacy
    # single-discount fields (still written by create_items_from_sales_order()); a line
    # with any entries in `discounts` uses that instead (see core.pricing.compute_line_discount).
    discount_type = models.CharField(max_length=10, choices=[
        ('percent', 'Percentage'),
        ('amount', 'Amount'),
    ], default='percent')
    discount_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discounts = models.JSONField(default=list, blank=True, help_text='[{"type": "fixed"|"percent"|"per_unit", "value": "10.00"}, ...]')
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

        # Calculate discount amount: `discounts` (multi-type, stackable) takes priority
        # when set; otherwise fall back to the legacy single discount_type/discount_value.
        from core.pricing import compute_line_discount
        subtotal = self.quantity * self.unit_price
        if self.discounts:
            self.discount_amount = compute_line_discount(subtotal, self.quantity, self.discounts)
        else:
            discount_value = Decimal(str(self.discount_value or 0))
            if self.discount_type == 'percent':
                self.discount_amount = subtotal * (discount_value / Decimal('100'))
            else:  # amount
                self.discount_amount = discount_value

        # Calculate line total
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

class Payment(SoftDeleteMixin, models.Model):
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
            self.payment_number = next_number(
                self.company, 'payment', 'PAY', 6, Payment, 'payment_number', 'all_objects',
            )
        super().save(*args, **kwargs)

        if self.customer:
            self.update_customer_ledger_credit()
        if self.invoice_id:
            self.update_invoice_paid_amount()

    def update_invoice_paid_amount(self):
        """
        Keep Invoice.paid_amount/status in sync - pos_checkout() sets it once at
        creation time, but nothing else did, so a payment recorded later (e.g. from the
        Invoices page against a partially-paid/outstanding invoice) silently never showed
        up on the invoice itself even though the customer ledger was updated correctly.
        Recomputed from all payments against this invoice rather than incremented, so
        edits/deletes of a Payment can't cause it to drift.
        """
        total_paid = self.invoice.payments.aggregate(total=Sum('amount'))['total'] or 0
        self.invoice.paid_amount = total_paid
        self.invoice.status = 'paid' if total_paid >= self.invoice.total else 'partially_paid'
        self.invoice.save(update_fields=['paid_amount', 'status'])

    def soft_delete(self, user):
        """save()'s ledger sync (update_customer_ledger_credit) always re-syncs the
        mirrored CustomerLedger row via get_or_create regardless of is_deleted, so it
        would otherwise survive a soft-delete unchanged - remove it explicitly here.
        restore() doesn't need the opposite fix: its own save() call recreates the
        ledger row via that same get_or_create the moment it runs.
        """
        super().soft_delete(user)
        from crm.models import CustomerLedger
        CustomerLedger.objects.filter(
            company=self.company, customer=self.customer, reference_type='payment', reference_id=self.id,
        ).delete()

    def update_customer_ledger_credit(self):
        from crm.models import CustomerLedger  # Avoid circular import

        description = f'Payment {self.payment_number}'
        ledger_entry, created = CustomerLedger.objects.get_or_create(
            company=self.company,
            customer=self.customer,
            reference_type='payment',
            reference_id=self.id,
            defaults={
                'transaction_date': self.payment_date,
                'description': description,
                'debit_amount': 0,
                'credit_amount': self.amount,
                'payment_method': self.method,
                'reference_number': self.reference,
                'created_by': self.received_by,
            }
        )
        if not created:
            ledger_entry.transaction_date = self.payment_date
            ledger_entry.description = description
            ledger_entry.credit_amount = self.amount
            ledger_entry.payment_method = self.method
            ledger_entry.reference_number = self.reference
            ledger_entry.save()

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
    credit_date = models.DateField(default=timezone.localdate)
    
    # Amounts - currency is optional (this shop, like Invoice, doesn't use multi-currency)
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='credit_notes', null=True, blank=True)
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
            self.credit_number = next_number(
                self.company, 'credit_note', 'CN', 6, CreditNote, 'credit_number', 'objects',
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.credit_number} - {self.customer.name}"


class CreditNoteItem(models.Model):
    """
    One returned line - either a specific tracked unit (IMEI/serial, always qty 1) or a
    quantity of an untracked product. Links back to the original InvoiceItem so a return
    can't outlive/exceed what was actually sold on that line.
    """
    credit_note = models.ForeignKey(CreditNote, on_delete=models.CASCADE, related_name='items')
    invoice_item = models.ForeignKey(InvoiceItem, on_delete=models.CASCADE, related_name='return_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='credit_note_items')
    tracking_unit = models.ForeignKey(
        'products.ProductTracking', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='credit_note_items',
        help_text="Specific IMEI/serial unit being returned - null for untracked/quantity-based items"
    )
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.credit_note.credit_number} - {self.product.name} x{self.quantity}"


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
