from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from decimal import Decimal
from .models import (
    UnitOfMeasure, Supplier, SupplierContact, SupplierProductCatalog, TaxChargesTemplate, 
    PurchaseRequisition, PurchaseRequisitionItem, RequestForQuotation, RFQItem, 
    SupplierQuotation, SupplierQuotationItem, PurchaseOrder, PurchaseOrderItem, 
    GoodsReceiptNote, GRNItem, GRNItemTracking, QualityInspection, QualityInspectionResult, 
    PurchaseReturn, PurchaseReturnItem, Bill, BillItem, BillItemTracking, 
    PurchasePayment, SupplierLedger, GRNInventoryLock
)
from products.models import Product
from user_auth.models import User
from inventory.models import Warehouse
from crm.models import Partner

# File size validation function
def validate_file_size(value):
    """Validate that file size does not exceed 32MB"""
    filesize = value.size
    if filesize > 32 * 1024 * 1024:  # 32MB limit
        raise ValidationError("The maximum file size that can be uploaded is 32MB")
    return value

# Multi-file field for handling multiple file uploads
class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


# ============= UNIT OF MEASURE FORM =============

class UnitOfMeasureForm(forms.ModelForm):
    class Meta:
        model = UnitOfMeasure
        fields = ['name', 'abbreviation', 'uom_type', 'conversion_factor', 'is_base_unit', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'abbreviation': forms.TextInput(attrs={'class': 'form-control'}),
            'uom_type': forms.Select(attrs={'class': 'form-control'}),
            'conversion_factor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'is_base_unit': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }


# ============= ENHANCED SUPPLIER FORMS =============

class SupplierForm(forms.ModelForm):
    """Enhanced Supplier form that works with Partner model integration"""
    
    # Partner fields - these will be used to create/update the Partner record
    partner_name = forms.CharField(
        max_length=255, 
        label="Company Name",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter supplier company name',
            'required': True
        })
    )
    
    contact_person = forms.CharField(
        max_length=255, 
        required=False, 
        label="Contact Person",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Primary contact person name'
        })
    )
    
    email = forms.EmailField(
        required=False, 
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'supplier@company.com'
        })
    )
    
    phone = forms.CharField(
        max_length=50, 
        required=False, 
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+1-234-567-8900'
        })
    )
    
    mobile = forms.CharField(
        max_length=50, 
        required=False, 
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+1-234-567-8901'
        })
    )
    
    website = forms.URLField(
        required=False, 
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://www.supplier.com'
        })
    )
    
    # Address fields
    street = forms.CharField(
        max_length=255, 
        required=False, 
        label="Address Line 1",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Street address line 1'
        })
    )
    
    street2 = forms.CharField(
        max_length=255, 
        required=False, 
        label="Address Line 2",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Street address line 2 (optional)'
        })
    )
    
    city = forms.CharField(
        max_length=100, 
        required=False, 
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'City'
        })
    )
    
    state = forms.CharField(
        max_length=100, 
        required=False, 
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'State/Province'
        })
    )
    
    zip_code = forms.CharField(
        max_length=20, 
        required=False, 
        label="Postal Code",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Postal/ZIP code'
        })
    )
    
    country = forms.CharField(
        max_length=100, 
        required=False, 
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Country'
        })
    )
    
    # Business Information
    tax_id = forms.CharField(
        max_length=50, 
        required=False, 
        label="Tax ID",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tax ID/VAT number'
        })
    )
    
    vat_number = forms.CharField(
        max_length=100, 
        required=False, 
        label="VAT Number",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'VAT registration number'
        })
    )
    
    registration_number = forms.CharField(
        max_length=50, 
        required=False, 
        label="Registration Number",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Business registration number'
        })
    )
    
    # Financial Information
    payment_terms = forms.ChoiceField(
        choices=[('', 'Select Payment Terms')] + Partner.PAYMENT_TERMS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    preferred_currency = forms.ChoiceField(
        choices=Partner.CURRENCY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    credit_limit = forms.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'placeholder': '0.00'
        })
    )
    
    credit_period_days = forms.IntegerField(
        required=False, 
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
            'placeholder': '30'
        })
    )
    
    bank_details = forms.CharField(
        required=False, 
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Bank account details for payments'
        })
    )
    
    # Business Details
    established_year = forms.IntegerField(
        required=False, 
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1800',
            'max': '2025',
            'placeholder': 'Year established'
        })
    )
    
    annual_revenue = forms.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'placeholder': 'Annual revenue'
        })
    )
    
    employee_count = forms.IntegerField(
        required=False, 
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'placeholder': 'Number of employees'
        })
    )
    
    certifications = forms.CharField(
        required=False, 
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'ISO certifications, quality standards, etc.'
        })
    )
    
    relationship_manager = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    notes = forms.CharField(
        required=False, 
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'General notes about the supplier'
        })
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Set queryset for relationship manager to users in the same company
            self.fields['relationship_manager'].queryset = User.objects.filter(
                company=user.company,
                is_active=True
            ).order_by('first_name', 'last_name')
            
        # If editing existing supplier, populate partner fields
        if self.instance and self.instance.pk and hasattr(self.instance, 'partner'):
            partner = self.instance.partner
            self.fields['partner_name'].initial = partner.name
            self.fields['contact_person'].initial = partner.contact_person
            self.fields['email'].initial = partner.email
            self.fields['phone'].initial = partner.phone
            self.fields['mobile'].initial = partner.mobile
            self.fields['website'].initial = partner.website
            self.fields['street'].initial = partner.street
            self.fields['street2'].initial = partner.street2
            self.fields['city'].initial = partner.city
            self.fields['state'].initial = partner.state
            self.fields['zip_code'].initial = partner.zip_code
            self.fields['country'].initial = partner.country
            self.fields['tax_id'].initial = partner.tax_id
            self.fields['vat_number'].initial = partner.vat_number
            self.fields['registration_number'].initial = partner.registration_number
            self.fields['payment_terms'].initial = partner.payment_terms
            self.fields['preferred_currency'].initial = partner.preferred_currency
            self.fields['credit_limit'].initial = partner.credit_limit
            self.fields['credit_period_days'].initial = partner.credit_period_days
            self.fields['bank_details'].initial = partner.bank_details
            self.fields['established_year'].initial = partner.established_year
            self.fields['annual_revenue'].initial = partner.annual_revenue
            self.fields['employee_count'].initial = partner.employee_count
            self.fields['certifications'].initial = partner.certifications
            self.fields['relationship_manager'].initial = partner.relationship_manager
            self.fields['notes'].initial = partner.notes

    class Meta:
        model = Supplier
        fields = [
            'supplier_type', 'status', 'delivery_lead_time', 'minimum_order_value', 
            'preferred_shipping_method', 'quality_rating', 'delivery_rating', 
            'price_rating', 'service_rating'
        ]
        
        widgets = {
            'supplier_type': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'delivery_lead_time': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': 'Days'
            }),
            'minimum_order_value': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'preferred_shipping_method': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Preferred shipping method'
            }),
            'quality_rating': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0',
                'max': '5',
                'placeholder': '5.0'
            }),
            'delivery_rating': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0',
                'max': '5',
                'placeholder': '5.0'
            }),
            'price_rating': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0',
                'max': '5',
                'placeholder': '5.0'
            }),
            'service_rating': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0',
                'max': '5',
                'placeholder': '5.0'
            }),
        }

    def save(self, commit=True):
        # Create or update the Partner record first
        from crm.models import Partner
        
        supplier = super().save(commit=False)
        
        if commit:
            # Create or get partner
            if supplier.pk and hasattr(supplier, 'partner'):
                # Editing existing supplier
                partner = supplier.partner
            else:
                # Creating new supplier
                partner = Partner(
                    company=supplier.company,
                    partner_type='company',
                    is_supplier=True
                )
            
            # Update partner fields from form
            partner.name = self.cleaned_data['partner_name']
            partner.contact_person = self.cleaned_data.get('contact_person', '')
            partner.email = self.cleaned_data.get('email', '')
            partner.phone = self.cleaned_data.get('phone', '')
            partner.mobile = self.cleaned_data.get('mobile', '')
            partner.website = self.cleaned_data.get('website', '')
            partner.street = self.cleaned_data.get('street', '')
            partner.street2 = self.cleaned_data.get('street2', '')
            partner.city = self.cleaned_data.get('city', '')
            partner.state = self.cleaned_data.get('state', '')
            partner.zip_code = self.cleaned_data.get('zip_code', '')
            partner.country = self.cleaned_data.get('country', '')
            partner.tax_id = self.cleaned_data.get('tax_id', '')
            partner.vat_number = self.cleaned_data.get('vat_number', '')
            partner.registration_number = self.cleaned_data.get('registration_number', '')
            partner.payment_terms = self.cleaned_data.get('payment_terms', '')
            partner.preferred_currency = self.cleaned_data.get('preferred_currency', 'USD')
            partner.credit_limit = self.cleaned_data.get('credit_limit', 0)
            partner.credit_period_days = self.cleaned_data.get('credit_period_days', 30)
            partner.bank_details = self.cleaned_data.get('bank_details', '')
            partner.established_year = self.cleaned_data.get('established_year')
            partner.annual_revenue = self.cleaned_data.get('annual_revenue')
            partner.employee_count = self.cleaned_data.get('employee_count')
            partner.certifications = self.cleaned_data.get('certifications', '')
            partner.relationship_manager = self.cleaned_data.get('relationship_manager')
            partner.notes = self.cleaned_data.get('notes', '')
            
            partner.save()
            
            # Link supplier to partner
            supplier.partner = partner
            supplier.save()
            
        return supplier


