from django.db import models
from django.utils import timezone
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
    """Enhanced Lead model with proper lifecycle management"""
    
    LEAD_SOURCE_CHOICES = [
        ('website', 'Website'),
        ('referral', 'Referral'),
        ('social_media', 'Social Media'),
        ('email_campaign', 'Email Campaign'),
        ('trade_show', 'Trade Show'),
        ('cold_call', 'Cold Call'),
        ('advertisement', 'Advertisement'),
        ('partner', 'Partner'),
        ('other', 'Other'),
    ]
    
    LEAD_STATUS_CHOICES = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('qualified', 'Qualified'),
        ('converted', 'Converted'),
        ('lost', 'Lost'),
        ('on_hold', 'On Hold'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='leads')
    name = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255, blank=True, help_text="Lead's company name")
    contact_person = models.CharField(max_length=255, blank=True, help_text="Primary contact person")
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    mobile = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
    
    # Address Information
    street = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    
    # Lead Management
    source = models.CharField(max_length=100, choices=LEAD_SOURCE_CHOICES, blank=True)
    status = models.CharField(max_length=50, choices=LEAD_STATUS_CHOICES, default='new')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_leads')
    
    # Lead Details
    estimated_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, help_text="Estimated deal value")
    expected_close_date = models.DateField(null=True, blank=True)
    industry = models.CharField(max_length=100, blank=True)
    product_interest = models.TextField(blank=True, help_text="Products/services of interest")
    requirements = models.TextField(blank=True, help_text="Customer requirements and notes")
    
    # Tags and Classification
    tags = models.CharField(max_length=255, blank=True, help_text="Comma-separated tags")
    lead_score = models.IntegerField(default=0, help_text="AI/Manual lead score (0-100)")
    
    # Follow-up Management
    last_contact_date = models.DateField(null=True, blank=True)
    next_follow_up_date = models.DateField(null=True, blank=True)
    follow_up_notes = models.TextField(blank=True)
    
    # Conversion tracking
    converted_to_customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='converted_from_lead')
    conversion_date = models.DateTimeField(null=True, blank=True)
    
    # Audit fields
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_leads')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.company_name}" if self.company_name else self.name
    
    def convert_to_customer(self, user=None):
        """Convert lead to customer"""
        if not self.converted_to_customer:
            # Create customer from lead
            customer = Customer.objects.create(
                company=self.company,
                name=self.company_name or self.name,
                email=self.email,
                phone=self.phone,
                address=f"{self.street}, {self.city}, {self.state}, {self.country}".strip(', '),
                created_by=user
            )
            
            # Update lead
            self.converted_to_customer = customer
            self.status = 'converted'
            self.conversion_date = timezone.now()
            self.save()
            
            return customer
        return self.converted_to_customer
    
    class Meta:
        ordering = ['-created_at']

