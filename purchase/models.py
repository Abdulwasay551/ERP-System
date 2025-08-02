from django.db import models
from django.db.models import Sum, Q
from django.core.validators import MinValueValidator
from user_auth.models import Company, User
from crm.models import Partner
from products.models import Product  # Import centralized Product model
from decimal import Decimal
from django.utils import timezone

# Create your models here.

# Unit of Measure for Purchase Module
class UnitOfMeasure(models.Model):
    """Master UOM definitions for purchase operations"""
    UOM_TYPE_CHOICES = [
        ('weight', 'Weight'),
        ('volume', 'Volume'), 
        ('length', 'Length'),
        ('area', 'Area'),
        ('quantity', 'Quantity'),
        ('time', 'Time'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='purchase_uoms')
    name = models.CharField(max_length=100)
    abbreviation = models.CharField(max_length=20)
    uom_type = models.CharField(max_length=50, choices=UOM_TYPE_CHOICES)
    is_base_unit = models.BooleanField(default=False, help_text="Base unit for this UOM type")
    conversion_factor = models.DecimalField(
        max_digits=12, 
        decimal_places=6, 
        default=1,
        help_text="Conversion factor to base unit"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['company', 'name']
        ordering = ['uom_type', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.abbreviation})"

class Supplier(models.Model):
    """Enhanced Supplier model with supplier-specific features - linked to Partner for basic info"""
    
    SUPPLIER_TYPE_CHOICES = [
        ('manufacturer', 'Manufacturer'),
        ('distributor', 'Distributor'),
        ('wholesaler', 'Wholesaler'),
        ('retailer', 'Retailer'),
        ('service_provider', 'Service Provider'),
        ('contractor', 'Contractor'),
        ('consultant', 'Consultant'),
        ('other', 'Other'),
    ]
    
    SUPPLIER_STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending_approval', 'Pending Approval'),
        ('blacklisted', 'Blacklisted'),
        ('on_hold', 'On Hold'),
        ('terminated', 'Terminated'),
    ]
    
    # Link to centralized Partner (required)
    partner = models.OneToOneField(Partner, on_delete=models.CASCADE, related_name='supplier_profile')

    # Supplier-specific Information
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='suppliers')
    supplier_code = models.CharField(max_length=50, unique=True, blank=True)
    supplier_type = models.CharField(max_length=50, choices=SUPPLIER_TYPE_CHOICES, default='manufacturer')
    status = models.CharField(max_length=50, choices=SUPPLIER_STATUS_CHOICES, default='active')
    
    # Operational Information
    delivery_lead_time = models.IntegerField(default=0, help_text="Default delivery time in days")
    minimum_order_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    preferred_shipping_method = models.CharField(max_length=100, blank=True)
    
    # Performance Metrics
    quality_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0, help_text="Quality rating 0-10")
    delivery_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0, help_text="Delivery rating 0-10")
    price_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0, help_text="Price competitiveness 0-10")
    service_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0, help_text="Service rating 0-10")
    overall_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0, help_text="Overall rating 0-10")
    
    # Legacy fields for backward compatibility
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_suppliers')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Generate supplier code if not exists
        if not self.supplier_code:
            last_supplier = Supplier.objects.filter(company=self.company).order_by('-id').first()
            if last_supplier and last_supplier.supplier_code:
                try:
                    last_number = int(last_supplier.supplier_code.split('-')[-1])
                    new_number = last_number + 1
                except (ValueError, IndexError):
                    new_number = 1
            else:
                new_number = 1
            
            self.supplier_code = f'SUP-{new_number:06d}'
        
        # Calculate overall rating
        ratings = [self.quality_rating, self.delivery_rating, self.price_rating, self.service_rating]
        valid_ratings = [r for r in ratings if r > 0]
        if valid_ratings:
            self.overall_rating = sum(valid_ratings) / len(valid_ratings)
        
        # Ensure partner is marked as supplier
        if self.partner:
            self.partner.is_supplier = True
            self.partner.save()
        
        super().save(*args, **kwargs)

    # Properties to access Partner fields easily
    @property
    def name(self):
        return self.partner.name if self.partner else ""
    
    @property
    def email(self):
        return self.partner.email if self.partner else ""
    
    @property
    def phone(self):
        return self.partner.phone if self.partner else ""
    
    @property
    def mobile(self):
        return self.partner.mobile if self.partner else ""
    
    @property
    def website(self):
        return self.partner.website if self.partner else ""
    
    @property
    def address(self):
        return self.partner.get_full_address() if self.partner else ""
    
    @property
    def city(self):
        return self.partner.city if self.partner else ""
    
    @property
    def state(self):
        return self.partner.state if self.partner else ""
    
    @property
    def country(self):
        return self.partner.country if self.partner else ""
    
    @property
    def postal_code(self):
        return self.partner.zip_code if self.partner else ""
    
    @property
    def contact_person(self):
        return self.partner.contact_person if self.partner else ""
    
    @property
    def tax_number(self):
        return self.partner.tax_id if self.partner else ""
    
    @property
    def vat_number(self):
        return self.partner.vat_number if self.partner else ""
    
    @property
    def payment_terms(self):
        return self.partner.payment_terms if self.partner else ""
    
    @property
    def preferred_currency(self):
        return self.partner.preferred_currency if self.partner else "USD"
    
    @property
    def credit_limit(self):
        return self.partner.credit_limit if self.partner else 0
    
    @property
    def credit_period_days(self):
        return self.partner.credit_period_days if self.partner else 30
    
    @property
    def bank_details(self):
        return self.partner.bank_details if self.partner else ""
    
    @property
    def business_registration_number(self):
        return self.partner.registration_number if self.partner else ""
    
    @property
    def established_year(self):
        return self.partner.established_year if self.partner else None
    
    @property
    def annual_revenue(self):
        return self.partner.annual_revenue if self.partner else None
    
    @property
    def employee_count(self):
        return self.partner.employee_count if self.partner else None
    
    @property
    def certifications(self):
        return self.partner.certifications if self.partner else ""
    
    @property
    def relationship_manager(self):
        return self.partner.relationship_manager if self.partner else None
    
    @property
    def last_contact_date(self):
        return self.partner.last_contact_date if self.partner else None
    
    @property
    def next_review_date(self):
        return self.partner.next_review_date if self.partner else None
    
    @property
    def notes(self):
        return self.partner.notes if self.partner else ""

    def get_outstanding_balance(self):
        """Get current outstanding balance with supplier"""
        from .models import SupplierLedger
        ledger_totals = SupplierLedger.objects.filter(supplier=self).aggregate(
            total_debit=Sum('debit_amount'),
            total_credit=Sum('credit_amount')
        )
        
        total_debit = ledger_totals['total_debit'] or 0
        total_credit = ledger_totals['total_credit'] or 0
        return total_debit - total_credit

    def get_total_purchases(self, year=None):
        """Get total purchase amount for a year or all time"""
        bills = self.bills.filter(status__in=['approved', 'paid'])
        if year:
            bills = bills.filter(bill_date__year=year)
        return bills.aggregate(total=Sum('total_amount'))['total'] or 0

    def get_average_payment_days(self):
        """Calculate average payment days"""
        payments = self.payments.filter(status='completed')
        if not payments.exists():
            return 0
        
        total_days = 0
        count = 0
        for payment in payments:
            if payment.bill and payment.actual_date:
                days = (payment.actual_date - payment.bill.bill_date).days
                total_days += days
                count += 1
        
        return total_days / count if count > 0 else 0

    def update_performance_ratings(self):
        """Update performance ratings based on historical data"""
        # This would be implemented based on your business logic
        # For now, it's a placeholder for future enhancement
        pass

    def __str__(self):
        return self.partner.name if self.partner else f"Supplier {self.supplier_code}"

    class Meta:
        ordering = ['partner__name']
        indexes = [
            models.Index(fields=['supplier_code']),
            models.Index(fields=['status', 'is_active']),
            models.Index(fields=['supplier_type']),
        ]


class SupplierContact(models.Model):
    """Additional contacts for suppliers"""
    
    CONTACT_TYPE_CHOICES = [
        ('primary', 'Primary Contact'),
        ('accounting', 'Accounting'),
        ('sales', 'Sales'),
        ('technical', 'Technical Support'),
        ('logistics', 'Logistics'),
        ('quality', 'Quality Assurance'),
        ('executive', 'Executive'),
        ('other', 'Other'),
    ]
    
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='contacts')
    contact_type = models.CharField(max_length=50, choices=CONTACT_TYPE_CHOICES)
    name = models.CharField(max_length=255)
    designation = models.CharField(max_length=100, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)
    mobile = models.CharField(max_length=50, blank=True)
    is_primary = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.supplier.name})"

    class Meta:
        ordering = ['supplier', 'contact_type', 'name']


class SupplierProductCatalog(models.Model):
    """Supplier's product catalog with pricing"""
    
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='product_catalog')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='supplier_catalogs')
    supplier_product_code = models.CharField(max_length=100, blank=True)
    supplier_product_name = models.CharField(max_length=255, blank=True)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, choices=Partner.CURRENCY_CHOICES, default='USD')
    minimum_order_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    lead_time_days = models.IntegerField(default=0)
    
    # Pricing tiers
    tier_1_qty = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tier_1_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    tier_2_qty = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tier_2_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    tier_3_qty = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tier_3_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Validity
    effective_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Additional information
    description = models.TextField(blank=True)
    technical_specifications = models.TextField(blank=True)
    warranty_terms = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_price_for_quantity(self, quantity):
        """Get the best price for a given quantity"""
        if self.tier_3_qty and quantity >= self.tier_3_qty and self.tier_3_price:
            return self.tier_3_price
        elif self.tier_2_qty and quantity >= self.tier_2_qty and self.tier_2_price:
            return self.tier_2_price
        elif self.tier_1_qty and quantity >= self.tier_1_qty and self.tier_1_price:
            return self.tier_1_price
        else:
            return self.unit_price

    def __str__(self):
        return f"{self.supplier.name} - {self.product.name}"

    class Meta:
        ordering = ['supplier', 'product']
        unique_together = ['supplier', 'product']