class SupplierContactForm(forms.ModelForm):
    """Form for managing supplier contact information"""
    
    class Meta:
        model = SupplierContact
        fields = [
            'name', 'contact_type', 'designation', 'email', 'phone', 'mobile',
            'is_primary', 'is_active', 'notes'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contact person name'
            }),
            'contact_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'designation': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Job title or position'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'contact@supplier.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1-234-567-8900'
            }),
            'mobile': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1-234-567-8901'
            }),
            'is_primary': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes about this contact'
            })
        }

    def __init__(self, *args, **kwargs):
        self.supplier = kwargs.pop('supplier', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        contact = super().save(commit=False)
        if self.supplier:
            contact.supplier = self.supplier
        if commit:
            contact.save()
        return contact


class SupplierProductCatalogForm(forms.ModelForm):
    """Form for managing supplier product catalog"""
    
    class Meta:
        model = SupplierProductCatalog
        fields = [
            'product', 'supplier_product_code', 'supplier_product_name',
            'unit_price', 'currency', 'minimum_order_quantity', 'lead_time_days',
            'tier_1_qty', 'tier_1_price', 'tier_2_qty', 'tier_2_price', 
            'tier_3_qty', 'tier_3_price', 'effective_date', 'expiry_date',
            'description', 'technical_specifications', 'warranty_terms'
        ]
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control'}),
            'supplier_product_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Supplier product code'
            }),
            'supplier_product_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Supplier product name'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'currency': forms.Select(attrs={'class': 'form-control'}),
            'minimum_order_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'lead_time_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'tier_1_qty': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'tier_1_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'tier_2_qty': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'tier_2_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'tier_3_qty': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'tier_3_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'effective_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'technical_specifications': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'warranty_terms': forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
        }

    def __init__(self, *args, **kwargs):
        self.supplier = kwargs.pop('supplier', None)
        super().__init__(*args, **kwargs)
        
        if self.supplier and hasattr(self.supplier, 'company'):
            # Filter products by company
            self.fields['product'].queryset = Product.objects.filter(
                company=self.supplier.company
            )

    def save(self, commit=True):
        catalog = super().save(commit=False)
        if self.supplier:
            catalog.supplier = self.supplier
        if commit:
            catalog.save()
        return catalog
    def clean(self):
        cleaned_data = super().clean()
        
        # Validate pricing tiers
        tier_1_qty = cleaned_data.get('tier_1_qty')
        tier_1_price = cleaned_data.get('tier_1_price')
        tier_2_qty = cleaned_data.get('tier_2_qty')
        tier_2_price = cleaned_data.get('tier_2_price')
        tier_3_qty = cleaned_data.get('tier_3_qty')
        tier_3_price = cleaned_data.get('tier_3_price')
        
        # Ensure tier quantities are in ascending order
        if tier_1_qty and tier_2_qty and tier_1_qty >= tier_2_qty:
            raise ValidationError('Tier 2 quantity must be greater than Tier 1 quantity.')
        
        if tier_2_qty and tier_3_qty and tier_2_qty >= tier_3_qty:
            raise ValidationError('Tier 3 quantity must be greater than Tier 2 quantity.')
        
        # Ensure tier prices are provided if quantities are provided
        if tier_1_qty and not tier_1_price:
            raise ValidationError('Tier 1 price is required when Tier 1 quantity is specified.')
        
        if tier_2_qty and not tier_2_price:
            raise ValidationError('Tier 2 price is required when Tier 2 quantity is specified.')
        
        if tier_3_qty and not tier_3_price:
            raise ValidationError('Tier 3 price is required when Tier 3 quantity is specified.')
        
        return cleaned_data


class PurchaseRequisitionForm(forms.ModelForm):

    def clean_bank_documents(self):
        file = self.cleaned_data.get('bank_documents')
        if file:
            validate_file_size(file)
        return file

    def clean_agreement_contract(self):
        file = self.cleaned_data.get('agreement_contract')
        if file:
            validate_file_size(file)
        return file