class Opportunity(models.Model):
    """Enhanced Opportunity model with proper pipeline management"""
    
    OPPORTUNITY_STAGE_CHOICES = [
        ('qualification', 'Qualification'),
        ('proposal', 'Proposal'),
        ('negotiation', 'Negotiation'),
        ('contract', 'Contract Review'),
        ('won', 'Won'),
        ('lost', 'Lost'),
        ('cancelled', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    PROBABILITY_CHOICES = [
        (10, '10%'),
        (25, '25%'),
        (50, '50%'),
        (75, '75%'),
        (90, '90%'),
        (100, '100%'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='opportunities')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, help_text="Opportunity description and details")
    
    # Relationships
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='opportunities')
    lead = models.ForeignKey('Lead', on_delete=models.SET_NULL, null=True, blank=True, related_name='opportunities', help_text="Original lead if converted")
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_opportunities')
    
    # Opportunity Details
    estimated_value = models.DecimalField(max_digits=15, decimal_places=2, help_text="Estimated opportunity value")
    stage = models.CharField(max_length=100, choices=OPPORTUNITY_STAGE_CHOICES, default='qualification')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    probability = models.IntegerField(choices=PROBABILITY_CHOICES, default=50, help_text="Win probability percentage")
    
    # Timeline
    expected_close_date = models.DateField(help_text="Expected close date")
    actual_close_date = models.DateField(null=True, blank=True)
    
    # Products/Services
    products_services = models.TextField(blank=True, help_text="Products/services involved in this opportunity")
    
    # Competition and Market Info
    competitors = models.TextField(blank=True, help_text="Known competitors for this opportunity")
    key_decision_makers = models.TextField(blank=True, help_text="Key decision makers and influencers")
    
    # Financial Details
    budget_confirmed = models.BooleanField(default=False)
    decision_timeline = models.CharField(max_length=255, blank=True, help_text="Customer's decision timeline")
    
    # Tags and Classification
    tags = models.CharField(max_length=255, blank=True, help_text="Comma-separated tags")
    industry_vertical = models.CharField(max_length=100, blank=True)
    
    # Stage History Tracking
    stage_history = models.JSONField(default=list, blank=True, help_text="History of stage changes")
    
    # Follow-up
    next_action = models.TextField(blank=True, help_text="Next action to be taken")
    next_action_date = models.DateField(null=True, blank=True)
    
    # Integration
    account = models.ForeignKey('accounting.Account', on_delete=models.SET_NULL, null=True, blank=True, related_name='crm_opportunities')
    
    # Audit fields
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_opportunities')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.customer.name}"
    
    def get_weighted_value(self):
        """Calculate weighted value based on probability"""
        return (self.estimated_value * self.probability) / 100
    
    def update_stage(self, new_stage, user=None, notes=""):
        """Update stage and maintain history"""
        old_stage = self.stage
        self.stage = new_stage
        
        # Update stage history
        if not self.stage_history:
            self.stage_history = []
        
        self.stage_history.append({
            'from_stage': old_stage,
            'to_stage': new_stage,
            'changed_by': user.email if user else 'System',
            'changed_at': timezone.now().isoformat(),
            'notes': notes
        })
        
        # Set actual close date if won or lost
        if new_stage in ['won', 'lost', 'cancelled'] and not self.actual_close_date:
            self.actual_close_date = timezone.now().date()
        
        self.save()
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Opportunities'

class CommunicationLog(models.Model):
    """Enhanced Communication and Interaction Logs"""
    
    COMMUNICATION_TYPE_CHOICES = [
        ('call', 'Phone Call'),
        ('email', 'Email'),
        ('meeting', 'Meeting'),
        ('video_call', 'Video Call'),
        ('sms', 'SMS'),
        ('whatsapp', 'WhatsApp'),
        ('chat', 'Live Chat'),
        ('letter', 'Letter'),
        ('fax', 'Fax'),
        ('other', 'Other'),
    ]
    
    DIRECTION_CHOICES = [
        ('inbound', 'Inbound'),
        ('outbound', 'Outbound'),
    ]
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_response', 'No Response'),
        ('follow_up_required', 'Follow-up Required'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='communications')
    
    # Relationships - flexible to link to different entities
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True, related_name='communications')
    lead = models.ForeignKey('Lead', on_delete=models.CASCADE, null=True, blank=True, related_name='communications')
    opportunity = models.ForeignKey('Opportunity', on_delete=models.CASCADE, null=True, blank=True, related_name='communications')
    partner = models.ForeignKey('Partner', on_delete=models.CASCADE, null=True, blank=True, related_name='communications')
    
    # Communication Details
    type = models.CharField(max_length=50, choices=COMMUNICATION_TYPE_CHOICES, default='call')
    direction = models.CharField(max_length=20, choices=DIRECTION_CHOICES, default='outbound')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='completed')
    
    subject = models.CharField(max_length=255, help_text="Communication subject/title")
    summary = models.TextField(blank=True, help_text="Brief summary of communication")
    detailed_notes = models.TextField(blank=True, help_text="Detailed notes and outcomes")
    
    # Participants
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='communications', help_text="Primary user who handled the communication")
    contact_person = models.CharField(max_length=255, blank=True, help_text="Contact person on the other side")
    participants = models.TextField(blank=True, help_text="Other participants (comma-separated)")
    
    # Timing
    scheduled_datetime = models.DateTimeField(null=True, blank=True, help_text="Scheduled date and time")
    actual_datetime = models.DateTimeField(null=True, blank=True, help_text="Actual date and time")
    duration_minutes = models.IntegerField(null=True, blank=True, help_text="Duration in minutes")
    
    # Outcomes and Follow-up
    outcome = models.TextField(blank=True, help_text="Communication outcome and results")
    action_items = models.TextField(blank=True, help_text="Action items and next steps")
    follow_up_required = models.BooleanField(default=False)
    follow_up_date = models.DateField(null=True, blank=True)
    follow_up_notes = models.TextField(blank=True)
    
    # Attachments and References
    attachments = models.FileField(upload_to='communications/', null=True, blank=True, help_text="Related documents or recordings")
    reference_number = models.CharField(max_length=100, blank=True, help_text="Reference or ticket number")
    
    # Integration with other modules
    related_quotation = models.ForeignKey('sales.Quotation', on_delete=models.SET_NULL, null=True, blank=True, related_name='communications')
    related_order = models.ForeignKey('sales.SalesOrder', on_delete=models.SET_NULL, null=True, blank=True, related_name='communications')
    related_invoice = models.ForeignKey('sales.Invoice', on_delete=models.SET_NULL, null=True, blank=True, related_name='communications')
    
    # Audit fields
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_communications')
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        entity_name = ""
        if self.customer:
            entity_name = self.customer.name
        elif self.lead:
            entity_name = self.lead.name
        elif self.partner:
            entity_name = self.partner.name
        
        return f"{self.get_type_display()} with {entity_name} - {self.subject}"
    
    def get_related_entity(self):
        """Get the primary related entity (customer, lead, or partner)"""
        if self.customer:
            return self.customer
        elif self.lead:
            return self.lead
        elif self.partner:
            return self.partner
        return None
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Communication Log'
        verbose_name_plural = 'Communication Logs'


