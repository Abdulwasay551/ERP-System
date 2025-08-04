from django import forms
from django.forms import ModelForm, DateInput, Textarea, Select, NumberInput
from .models import (Customer, Lead, Opportunity, CommunicationLog, Campaign, 
                    CampaignTarget, SupplierRating, Partner)


class CustomerForm(ModelForm):
    class Meta:
        model = Customer
        fields = '__all__'
        widgets = {
            'created_at': DateInput(attrs={'type': 'date'}),
        }


class PartnerForm(ModelForm):
    class Meta:
        model = Partner
        exclude = ['created_by', 'created_at', 'updated_at']
        widgets = {
            'notes': Textarea(attrs={'rows': 4}),
            'certifications': Textarea(attrs={'rows': 3}),
            'bank_details': Textarea(attrs={'rows': 3}),
            'next_review_date': DateInput(attrs={'type': 'date'}),
            'last_contact_date': DateInput(attrs={'type': 'date'}),
            'credit_limit': NumberInput(attrs={'step': '0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        if company:
            self.fields['company'].initial = company
            self.fields['company'].widget = forms.HiddenInput()


class LeadForm(ModelForm):
    class Meta:
        model = Lead
        exclude = ['created_by', 'created_at', 'updated_at', 'converted_to_customer', 'conversion_date']
        widgets = {
            'requirements': Textarea(attrs={'rows': 4}),
            'product_interest': Textarea(attrs={'rows': 3}),
            'follow_up_notes': Textarea(attrs={'rows': 3}),
            'expected_close_date': DateInput(attrs={'type': 'date'}),
            'last_contact_date': DateInput(attrs={'type': 'date'}),
            'next_follow_up_date': DateInput(attrs={'type': 'date'}),
            'estimated_value': NumberInput(attrs={'step': '0.01'}),
            'lead_score': NumberInput(attrs={'min': 0, 'max': 100}),
        }
    
    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        if company:
            self.fields['company'].initial = company
            self.fields['company'].widget = forms.HiddenInput()
            
            # Filter assigned_to to company users
            self.fields['assigned_to'].queryset = company.users.all()


class OpportunityForm(ModelForm):
    class Meta:
        model = Opportunity
        exclude = ['created_by', 'created_at', 'updated_at', 'stage_history', 'actual_close_date']
        widgets = {
            'description': Textarea(attrs={'rows': 4}),
            'products_services': Textarea(attrs={'rows': 3}),
            'competitors': Textarea(attrs={'rows': 3}),
            'key_decision_makers': Textarea(attrs={'rows': 3}),
            'next_action': Textarea(attrs={'rows': 3}),
            'expected_close_date': DateInput(attrs={'type': 'date'}),
            'next_action_date': DateInput(attrs={'type': 'date'}),
            'estimated_value': NumberInput(attrs={'step': '0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        if company:
            self.fields['company'].initial = company
            self.fields['company'].widget = forms.HiddenInput()
            
            # Filter related fields to company data
            self.fields['customer'].queryset = company.customers.all()
            self.fields['lead'].queryset = company.leads.all()
            self.fields['assigned_to'].queryset = company.users.all()


class CommunicationLogForm(ModelForm):
    class Meta:
        model = CommunicationLog
        exclude = ['created_by', 'timestamp', 'updated_at']
        widgets = {
            'summary': Textarea(attrs={'rows': 3}),
            'detailed_notes': Textarea(attrs={'rows': 4}),
            'outcome': Textarea(attrs={'rows': 3}),
            'action_items': Textarea(attrs={'rows': 3}),
            'follow_up_notes': Textarea(attrs={'rows': 3}),
            'participants': Textarea(attrs={'rows': 2}),
            'scheduled_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'actual_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'follow_up_date': DateInput(attrs={'type': 'date'}),
            'duration_minutes': NumberInput(attrs={'min': 0}),
        }
    
    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        if company:
            self.fields['company'].initial = company
            self.fields['company'].widget = forms.HiddenInput()
            
            # Filter related fields to company data
            self.fields['customer'].queryset = company.customers.all()
            self.fields['lead'].queryset = company.leads.all()
            self.fields['opportunity'].queryset = company.opportunities.all()
            self.fields['partner'].queryset = company.partners.all()
            self.fields['user'].queryset = company.users.all()


class CampaignForm(ModelForm):
    class Meta:
        model = Campaign
        exclude = ['created_by', 'created_at', 'updated_at', 'impressions', 'clicks', 'opens', 
                  'leads_generated', 'conversions', 'revenue_generated', 'cost_per_lead']
        widgets = {
            'description': Textarea(attrs={'rows': 4}),
            'target_audience': Textarea(attrs={'rows': 3}),
            'target_segments': Textarea(attrs={'rows': 3}),
            'message_content': Textarea(attrs={'rows': 5}),
            'start_date': DateInput(attrs={'type': 'date'}),
            'end_date': DateInput(attrs={'type': 'date'}),
            'budget': NumberInput(attrs={'step': '0.01'}),
            'actual_cost': NumberInput(attrs={'step': '0.01'}),
            'target_revenue': NumberInput(attrs={'step': '0.01'}),
            'target_conversion_rate': NumberInput(attrs={'step': '0.01', 'min': 0, 'max': 100}),
            'target_leads': NumberInput(attrs={'min': 0}),
        }
    
    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        if company:
            self.fields['company'].initial = company
            self.fields['company'].widget = forms.HiddenInput()
            
            # Filter related fields to company data
            self.fields['campaign_manager'].queryset = company.users.all()
            self.fields['team_members'].queryset = company.users.all()


class SupplierRatingForm(ModelForm):
    class Meta:
        model = SupplierRating
        exclude = ['overall_rating', 'rating_date']
        widgets = {
            'rating_period_start': DateInput(attrs={'type': 'date'}),
            'rating_period_end': DateInput(attrs={'type': 'date'}),
            'comments': Textarea(attrs={'rows': 4}),
            'recommendations': Textarea(attrs={'rows': 3}),
            'quality_rating': NumberInput(attrs={'step': '0.1', 'min': 0, 'max': 10}),
            'delivery_rating': NumberInput(attrs={'step': '0.1', 'min': 0, 'max': 10}),
            'price_rating': NumberInput(attrs={'step': '0.1', 'min': 0, 'max': 10}),
            'service_rating': NumberInput(attrs={'step': '0.1', 'min': 0, 'max': 10}),
            'communication_rating': NumberInput(attrs={'step': '0.1', 'min': 0, 'max': 10}),
        }
    
    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        if company:
            self.fields['company'].initial = company
            self.fields['company'].widget = forms.HiddenInput()
            
            # Filter suppliers to company suppliers
            self.fields['supplier'].queryset = company.suppliers.all()
            self.fields['rated_by'].queryset = company.users.all()


# Quick Forms for AJAX operations
class QuickLeadForm(forms.Form):
    name = forms.CharField(max_length=255)
    company_name = forms.CharField(max_length=255, required=False)
    email = forms.EmailField(required=False)
    phone = forms.CharField(max_length=50, required=False)
    source = forms.ChoiceField(choices=Lead.LEAD_SOURCE_CHOICES, required=False)
    estimated_value = forms.DecimalField(max_digits=15, decimal_places=2, required=False)
    requirements = forms.CharField(widget=Textarea(attrs={'rows': 3}), required=False)


class QuickOpportunityForm(forms.Form):
    name = forms.CharField(max_length=255)
    customer = forms.ModelChoiceField(queryset=Customer.objects.none())
    estimated_value = forms.DecimalField(max_digits=15, decimal_places=2)
    expected_close_date = forms.DateField(widget=DateInput(attrs={'type': 'date'}))
    stage = forms.ChoiceField(choices=Opportunity.OPPORTUNITY_STAGE_CHOICES)
    probability = forms.ChoiceField(choices=Opportunity.PROBABILITY_CHOICES)
    
    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        if company:
            self.fields['customer'].queryset = company.customers.all()


class QuickCommunicationForm(forms.Form):
    type = forms.ChoiceField(choices=CommunicationLog.COMMUNICATION_TYPE_CHOICES)
    subject = forms.CharField(max_length=255)
    summary = forms.CharField(widget=Textarea(attrs={'rows': 3}))
    customer = forms.ModelChoiceField(queryset=Customer.objects.none(), required=False)
    lead = forms.ModelChoiceField(queryset=Lead.objects.none(), required=False)
    follow_up_required = forms.BooleanField(required=False)
    follow_up_date = forms.DateField(widget=DateInput(attrs={'type': 'date'}), required=False)
    
    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        if company:
            self.fields['customer'].queryset = company.customers.all()
            self.fields['lead'].queryset = company.leads.all() 