class PurchaseRequisitionForm(forms.ModelForm):
    # Additional fields for enhanced requisition management
    priority = forms.ChoiceField(
        choices=[
            ('low', 'Low Priority'),
            ('medium', 'Medium Priority'),
            ('high', 'High Priority'),
            ('urgent', 'Urgent'),
        ],
        initial='medium',
        widget=forms.Select(attrs={
            'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'help_text': 'Set request priority for approval workflow'
        }),
        help_text='Priority level affects approval routing and processing speed'
    )
    
    justification = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'rows': 4,
            'placeholder': 'Provide detailed business justification for this purchase request...',
            'help_text': 'Explain business need, impact if not approved, and why these specific items are required'
        }),
        help_text='Detailed explanation to help approvers understand the business need and make informed decisions',
        required=True
    )
    
    project_code = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'placeholder': 'e.g., PROJ-2025-001, CC-IT-001',
            'help_text': 'Project code or cost center for budget allocation and tracking'
        }),
        help_text='Project code or cost center reference for expense allocation and budget tracking'
    )
    
    estimated_budget = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'step': '0.01',
            'min': '0',
            'placeholder': 'Enter estimated total budget',
            'help_text': 'Estimated total budget for this requisition'
        }),
        help_text='Rough estimate of total cost for budget planning and approval purposes'
    )
    
    urgency_reason = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Explain why this request is urgent (if applicable)',
            'help_text': 'Required if priority is set to High or Urgent'
        }),
        help_text='Explanation of urgency - required when priority is set to High or Urgent'
    )

    class Meta:
        model = PurchaseRequisition
        fields = [
            'department', 'warehouse', 'required_date', 'purpose',
            'requisition_document', 'technical_specifications', 'budget_approval'
        ]
        widgets = {
            'department': forms.Select(choices=[
                ('', 'Select Department'),
                ('IT', 'Information Technology'),
                ('HR', 'Human Resources'),
                ('Finance', 'Finance & Accounting'),
                ('Operations', 'Operations'),
                ('Marketing', 'Marketing'),
                ('Production', 'Production'),
                ('Maintenance', 'Maintenance'),
                ('Security', 'Security'),
                ('R&D', 'Research & Development'),
                ('Quality', 'Quality Assurance'),
                ('Procurement', 'Procurement'),
                ('Administration', 'Administration'),
            ], attrs={
                'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'help_text': 'Select your department for proper approval workflow routing'
            }),
            'warehouse': forms.Select(attrs={
                'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'help_text': 'Warehouse where items should be delivered upon receipt'
            }),
            'required_date': forms.DateInput(attrs={
                'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'type': 'date',
                'help_text': 'Date when you need these items - affects procurement timeline'
            }),
            'purpose': forms.Select(choices=[
                ('', 'Select Purpose'),
                ('new_project', 'New Project Requirements'),
                ('replacement', 'Equipment Replacement'),
                ('maintenance', 'Maintenance & Repair'),
                ('expansion', 'Business Expansion'),
                ('office_supplies', 'Office Supplies'),
                ('software_license', 'Software/License'),
                ('safety_equipment', 'Safety Equipment'),
                ('training', 'Training & Development'),
                ('other', 'Other'),
            ], attrs={
                'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'help_text': 'Primary business reason for this purchase request'
            }),
            'requisition_document': forms.FileInput(attrs={
                'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 file-input',
                'accept': '.pdf,.doc,.docx,.xls,.xlsx,.jpg,.png',
                'help_text': 'Upload quotations, price lists, or supporting documents - Max 32MB'
            }),
            'technical_specifications': forms.FileInput(attrs={
                'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 file-input',
                'accept': '.pdf,.doc,.docx',
                'help_text': 'Upload detailed technical requirements document - Max 32MB'
            }),
            'budget_approval': forms.FileInput(attrs={
                'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 file-input',
                'accept': '.pdf,.doc,.docx,.xls,.xlsx,.jpg,.png',
                'help_text': 'Upload additional supporting documents - Max 32MB'
            })
        }
        help_texts = {
            'department': 'Select your department - this determines the approval workflow and budget allocation',
            'warehouse': 'Destination warehouse for delivery - helps with logistics planning and inventory management',
            'required_date': 'Target date when items are needed - allows procurement team to plan timeline effectively',
            'purpose': 'Primary business reason for this purchase - helps approvers understand context and priority',
            'requisition_document': 'Upload supporting documents like vendor quotations, price lists, or requirement specifications',
            'technical_specifications': 'Upload detailed technical requirements, specifications, or engineering documents',
            'budget_approval': 'Upload additional supporting documents like budget approvals, business cases, or compliance docs'
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        # Populate warehouse choices if company is available
        if self.company:
            self.fields['warehouse'].queryset = Warehouse.objects.filter(
                company=self.company, is_active=True
            )
        
        # Make warehouse field required
        self.fields['warehouse'].required = True

    def clean_urgency_reason(self):
        priority = self.cleaned_data.get('priority')
        urgency_reason = self.cleaned_data.get('urgency_reason')
        
        if priority in ['high', 'urgent'] and not urgency_reason:
            raise forms.ValidationError(
                'Urgency reason is required when priority is set to High or Urgent.'
            )
        
        return urgency_reason

    def clean_justification(self):
        justification = self.cleaned_data.get('justification')
        
        if justification and len(justification.strip()) < 50:
            raise forms.ValidationError(
                'Please provide a more detailed justification (minimum 50 characters).'
            )
        
        return justification

    def clean_required_date(self):
        required_date = self.cleaned_data.get('required_date')
        
        if required_date:
            from django.utils import timezone
            today = timezone.now().date()
            
            if required_date < today:
                raise forms.ValidationError(
                    'Required date cannot be in the past.'
                )
            
            # Warning for very urgent requests (less than 7 days)
            days_diff = (required_date - today).days
            if days_diff < 7:
                # This would be handled in the view to show a warning message
                pass
        
        return required_date

    def clean_estimated_budget(self):
        estimated_budget = self.cleaned_data.get('estimated_budget')
        
        if estimated_budget and estimated_budget < 0:
            raise forms.ValidationError(
                'Estimated budget cannot be negative.'
            )
        
        return estimated_budget

    def clean_requisition_document(self):
        file = self.cleaned_data.get('requisition_document')
        if file:
            validate_file_size(file)
        return file

    def clean_technical_specifications(self):
        file = self.cleaned_data.get('technical_specifications')
        if file:
            validate_file_size(file)
        return file

    def clean_budget_approval(self):
        file = self.cleaned_data.get('budget_approval')
        if file:
            validate_file_size(file)
        return file


# Purchase Requisition Item Form for dynamic item management
class PurchaseRequisitionItemForm(forms.Form):
    item_description = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Describe the item you need',
            'help_text': 'Be specific about brand, model, specifications, quality requirements'
        }),
        help_text='Detailed description including brand, model, specifications, and quality requirements'
    )
    
    quantity = forms.DecimalField(
        widget=forms.NumberInput(attrs={
            'class': 'w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'step': '0.01',
            'min': '0',
            'help_text': 'Quantity needed - be precise for accurate procurement'
        }),
        help_text='Exact quantity required - helps with accurate cost estimation and procurement planning'
    )
    
    unit_of_measure = forms.ModelChoiceField(
        queryset=UnitOfMeasure.objects.none(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'help_text': 'Unit of measurement for this item'
        }),
        help_text='Standard unit of measurement - ensures clarity for suppliers and receiving'
    )
    
    estimated_cost = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'step': '0.01',
            'min': '0',
            'placeholder': 'Estimated price per unit',
            'help_text': 'Estimated cost per unit for budget planning'
        }),
        help_text='Estimated price per unit - helps with budget planning and approval decisions'
    )
    
    preferred_supplier = forms.ModelChoiceField(
        queryset=Supplier.objects.none(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'help_text': 'Preferred supplier for this item (optional)'
        }),
        help_text='Preferred supplier if you have a specific vendor in mind - helps procurement team'
    )
    
    item_notes = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Any specific requirements, preferences, or notes',
            'help_text': 'Additional specifications, quality requirements, or special instructions'
        }),
        help_text='Additional specifications, quality requirements, delivery instructions, or special considerations'
    )

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        if company:
            self.fields['unit_of_measure'].queryset = UnitOfMeasure.objects.filter(
                company=company, is_active=True
            )
            self.fields['preferred_supplier'].queryset = Supplier.objects.filter(
                company=company, is_active=True
            )

class RequestForQuotationForm(forms.ModelForm):
    class Meta:
        model = RequestForQuotation
        fields = [
            'rfq_number', 'company', 'purchase_requisition', 'warehouse', 'suppliers',
            'response_deadline', 'payment_terms', 'delivery_terms', 'description',
            'terms_and_conditions', 'rfq_document', 'technical_specifications', 'drawing_attachments'
        ]
        widgets = {
            'rfq_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter RFQ number (e.g., RFQ-2025-001)',
                'help_text': 'Unique request for quotation number'
            }),
            'suppliers': forms.SelectMultiple(attrs={
                'class': 'form-control',
                'help_text': 'Select suppliers to send this RFQ to'
            }),
            'response_deadline': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'help_text': 'Deadline for suppliers to respond'
            }),
            'payment_terms': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter payment terms (e.g., Net 30 days)',
                'help_text': 'Payment terms for this RFQ'
            }),
            'delivery_terms': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter delivery terms (e.g., FOB Destination)',
                'help_text': 'Delivery and shipping terms'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe what you are looking to purchase',
                'help_text': 'General description of items being quoted'
            }),
            'terms_and_conditions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter terms and conditions for this RFQ',
                'help_text': 'Legal terms and conditions for suppliers'
            }),
            'rfq_document': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx',
                'help_text': 'Upload RFQ document file (Max 32MB)'
            }),
            'technical_specifications': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.xls,.xlsx',
                'help_text': 'Upload technical specifications (Max 32MB)'
            }),
            'drawing_attachments': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.dwg,.jpg,.jpeg,.png,.tiff',
                'help_text': 'Upload technical drawings or blueprints (Max 32MB)'
            })
        }
        help_texts = {
            'rfq_number': 'Unique identifier for this RFQ',
            'company': 'Company issuing the RFQ',
            'purchase_requisition': 'Related purchase requisition if applicable',
            'warehouse': 'Delivery location for quoted items',
            'suppliers': 'Suppliers who will receive this RFQ',
            'response_deadline': 'Last date for suppliers to submit quotes',
            'payment_terms': 'Payment terms for potential purchase',
            'delivery_terms': 'Shipping and delivery requirements',
            'description': 'Overview of what is being requested',
            'terms_and_conditions': 'Legal terms governing this RFQ'
        }

    def clean_rfq_document(self):
        file = self.cleaned_data.get('rfq_document')
        if file:
            validate_file_size(file)
        return file

    def clean_technical_specifications(self):
        file = self.cleaned_data.get('technical_specifications')
        if file:
            validate_file_size(file)
        return file

    def clean_drawing_attachments(self):
        file = self.cleaned_data.get('drawing_attachments')
        if file:
            validate_file_size(file)
        return file