class Campaign(models.Model):
    """Campaign Management for marketing and outreach"""
    
    CAMPAIGN_TYPE_CHOICES = [
        ('email', 'Email Campaign'),
        ('sms', 'SMS Campaign'),
        ('social_media', 'Social Media'),
        ('trade_show', 'Trade Show'),
        ('webinar', 'Webinar'),
        ('content_marketing', 'Content Marketing'),
        ('advertisement', 'Advertisement'),
        ('cold_calling', 'Cold Calling'),
        ('direct_mail', 'Direct Mail'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='campaigns')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    campaign_type = models.CharField(max_length=50, choices=CAMPAIGN_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Timeline
    start_date = models.DateField()
    end_date = models.DateField()
    created_date = models.DateField(auto_now_add=True)
    
    # Targeting
    target_audience = models.TextField(help_text="Description of target audience")
    target_segments = models.TextField(blank=True, help_text="Specific customer segments targeted")
    
    # Budget and Cost
    budget = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    actual_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cost_per_lead = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Goals and KPIs
    target_leads = models.IntegerField(default=0, help_text="Target number of leads")
    target_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    target_conversion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Target conversion rate as percentage")
    
    # Campaign Content
    subject_line = models.CharField(max_length=255, blank=True)
    message_content = models.TextField(blank=True)
    call_to_action = models.CharField(max_length=255, blank=True)
    landing_page_url = models.URLField(blank=True)
    
    # Results and Analytics
    impressions = models.IntegerField(default=0)
    clicks = models.IntegerField(default=0)
    opens = models.IntegerField(default=0)
    leads_generated = models.IntegerField(default=0)
    conversions = models.IntegerField(default=0)
    revenue_generated = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Management
    campaign_manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_campaigns')
    team_members = models.ManyToManyField(User, blank=True, related_name='campaign_teams')
    
    # Audit fields
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_campaigns')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    def get_click_through_rate(self):
        """Calculate click-through rate"""
        if self.impressions > 0:
            return (self.clicks / self.impressions) * 100
        return 0
    
    def get_conversion_rate(self):
        """Calculate conversion rate"""
        if self.clicks > 0:
            return (self.conversions / self.clicks) * 100
        return 0
    
    def get_roi(self):
        """Calculate Return on Investment"""
        if self.actual_cost > 0:
            return ((self.revenue_generated - self.actual_cost) / self.actual_cost) * 100
        return 0
    
    class Meta:
        ordering = ['-created_at']


class CampaignTarget(models.Model):
    """Track specific targets (leads/customers) for campaigns"""
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='targets')
    lead = models.ForeignKey('Lead', on_delete=models.CASCADE, null=True, blank=True, related_name='campaign_targets')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True, related_name='campaign_targets')
    partner = models.ForeignKey('Partner', on_delete=models.CASCADE, null=True, blank=True, related_name='campaign_targets')
    
    # Engagement tracking
    sent_date = models.DateTimeField(null=True, blank=True)
    opened_date = models.DateTimeField(null=True, blank=True)
    clicked_date = models.DateTimeField(null=True, blank=True)
    responded_date = models.DateTimeField(null=True, blank=True)
    converted_date = models.DateTimeField(null=True, blank=True)
    
    # Response details
    response_type = models.CharField(max_length=50, blank=True)
    response_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        target_name = ""
        if self.lead:
            target_name = self.lead.name
        elif self.customer:
            target_name = self.customer.name
        elif self.partner:
            target_name = self.partner.name
        
        return f"{self.campaign.name} - {target_name}"
    
    class Meta:
        unique_together = ['campaign', 'lead', 'customer', 'partner']