# Tax and Charges Template
class TaxChargesTemplate(models.Model):
    CHARGE_TYPE_CHOICES = [
        ('tax', 'Tax'),
        ('freight', 'Freight'),
        ('customs', 'Customs'),
        ('insurance', 'Insurance'),
        ('other', 'Other'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='tax_charges_templates')
    name = models.CharField(max_length=255)
    charge_type = models.CharField(max_length=50, choices=CHARGE_TYPE_CHOICES)
    rate = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    is_percentage = models.BooleanField(default=True)
    account = models.ForeignKey('accounting.Account', on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.rate}{'%' if self.is_percentage else ''}"

    class Meta:
        ordering = ['name']

# Purchase Requisition
class PurchaseRequisition(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('partially_ordered', 'Partially Ordered'),
        ('fully_ordered', 'Fully Ordered'),
        ('cancelled', 'Cancelled'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='purchase_requisitions')
    pr_number = models.CharField(max_length=100, unique=True)
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requested_prs')
    department = models.CharField(max_length=255, blank=True)
    warehouse = models.ForeignKey('inventory.Warehouse', on_delete=models.SET_NULL, null=True, blank=True, help_text="Delivery warehouse")
    request_date = models.DateField(auto_now_add=True)
    required_date = models.DateField()
    purpose = models.TextField(blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='draft')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_prs')
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_reason = models.TextField(blank=True)
    total_estimated_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Document uploads
    requisition_document = models.FileField(upload_to='purchase/requisitions/', null=True, blank=True, help_text="Requisition document")
    technical_specifications = models.FileField(upload_to='purchase/requisitions/specs/', null=True, blank=True, help_text="Technical specifications")
    budget_approval = models.FileField(upload_to='purchase/requisitions/budget/', null=True, blank=True, help_text="Budget approval document")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"PR-{self.pr_number}"

    class Meta:
        ordering = ['-created_at']

# Purchase Requisition Items
class PurchaseRequisitionItem(models.Model):
    purchase_requisition = models.ForeignKey(PurchaseRequisition, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    preferred_supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    specifications = models.TextField(blank=True)
    ordered_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    def save(self, *args, **kwargs):
        self.total_amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

# Request for Quotation
class RequestForQuotation(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('responses_received', 'Responses Received'),
        ('completed', 'Completed'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='rfqs')
    rfq_number = models.CharField(max_length=100, unique=True)
    purchase_requisition = models.ForeignKey(PurchaseRequisition, on_delete=models.SET_NULL, null=True, blank=True)
    warehouse = models.ForeignKey('inventory.Warehouse', on_delete=models.SET_NULL, null=True, blank=True, help_text="Delivery warehouse")
    suppliers = models.ManyToManyField(Supplier, related_name='rfqs')
    issue_date = models.DateField(auto_now_add=True)
    response_deadline = models.DateField()
    payment_terms = models.CharField(max_length=255, blank=True)
    delivery_terms = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    terms_and_conditions = models.TextField(blank=True)
    
    # Document uploads
    rfq_document = models.FileField(upload_to='purchase/rfq/', null=True, blank=True, help_text="RFQ document file")
    technical_specifications = models.FileField(upload_to='purchase/rfq/specs/', null=True, blank=True, help_text="Technical specifications document")
    drawing_attachments = models.FileField(upload_to='purchase/rfq/drawings/', null=True, blank=True, help_text="Technical drawings or blueprints")
    
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='draft')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_rfqs')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"RFQ-{self.rfq_number}"

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"RFQ-{self.rfq_number}"

    class Meta:
        ordering = ['-created_at']

# RFQ Items
class RFQItem(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    rfq = models.ForeignKey(RequestForQuotation, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    required_uom = models.ForeignKey('UnitOfMeasure', on_delete=models.SET_NULL, null=True, blank=True, help_text="Required UOM for quotation")
    specifications = models.TextField(blank=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    # Additional requirements
    minimum_qty_required = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    maximum_qty_acceptable = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    target_unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0, blank=True, null=True)
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

# Supplier Quotation
class SupplierQuotation(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='supplier_quotations')
    quotation_number = models.CharField(max_length=100)
    rfq = models.ForeignKey(RequestForQuotation, on_delete=models.CASCADE, related_name='quotations')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='quotations')
    quotation_date = models.DateField()
    valid_until = models.DateField()
    payment_terms = models.CharField(max_length=255, blank=True)
    delivery_terms = models.CharField(max_length=255, blank=True)
    delivery_time_days = models.IntegerField(default=0, help_text="Delivery time in days")
    
    # Enhanced discount/rebate fields with three types
    discount_type = models.CharField(max_length=20, choices=[
        ('percentage', 'Percentage Discount/Rebate'),
        ('fixed_amount', 'Fixed Amount Discount/Rebate'),
        ('quantity_based', 'Quantity Based Discount/Rebate'),
    ], default='percentage')
    discount_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        help_text="Percentage discount/rebate (negative for rebate, positive for discount)"
    )
    discount_amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0,
        help_text="Fixed discount/rebate amount (negative for rebate, positive for discount)"
    )
    
    # Application type for discount/rebate
    discount_application = models.CharField(max_length=20, choices=[
        ('subtract', 'Subtract from Total (Discount)'),
        ('add', 'Add to Total (Rebate/Fee)'),
    ], default='subtract', help_text="Whether to subtract (discount) or add (rebate/fee) to total")
    
    # Quantity-based discount configuration
    quantity_discount_min_qty = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        help_text="Minimum quantity for quantity-based discount"
    )
    quantity_discount_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        help_text="Discount rate for quantity-based discount"
    )
    
    # Minimum order requirements
    minimum_order_value = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0,
        help_text="Minimum order value requirement"
    )
    
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField(blank=True)
    
    # Document uploads
    quotation_document = models.FileField(upload_to='purchase/quotations/', null=True, blank=True, help_text="Supplier quotation document")
    price_list = models.FileField(upload_to='purchase/quotations/pricelists/', null=True, blank=True, help_text="Supplier price list")
    technical_brochure = models.FileField(upload_to='purchase/quotations/brochures/', null=True, blank=True, help_text="Product technical brochure")
    certificate_documents = models.FileField(upload_to='purchase/quotations/certificates/', null=True, blank=True, help_text="Quality certificates, compliance docs")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Quote-{self.quotation_number} from {self.supplier.name}"

    class Meta:
        ordering = ['-created_at']

# Supplier Quotation Items
class SupplierQuotationItem(models.Model):
    quotation = models.ForeignKey(SupplierQuotation, on_delete=models.CASCADE, related_name='items')
    rfq_item = models.ForeignKey(RFQItem, on_delete=models.CASCADE,null=True, blank=True, related_name='supplier_quotation_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    
    # UOM Enhancement
    quoted_uom = models.ForeignKey('UnitOfMeasure', on_delete=models.SET_NULL, null=True, blank=True, help_text="UOM as quoted by supplier")
    package_qty = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=1,
        help_text="Quantity of base units in this UOM (e.g., 10 pieces per packet)"
    )
    # Enhanced minimum order requirements
    minimum_order_qty = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=1,
        help_text="Minimum order quantity as specified by supplier"
    )
    
    # Enhanced discount/rebate fields for individual items
    item_discount_type = models.CharField(max_length=20, choices=[
        ('percentage', 'Percentage'),
        ('fixed_amount', 'Fixed Amount'),
        ('quantity_based', 'Quantity Based'),
    ], default='percentage', help_text="Type of discount/rebate applied to this item")
    item_discount_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        help_text="Item-specific percentage discount/rebate"
    )
    item_discount_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        help_text="Item-specific fixed discount/rebate amount"
    )
    
    # Application type for item discount/rebate
    item_discount_application = models.CharField(max_length=20, choices=[
        ('subtract', 'Subtract (Discount)'),
        ('add', 'Add (Rebate/Fee)'),
    ], default='subtract', help_text="Whether to subtract or add to item total")
    
    # Quantity-based discount for items
    item_qty_discount_min = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        help_text="Minimum quantity for item quantity discount"
    )
    item_qty_discount_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        help_text="Discount rate for quantity-based discount"
    )
    
    # Calculated fields
    base_unit_price = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        help_text="Price per base unit (auto-calculated)"
    )
    total_base_units = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0,
        help_text="Total base units for quoted quantity"
    )
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    delivery_time_days = models.IntegerField(default=0)
    specifications = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        # Calculate base unit price
        if self.package_qty > 0:
            self.base_unit_price = self.unit_price / self.package_qty
        else:
            self.base_unit_price = self.unit_price
        
        # Calculate total base units
        self.total_base_units = self.quantity * self.package_qty
        
        # Calculate total amount with enhanced discount/rebate logic
        base_amount = self.quantity * self.unit_price
        discount_amount = 0
        
        # Apply discount/rebate based on type
        if self.item_discount_type == 'percentage' and self.item_discount_percentage > 0:
            discount_amount = base_amount * (self.item_discount_percentage / 100)
        elif self.item_discount_type == 'fixed_amount' and self.item_discount_amount > 0:
            discount_amount = self.item_discount_amount
        elif self.item_discount_type == 'quantity_based' and self.quantity >= self.item_qty_discount_min:
            discount_amount = base_amount * (self.item_qty_discount_rate / 100)
        
        # Apply discount or rebate based on application type
        if self.item_discount_application == 'subtract':
            self.total_amount = base_amount - discount_amount  # Discount
        else:
            self.total_amount = base_amount + discount_amount  # Rebate/Fee
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} - ${self.unit_price}/{self.quoted_uom}"
    
    def get_comparable_price(self):
        """Get price per base unit for comparison across suppliers"""
        return self.base_unit_price
    
    def calculate_cost_for_base_units(self, base_units_needed):
        """Calculate cost for specific number of base units"""
        packages_needed = base_units_needed / self.package_qty
        # Round up to minimum order quantity
        packages_needed = max(packages_needed, self.minimum_order_qty)
        return packages_needed * self.unit_price
    
    def validate_minimum_quantity(self):
        """Validate if quoted quantity meets minimum order requirements"""
        return self.quantity >= self.minimum_order_qty
    
    def get_discount_amount(self):
        """Calculate the actual discount/rebate amount based on discount type"""
        base_amount = self.quantity * self.unit_price
        discount_amount = 0
        
        if self.item_discount_type == 'percentage' and self.item_discount_percentage > 0:
            discount_amount = base_amount * (self.item_discount_percentage / 100)
        elif self.item_discount_type == 'fixed_amount' and self.item_discount_amount > 0:
            discount_amount = self.item_discount_amount
        elif self.item_discount_type == 'quantity_based' and self.quantity >= self.item_qty_discount_min:
            discount_amount = base_amount * (self.item_qty_discount_rate / 100)
        
        # Return positive for discount, negative for rebate/fee
        if self.item_discount_application == 'subtract':
            return discount_amount  # Positive means discount (subtract from total)
        else:
            return -discount_amount  # Negative means rebate/fee (add to total)
    
    def get_discount_type_display_text(self):
        """Get display text for discount type with application"""
        if self.item_discount_application == 'add':
            return f"{self.get_item_discount_type_display()} Rebate/Fee"
        else:
            return f"{self.get_item_discount_type_display()} Discount"

class PurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('sent_to_supplier', 'Sent to Supplier'),
        ('acknowledged', 'Acknowledged'),
        ('partially_received', 'Partially Received'),
        ('fully_received', 'Fully Received'),
        ('cancelled', 'Cancelled'),
    ]
    
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage Discount/Rebate'),
        ('fixed_amount', 'Fixed Amount Discount/Rebate'),
        ('quantity_based', 'Quantity Based Discount/Rebate'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='purchase_orders')
    po_number = models.CharField(max_length=100, unique=True, null=True, blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='purchase_orders')
    purchase_requisition = models.ForeignKey(PurchaseRequisition, on_delete=models.SET_NULL, null=True, blank=True, help_text="Optional: Link to purchase requisition")
    supplier_quotation = models.ForeignKey(SupplierQuotation, on_delete=models.SET_NULL, null=True, blank=True, help_text="Optional: Reference quotation (items can vary)")
    warehouse = models.ForeignKey('inventory.Warehouse', on_delete=models.SET_NULL, null=True, blank=True, help_text="Delivery warehouse")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_purchase_orders')
    order_date = models.DateField(auto_now_add=True)
    expected_delivery_date = models.DateField(null=True, blank=True)
    
    # Enhanced fields
    purchase_limit = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Maximum allowed purchase amount")
    delivery_terms = models.CharField(max_length=255, blank=True)
    payment_terms = models.CharField(max_length=255, blank=True)
    
    # Enhanced discount/rebate fields with three types (same as quotation)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES, default='percentage')
    discount_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        help_text="Percentage discount/rebate (negative for rebate, positive for discount)"
    )
    discount_amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0,
        help_text="Fixed discount/rebate amount (negative for rebate, positive for discount)"
    )
    
    # Application type for discount/rebate
    discount_application = models.CharField(max_length=20, choices=[
        ('subtract', 'Subtract from Total (Discount)'),
        ('add', 'Add to Total (Rebate/Fee)'),
    ], default='subtract', help_text="Whether to subtract (discount) or add (rebate/fee) to total")
    
    # Quantity-based discount configuration
    quantity_discount_min_qty = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        help_text="Minimum quantity for quantity-based discount"
    )
    quantity_discount_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        help_text="Discount rate for quantity-based discount"
    )
    
    # Calculated fields
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    discount_total = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Total discount/rebate amount applied")
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField(blank=True)
    terms_conditions = models.TextField(blank=True)
    
    # Document uploads
    purchase_order_document = models.FileField(upload_to='purchase/orders/', null=True, blank=True, help_text="Generated PO document")
    supplier_agreement = models.FileField(upload_to='purchase/orders/agreements/', null=True, blank=True, help_text="Supplier agreement/contract")
    technical_drawings = models.FileField(upload_to='purchase/orders/drawings/', null=True, blank=True, help_text="Technical drawings or specifications")
    amendment_documents = models.FileField(upload_to='purchase/orders/amendments/', null=True, blank=True, help_text="PO amendments or revisions")
    
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_pos')
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # Note: Removed account field - PO is for documentation only, no accounting impact

    def save(self, *args, **kwargs):
        # Auto-generate PO number if not provided
        if not self.po_number:
            current_year = timezone.now().year
            last_po = PurchaseOrder.objects.filter(
                company=self.company,
                po_number__startswith=f'PO-{current_year}'
            ).order_by('-id').first()
            
            if last_po and last_po.po_number:
                try:
                    last_number = int(last_po.po_number.split('-')[-1])
                    new_number = last_number + 1
                except (ValueError, IndexError):
                    new_number = 1
            else:
                new_number = 1
            
            self.po_number = f'PO-{current_year}-{new_number:04d}'
        
        # Calculate totals
        if self.pk:  # Only calculate if object exists (has items)
            item_total = sum(item.line_total for item in self.items.all())
            self.subtotal = item_total
            
            # Enhanced discount calculation with three types
            total_quantity = sum(item.quantity for item in self.items.all())
            discount_total = 0
            
            if self.discount_type == 'percentage' and self.discount_percentage > 0:
                discount_total = self.subtotal * (self.discount_percentage / 100)
            elif self.discount_type == 'fixed_amount' and self.discount_amount > 0:
                discount_total = self.discount_amount
            elif self.discount_type == 'quantity_based' and total_quantity >= self.quantity_discount_min_qty:
                discount_total = self.subtotal * (self.quantity_discount_rate / 100)
            
            # Apply discount or rebate based on application type
            if self.discount_application == 'subtract':
                self.discount_total = discount_total  # Discount
                self.total_amount = self.subtotal - self.discount_total + self.tax_amount
            else:
                self.discount_total = -discount_total  # Rebate/Fee (store as negative)
                self.total_amount = self.subtotal + abs(self.discount_total) + self.tax_amount
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"PO-{self.po_number} - {self.supplier.name}"

    class Meta:
        ordering = ['-created_at']
    
    def get_total_items(self):
        """Get total number of items in this PO"""
        return self.items.count()
    
    def get_total_quantity(self):
        """Get total quantity across all items"""
        return sum(item.quantity for item in self.items.all())
    
    def get_received_percentage(self):
        """Calculate percentage of items received"""
        total_ordered = sum(item.quantity for item in self.items.all())
        total_received = sum(item.received_quantity for item in self.items.all())
        if total_ordered > 0:
            return (total_received / total_ordered) * 100
        return 0
    
    def can_be_approved(self):
        """Check if PO can be approved"""
        return self.status == 'draft' and self.items.exists()
    
    def can_be_cancelled(self):
        """Check if PO can be cancelled"""
        return self.status in ['draft', 'pending_approval', 'approved']
    
    def update_status_based_on_receipts(self):
        """Update PO status based on received quantities"""
        if not self.items.exists():
            return
        
        total_ordered = sum(item.quantity for item in self.items.all())
        total_received = sum(item.received_quantity for item in self.items.all())
        
        if total_received == 0:
            # No items received yet
            pass
        elif total_received >= total_ordered:
            self.status = 'fully_received'
        else:
            self.status = 'partially_received'
        
        self.save()

class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quotation_item = models.ForeignKey(SupplierQuotationItem, on_delete=models.SET_NULL, null=True, blank=True, help_text="Optional: Reference to quotation item")
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    uom = models.ForeignKey('UnitOfMeasure', on_delete=models.SET_NULL, null=True, blank=True)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))], default=0)
    
    # Enhanced discount/rebate fields for individual items (same as quotation)
    item_discount_type = models.CharField(max_length=20, choices=[
        ('percentage', 'Percentage'),
        ('fixed_amount', 'Fixed Amount'),
        ('quantity_based', 'Quantity Based'),
    ], default='percentage', help_text="Type of discount/rebate applied to this item")
    item_discount_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        help_text="Item-specific percentage discount/rebate"
    )
    item_discount_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        help_text="Item-specific fixed discount/rebate amount"
    )
    
    # Application type for item discount/rebate
    item_discount_application = models.CharField(max_length=20, choices=[
        ('subtract', 'Subtract (Discount)'),
        ('add', 'Add (Rebate/Fee)'),
    ], default='subtract', help_text="Whether to subtract or add to item total")
    
    # Quantity-based discount for items
    item_qty_discount_min = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        help_text="Minimum quantity for item quantity discount"
    )
    item_qty_discount_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        help_text="Discount rate for quantity-based discount"
    )
    
    # Minimum order requirements
    minimum_order_qty = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=1,
        help_text="Minimum order quantity for this item"
    )
    
    # Calculated fields
    line_total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    received_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_date = models.DateField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        # Calculate line total with enhanced discount/rebate logic
        base_amount = self.quantity * self.unit_price
        discount_amount = 0
        
        # Apply discount/rebate based on type
        if self.item_discount_type == 'percentage' and self.item_discount_percentage > 0:
            discount_amount = base_amount * (self.item_discount_percentage / 100)
        elif self.item_discount_type == 'fixed_amount' and self.item_discount_amount > 0:
            discount_amount = self.item_discount_amount
        elif self.item_discount_type == 'quantity_based' and self.quantity >= self.item_qty_discount_min:
            discount_amount = base_amount * (self.item_qty_discount_rate / 100)
        
        # Apply discount or rebate based on application type
        if self.item_discount_application == 'subtract':
            self.line_total = base_amount - discount_amount  # Discount
        else:
            self.line_total = base_amount + discount_amount  # Rebate/Fee
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
    
    def get_discount_amount(self):
        """Calculate the actual discount/rebate amount based on discount type"""
        base_amount = self.quantity * self.unit_price
        discount_amount = 0
        
        if self.item_discount_type == 'percentage' and self.item_discount_percentage > 0:
            discount_amount = base_amount * (self.item_discount_percentage / 100)
        elif self.item_discount_type == 'fixed_amount' and self.item_discount_amount > 0:
            discount_amount = self.item_discount_amount
        elif self.item_discount_type == 'quantity_based' and self.quantity >= self.item_qty_discount_min:
            discount_amount = base_amount * (self.item_qty_discount_rate / 100)
        
        # Return positive for discount, negative for rebate/fee
        if self.item_discount_application == 'subtract':
            return discount_amount  # Positive means discount (subtract from total)
        else:
            return -discount_amount  # Negative means rebate/fee (add to total)
    
    def get_discount_type_display_text(self):
        """Get display text for discount type with application"""
        if self.item_discount_application == 'add':
            return f"{self.get_item_discount_type_display()} Rebate/Fee"
        else:
            return f"{self.get_item_discount_type_display()} Discount"
    
    def validate_minimum_quantity(self):
        """Validate if ordered quantity meets minimum order requirements"""
        return self.quantity >= self.minimum_order_qty

