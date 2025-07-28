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
    
    # Basic Information
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='partners')
    name = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255, blank=True, help_text="Name to display in reports")
    partner_type = models.CharField(max_length=50, choices=PARTNER_TYPE_CHOICES, default='individual')
    
    # Contact Information
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    mobile = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
    
    # Address Information
    street = models.CharField(max_length=255, blank=True)
    street2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    zip_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    
    # Business Information
    company_name = models.CharField(max_length=255, blank=True)
    tax_id = models.CharField(max_length=50, blank=True, help_text="VAT/Tax Identification Number")
    registration_number = models.CharField(max_length=50, blank=True)
    
    # Role Flags - A partner can have multiple roles
    is_customer = models.BooleanField(default=False, help_text="Can be sold to")
    is_supplier = models.BooleanField(default=False, help_text="Can purchase from")
    is_employee = models.BooleanField(default=False, help_text="Is an employee")
    is_project_stakeholder = models.BooleanField(default=False, help_text="Can be assigned to projects")
    is_lead = models.BooleanField(default=False, help_text="Is a potential customer")
    
    # Financial Information
    payment_terms = models.CharField(max_length=100, blank=True)
    credit_limit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Additional Information
    notes = models.TextField(blank=True)
    image = models.ImageField(upload_to='partners/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
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