class SupplierQuotationForm(forms.ModelForm):
    class Meta:
        model = SupplierQuotation
        fields = [
            'quotation_number', 'company', 'rfq', 'supplier', 'quotation_date', 'valid_until',
            'payment_terms', 'delivery_terms', 'delivery_time_days', 'discount_type',
            'discount_percentage', 'discount_amount', 'discount_application', 'notes',
            'quotation_document', 'price_list', 'technical_brochure', 'certificate_documents'
        ]
        widgets = {
            'quotation_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter quotation number from supplier',
                'help_text': 'Supplier\'s quotation reference number'
            }),
            'quotation_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'help_text': 'Date when supplier submitted quotation'
            }),
            'valid_until': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'help_text': 'Quotation validity end date'
            }),
            'payment_terms': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter payment terms offered by supplier',
                'help_text': 'Payment terms as quoted by supplier'
            }),
            'delivery_terms': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter delivery terms',
                'help_text': 'Delivery terms and conditions'
            }),
            'delivery_time_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter delivery time in days',
                'help_text': 'Number of days for delivery after order'
            }),
            'discount_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00',
                'help_text': 'Discount percentage offered'
            }),
            'discount_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00',
                'help_text': 'Fixed discount amount offered'
            }),
            'discount_application': forms.Select(attrs={
                'class': 'form-control',
                'help_text': 'Whether to subtract (discount) or add (rebate/fee) to total'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes from supplier',
                'help_text': 'Any additional information from supplier'
            }),
            'quotation_document': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.xls,.xlsx',
                'help_text': 'Upload supplier quotation document (Max 32MB)'
            }),
            'price_list': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.xls,.xlsx',
                'help_text': 'Upload supplier price list (Max 32MB)'
            }),
            'technical_brochure': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png',
                'help_text': 'Upload product technical brochure (Max 32MB)'
            }),
            'certificate_documents': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png',
                'help_text': 'Upload quality certificates, compliance docs (Max 32MB)'
            })
        }

    def clean_quotation_document(self):
        file = self.cleaned_data.get('quotation_document')
        if file:
            validate_file_size(file)
        return file

    def clean_price_list(self):
        file = self.cleaned_data.get('price_list')
        if file:
            validate_file_size(file)
        return file

    def clean_technical_brochure(self):
        file = self.cleaned_data.get('technical_brochure')
        if file:
            validate_file_size(file)
        return file

    def clean_certificate_documents(self):
        file = self.cleaned_data.get('certificate_documents')
        if file:
            validate_file_size(file)
        return file

class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = [
            'po_number', 'supplier', 'purchase_requisition', 'supplier_quotation',
            'warehouse', 'expected_delivery_date', 'delivery_terms', 'payment_terms',
            'purchase_limit', 'discount_type', 'discount_percentage', 'discount_amount',
            'discount_application', 'quantity_discount_min_qty', 'quantity_discount_rate',
            'notes', 'terms_conditions',
            'purchase_order_document', 'supplier_agreement', 'technical_drawings', 'amendment_documents'
        ]
        widgets = {
            'po_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter PO number (e.g., PO-2025-001)',
                'help_text': 'Unique purchase order number (auto-generated if empty)'
            }),
            'supplier': forms.Select(attrs={
                'class': 'form-control',
                'help_text': 'Select supplier for this purchase order'
            }),
            'purchase_requisition': forms.Select(attrs={
                'class': 'form-control',
                'help_text': 'Optional: Link to purchase requisition'
            }),
            'supplier_quotation': forms.Select(attrs={
                'class': 'form-control',
                'help_text': 'Optional: Reference quotation (items can vary from quotation)'
            }),
            'warehouse': forms.Select(attrs={
                'class': 'form-control',
                'help_text': 'Delivery warehouse for this order'
            }),
            'expected_delivery_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'help_text': 'Expected delivery date for this order'
            }),
            'delivery_terms': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter delivery terms (e.g., FOB Destination)',
                'help_text': 'Delivery and shipping terms'
            }),
            'payment_terms': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter payment terms (e.g., Net 30 days)',
                'help_text': 'Payment terms for this order'
            }),
            'purchase_limit': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00',
                'help_text': 'Maximum allowed purchase amount'
            }),
            'discount_type': forms.Select(attrs={
                'class': 'form-control',
                'id': 'discount_type',
                'help_text': 'Type of discount/rebate to apply'
            }),
            'discount_percentage': forms.NumberInput(attrs={
                'class': 'form-control discount-field percentage-field',
                'step': '0.01',
                'placeholder': '0.00',
                'help_text': 'Percentage discount/rebate'
            }),
            'discount_amount': forms.NumberInput(attrs={
                'class': 'form-control discount-field amount-field',
                'step': '0.01',
                'placeholder': '0.00',
                'help_text': 'Fixed discount/rebate amount'
            }),
            'discount_application': forms.Select(attrs={
                'class': 'form-control',
                'help_text': 'Whether to subtract (discount) or add (rebate/fee) to total'
            }),
            'quantity_discount_min_qty': forms.NumberInput(attrs={
                'class': 'form-control discount-field quantity-field',
                'step': '0.01',
                'placeholder': '0.00',
                'help_text': 'Minimum quantity for quantity-based discount'
            }),
            'quantity_discount_rate': forms.NumberInput(attrs={
                'class': 'form-control discount-field quantity-field',
                'step': '0.01',
                'placeholder': '0.00',
                'help_text': 'Discount rate for quantity-based discount'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes for this purchase order',
                'help_text': 'Any special instructions or notes'
            }),
            'terms_conditions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter terms and conditions',
                'help_text': 'Legal terms and conditions for this order'
            }),
            'purchase_order_document': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx',
                'help_text': 'Upload generated PO document (Max 32MB)'
            }),
            'supplier_agreement': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx',
                'help_text': 'Upload supplier agreement/contract (Max 32MB)'
            }),
            'technical_drawings': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.dwg,.jpg,.jpeg,.png,.tiff',
                'help_text': 'Upload technical drawings or specifications (Max 32MB)'
            }),
            'amendment_documents': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx',
                'help_text': 'Upload PO amendments or revisions (Max 32MB)'
            })
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        # Make company field hidden and set from request
        if 'company' in self.fields:
            self.fields['company'].widget = forms.HiddenInput()
        
        # Make quotation optional
        self.fields['supplier_quotation'].required = False
        self.fields['purchase_requisition'].required = False
        
        # Filter choices based on company
        if company:
            self.fields['supplier'].queryset = Supplier.objects.filter(company=company, is_active=True)
            self.fields['supplier_quotation'].queryset = SupplierQuotation.objects.filter(company=company, status='submitted')
            self.fields['purchase_requisition'].queryset = PurchaseRequisition.objects.filter(company=company, status='approved')
            if 'warehouse' in self.fields:
                self.fields['warehouse'].queryset = Warehouse.objects.filter(company=company, is_active=True)

    def clean(self):
        cleaned_data = super().clean()
        discount_type = cleaned_data.get('discount_type')
        
        # Validate discount fields based on type
        if discount_type == 'percentage':
            if not cleaned_data.get('discount_percentage'):
                cleaned_data['discount_percentage'] = 0
        elif discount_type == 'fixed_amount':
            if not cleaned_data.get('discount_amount'):
                cleaned_data['discount_amount'] = 0
        elif discount_type == 'quantity_based':
            min_qty = cleaned_data.get('quantity_discount_min_qty', 0)
            rate = cleaned_data.get('quantity_discount_rate', 0)
            if min_qty <= 0:
                raise forms.ValidationError("Minimum quantity must be greater than 0 for quantity-based discount.")
            if rate <= 0:
                raise forms.ValidationError("Discount rate must be greater than 0 for quantity-based discount.")
        
        return cleaned_data

    def clean_purchase_order_document(self):
        file = self.cleaned_data.get('purchase_order_document')
        if file:
            validate_file_size(file)
        return file

    def clean_supplier_agreement(self):
        file = self.cleaned_data.get('supplier_agreement')
        if file:
            validate_file_size(file)
        return file

    def clean_technical_drawings(self):
        file = self.cleaned_data.get('technical_drawings')
        if file:
            validate_file_size(file)
        return file

    def clean_amendment_documents(self):
        file = self.cleaned_data.get('amendment_documents')
        if file:
            validate_file_size(file)
        return file