# PO Tax and Charges
class PurchaseOrderTaxCharge(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='tax_charges')
    tax_template = models.ForeignKey(TaxChargesTemplate, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    def __str__(self):
        return f"{self.tax_template.name} - ${self.amount}"

# Goods Receipt Note (GRN) - Enhanced with Optional PO
class GoodsReceiptNote(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('received', 'Received'),
        ('inspection_pending', 'Inspection Pending'),
        ('under_inspection', 'Under Inspection'),
        ('inspection_completed', 'Inspection Completed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='grns')
    grn_number = models.CharField(max_length=100, unique=True, blank=True)
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.SET_NULL, null=True, blank=True, help_text="Optional: Link to purchase order")
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    received_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_grns')
    warehouse = models.ForeignKey('inventory.Warehouse', on_delete=models.SET_NULL, null=True, blank=True, help_text="Receiving warehouse")
    received_date = models.DateTimeField(auto_now_add=True)
    
    # Enhanced fields
    vehicle_number = models.CharField(max_length=100, blank=True)
    gate_entry_number = models.CharField(max_length=100, blank=True)
    supplier_delivery_note = models.CharField(max_length=255, blank=True)
    transporter = models.CharField(max_length=255, blank=True)
    driver_name = models.CharField(max_length=255, blank=True)
    driver_phone = models.CharField(max_length=20, blank=True)
    
    # Quality and inspection workflow
    requires_inspection = models.BooleanField(default=True, help_text="Whether items require quality inspection")
    requires_quality_inspection = models.BooleanField(default=True, help_text="Alias for requires_inspection")
    inspection_assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_inspections')
    inspected_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='inspected_grns', help_text="User who performed the inspection")
    inspection_assigned_at = models.DateTimeField(null=True, blank=True)
    inspection_due_date = models.DateField(null=True, blank=True)
    inspection_completed_at = models.DateTimeField(null=True, blank=True)
    
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField(blank=True)
    
    # Document uploads
    delivery_challan = models.FileField(upload_to='purchase/grn/challan/', null=True, blank=True, help_text="Supplier delivery challan")
    packing_list = models.FileField(upload_to='purchase/grn/packing/', null=True, blank=True, help_text="Packing list document")
    quality_certificates = models.FileField(upload_to='purchase/grn/quality/', null=True, blank=True, help_text="Quality certificates from supplier")
    inspection_report = models.FileField(upload_to='purchase/grn/inspection/', null=True, blank=True, help_text="Quality inspection report")
    photos_received_goods = models.FileField(upload_to='purchase/grn/photos/', null=True, blank=True, help_text="Photos of received goods")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Auto-generate GRN number if not provided
        if not self.grn_number:
            current_year = timezone.now().year
            last_grn = GoodsReceiptNote.objects.filter(
                company=self.company,
                grn_number__startswith=f'GRN-{current_year}'
            ).order_by('-id').first()
            
            if last_grn and last_grn.grn_number:
                try:
                    last_number = int(last_grn.grn_number.split('-')[-1])
                    new_number = last_number + 1
                except (ValueError, IndexError):
                    new_number = 1
            else:
                new_number = 1
            
            self.grn_number = f'GRN-{current_year}-{new_number:04d}'
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"GRN-{self.grn_number}"

    class Meta:
        ordering = ['-created_at']
    
    def get_total_items(self):
        """Get total number of unique items in this GRN"""
        return self.items.count()
    
    def get_total_quantity(self):
        """Get total quantity across all items"""
        return sum(item.received_qty for item in self.items.all())
    
    def can_start_inspection(self):
        """Check if inspection can be started"""
        return self.status in ['received', 'inspection_pending'] and self.requires_inspection
    
    def update_status_based_on_inspection(self):
        """Update GRN status based on inspection results"""
        if not self.requires_inspection:
            self.status = 'completed'
        else:
            # Check inspection status of all items
            items = self.items.all()
            if not items:
                return
            
            pending_items = items.filter(quality_status='pending')
            if pending_items.exists():
                self.status = 'inspection_pending'
            elif items.filter(quality_status='under_inspection').exists():
                self.status = 'under_inspection'
            else:
                # All items have been inspected
                self.status = 'inspection_completed'
        
        self.save()

# Enhanced GRN Items with Tracking
class GRNItem(models.Model):
    QUALITY_STATUS_CHOICES = [
        ('pending', 'Pending Inspection'),
        ('under_inspection', 'Under Inspection'),
        ('passed', 'Quality Passed'),
        ('failed', 'Quality Failed'),
        ('partial', 'Partially Passed'),
        ('returned', 'Returned to Supplier'),
    ]
    
    TRACKING_TYPE_CHOICES = [
        ('none', 'No Tracking'),
        ('batch', 'Batch/Lot Tracking'),
        ('serial', 'Serial Number'),
        ('imei', 'IMEI Number'),
        ('barcode', 'Barcode Tracking'),
        ('expiry', 'Expiry Date Tracking'),
    ]
    
    grn = models.ForeignKey(GoodsReceiptNote, on_delete=models.CASCADE, related_name='items')
    po_item = models.ForeignKey(PurchaseOrderItem, on_delete=models.SET_NULL, null=True, blank=True, help_text="Optional: Reference to PO item")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)

    # UOM and quantities
    uom = models.ForeignKey('UnitOfMeasure', on_delete=models.SET_NULL, null=True, blank=True)
    ordered_qty = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Quantity from PO if linked")
    received_qty = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    accepted_qty = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Quantity accepted after inspection")
    rejected_qty = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Quantity rejected after inspection")
    returned_qty = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Quantity returned to supplier")
    
    # Quality control
    quality_status = models.CharField(max_length=50, choices=QUALITY_STATUS_CHOICES, default='pending')
    inspection_notes = models.TextField(blank=True, help_text="Quality inspection notes")
    inspector = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='inspected_items')
    inspected_at = models.DateTimeField(null=True, blank=True)
    
    # Item tracking system
    tracking_type = models.CharField(max_length=20, choices=TRACKING_TYPE_CHOICES, default='none')
    tracking_required = models.BooleanField(default=False, help_text="Whether this item requires individual tracking")
    
    # Storage information
    warehouse = models.ForeignKey('inventory.Warehouse', on_delete=models.SET_NULL, null=True, blank=True)
    location = models.CharField(max_length=255, blank=True, help_text="Storage location within warehouse")
    
    # Additional fields
    expiry_date = models.DateField(null=True, blank=True, help_text="Expiry date for perishable items")
    manufacturer_date = models.DateField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Set ordered quantity from PO item if linked
        if self.po_item:
            self.ordered_qty = self.po_item.quantity
        
        # Auto-determine tracking type based on product
        if self.product:
            # Inherit tracking settings from product
            if self.product.tracking_method != 'none':
                self.tracking_type = self.product.tracking_method
                self.tracking_required = self.product.requires_individual_tracking
            else:
                self.tracking_type = 'none'
                self.tracking_required = False
        
        super().save(*args, **kwargs)
        
        # Create inventory lock for received items
        if self.pk and self.received_qty > 0 and self.grn.status == 'received':
            self.create_inventory_lock()
    
    def create_inventory_lock(self):
        """Create inventory lock for received items pending bill creation using existing GRNInventoryLock"""
        if not self.product or not getattr(self.product, 'is_stockable', True):
            return None
            
        # Create inventory tracking in inventory app
        if self._create_stock_item_and_movement():
            # Create GRN inventory lock using existing model
            lock = GRNInventoryLock.objects.create(
                grn=self.grn,
                grn_item=self,
                locked_quantity=self.received_qty,
                lock_reason='pending_invoice',
                locked_by=self.grn.received_by,
                lock_notes=f"GRN {self.grn.grn_number} pending bill creation",
            )
            
            # Also lock any tracking items
            for tracking_item in self.tracking_items.all():
                GRNInventoryLock.objects.create(
                    grn=self.grn,
                    grn_item=self,
                    tracking_item=tracking_item,
                    locked_quantity=1,  # Individual items are quantity 1
                    lock_reason='pending_invoice',
                    locked_by=self.grn.received_by,
                    lock_notes=f"Tracking item {tracking_item.tracking_number} locked pending bill",
                )
            
            return lock
        
        return None
    
    def _create_stock_item_and_movement(self):
        """Create stock item and initial movement in inventory app"""
        try:
            # Import here to avoid circular imports
            from inventory.models import StockItem, StockMovement, Warehouse
            
            # Get warehouse for this item
            warehouse = self.warehouse
            if not warehouse:
                warehouse = self.grn.warehouse
            if not warehouse:
                # Get company's first active warehouse as fallback
                warehouse = Warehouse.objects.filter(
                    company=self.grn.company, 
                    is_active=True
                ).first()
                
            if not warehouse:
                return False
                
            # Get or create stock item
            stock_item, created = StockItem.objects.get_or_create(
                company=self.grn.company,
                product=self.product,
                warehouse=warehouse,
                defaults={
                    'category': getattr(self.product, 'category', None),
                    'valuation_method': getattr(self.product, 'valuation_method', 'weighted_avg'),
                    'min_stock': getattr(self.product, 'minimum_stock', 0),
                    'max_stock': getattr(self.product, 'maximum_stock', 0),
                    'reorder_point': getattr(self.product, 'reorder_level', 0),
                    'purchase_status': 'received_unbilled',
                    'stock_status': 'locked',
                }
            )
            
            # Update status if stock item already exists
            if not created:
                stock_item.purchase_status = 'received_unbilled'
                stock_item.stock_status = 'locked'
                stock_item.save()
            
            # Create stock movement for GRN receipt (locked)
            movement = StockMovement.objects.create(
                company=self.grn.company,
                stock_item=stock_item,
                movement_type='grn_receipt',
                quantity=self.received_qty,
                unit_cost=0,  # Will be updated when bill is created
                reference_type='grn',
                reference_id=self.grn.id,
                reference_number=self.grn.grn_number,
                batch_number=getattr(self, 'batch_number', ''),
                lot_number=getattr(self, 'lot_number', ''),
                expiry_date=self.expiry_date,
                grn_item=self,
                notes=f"GRN Receipt: {self.grn.grn_number} - Locked pending bill",
                performed_by=self.grn.received_by,
            )
            
            return True
            
        except Exception as e:
            print(f"Error creating stock item and movement: {e}")
            return False
    
    def unlock_inventory_on_bill(self, bill_item):
        """Unlock inventory when bill is created and update costs"""
        # Use existing GRNInventoryLock instead of creating new inventory locks
        locks = GRNInventoryLock.objects.filter(
            grn=self.grn,
            grn_item=self,
            is_active=True,
            lock_reason='pending_invoice'
        )
        
        for lock in locks:
            # Release the lock
            lock.release_lock(
                user=bill_item.bill.created_by,
                notes=f"Bill created: {bill_item.bill.bill_number}",
                bill=bill_item.bill
            )
            
            # Update inventory with cost information
            if self.product and self.product.is_stockable:
                self._update_inventory_cost(bill_item)
        
        return True
    
    def _update_inventory_cost(self, bill_item):
        """Update inventory stock item with actual cost from bill"""
        try:
            from inventory.models import StockItem, StockMovement
            
            # Get the warehouse for this item
            warehouse = self.warehouse or self.grn.warehouse
            if not warehouse:
                return False
                
            # Get or create stock item
            stock_item, created = StockItem.objects.get_or_create(
                company=self.grn.company,
                product=self.product,
                warehouse=warehouse,
                defaults={
                    'category': self.product.category,
                    'valuation_method': getattr(self.product, 'valuation_method', 'weighted_avg'),
                    'min_stock': getattr(self.product, 'minimum_stock', 0),
                    'max_stock': getattr(self.product, 'maximum_stock', 0),
                    'reorder_point': getattr(self.product, 'reorder_level', 0),
                }
            )
            
            # Update purchase status to show items are ready for use
            stock_item.purchase_status = 'ready_for_use'
            stock_item.stock_status = 'available'
            
            # Update average cost with bill price
            stock_item.update_average_cost(self.received_qty, bill_item.unit_price)
            
            # Create movement to unlock inventory (convert from locked to available)
            StockMovement.objects.create(
                company=self.grn.company,
                stock_item=stock_item,
                movement_type='unlock',
                quantity=self.received_qty,
                unit_cost=bill_item.unit_price,
                reference_type='bill',
                reference_id=bill_item.bill.id,
                reference_number=bill_item.bill.bill_number,
                grn_item=self,
                bill_item=bill_item,
                notes=f"Inventory unlocked via bill: {bill_item.bill.bill_number}",
                performed_by=bill_item.bill.created_by,
            )
            
            return True
            
        except Exception as e:
            print(f"Error updating inventory cost: {e}")
            return False
        
    def quality_pass_inventory(self, inspector):
        """Pass quality inspection and unlock inventory"""
        if self.quality_status == 'passed':
            from inventory.models import StockMovement
            
            # Find the stock item
            from inventory.models import StockItem
            try:
                stock_item = StockItem.objects.get(
                    product=self.product,
                    warehouse=self.warehouse,
                    company=self.grn.company
                )
                
                # Create quality pass movement
                StockMovement.objects.create(
                    company=self.grn.company,
                    stock_item=stock_item,
                    movement_type='quality_pass',
                    quantity=self.accepted_qty,
                    unit_cost=stock_item.average_cost,
                    reference_type='quality_inspection',
                    reference_id=self.id,
                    reference_number=f"QC-{self.grn.grn_number}-{self.product.sku}",
                    notes=f"Quality passed for GRN: {self.grn.grn_number}",
                    performed_by=inspector,
                )
                
            except StockItem.DoesNotExist:
                pass
                
        return True
    
    def __str__(self):
        return f"{self.product.name} - Received: {self.received_qty}"
    
    def get_pending_inspection_qty(self):
        """Get quantity still pending inspection"""
        return self.received_qty - self.accepted_qty - self.rejected_qty - self.returned_qty
    
    def can_create_tracking_items(self):
        """Check if tracking items can be created"""
        return (self.tracking_required and 
                self.tracking_type != 'none' and 
                self.accepted_qty > 0 and
                self.quality_status == 'passed')
    
    def validate_tracking_quantity(self):
        """Validate that tracking items match received quantity"""
        if self.tracking_required and self.tracking_type != 'none':
            # Count tracking items
            tracking_count = self.tracking_items.count()
            
            # For individual tracking (serial, IMEI, barcode), count must match received quantity
            if self.product.requires_individual_tracking:
                if tracking_count != int(self.received_qty):
                    from django.core.exceptions import ValidationError
                    raise ValidationError(
                        f"For {self.product.name}, you must provide {int(self.received_qty)} "
                        f"{self.product.get_tracking_method_display()} numbers, "
                        f"but only {tracking_count} were provided."
                    )
            
            # For batch/expiry tracking, at least one tracking item should exist
            elif self.tracking_type in ['batch', 'expiry']:
                if tracking_count == 0:
                    from django.core.exceptions import ValidationError
                    raise ValidationError(
                        f"For {self.product.name}, at least one batch/lot entry is required."
                    )
        
        return True