class SupplierRating(models.Model):
    """Supplier performance rating and evaluation"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='supplier_ratings')
    supplier = models.ForeignKey('purchase.Supplier', on_delete=models.CASCADE, related_name='ratings')
    
    # Rating Criteria (0-10 scale)
    quality_rating = models.DecimalField(max_digits=3, decimal_places=1, default=0, help_text="Quality rating (0-10)")
    delivery_rating = models.DecimalField(max_digits=3, decimal_places=1, default=0, help_text="Delivery performance (0-10)")
    price_rating = models.DecimalField(max_digits=3, decimal_places=1, default=0, help_text="Price competitiveness (0-10)")
    service_rating = models.DecimalField(max_digits=3, decimal_places=1, default=0, help_text="Service quality (0-10)")
    communication_rating = models.DecimalField(max_digits=3, decimal_places=1, default=0, help_text="Communication (0-10)")
    
    # Overall rating (calculated)
    overall_rating = models.DecimalField(max_digits=3, decimal_places=1, default=0, help_text="Overall rating (0-10)")
    
    # Rating Details
    rating_period_start = models.DateField()
    rating_period_end = models.DateField()
    comments = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    
    # Evaluator
    rated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='supplier_ratings')
    rating_date = models.DateField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        # Calculate overall rating as average
        ratings = [self.quality_rating, self.delivery_rating, self.price_rating, self.service_rating, self.communication_rating]
        non_zero_ratings = [r for r in ratings if r > 0]
        if non_zero_ratings:
            self.overall_rating = sum(non_zero_ratings) / len(non_zero_ratings)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.supplier} - {self.overall_rating}/10 ({self.rating_date})"
    
    class Meta:
        ordering = ['-rating_date']


class CRMConfiguration(models.Model):
    """CRM Configuration and Settings"""
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name='crm_config')
    
    # Lead Configuration
    lead_stages = models.JSONField(default=list, help_text="Custom lead stages configuration")
    lead_assignment_rules = models.TextField(blank=True, help_text="Lead assignment rules and criteria")
    lead_scoring_rules = models.JSONField(default=dict, help_text="Lead scoring configuration")
    
    # Opportunity Configuration
    opportunity_stages = models.JSONField(default=list, help_text="Custom opportunity pipeline stages")
    default_probability_by_stage = models.JSONField(default=dict, help_text="Default probability for each stage")
    
    # Customer Configuration
    customer_categories = models.JSONField(default=list, help_text="Customer categories (Retailer, Distributor, etc.)")
    payment_terms_options = models.JSONField(default=list, help_text="Available payment terms")
    
    # Supplier Configuration
    supplier_rating_scale = models.JSONField(default=dict, help_text="Supplier rating scale and criteria")
    supplier_categories = models.JSONField(default=list, help_text="Supplier categories")
    
    # Communication Configuration
    email_templates = models.JSONField(default=dict, help_text="Email templates by stakeholder type")
    sms_templates = models.JSONField(default=dict, help_text="SMS templates by stakeholder type")
    communication_preferences = models.JSONField(default=dict, help_text="Default communication preferences")
    
    # Campaign Configuration
    campaign_templates = models.JSONField(default=list, help_text="Campaign templates and workflows")
    automation_workflows = models.JSONField(default=list, help_text="Automation workflow configurations")
    
    # Integration Settings
    email_integration_enabled = models.BooleanField(default=False)
    sms_integration_enabled = models.BooleanField(default=False)
    whatsapp_integration_enabled = models.BooleanField(default=False)
    voip_integration_enabled = models.BooleanField(default=False)
    
    # Security and Access
    data_sharing_settings = models.JSONField(default=dict, help_text="Data sharing and privacy settings")
    role_permissions = models.JSONField(default=dict, help_text="Custom role permissions")
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"CRM Config - {self.company.name}"
    
    class Meta:
        verbose_name = 'CRM Configuration'
        verbose_name_plural = 'CRM Configurations'