class GoodsReceiptNoteForm(forms.ModelForm):
    """Enhanced GRN form with optional PO integration and quality workflow"""
    
    class Meta:
        model = GoodsReceiptNote
        fields = [
            'grn_number', 'company', 'purchase_order', 'supplier', 'received_by', 'inspected_by',
            'vehicle_number', 'gate_entry_number', 'supplier_delivery_note', 'transporter',
            'requires_quality_inspection', 'notes', 'delivery_challan', 'packing_list', 
            'quality_certificates', 'inspection_report', 'photos_received_goods'
        ]
        widgets = {
            'grn_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Auto-generated (e.g., GRN-2025-001)',
                'readonly': 'readonly',
                'help_text': 'Unique goods receipt note number - auto-generated'
            }),
            'purchase_order': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_purchase_order',
                'help_text': 'Optional - Select PO to auto-populate items'
            }),
            'supplier': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_supplier',
                'help_text': 'Required if no PO selected'
            }),
            'received_by': forms.Select(attrs={
                'class': 'form-control',
                'help_text': 'Employee who received the goods'
            }),
            'inspected_by': forms.Select(attrs={
                'class': 'form-control',
                'help_text': 'Employee who inspected the goods'
            }),
            'vehicle_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter delivery vehicle number',
                'help_text': 'Vehicle registration number for delivery'
            }),
            'gate_entry_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter gate entry number',
                'help_text': 'Security gate entry reference number'
            }),
            'supplier_delivery_note': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter supplier delivery note number',
                'help_text': 'Supplier\'s delivery challan or note number'
            }),
            'transporter': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter transporter name',
                'help_text': 'Name of the transportation company'
            }),
            'requires_quality_inspection': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'id_requires_quality_inspection',
                'help_text': 'Check if items need quality inspection'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes about the receipt',
                'help_text': 'Any observations during goods receipt'
            }),
            'delivery_challan': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png',
                'help_text': 'Upload supplier delivery challan (Max 32MB)'
            }),
            'packing_list': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.xls,.xlsx',
                'help_text': 'Upload packing list document (Max 32MB)'
            }),
            'quality_certificates': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png',
                'help_text': 'Upload quality certificates from supplier (Max 32MB)'
            }),
            'inspection_report': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.xls,.xlsx',
                'help_text': 'Upload internal quality inspection report (Max 32MB)'
            }),
            'photos_received_goods': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.jpg,.jpeg,.png,.gif,.tiff',
                'help_text': 'Upload photos of received goods (Max 32MB)'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make PO optional
        self.fields['purchase_order'].required = False
        self.fields['supplier'].required = False
        
        # Add JavaScript attributes for dynamic form behavior
        self.fields['purchase_order'].widget.attrs.update({
            'onchange': 'handlePOSelection(this.value)'
        })

    def clean(self):
        cleaned_data = super().clean()
        purchase_order = cleaned_data.get('purchase_order')
        supplier = cleaned_data.get('supplier')
        
        # Either PO or supplier must be provided
        if not purchase_order and not supplier:
            raise ValidationError('Either Purchase Order or Supplier must be selected.')
        
        # If PO is selected, supplier should match PO supplier
        if purchase_order and supplier and purchase_order.supplier != supplier:
            raise ValidationError('Selected supplier must match the Purchase Order supplier.')
            
        return cleaned_data

    def clean_delivery_challan(self):
        file = self.cleaned_data.get('delivery_challan')
        if file:
            validate_file_size(file)
        return file

    def clean_packing_list(self):
        file = self.cleaned_data.get('packing_list')
        if file:
            validate_file_size(file)
        return file

    def clean_quality_certificates(self):
        file = self.cleaned_data.get('quality_certificates')
        if file:
            validate_file_size(file)
        return file

    def clean_inspection_report(self):
        file = self.cleaned_data.get('inspection_report')
        if file:
            validate_file_size(file)
        return file

    def clean_photos_received_goods(self):
        file = self.cleaned_data.get('photos_received_goods')
        if file:
            validate_file_size(file)
        return file


class GRNItemForm(forms.ModelForm):
    """Enhanced GRN Item form with tracking and quality features"""
    
    class Meta:
        model = GRNItem
        fields = [
            'product', 'ordered_qty', 'received_qty', 
            'tracking_type', 'tracking_required', 'quality_status',
            'inspection_notes', 'remarks'
        ]
        widgets = {
            'product': forms.Select(attrs={
                'class': 'form-control product-select',
                'onchange': 'updateProductDetails(this)',
                'help_text': 'Select product from inventory'
            }),
            'ordered_qty': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
                'readonly': 'readonly',
                'help_text': 'Quantity from PO (if applicable)'
            }),
            'received_qty': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
                'required': True,
                'help_text': 'Actual quantity received'
            }),
            'tracking_type': forms.Select(attrs={
                'class': 'form-control',
                'onchange': 'toggleTrackingFields(this)',
                'help_text': 'Type of tracking for this item'
            }),
            'tracking_required': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'onchange': 'toggleIndividualTracking(this)',
                'help_text': 'Track each item individually'
            }),
            'quality_status': forms.Select(attrs={
                'class': 'form-control',
                'help_text': 'Quality status after initial inspection'
            }),
            'inspection_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Note any defects or issues observed',
                'help_text': 'Describe any visible defects'
            }),
            'remarks': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'General condition notes',
                'help_text': 'Overall condition observations'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # If instance has PO item, make certain fields readonly
        if self.instance and hasattr(self.instance, 'po_item') and self.instance.po_item:
            self.fields['ordered_qty'].widget.attrs['readonly'] = True

    def clean_received_qty(self):
        received_qty = self.cleaned_data.get('received_qty')
        if received_qty <= 0:
            raise ValidationError('Received quantity must be greater than 0.')
        return received_qty
    
    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        received_qty = cleaned_data.get('received_qty')
        
        if product and received_qty:
            # Auto-set tracking requirements based on product
            if product.tracking_method != 'none':
                cleaned_data['tracking_type'] = product.tracking_method
                cleaned_data['tracking_required'] = product.requires_individual_tracking
            else:
                cleaned_data['tracking_type'] = 'none'
                cleaned_data['tracking_required'] = False
        
        return cleaned_data


class GRNItemTrackingForm(forms.ModelForm):
    """Form for individual item tracking (barcode, serial, IMEI)"""
    
    class Meta:
        model = GRNItemTracking
        fields = [
            'tracking_number', 'tracking_type', 'batch_number', 
            'expiry_date', 'manufacturing_date', 'quality_status',
            'condition', 'defects', 'notes'
        ]
        widgets = {
            'tracking_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter barcode/serial/IMEI',
                'help_text': 'Unique identifier for this item'
            }),
            'tracking_type': forms.Select(attrs={
                'class': 'form-control',
                'help_text': 'Type of tracking number'
            }),
            'batch_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter batch number',
                'help_text': 'Batch or lot number'
            }),
            'expiry_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'help_text': 'Expiry date (if applicable)'
            }),
            'manufacturing_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'help_text': 'Manufacturing date (if available)'
            }),
            'quality_status': forms.Select(attrs={
                'class': 'form-control',
                'help_text': 'Quality status of this specific item'
            }),
            'condition': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Item condition',
                'help_text': 'Physical condition of the item'
            }),
            'defects': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Note any defects',
                'help_text': 'Specific defects for this item'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Additional notes',
                'help_text': 'Any additional observations'
            })
        }

    def clean_tracking_number(self):
        tracking_number = self.cleaned_data.get('tracking_number')
        if not tracking_number:
            raise ValidationError('Tracking number is required.')
        
        # Check for uniqueness within the system
        if GRNItemTracking.objects.filter(tracking_number=tracking_number).exclude(id=self.instance.id if self.instance else None).exists():
            raise ValidationError('This tracking number already exists in the system.')
        
        return tracking_number


class QualityInspectionForm(forms.ModelForm):
    """Form for quality inspection assignment and management"""
    
    class Meta:
        model = QualityInspection
        fields = [
            'grn', 'assigned_to', 'inspection_type', 'priority',
            'due_date', 'notes'
        ]
        widgets = {
            'grn': forms.Select(attrs={
                'class': 'form-control',
                'help_text': 'GRN to be inspected'
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'form-control',
                'help_text': 'Quality inspector assigned'
            }),
            'inspection_type': forms.Select(attrs={
                'class': 'form-control',
                'help_text': 'Type of quality inspection'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-control',
                'help_text': 'Inspection priority level'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'help_text': 'When inspection should be completed by'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Inspection instructions or notes',
                'help_text': 'Special instructions for the inspector'
            })
        }