# Individual Item Tracking
class GRNItemTracking(models.Model):
    """Individual tracking for items that require serial numbers, barcodes, etc."""
    grn_item = models.ForeignKey(GRNItem, on_delete=models.CASCADE, related_name='tracking_items')
    tracking_number = models.CharField(max_length=100, help_text="Barcode, Serial Number, IMEI, etc.")
    tracking_type = models.CharField(max_length=20, choices=GRNItem.TRACKING_TYPE_CHOICES)
    
    # Batch and expiry information
    batch_number = models.CharField(max_length=100, blank=True, help_text="Batch or lot number")
    manufacturing_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    supplier_batch_reference = models.CharField(max_length=100, blank=True)
    
    # Quality status for individual items
    quality_status = models.CharField(max_length=50, choices=GRNItem.QUALITY_STATUS_CHOICES, default='pending')
    inspection_notes = models.TextField(blank=True)
    inspected_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    inspected_at = models.DateTimeField(null=True, blank=True)
    
    # Physical condition
    condition = models.CharField(max_length=100, blank=True, help_text="Physical condition of the item")
    defects = models.TextField(blank=True, help_text="Any defects or issues found")
    notes = models.TextField(blank=True, help_text="Additional notes")
    
    # Current status
    is_available = models.BooleanField(default=True, help_text="Whether item is available in inventory")
    is_locked = models.BooleanField(default=True, help_text="Locked until purchase invoice is created")
    current_location = models.CharField(max_length=255, blank=True)
    
    # Link to product tracking (created automatically)
    product_tracking = models.OneToOneField(
        'products.ProductTracking',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='grn_tracking'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['grn_item', 'tracking_number']
    
    def save(self, *args, **kwargs):
        # Auto-calculate expiry date if product has shelf life
        if (not self.expiry_date and self.manufacturing_date and 
            self.grn_item.product.shelf_life_days):
            from datetime import timedelta
            self.expiry_date = self.manufacturing_date + timedelta(
                days=self.grn_item.product.shelf_life_days
            )
        
        super().save(*args, **kwargs)
        
        # Create or update corresponding ProductTracking entry
        self.create_or_update_product_tracking()
    
    def create_or_update_product_tracking(self):
        """Create or update the corresponding ProductTracking entry"""
        from products.models import ProductTracking
        
        if not self.product_tracking:
            # Create new ProductTracking
            self.product_tracking = ProductTracking.objects.create(
                product=self.grn_item.product,
                grn_item=self.grn_item,
                current_warehouse=self.grn_item.warehouse,
                purchase_price=self.grn_item.unit_price,
                purchase_date=self.grn_item.grn.received_date.date(),
                supplier=self.grn_item.grn.supplier,
                manufacturing_date=self.manufacturing_date,
                expiry_date=self.expiry_date,
                batch_number=self.batch_number,
                quality_status=self.quality_status,
                notes=self.notes,
                created_by=self.grn_item.grn.received_by
            )
            
            # Set the tracking value based on tracking type
            self.product_tracking.set_tracking_value(self.tracking_number)
            self.product_tracking.save()
            
            # Save the link back to this GRN tracking
            super().save(update_fields=['product_tracking'])
        else:
            # Update existing ProductTracking
            self.product_tracking.current_warehouse = self.grn_item.warehouse
            self.product_tracking.manufacturing_date = self.manufacturing_date
            self.product_tracking.expiry_date = self.expiry_date
            self.product_tracking.batch_number = self.batch_number
            self.product_tracking.quality_status = self.quality_status
            self.product_tracking.notes = self.notes
            self.product_tracking.set_tracking_value(self.tracking_number)
            self.product_tracking.save()

    def __str__(self):
        return f"{self.grn_item.product.name} - {self.tracking_type}: {self.tracking_number}"

# Quality Assurance - Separate from GRN
class QualityInspection(models.Model):
    """Separate quality inspection process for received items"""
    STATUS_CHOICES = [
        ('pending', 'Pending Assignment'),
        ('assigned', 'Assigned to Inspector'),
        ('in_progress', 'Inspection in Progress'),
        ('completed', 'Inspection Completed'),
        ('on_hold', 'On Hold'),
        ('cancelled', 'Cancelled'),
    ]
    
    INSPECTION_TYPE_CHOICES = [
        ('receiving', 'Receiving Inspection'),
        ('random', 'Random Quality Check'),
        ('customer_complaint', 'Customer Complaint Investigation'),
        ('supplier_audit', 'Supplier Audit'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='quality_inspections')
    inspection_number = models.CharField(max_length=100, unique=True, blank=True)
    grn = models.ForeignKey(GoodsReceiptNote, on_delete=models.CASCADE, related_name='quality_inspections')
    inspection_type = models.CharField(max_length=50, choices=INSPECTION_TYPE_CHOICES, default='receiving')
    
    # Assignment
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_quality_inspections')
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_quality_inspections_by')
    assigned_at = models.DateTimeField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    
    # Status and results
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ], default='medium')
    
    # Inspection details
    inspection_criteria = models.TextField(blank=True, help_text="Specific criteria to check")
    sampling_method = models.CharField(max_length=100, blank=True, help_text="How samples were selected")
    sample_size = models.IntegerField(default=0, help_text="Number of items inspected")
    
    # Results
    overall_result = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('conditional', 'Conditional Pass'),
    ], default='pending')
    
    pass_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Percentage of items that passed")
    
    # Documentation
    inspection_report = models.FileField(upload_to='purchase/quality/reports/', null=True, blank=True)
    photos = models.FileField(upload_to='purchase/quality/photos/', null=True, blank=True)
    test_certificates = models.FileField(upload_to='purchase/quality/certificates/', null=True, blank=True)
    
    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # General notes
    notes = models.TextField(blank=True)
    recommendations = models.TextField(blank=True, help_text="Recommendations for future")
    
    def save(self, *args, **kwargs):
        # Auto-generate inspection number if not provided
        if not self.inspection_number:
            current_year = timezone.now().year
            last_inspection = QualityInspection.objects.filter(
                company=self.company,
                inspection_number__startswith=f'QI-{current_year}'
            ).order_by('-id').first()
            
            if last_inspection and last_inspection.inspection_number:
                try:
                    last_number = int(last_inspection.inspection_number.split('-')[-1])
                    new_number = last_number + 1
                except (ValueError, IndexError):
                    new_number = 1
            else:
                new_number = 1
            
            self.inspection_number = f'QI-{current_year}-{new_number:04d}'
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"QI-{self.inspection_number} - {self.grn.grn_number}"
    
    class Meta:
        ordering = ['-created_at']

