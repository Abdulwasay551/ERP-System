from django.db import models
from user_auth.models import Company, User

# Create your models here.

class Partner(models.Model):
    """Centralized Partner model used across all ERP modules"""
    
    PARTNER_TYPE_CHOICES = [
        ('individual', 'Individual'),
        ('company', 'Company'),
        ('government', 'Government'),
        ('non_profit', 'Non-Profit'),
    ]
    
    PAYMENT_TERMS_CHOICES = [
        ('net_15', 'Net 15'),
        ('net_30', 'Net 30'),
        ('net_45', 'Net 45'),
        ('net_60', 'Net 60'),
        ('net_90', 'Net 90'),
        ('cash_on_delivery', 'Cash on Delivery'),
        ('advance_payment', 'Advance Payment'),
        ('30_60_90', '30% Advance, 70% on Delivery'),
        ('2_10_net_30', '2/10 Net 30'),
        ('custom', 'Custom Terms'),
    ]
    
    CURRENCY_CHOICES = [
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
        ('GBP', 'British Pound'),
        ('JPY', 'Japanese Yen'),
        ('CAD', 'Canadian Dollar'),
        ('AUD', 'Australian Dollar'),
        ('INR', 'Indian Rupee'),
        ('CNY', 'Chinese Yuan'),
    ]
    
    # Basic Information
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='partners')
    name = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255, blank=True, help_text="Name to display in reports")
    partner_type = models.CharField(max_length=50, choices=PARTNER_TYPE_CHOICES, default='company')
    
    # Contact Information
    contact_person = models.CharField(max_length=255, blank=True, help_text="Primary contact person")
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    mobile = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
    
    # Address Information
    street = models.CharField(max_length=255, blank=True, verbose_name="Address Line 1")
    street2 = models.CharField(max_length=255, blank=True, verbose_name="Address Line 2")
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    zip_code = models.CharField(max_length=20, blank=True, verbose_name="Postal Code")
    country = models.CharField(max_length=100, blank=True)
    
    # Business Information
    company_name = models.CharField(max_length=255, blank=True, help_text="Company name if different from display name")
    tax_id = models.CharField(max_length=50, blank=True, help_text="VAT/Tax Identification Number")
    vat_number = models.CharField(max_length=100, blank=True, help_text="VAT Registration Number")
    registration_number = models.CharField(max_length=50, blank=True, help_text="Business Registration Number")
    
    # Financial Information
    payment_terms = models.CharField(max_length=50, choices=PAYMENT_TERMS_CHOICES, blank=True)
    preferred_currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    credit_limit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    credit_period_days = models.IntegerField(default=30, help_text="Credit period in days")
    
    # Banking Information
    bank_details = models.TextField(blank=True, help_text="Bank account details for payments")
    
    # Business Details
    established_year = models.IntegerField(null=True, blank=True)
    annual_revenue = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    employee_count = models.IntegerField(null=True, blank=True)
    certifications = models.TextField(blank=True, help_text="ISO, quality certifications, etc.")
    
    # Role Flags - A partner can have multiple roles
    is_customer = models.BooleanField(default=False, help_text="Can be sold to")
    is_supplier = models.BooleanField(default=False, help_text="Can purchase from")
    is_employee = models.BooleanField(default=False, help_text="Is an employee")
    is_project_stakeholder = models.BooleanField(default=False, help_text="Can be assigned to projects")
    is_lead = models.BooleanField(default=False, help_text="Is a potential customer")
    
    # Relationship Management
    relationship_manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_partners')
    last_contact_date = models.DateField(null=True, blank=True)
    next_review_date = models.DateField(null=True, blank=True)
    
    # Additional Information
    notes = models.TextField(blank=True)
    image = models.ImageField(upload_to='partners/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    # Document uploads
    registration_certificate = models.FileField(upload_to='partners/registration/', null=True, blank=True, help_text="Business registration certificate")
    tax_certificate = models.FileField(upload_to='partners/tax/', null=True, blank=True, help_text="Tax registration certificate")
    quality_certificates = models.FileField(upload_to='partners/quality/', null=True, blank=True, help_text="Quality certifications (ISO, etc.)")
    bank_documents = models.FileField(upload_to='partners/bank/', null=True, blank=True, help_text="Bank account verification documents")
    agreement_contract = models.FileField(upload_to='partners/contracts/', null=True, blank=True, help_text="Master agreement or contract")
    insurance_certificate = models.FileField(upload_to='partners/insurance/', null=True, blank=True, help_text="Insurance certificate")
    compliance_documents = models.FileField(upload_to='partners/compliance/', null=True, blank=True, help_text="Compliance and regulatory documents")
    
    # Audit fields
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_partners')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.display_name or self.name

    def get_full_address(self):
        """Return formatted address"""
        address_parts = [self.street, self.street2, self.city, self.state, self.zip_code, self.country]
        return ', '.join([part for part in address_parts if part])

    class Meta:
        ordering = ['name']


class Customer(models.Model):
    """Extended Customer model that links to Partner"""
    partner = models.OneToOneField(Partner, on_delete=models.CASCADE, related_name='customer_profile',null=True, blank=True)
    customer_code = models.CharField(max_length=50, unique=True, blank=True)
    customer_group = models.CharField(max_length=100, blank=True)
    loyalty_points = models.IntegerField(default=0)
    preferred_payment_method = models.CharField(max_length=100, blank=True)
    account = models.ForeignKey('accounting.Account', on_delete=models.SET_NULL, null=True, blank=True, related_name='crm_customers')
    
    # Legacy fields for backward compatibility
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='customers')
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_customers')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.partner.name if self.partner else self.name

    def save(self, *args, **kwargs):
        # Ensure partner is marked as customer
        if self.partner:
            self.partner.is_customer = True
            self.partner.save()
        super().save(*args, **kwargs)

class Lead(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='leads')
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    source = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=50, default='New')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_leads')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Opportunity(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='opportunities')
    name = models.CharField(max_length=255)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='opportunities')
    value = models.DecimalField(max_digits=12, decimal_places=2)
    stage = models.CharField(max_length=100, default='Qualification')
    close_date = models.DateField(null=True, blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_opportunities')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    account = models.ForeignKey('accounting.Account', on_delete=models.SET_NULL, null=True, blank=True, related_name='crm_opportunities')

    def __str__(self):
        return self.name

class CommunicationLog(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='communications')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='communications')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='communications')
    type = models.CharField(max_length=50, choices=[('call', 'Call'), ('email', 'Email'), ('meeting', 'Meeting')], default='call')
    subject = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type.title()} with {self.customer.name} on {self.timestamp.strftime('%Y-%m-%d')}"