class QualityInspectionResultForm(forms.ModelForm):
    """Form for recording quality inspection results"""
    
    class Meta:
        model = QualityInspectionResult
        fields = [
            'grn_item', 'inspected_quantity', 'passed_quantity',
            'failed_quantity', 'result', 'defects_found',
            'severity_level', 'action_taken', 'notes', 'photos'
        ]
        widgets = {
            'grn_item': forms.Select(attrs={
                'class': 'form-control',
                'help_text': 'GRN item being inspected'
            }),
            'inspected_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
                'help_text': 'Quantity inspected in this test'
            }),
            'passed_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
                'onchange': 'updateFailedQuantity(this)',
                'help_text': 'Quantity that passed inspection'
            }),
            'failed_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
                'help_text': 'Quantity that failed inspection'
            }),
            'result': forms.Select(attrs={
                'class': 'form-control',
                'help_text': 'Overall inspection result'
            }),
            'defects_found': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'List defects found (JSON format)',
                'help_text': 'Detailed description of defects found'
            }),
            'severity_level': forms.Select(attrs={
                'class': 'form-control',
                'help_text': 'Severity level of defects'
            }),
            'action_taken': forms.Select(attrs={
                'class': 'form-control',
                'help_text': 'Action taken based on inspection'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Additional notes',
                'help_text': 'Any additional observations'
            }),
            'photos': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.jpg,.jpeg,.png,.gif',
                'help_text': 'Photos from quality testing'
            })
        }

    def clean(self):
        cleaned_data = super().clean()
        inspected_quantity = cleaned_data.get('inspected_quantity')
        passed_quantity = cleaned_data.get('passed_quantity')
        failed_quantity = cleaned_data.get('failed_quantity')
        
        if inspected_quantity and passed_quantity and failed_quantity:
            if passed_quantity + failed_quantity != inspected_quantity:
                raise ValidationError('Passed quantity + Failed quantity must equal Inspected quantity.')
        
        return cleaned_data

class BillForm(forms.ModelForm):
    """Enhanced Bill form with GRN and PO integration"""
    
    class Meta:
        model = Bill
        fields = [
            'supplier', 'purchase_order', 'grn', 'supplier_invoice_number', 
            'bill_date', 'due_date', 'notes',
            'supplier_invoice', 'tax_invoice', 'supporting_documents', 'approval_documents'
        ]
        widgets = {
            'supplier': forms.Select(attrs={
                'class': 'form-control',
                'onchange': 'filterPOAndGRN(this.value)',
                'help_text': 'Select supplier for this invoice'
            }),
            'purchase_order': forms.Select(attrs={
                'class': 'form-control',
                'onchange': 'loadPOItems(this.value)',
                'help_text': 'Optional: Link to purchase order for matching'
            }),
            'grn': forms.Select(attrs={
                'class': 'form-control',
                'onchange': 'loadGRNItems(this.value)',
                'help_text': 'Optional: Link to GRN for matching'
            }),
            'supplier_invoice_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter supplier invoice number',
                'help_text': 'Invoice number provided by supplier',
                'required': True
            }),
            'bill_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'help_text': 'Date on the supplier invoice',
                'required': True
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'help_text': 'Payment due date',
                'required': True
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes about this bill',
                'help_text': 'Any special notes or comments'
            }),
            'supplier_invoice': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png',
                'help_text': 'Upload supplier invoice document'
            }),
            'tax_invoice': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png',
                'help_text': 'Upload tax invoice document'
            }),
            'supporting_documents': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png',
                'help_text': 'Upload supporting documents'
            }),
            'approval_documents': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx',
                'help_text': 'Upload internal approval documents'
            })
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Filter suppliers, POs, and GRNs by company
            self.fields['supplier'].queryset = Supplier.objects.filter(
                company=user.company, is_active=True
            )
            self.fields['purchase_order'].queryset = PurchaseOrder.objects.filter(
                company=user.company, status__in=['approved', 'sent_to_supplier', 'partially_received', 'completed']
            )
            self.fields['grn'].queryset = GoodsReceiptNote.objects.filter(
                company=user.company, status__in=['completed', 'inspection_completed']
            )
        
        # Make PO and GRN optional
        self.fields['purchase_order'].required = False
        self.fields['grn'].required = False

    def clean(self):
        cleaned_data = super().clean()
        po = cleaned_data.get('purchase_order')
        grn = cleaned_data.get('grn')
        supplier = cleaned_data.get('supplier')
        
        # Validation rules
        if po and grn:
            # Three-way matching - ensure PO and GRN are related
            if grn.purchase_order != po:
                raise ValidationError('Selected GRN must be from the selected Purchase Order.')
            if po.supplier != supplier:
                raise ValidationError('Purchase Order supplier must match selected supplier.')
        elif po:
            # Two-way matching with PO
            if po.supplier != supplier:
                raise ValidationError('Purchase Order supplier must match selected supplier.')
        elif grn:
            # Two-way matching with GRN
            if grn.supplier != supplier:
                raise ValidationError('GRN supplier must match selected supplier.')
        
        return cleaned_data

    def clean_supplier_invoice(self):
        file = self.cleaned_data.get('supplier_invoice')
        if file:
            validate_file_size(file)
        return file

    def clean_tax_invoice(self):
        file = self.cleaned_data.get('tax_invoice')
        if file:
            validate_file_size(file)
        return file

    def clean_supporting_documents(self):
        file = self.cleaned_data.get('supporting_documents')
        if file:
            validate_file_size(file)
        return file


class BillItemForm(forms.ModelForm):
    """Enhanced Bill Item form with tracking support"""
    
    class Meta:
        model = BillItem
        fields = [
            'product', 'quantity', 'unit_price', 'item_source', 
            'po_item', 'grn_item', 'notes'
        ]
        widgets = {
            'product': forms.Select(attrs={
                'class': 'form-control product-select',
                'onchange': 'updateProductTrackingInfo(this)',
                'help_text': 'Select product for this line'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0.01',
                'step': '0.01',
                'onchange': 'calculateLineTotal(this); updateTrackingFields(this)',
                'help_text': 'Invoiced quantity'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0.00',
                'step': '0.01',
                'onchange': 'calculateLineTotal(this)',
                'help_text': 'Unit price from supplier invoice'
            }),
            'item_source': forms.Select(attrs={
                'class': 'form-control',
                'help_text': 'Source of this item'
            }),
            'po_item': forms.Select(attrs={
                'class': 'form-control',
                'help_text': 'Link to PO item if applicable'
            }),
            'grn_item': forms.Select(attrs={
                'class': 'form-control',
                'help_text': 'Link to GRN item if applicable'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Additional notes about this item',
                'help_text': 'Any special notes'
            })
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['product'].queryset = Product.objects.filter(
                company=user.company, is_active=True
            )

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        quantity = cleaned_data.get('quantity')
        po_item = cleaned_data.get('po_item')
        grn_item = cleaned_data.get('grn_item')
        
        # Validate product matches PO/GRN item
        if po_item and product != po_item.product:
            raise ValidationError('Product must match PO item product.')
        
        if grn_item and product != grn_item.product:
            raise ValidationError('Product must match GRN item product.')
        
        # Check quantity variances
        if po_item and quantity > po_item.quantity:
            # Allow over-invoicing but flag it
            cleaned_data['po_quantity_variance'] = quantity - po_item.quantity
        
        if grn_item and quantity > grn_item.received_qty:
            # Allow over-invoicing but flag it
            cleaned_data['grn_quantity_variance'] = quantity - grn_item.received_qty
        
        return cleaned_data


class BillItemTrackingForm(forms.ModelForm):
    """Form for individual item tracking in bills"""
    
    class Meta:
        model = BillItemTracking
        fields = [
            'tracking_number', 'tracking_type', 'grn_tracking',
            'creates_asset', 'asset_value', 'batch_number',
            'manufacturing_date', 'expiry_date', 'warranty_expiry',
            'condition', 'notes'
        ]
        widgets = {
            'tracking_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter tracking number',
                'help_text': 'Serial, IMEI, Barcode, etc.'
            }),
            'tracking_type': forms.Select(attrs={
                'class': 'form-control',
                'help_text': 'Type of tracking number'
            }),
            'grn_tracking': forms.Select(attrs={
                'class': 'form-control',
                'help_text': 'Link to GRN tracking if available'
            }),
            'creates_asset': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'help_text': 'Create fixed asset for this item'
            }),
            'asset_value': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0.00',
                'step': '0.01',
                'help_text': 'Asset value if creating asset'
            }),
            'batch_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Batch/Lot number',
                'help_text': 'Batch or lot number'
            }),
            'manufacturing_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'help_text': 'Manufacturing date'
            }),
            'expiry_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'help_text': 'Expiry date'
            }),
            'warranty_expiry': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'help_text': 'Warranty expiry date'
            }),
            'condition': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Item condition',
                'help_text': 'Physical condition'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Additional notes',
                'help_text': 'Any additional information'
            })
        }

    def clean_tracking_number(self):
        tracking_number = self.cleaned_data.get('tracking_number')
        if not tracking_number:
            raise ValidationError('Tracking number is required.')
        
        # Check for uniqueness within the system
        if BillItemTracking.objects.filter(
            tracking_number=tracking_number
        ).exclude(id=self.instance.id if self.instance else None).exists():
            raise ValidationError('This tracking number already exists in the system.')
        
        return tracking_number

    def clean_approval_documents(self):
        file = self.cleaned_data.get('approval_documents')
        if file:
            validate_file_size(file)
        return file