# Quality Inspection Results per Item
class QualityInspectionResult(models.Model):
    """Detailed inspection results for each item in a quality inspection"""
    inspection = models.ForeignKey(QualityInspection, on_delete=models.CASCADE, related_name='results')
    grn_item = models.ForeignKey(GRNItem, on_delete=models.CASCADE, related_name='inspection_results')
    tracking_item = models.ForeignKey(GRNItemTracking, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Inspection details
    inspected_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    passed_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    failed_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Result
    result = models.CharField(max_length=20, choices=[
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('conditional', 'Conditional Pass'),
        ('pending', 'Pending'),
    ], default='pending')
    
    # Defects and issues
    defects_found = models.JSONField(default=list, blank=True, help_text="List of defects found")
    severity_level = models.CharField(max_length=20, choices=[
        ('minor', 'Minor'),
        ('major', 'Major'),
        ('critical', 'Critical'),
    ], blank=True)
    
    # Actions taken
    action_taken = models.CharField(max_length=50, choices=[
        ('accept', 'Accept'),
        ('reject', 'Reject'),
        ('return', 'Return to Supplier'),
        ('rework', 'Rework Required'),
        ('quarantine', 'Quarantine'),
    ], blank=True)
    
    # Documentation
    notes = models.TextField(blank=True)
    photos = models.FileField(upload_to='purchase/quality/item_photos/', null=True, blank=True)
    
    # Timestamps
    inspected_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.grn_item.product.name} - {self.result}"

# Duplicate model removed - using the one at line 1441

# Purchase Invoice/Bill (Enhanced)
class Bill(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('partially_paid', 'Partially Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    
    MATCHING_TYPE_CHOICES = [
        ('three_way', 'Three-Way Match (PO + GRN + Invoice)'),
        ('two_way_po', 'Two-Way Match (PO + Invoice)'),
        ('two_way_grn', 'Two-Way Match (GRN + Invoice)'),
        ('manual', 'Manual Entry (No Match)'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='bills')
    bill_number = models.CharField(max_length=100, unique=True, null=True, blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='bills')
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name='bills')
    grn = models.ForeignKey(GoodsReceiptNote, on_delete=models.SET_NULL, null=True, blank=True, related_name='bills')
    supplier_invoice_number = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_bills')
    bill_date = models.DateField()
    due_date = models.DateField(default=timezone.now)
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    outstanding_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='draft')
    
    # Enhanced matching system
    matching_type = models.CharField(max_length=20, choices=MATCHING_TYPE_CHOICES, default='manual')
    three_way_match_status = models.BooleanField(default=False)  # PO = GRN = Invoice matching
    po_match_status = models.BooleanField(default=False)  # PO matches invoice
    grn_match_status = models.BooleanField(default=False)  # GRN matches invoice
    has_additional_items = models.BooleanField(default=False)  # Items not in PO/GRN
    has_quantity_variances = models.BooleanField(default=False)  # Quantity differences
    
    notes = models.TextField(blank=True)
    
    # Document uploads
    supplier_invoice = models.FileField(upload_to='purchase/bills/invoices/', null=True, blank=True, help_text="Supplier invoice document")
    tax_invoice = models.FileField(upload_to='purchase/bills/tax/', null=True, blank=True, help_text="Tax invoice document")
    supporting_documents = models.FileField(upload_to='purchase/bills/supporting/', null=True, blank=True, help_text="Supporting documents (receipts, etc.)")
    approval_documents = models.FileField(upload_to='purchase/bills/approvals/', null=True, blank=True, help_text="Internal approval documents")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Auto-generate bill number if not provided
        if not self.bill_number:
            current_year = timezone.now().year
            last_bill = Bill.objects.filter(
                company=self.company,
                bill_number__startswith=f'BILL-{current_year}'
            ).order_by('-id').first()
            
            if last_bill and last_bill.bill_number:
                try:
                    last_number = int(last_bill.bill_number.split('-')[-1])
                    new_number = last_number + 1
                except (ValueError, IndexError):
                    new_number = 1
            else:
                new_number = 1
            
            self.bill_number = f'BILL-{current_year}-{new_number:04d}'
        
        self.outstanding_amount = self.total_amount - self.paid_amount
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Bill-{self.bill_number} - {self.supplier.name}"
    
    def determine_matching_type(self):
        """Determine the matching type based on linked documents"""
        if self.purchase_order and self.grn:
            return 'three_way'
        elif self.purchase_order:
            return 'two_way_po'
        elif self.grn:
            return 'two_way_grn'
        else:
            return 'manual'
    
    def perform_matching_validation(self):
        """Perform matching validation based on matching type"""
        self.matching_type = self.determine_matching_type()
        
        if self.matching_type == 'three_way':
            self.validate_three_way_match()
        elif self.matching_type == 'two_way_po':
            self.validate_po_match()
        elif self.matching_type == 'two_way_grn':
            self.validate_grn_match()
        
        self.save()
    
    def validate_three_way_match(self):
        """Validate three-way match between PO, GRN, and Invoice"""
        if not (self.purchase_order and self.grn):
            self.three_way_match_status = False
            return False
        
        # Check if all quantities and items match
        po_items = {item.product_id: item.quantity for item in self.purchase_order.items.all()}
        grn_items = {item.product_id: item.received_qty for item in self.grn.items.all()}
        bill_items = {item.product_id: item.quantity for item in self.items.all()}
        
        # Check if all items are present in all three documents
        po_products = set(po_items.keys())
        grn_products = set(grn_items.keys())
        bill_products = set(bill_items.keys())
        
        self.three_way_match_status = (po_products == grn_products == bill_products)
        self.po_match_status = (po_products == bill_products)
        self.grn_match_status = (grn_products == bill_products)
        
        # Check for additional items not in PO/GRN
        self.has_additional_items = bool(bill_products - (po_products | grn_products))
        
        # Check for quantity variances
        self.has_quantity_variances = False
        for product_id in bill_products:
            if product_id in po_items and product_id in grn_items:
                if not (bill_items[product_id] == grn_items[product_id]):
                    self.has_quantity_variances = True
                    break
        
        return self.three_way_match_status
    
    def validate_po_match(self):
        """Validate two-way match between PO and Invoice"""
        if not self.purchase_order:
            self.po_match_status = False
            return False
        
        po_items = {item.product_id: item.quantity for item in self.purchase_order.items.all()}
        bill_items = {item.product_id: item.quantity for item in self.items.all()}
        
        po_products = set(po_items.keys())
        bill_products = set(bill_items.keys())
        
        self.po_match_status = po_products.issubset(bill_products)
        self.has_additional_items = bool(bill_products - po_products)
        
        return self.po_match_status
    
    def validate_grn_match(self):
        """Validate two-way match between GRN and Invoice"""
        if not self.grn:
            self.grn_match_status = False
            return False
        
        grn_items = {item.product_id: item.received_qty for item in self.grn.items.all()}
        bill_items = {item.product_id: item.quantity for item in self.items.all()}
        
        grn_products = set(grn_items.keys())
        bill_products = set(bill_items.keys())
        
        self.grn_match_status = grn_products.issubset(bill_products)
        self.has_additional_items = bool(bill_products - grn_products)
        
        return self.grn_match_status
    
    def unlock_grn_items(self):
        """Unlock GRN items when bill is created/approved"""
        if self.grn and self.status in ['approved', 'paid']:
            # Remove locks from GRN items
            locks = GRNInventoryLock.objects.filter(
                grn=self.grn, 
                lock_reason='pending_invoice',
                is_active=True
            )
            
            for lock in locks:
                # Release the lock and update inventory
                lock.release_lock(
                    user=self.created_by,
                    notes=f"Released due to bill approval: {self.bill_number}",
                    bill=self
                )
                
                # Update inventory status for the related stock item
                if lock.grn_item:
                    self._update_inventory_for_unlock(lock.grn_item)
    
    def _update_inventory_for_unlock(self, grn_item):
        """Update inventory status when GRN item is unlocked"""
        try:
            from inventory.models import StockItem, StockMovement
            
            # Find the corresponding stock item
            warehouse = grn_item.warehouse or self.grn.warehouse
            stock_item = StockItem.objects.filter(
                company=self.company,
                product=grn_item.product,
                warehouse=warehouse
            ).first()
            
            if stock_item:
                # Find the corresponding bill item for pricing
                bill_item = self.items.filter(product=grn_item.product).first()
                unit_cost = bill_item.unit_price if bill_item else 0
                
                # Update stock status
                stock_item.purchase_status = 'ready_for_use'
                stock_item.stock_status = 'available'
                
                # Update cost information
                if unit_cost > 0:
                    stock_item.update_average_cost(grn_item.received_qty, unit_cost)
                
                stock_item.save()
                
                # Create unlock movement
                StockMovement.objects.create(
                    company=self.company,
                    stock_item=stock_item,
                    movement_type='unlock',
                    quantity=grn_item.received_qty,
                    unit_cost=unit_cost,
                    reference_type='bill',
                    reference_id=self.id,
                    reference_number=self.bill_number,
                    grn_item=grn_item,
                    bill_item=bill_item,
                    notes=f"Inventory unlocked via bill approval: {self.bill_number}",
                    performed_by=self.created_by,
                )
                
        except Exception as e:
            print(f"Error updating inventory for unlock: {e}")

    class Meta:
        ordering = ['-created_at']

# Enhanced Bill Items with Tracking Support
class BillItem(models.Model):
    ITEM_SOURCE_CHOICES = [
        ('po', 'From Purchase Order'),
        ('grn', 'From GRN'),
        ('manual', 'Manual Entry'),
    ]
    
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    line_total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Source references
    po_item = models.ForeignKey(PurchaseOrderItem, on_delete=models.SET_NULL, null=True, blank=True)
    grn_item = models.ForeignKey(GRNItem, on_delete=models.SET_NULL, null=True, blank=True)
    item_source = models.CharField(max_length=10, choices=ITEM_SOURCE_CHOICES, default='manual')
    
    # Tracking information
    tracking_required = models.BooleanField(default=False)
    tracking_type = models.CharField(max_length=20, choices=GRNItem.TRACKING_TYPE_CHOICES, default='none')
    
    # Variance tracking
    po_quantity_variance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    grn_quantity_variance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_additional_item = models.BooleanField(default=False, help_text="Item not in PO/GRN")
    
    # Notes and additional info
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        self.line_total = self.quantity * self.unit_price
        
        # Auto-determine tracking requirements from product
        if self.product:
            self.tracking_required = self.product.tracking_method != 'none'
            self.tracking_type = self.product.tracking_method
        
        # Calculate variances if linked to PO/GRN
        if self.po_item:
            self.po_quantity_variance = self.quantity - self.po_item.quantity
        
        if self.grn_item:
            self.grn_quantity_variance = self.quantity - self.grn_item.received_qty
        
        super().save(*args, **kwargs)
        
        # Unlock inventory when bill item is created/updated
        if self.grn_item and self.bill.status in ['approved', 'paid']:
            self.unlock_grn_inventory()

    def unlock_grn_inventory(self):
        """Unlock GRN inventory and update costs when bill is approved"""
        if self.grn_item:
            return self.grn_item.unlock_inventory_on_bill(self)
        return False

    def __str__(self):
        return f"{self.product.name} x {self.quantity} @ ${self.unit_price}"
    
    def validate_tracking_quantity(self):
        """Validate that tracking items match invoiced quantity"""
        if self.tracking_required and self.tracking_type != 'none':
            tracking_count = self.tracking_items.count()
            
            # For individual tracking, count must match quantity
            if self.product.requires_individual_tracking:
                if tracking_count != int(self.quantity):
                    from django.core.exceptions import ValidationError
                    raise ValidationError(
                        f"For {self.product.name}, you must provide {int(self.quantity)} "
                        f"{self.product.get_tracking_method_display()} numbers, "
                        f"but only {tracking_count} were provided."
                    )
        return True


class BillItemTracking(models.Model):
    """Individual tracking for bill items"""
    
    TRACKING_TYPE_CHOICES = [
        ('none', 'No Tracking'),
        ('batch', 'Batch/Lot Tracking'),
        ('serial', 'Serial Number'),
        ('imei', 'IMEI Number'),
        ('barcode', 'Barcode Tracking'),
        ('expiry', 'Expiry Date Tracking'),
    ]
    
    bill_item = models.ForeignKey(BillItem, on_delete=models.CASCADE, related_name='tracking_items')
    tracking_number = models.CharField(max_length=100, help_text="Serial, IMEI, Barcode, etc.")
    tracking_type = models.CharField(max_length=20, choices=TRACKING_TYPE_CHOICES)
    
    # Link to GRN tracking if available
    grn_tracking = models.ForeignKey(GRNItemTracking, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Asset creation info
    creates_asset = models.BooleanField(default=False, help_text="Whether this item creates a fixed asset")
    asset_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Additional tracking info
    batch_number = models.CharField(max_length=100, blank=True)
    manufacturing_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    warranty_expiry = models.DateField(null=True, blank=True)
    condition = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['bill_item', 'tracking_number']
    
    def save(self, *args, **kwargs):
        # If linked to GRN tracking, inherit some values
        if self.grn_tracking:
            self.tracking_type = self.grn_tracking.tracking_type
            self.batch_number = self.grn_tracking.batch_number
            self.manufacturing_date = self.grn_tracking.manufacturing_date
            self.expiry_date = self.grn_tracking.expiry_date
        
        super().save(*args, **kwargs)
        
        # Create or update corresponding ProductTracking entry
        self.update_product_tracking()
    
    def update_product_tracking(self):
        """Update the corresponding ProductTracking entry with invoice information"""
        if self.grn_tracking and self.grn_tracking.product_tracking:
            # Update existing ProductTracking with invoice info
            product_tracking = self.grn_tracking.product_tracking
            product_tracking.purchase_price = self.bill_item.unit_price
            product_tracking.status = 'available'  # Unlock the item
            product_tracking.save()
        else:
            # Create new ProductTracking if not linked to GRN
            from products.models import ProductTracking
            ProductTracking.objects.create(
                product=self.bill_item.product,
                purchase_price=self.bill_item.unit_price,
                purchase_date=self.bill_item.bill.bill_date,
                supplier=self.bill_item.bill.supplier,
                manufacturing_date=self.manufacturing_date,
                expiry_date=self.expiry_date,
                batch_number=self.batch_number,
                warranty_expiry=self.warranty_expiry,
                status='available',
                notes=self.notes,
                created_by=self.bill_item.bill.created_by
            )

    def __str__(self):
        return f"{self.bill_item.product.name} - {self.tracking_type}: {self.tracking_number}"

# Enhanced Purchase Payment
class PurchasePayment(models.Model):
    """Enhanced Purchase Payment with supplier ledger management"""
    
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('check', 'Check'),
        ('bank_transfer', 'Bank Transfer'),
        ('credit_card', 'Credit Card'),
        ('online', 'Online Payment'),
        ('credit_note', 'Credit Note'),
        ('advance', 'Advance Payment'),
    ]
    
    PAYMENT_TYPE_CHOICES = [
        ('bill_payment', 'Bill Payment'),
        ('advance_payment', 'Advance Payment'),
        ('partial_payment', 'Partial Payment'),
        ('refund', 'Refund'),
        ('credit_note', 'Credit Note Application'),
        ('adjustment', 'Adjustment'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('on_hold', 'On Hold'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='purchase_payments')
    payment_number = models.CharField(max_length=100, unique=True, null=True, blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='payments')
    bill = models.ForeignKey(Bill, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    
    # Payment details
    payment_type = models.CharField(max_length=50, choices=PAYMENT_TYPE_CHOICES, default='bill_payment')
    amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    currency = models.CharField(max_length=3, default='USD')
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=4, default=1.0000)
    base_currency_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    # Payment method and details
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES, default='bank_transfer')
    payment_date = models.DateField()
    expected_date = models.DateField(null=True, blank=True, help_text="Expected payment date")
    actual_date = models.DateField(null=True, blank=True, help_text="Actual payment date")
    
    # Reference details
    reference_number = models.CharField(max_length=255, blank=True, help_text="Bank reference, check number, etc.")
    transaction_id = models.CharField(max_length=255, blank=True, help_text="Bank transaction ID")
    approval_code = models.CharField(max_length=100, blank=True, help_text="Approval code for card payments")
    
    # Bank details
    bank_account = models.CharField(max_length=255, blank=True, help_text="Bank account used for payment")
    beneficiary_bank = models.CharField(max_length=255, blank=True, help_text="Supplier's bank details")
    swift_code = models.CharField(max_length=50, blank=True)
    
    # Status and workflow
    status = models.CharField(max_length=50, choices=PAYMENT_STATUS_CHOICES, default='pending')
    is_advance = models.BooleanField(default=False, help_text="Is this an advance payment?")
    advance_adjusted = models.BooleanField(default=False, help_text="Has advance been adjusted against bills?")
    
    # Users
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_payments')
    paid_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='paid_purchase_payments')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_payments')
    
    # Additional details
    notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True, help_text="Internal notes not visible to supplier")
    
    # Document uploads
    payment_receipt = models.FileField(upload_to='purchase/payments/receipts/', null=True, blank=True, help_text="Payment receipt document")
    bank_statement = models.FileField(upload_to='purchase/payments/statements/', null=True, blank=True, help_text="Bank statement showing payment")
    check_copy = models.FileField(upload_to='purchase/payments/checks/', null=True, blank=True, help_text="Copy of check if payment by check")
    wire_transfer_advice = models.FileField(upload_to='purchase/payments/wire/', null=True, blank=True, help_text="Wire transfer advice document")
    approval_document = models.FileField(upload_to='purchase/payments/approvals/', null=True, blank=True, help_text="Payment approval document")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # Generate payment number if not exists
        if not self.payment_number:
            current_year = timezone.now().year
            last_payment = PurchasePayment.objects.filter(
                company=self.company,
                payment_number__isnull=False
            ).order_by('-id').first()
            
            if last_payment and last_payment.payment_number:
                try:
                    last_number = int(last_payment.payment_number.split('-')[-1])
                    new_number = last_number + 1
                except (ValueError, IndexError):
                    new_number = 1
            else:
                new_number = 1
            
            self.payment_number = f'PAY-{current_year}-{new_number:06d}'
        
        # Calculate base currency amount
        if self.exchange_rate and self.amount:
            self.base_currency_amount = self.amount * self.exchange_rate
        
        super().save(*args, **kwargs)
        
        # Update supplier ledger
        self.update_supplier_ledger()
    
    def update_supplier_ledger(self):
        """Update supplier ledger entry for this payment"""
        from .models import SupplierLedger  # Avoid circular import
        
        # Create or update ledger entry
        ledger_entry, created = SupplierLedger.objects.get_or_create(
            company=self.company,
            supplier=self.supplier,
            reference_type='payment',
            reference_id=self.id,
            defaults={
                'transaction_date': self.payment_date,
                'description': f'Payment {self.payment_number}',
                'credit_amount': self.amount if self.payment_type in ['bill_payment', 'advance_payment'] else 0,
                'debit_amount': self.amount if self.payment_type == 'refund' else 0,
                'payment_method': self.payment_method,
                'reference_number': self.reference_number,
                'created_by': self.created_by
            }
        )
        
        if not created:
            # Update existing entry
            ledger_entry.transaction_date = self.payment_date
            ledger_entry.description = f'Payment {self.payment_number}'
            ledger_entry.credit_amount = self.amount if self.payment_type in ['bill_payment', 'advance_payment'] else 0
            ledger_entry.debit_amount = self.amount if self.payment_type == 'refund' else 0
            ledger_entry.payment_method = self.payment_method
            ledger_entry.reference_number = self.reference_number
            ledger_entry.save()

    def __str__(self):
        return f"Payment-{self.payment_number} - {self.supplier.name} - ${self.amount}"

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['supplier', 'payment_date']),
            models.Index(fields=['status', 'payment_date']),
            models.Index(fields=['payment_type', 'created_at']),
        ]