class PurchasePaymentForm(forms.ModelForm):
    """Enhanced Payment form with supplier ledger integration"""
    
    class Meta:
        model = PurchasePayment
        fields = [
            'supplier', 'bill', 'payment_type', 'amount', 'currency', 'exchange_rate',
            'payment_method', 'payment_date', 'expected_date', 'reference_number', 
            'transaction_id', 'bank_account', 'beneficiary_bank', 'swift_code',
            'notes', 'internal_notes', 'payment_receipt', 'bank_statement', 
            'check_copy', 'wire_transfer_advice', 'approval_document'
        ]
        widgets = {
            'supplier': forms.Select(attrs={
                'class': 'form-control supplier-select',
                'onchange': 'filterBillsBySupplier(this.value); loadSupplierLedger(this.value)',
                'help_text': 'Select supplier for this payment',
                'required': True
            }),
            'bill': forms.Select(attrs={
                'class': 'form-control bill-select',
                'onchange': 'populatePaymentAmount(this)',
                'help_text': 'Select bill to pay (optional for advance payments)'
            }),
            'payment_type': forms.Select(attrs={
                'class': 'form-control',
                'onchange': 'togglePaymentFields(this.value)',
                'help_text': 'Type of payment being made'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control payment-amount',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00',
                'onchange': 'calculateConvertedAmount()',
                'help_text': 'Payment amount',
                'required': True
            }),
            'currency': forms.Select(attrs={
                'class': 'form-control',
                'onchange': 'updateExchangeRate(this.value)',
                'help_text': 'Payment currency'
            }),
            'exchange_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.0001',
                'min': '0.0001',
                'placeholder': '1.0000',
                'onchange': 'calculateConvertedAmount()',
                'help_text': 'Exchange rate to base currency'
            }),
            'payment_method': forms.Select(attrs={
                'class': 'form-control',
                'onchange': 'toggleMethodFields(this.value)',
                'help_text': 'Method of payment'
            }),
            'payment_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'help_text': 'Date when payment was made',
                'required': True
            }),
            'expected_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'help_text': 'Expected payment processing date'
            }),
            'reference_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter payment reference/transaction number',
                'help_text': 'Bank transaction, check number, or reference'
            }),
            'transaction_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Bank transaction ID',
                'help_text': 'Unique bank transaction identifier'
            }),
            'bank_account': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Bank account used for payment',
                'help_text': 'Company bank account details'
            }),
            'beneficiary_bank': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': "Supplier's bank details",
                'help_text': 'Supplier bank account information'
            }),
            'swift_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'SWIFT/BIC code',
                'help_text': 'Bank SWIFT code for international transfers'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Payment description and notes',
                'help_text': 'Public notes visible in reports'
            }),
            'internal_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Internal notes (not visible to supplier)',
                'help_text': 'Internal comments for company use only'
            }),
            'payment_receipt': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png',
                'help_text': 'Upload payment receipt document'
            }),
            'bank_statement': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.xls,.xlsx',
                'help_text': 'Upload bank statement showing payment'
            }),
            'check_copy': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png',
                'help_text': 'Upload copy of check if payment by check'
            }),
            'wire_transfer_advice': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx',
                'help_text': 'Upload wire transfer advice document'
            }),
            'approval_document': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx',
                'help_text': 'Upload payment approval document'
            })
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Filter choices based on company
            self.fields['supplier'].queryset = Supplier.objects.filter(
                company=user.company, is_active=True
            )
            self.fields['bill'].queryset = Bill.objects.filter(
                company=user.company, 
                status__in=['submitted', 'approved', 'partially_paid'],
                outstanding_amount__gt=0
            )
        
        # Add currency choices (you can expand this list)
        self.fields['currency'].widget.choices = [
            ('USD', 'US Dollar'),
            ('EUR', 'Euro'),
            ('GBP', 'British Pound'),
            ('JPY', 'Japanese Yen'),
            ('CAD', 'Canadian Dollar'),
            ('AUD', 'Australian Dollar'),
        ]
        
        # Make bill optional for advance payments
        self.fields['bill'].required = False

    def clean(self):
        cleaned_data = super().clean()
        payment_type = cleaned_data.get('payment_type')
        bill = cleaned_data.get('bill')
        supplier = cleaned_data.get('supplier')
        amount = cleaned_data.get('amount')
        
        # Validation rules
        if payment_type == 'bill_payment' and not bill:
            raise ValidationError('Bill is required for bill payments.')
        
        if bill and supplier and bill.supplier != supplier:
            raise ValidationError('Bill supplier must match selected supplier.')
        
        if bill and amount and amount > bill.outstanding_amount:
            # Allow overpayment but warn
            cleaned_data['_overpayment_warning'] = f'Payment amount exceeds outstanding balance by ${amount - bill.outstanding_amount}'
        
        # Currency validation
        exchange_rate = cleaned_data.get('exchange_rate', 1.0)
        if exchange_rate <= 0:
            raise ValidationError('Exchange rate must be greater than 0.')
        
        return cleaned_data

    def clean_payment_receipt(self):
        file = self.cleaned_data.get('payment_receipt')
        if file:
            validate_file_size(file)
        return file

    def clean_bank_statement(self):
        file = self.cleaned_data.get('bank_statement')
        if file:
            validate_file_size(file)
        return file

    def clean_check_copy(self):
        file = self.cleaned_data.get('check_copy')
        if file:
            validate_file_size(file)
        return file

    def clean_wire_transfer_advice(self):
        file = self.cleaned_data.get('wire_transfer_advice')
        if file:
            validate_file_size(file)
        return file

    def clean_approval_document(self):
        file = self.cleaned_data.get('approval_document')
        if file:
            validate_file_size(file)
        return file


class SupplierLedgerFilterForm(forms.Form):
    """Form for filtering supplier ledger entries"""
    
    supplier = forms.ModelChoiceField(
        queryset=Supplier.objects.none(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'onchange': 'filterLedgerEntries()'
        })
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'onchange': 'filterLedgerEntries()'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'onchange': 'filterLedgerEntries()'
        })
    )
    
    reference_type = forms.ChoiceField(
        choices=[('', 'All Types')] + SupplierLedger.REFERENCE_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'onchange': 'filterLedgerEntries()'
        })
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search description, reference number...',
            'onkeyup': 'filterLedgerEntries()'
        })
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['supplier'].queryset = Supplier.objects.filter(
                company=user.company, is_active=True
            )