class SupplierLedger(models.Model):
    """Supplier ledger for tracking all financial transactions"""
    
    REFERENCE_TYPE_CHOICES = [
        ('bill', 'Purchase Bill/Invoice'),
        ('payment', 'Payment Made'),
        ('credit_note', 'Credit Note'),
        ('debit_note', 'Debit Note'),
        ('advance', 'Advance Payment'),
        ('adjustment', 'Manual Adjustment'),
        ('opening_balance', 'Opening Balance'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='supplier_ledgers')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='ledger_entries')
    
    # Transaction details
    transaction_date = models.DateField()
    reference_type = models.CharField(max_length=50, choices=REFERENCE_TYPE_CHOICES)
    reference_id = models.IntegerField(help_text="ID of the referenced document")
    description = models.TextField()
    
    # Financial amounts
    debit_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Amount owed TO supplier")
    credit_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Amount paid BY company")
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Running balance")
    
    # Payment details (if applicable)
    payment_method = models.CharField(max_length=50, blank=True)
    reference_number = models.CharField(max_length=255, blank=True)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Calculate running balance before saving
        if not self.balance and self.id is None:  # New record
            previous_balance = SupplierLedger.objects.filter(
                supplier=self.supplier,
                transaction_date__lte=self.transaction_date
            ).exclude(id=self.id if self.id else None).aggregate(
                total_debit=Sum('debit_amount'),
                total_credit=Sum('credit_amount')
            )
            
            total_debit = previous_balance['total_debit'] or 0
            total_credit = previous_balance['total_credit'] or 0
            previous_balance_amount = total_debit - total_credit
            
            self.balance = previous_balance_amount + self.debit_amount - self.credit_amount
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.supplier.name} - {self.transaction_date} - {self.reference_type}"

    class Meta:
        ordering = ['-transaction_date', '-created_at']
        indexes = [
            models.Index(fields=['supplier', 'transaction_date']),
            models.Index(fields=['reference_type', 'reference_id']),
        ]

# Purchase Return
class PurchaseReturn(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('processed', 'Processed'),
        ('cancelled', 'Cancelled'),
    ]
    
    RETURN_TYPE_CHOICES = [
        ('defective', 'Defective Items'),
        ('excess', 'Excess Quantity'),
        ('wrong_item', 'Wrong Item'),
        ('damaged', 'Damaged in Transit'),
        ('quality_issue', 'Quality Issue'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='purchase_returns')
    return_number = models.CharField(max_length=100, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='returns')
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='returns')
    grn = models.ForeignKey(GoodsReceiptNote, on_delete=models.SET_NULL, null=True, blank=True)
    return_date = models.DateField(auto_now_add=True)
    return_type = models.CharField(max_length=50, choices=RETURN_TYPE_CHOICES)
    reason = models.TextField()
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='draft')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_purchase_returns')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_purchase_returns')
    
    # Document uploads
    return_authorization = models.FileField(upload_to='purchase/returns/authorization/', null=True, blank=True, help_text="Return authorization document")
    quality_report = models.FileField(upload_to='purchase/returns/quality/', null=True, blank=True, help_text="Quality inspection report for return")
    photos_returned_items = models.FileField(upload_to='purchase/returns/photos/', null=True, blank=True, help_text="Photos of returned items")
    supplier_acknowledgment = models.FileField(upload_to='purchase/returns/acknowledgment/', null=True, blank=True, help_text="Supplier acknowledgment of return")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Return-{self.return_number} to {self.supplier.name}"

    class Meta:
        ordering = ['-created_at']

# Purchase Return Items - Enhanced
class PurchaseReturnItem(models.Model):
    """Items being returned to supplier with detailed tracking"""
    purchase_return = models.ForeignKey(PurchaseReturn, on_delete=models.CASCADE, related_name='items')
    grn_item = models.ForeignKey(GRNItem, on_delete=models.CASCADE, related_name='return_items')
    tracking_item = models.ForeignKey(GRNItemTracking, on_delete=models.SET_NULL, null=True, blank=True, related_name='return_items')
    quality_result = models.ForeignKey(QualityInspectionResult, on_delete=models.SET_NULL, null=True, blank=True, related_name='return_items')
    
    # Return quantities
    return_quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    line_total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Return details
    return_reason = models.CharField(max_length=50, choices=PurchaseReturn.RETURN_TYPE_CHOICES)
    condition_at_return = models.CharField(max_length=255, blank=True, help_text="Physical condition when returned")
    defects_description = models.TextField(blank=True, help_text="Detailed description of defects/issues")
    
    # Replacement/refund preferences
    replacement_requested = models.BooleanField(default=False)
    refund_requested = models.BooleanField(default=False)
    credit_note_requested = models.BooleanField(default=False)
    
    # Status tracking
    packed_for_return = models.BooleanField(default=False)
    shipped_date = models.DateField(null=True, blank=True)
    supplier_acknowledged = models.BooleanField(default=False)
    resolution_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('replaced', 'Replaced'),
        ('refunded', 'Refunded'),
        ('credit_issued', 'Credit Note Issued'),
        ('disputed', 'Disputed'),
        ('resolved', 'Resolved'),
    ], default='pending')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        self.line_total = self.return_quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.grn_item.product.name} x {self.return_quantity} - {self.return_reason}"

# Inventory Lock for GRN Items (until invoice is created)
class GRNInventoryLock(models.Model):
    """Lock mechanism for GRN items until purchase invoice is created"""
    grn = models.ForeignKey(GoodsReceiptNote, on_delete=models.CASCADE, related_name='inventory_locks')
    grn_item = models.ForeignKey(GRNItem, on_delete=models.CASCADE, related_name='inventory_locks')
    tracking_item = models.ForeignKey(GRNItemTracking, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Lock details
    locked_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    lock_reason = models.CharField(max_length=50, choices=[
        ('pending_invoice', 'Pending Purchase Invoice'),
        ('quality_hold', 'Quality Hold'),
        ('damage_investigation', 'Damage Investigation'),
        ('customs_clearance', 'Customs Clearance'),
        ('manual_hold', 'Manual Hold'),
    ], default='pending_invoice')
    
    # Lock status
    is_active = models.BooleanField(default=True)
    is_released = models.BooleanField(default=False)  # Added for better tracking
    locked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    locked_at = models.DateTimeField(auto_now_add=True)
    released_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='released_locks')
    released_at = models.DateTimeField(null=True, blank=True)
    
    # Bill reference (when released due to invoice creation)
    released_for_bill = models.ForeignKey(Bill, on_delete=models.SET_NULL, null=True, blank=True, related_name='released_locks')
    
    # Notes
    lock_notes = models.TextField(blank=True)
    release_notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"Lock: {self.grn_item.product.name} - {self.locked_quantity} - {self.lock_reason}"
    
    def release_lock(self, user, notes="", bill=None):
        """Release the inventory lock"""
        self.is_active = False
        self.is_released = True
        self.released_by = user
        self.released_at = timezone.now()
        self.release_notes = notes
        self.released_for_bill = bill
        self.save()
        
        # Update tracking item if exists
        if self.tracking_item:
            self.tracking_item.is_locked = False
            self.tracking_item.is_available = True
            self.tracking_item.save()

    class Meta:
        ordering = ['-locked_at']

# Approval Workflow
class PurchaseApproval(models.Model):
    DOCUMENT_TYPE_CHOICES = [
        ('requisition', 'Purchase Requisition'),
        ('purchase_order', 'Purchase Order'),
        ('bill', 'Bill'),
        ('payment', 'Payment'),
        ('return', 'Purchase Return'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='purchase_approvals')
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPE_CHOICES)
    document_id = models.IntegerField()  # Generic foreign key to any document
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchase_approval_requests')
    approver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchase_approvals')
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    comments = models.TextField(blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.document_type} #{self.document_id} - {self.status}"

    class Meta:
        ordering = ['-created_at']