class PurchaseReturnForm(forms.ModelForm):
    """Enhanced Purchase Return form with quality integration"""
    
    class Meta:
        model = PurchaseReturn
        fields = [
            'return_number', 'supplier', 'purchase_order', 'grn', 
            'return_type', 'reason', 'total_amount',
            'return_authorization', 'quality_report', 'photos_returned_items', 
            'supplier_acknowledgment'
        ]
        widgets = {
            'return_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Auto-generated (e.g., RET-2025-001)',
                'readonly': 'readonly',
                'help_text': 'Unique purchase return number - auto-generated'
            }),
            'supplier': forms.Select(attrs={
                'class': 'form-control',
                'help_text': 'Supplier to return items to'
            }),
            'purchase_order': forms.Select(attrs={
                'class': 'form-control',
                'help_text': 'Purchase order related to this return'
            }),
            'grn': forms.Select(attrs={
                'class': 'form-control',
                'onchange': 'loadGRNDetails(this.value)',
                'help_text': 'Select GRN containing items to return (optional)'
            }),
            'return_type': forms.Select(attrs={
                'class': 'form-control',
                'help_text': 'Type of return being processed'
            }),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe the reason for return in detail',
                'help_text': 'Detailed explanation of why items are being returned'
            }),
            'total_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
                'placeholder': '0.00',
                'help_text': 'Total return amount'
            }),
            'return_authorization': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx',
                'help_text': 'Upload return authorization document (Max 32MB)'
            }),
            'quality_report': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.xls,.xlsx',
                'help_text': 'Upload quality inspection report for return (Max 32MB)'
            }),
            'photos_returned_items': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.jpg,.jpeg,.png,.gif,.tiff',
                'help_text': 'Upload photos of returned items (Max 32MB)'
            }),
            'supplier_acknowledgment': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png',
                'help_text': 'Upload supplier acknowledgment of return (Max 32MB)'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # GRN is optional
        self.fields['grn'].required = False

    def clean_return_authorization(self):
        file = self.cleaned_data.get('return_authorization')
        if file:
            validate_file_size(file)
        return file

    def clean_quality_report(self):
        file = self.cleaned_data.get('quality_report')
        if file:
            validate_file_size(file)
        return file

    def clean_photos_returned_items(self):
        file = self.cleaned_data.get('photos_returned_items')
        if file:
            validate_file_size(file)
        return file

    def clean_supplier_acknowledgment(self):
        file = self.cleaned_data.get('supplier_acknowledgment')
        if file:
            validate_file_size(file)
        return file


class PurchaseReturnItemForm(forms.ModelForm):
    """Enhanced Purchase Return Item form with quality and tracking integration"""
    
    class Meta:
        model = PurchaseReturnItem
        fields = [
            'grn_item', 'tracking_item', 'return_quantity', 'unit_price',
            'return_reason', 'condition_at_return', 'defects_description',
            'replacement_requested', 'refund_requested', 'credit_note_requested'
        ]
        widgets = {
            'grn_item': forms.Select(attrs={
                'class': 'form-control',
                'onchange': 'loadGRNItemDetails(this.value)',
                'help_text': 'Select item from GRN to return'
            }),
            'tracking_item': forms.Select(attrs={
                'class': 'form-control',
                'help_text': 'Select specific tracked item (if applicable)'
            }),
            'return_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
                'onchange': 'updateReturnValue(this)',
                'help_text': 'Quantity being returned'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
                'readonly': 'readonly',
                'help_text': 'Unit price from original GRN'
            }),
            'return_reason': forms.Select(attrs={
                'class': 'form-control',
                'help_text': 'Primary reason for return'
            }),
            'condition_at_return': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Condition when returned',
                'help_text': 'Physical condition at time of return'
            }),
            'defects_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe defects or issues in detail',
                'help_text': 'Detailed description of defects/issues'
            }),
            'replacement_requested': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'help_text': 'Request replacement from supplier'
            }),
            'refund_requested': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'help_text': 'Request refund from supplier'
            }),
            'credit_note_requested': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'help_text': 'Request credit note from supplier'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tracking item is optional
        self.fields['tracking_item'].required = False

    def clean_return_quantity(self):
        return_quantity = self.cleaned_data.get('return_quantity')
        grn_item = self.cleaned_data.get('grn_item')
        
        if return_quantity <= 0:
            raise ValidationError('Return quantity must be greater than 0.')
        
        if grn_item and return_quantity > grn_item.received_qty:
            raise ValidationError('Return quantity cannot exceed received quantity.')
        
        return return_quantity

# Item Forms
class PurchaseRequisitionItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseRequisitionItem
        fields = ['product', 'quantity', 'unit_price', 'preferred_supplier', 'specifications']
        widgets = {
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '1.00',
                'help_text': 'Quantity needed'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00',
                'help_text': 'Estimated unit price'
            }),
            'specifications': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Enter specific requirements or specifications',
                'help_text': 'Detailed specifications for this item'
            })
        }

class RFQItemForm(forms.ModelForm):
    class Meta:
        model = RFQItem
        fields = ['product', 'quantity', 'required_uom', 'specifications', 'priority', 'minimum_qty_required', 'maximum_qty_acceptable', 'target_unit_price']
        widgets = {
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '1.00',
                'help_text': 'Quantity to quote'
            }),
            'specifications': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Enter specifications for quotation',
                'help_text': 'Detailed specifications for suppliers'
            }),
            'minimum_qty_required': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '1.00',
                'help_text': 'Minimum acceptable quantity'
            }),
            'maximum_qty_acceptable': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00',
                'help_text': 'Maximum quantity we can accept (0 for unlimited)'
            }),
            'target_unit_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00',
                'help_text': 'Target unit price for budgeting'
            })
        }

class SupplierQuotationItemForm(forms.ModelForm):
    class Meta:
        model = SupplierQuotationItem
        fields = ['product', 'quantity', 'quoted_uom', 'unit_price', 'package_qty', 'minimum_order_qty', 'item_discount_percentage', 'item_discount_amount', 'delivery_time_days', 'specifications']
        widgets = {
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '1.00',
                'help_text': 'Quoted quantity'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00',
                'help_text': 'Price per unit as quoted'
            }),
            'package_qty': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '1.00',
                'help_text': 'Base units per package (e.g., 10 pieces per packet)'
            }),
            'minimum_order_qty': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '1.00',
                'help_text': 'Minimum order quantity'
            }),
            'item_discount_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00',
                'help_text': 'Item-specific discount percentage'
            }),
            'item_discount_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00',
                'help_text': 'Item-specific discount amount'
            }),
            'delivery_time_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0',
                'help_text': 'Delivery time for this item in days'
            }),
            'specifications': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Enter item specifications as quoted',
                'help_text': 'Product specifications as confirmed by supplier'
            })
        }


# Formsets for managing multiple items
from django.forms import inlineformset_factory

# GRN Item Formset
GRNItemFormSet = inlineformset_factory(
    GoodsReceiptNote,
    GRNItem,
    form=GRNItemForm,
    extra=1,
    min_num=1,
    can_delete=True,
    validate_min=True
)

# GRN Item Tracking Formset
GRNItemTrackingFormSet = inlineformset_factory(
    GRNItem,
    GRNItemTracking,
    form=GRNItemTrackingForm,
    extra=0,
    can_delete=True
)

# Quality Inspection Result Formset
QualityInspectionResultFormSet = inlineformset_factory(
    QualityInspection,
    QualityInspectionResult,
    form=QualityInspectionResultForm,
    extra=1,
    can_delete=True
)

# Purchase Return Item Formset
PurchaseReturnItemFormSet = inlineformset_factory(
    PurchaseReturn,
    PurchaseReturnItem,
    form=PurchaseReturnItemForm,
    extra=1,
    min_num=1,
    can_delete=True,
    validate_min=True
)


class SupplierContactForm(forms.ModelForm):
    """Form for managing supplier contacts"""
    
    class Meta:
        model = SupplierContact
        fields = [
            'name', 'contact_type', 'designation', 'email', 
            'phone', 'mobile', 'is_primary', 'is_active', 'notes'
        ]
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contact person name',
                'required': True
            }),
            'contact_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'designation': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Job title/Position'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'contact@supplier.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1-234-567-8900'
            }),
            'mobile': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1-234-567-8901'
            }),
            'is_primary': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes about this contact'
            })
        }


class SupplierProductCatalogForm(forms.ModelForm):
    """Form for managing supplier product catalog"""
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user and hasattr(user, 'company'):
            # Filter products by company
            self.fields['product'].queryset = Product.objects.filter(
                company=user.company,
                is_active=True
            ).order_by('name')
    
    class Meta:
        model = SupplierProductCatalog
        fields = [
            'product', 'supplier_product_code', 'supplier_product_name',
            'unit_price', 'currency', 'minimum_order_quantity', 
            'lead_time_days', 'effective_date', 'expiry_date',
            'is_active', 'description', 'technical_specifications', 'warranty_terms'
        ]
        
        widgets = {
            'product': forms.Select(attrs={
                'class': 'form-control select2',
                'required': True
            }),
            'supplier_product_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Supplier\'s product code/SKU'
            }),
            'supplier_product_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Product name as per supplier catalog'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'currency': forms.Select(attrs={
                'class': 'form-control'
            }),
            'minimum_order_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '1',
                'min': '1',
                'placeholder': '1'
            }),
            'lead_time_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '1',
                'min': '0',
                'placeholder': 'Days'
            }),
            'effective_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'expiry_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Product description'
            }),
            'technical_specifications': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Technical specifications'
            }),
            'warranty_terms': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Warranty terms and conditions'
            })
        }
