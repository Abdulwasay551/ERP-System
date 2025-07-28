from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from decimal import Decimal
from .models import (
    UnitOfMeasure, Supplier, TaxChargesTemplate, PurchaseRequisition, PurchaseRequisitionItem,
    RequestForQuotation, RFQItem, SupplierQuotation, SupplierQuotationItem,
    PurchaseOrder, PurchaseOrderItem, GoodsReceiptNote, GRNItem, GRNItemTracking,
    QualityInspection, QualityInspectionResult, PurchaseReturn, PurchaseReturnItem,
    Bill, BillItem, PurchasePayment, GRNInventoryLock
)
from inventory.models import Warehouse

# File size validation function
def validate_file_size(value):
    """Validate that file size does not exceed 32MB"""
    if value.size > 32 * 1024 * 1024:  # 32MB in bytes
        raise ValidationError('File size cannot exceed 32MB.')
    return value

# Allowed file extensions for documents
DOCUMENT_EXTENSIONS = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'jpg', 'jpeg', 'png', 'gif', 'tiff']
IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'tiff', 'bmp']

class UnitOfMeasureForm(forms.ModelForm):
    class Meta:
        model = UnitOfMeasure
        fields = ['company', 'name', 'abbreviation', 'uom_type', 'is_base_unit', 'conversion_factor', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter UOM name (e.g., Kilogram, Meter)',
                'help_text': 'Full name of the unit of measure'
            }),
            'abbreviation': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter abbreviation (e.g., KG, M)',
                'help_text': 'Short form or symbol for the unit'
            }),
            'uom_type': forms.Select(attrs={
                'class': 'form-control',
                'help_text': 'Category this unit belongs to'
            }),
            'conversion_factor': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.000001',
                'placeholder': '1.000000',
                'help_text': 'Conversion factor to base unit (e.g., 1000 for KG to Gram)'
            }),
            'is_base_unit': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'help_text': 'Check if this is the base unit for its category'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'help_text': 'Uncheck to disable this UOM'
            })
        }
        help_texts = {
            'name': 'Enter the full name of the unit of measure',
            'abbreviation': 'Enter a short abbreviation or symbol',
            'uom_type': 'Select the category this unit belongs to',
            'is_base_unit': 'Mark as base unit if other units convert to this',
            'conversion_factor': 'Factor to convert this unit to the base unit',
            'is_active': 'Whether this UOM is available for use'
        }

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = [
            'name', 'supplier_code', 'company', 'partner', 'contact_person', 'email', 'phone', 
            'address', 'tax_number', 'bank_details', 'payment_terms', 'credit_limit', 
            'delivery_lead_time', 'quality_rating', 'delivery_rating', 'is_active',
            'registration_certificate', 'tax_certificate', 'quality_certificates', 
            'bank_documents', 'agreement_contract'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter supplier company name',
                'help_text': 'Official registered name of the supplier company'
            }),
            'supplier_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter unique supplier code (e.g., SUP001)',
                'help_text': 'Unique identifier for this supplier'
            }),
            'contact_person': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter primary contact person name',
                'help_text': 'Name of main contact person at supplier'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter supplier email address',
                'help_text': 'Primary email for purchase communications'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter phone number with country code',
                'help_text': 'Primary contact phone number'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter complete supplier address',
                'help_text': 'Complete address including city, state, country'
            }),
            'tax_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter tax registration number',
                'help_text': 'Tax ID or VAT registration number'
            }),
            'bank_details': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter bank account details for payments',
                'help_text': 'Bank name, account number, routing details'
            }),
            'credit_limit': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00',
                'help_text': 'Maximum credit limit for this supplier'
            }),
            'delivery_lead_time': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter days',
                'help_text': 'Default delivery time in days'
            }),
            'quality_rating': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0',
                'max': '10',
                'placeholder': '0.0',
                'help_text': 'Quality rating from 0 to 10'
            }),
            'delivery_rating': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0',
                'max': '10',
                'placeholder': '0.0',
                'help_text': 'Delivery performance rating from 0 to 10'
            }),
            'registration_certificate': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png',
                'help_text': 'Upload business registration certificate (Max 32MB)'
            }),
            'tax_certificate': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png',
                'help_text': 'Upload tax registration certificate (Max 32MB)'
            }),
            'quality_certificates': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png',
                'help_text': 'Upload quality certifications like ISO (Max 32MB)'
            }),
            'bank_documents': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png',
                'help_text': 'Upload bank account verification documents (Max 32MB)'
            }),
            'agreement_contract': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx',
                'help_text': 'Upload master agreement or contract (Max 32MB)'
            })
        }
        help_texts = {
            'name': 'Enter the official registered name of the supplier company',
            'supplier_code': 'Unique code to identify this supplier in the system',
            'partner': 'Link to existing partner record if available',
            'contact_person': 'Primary contact person for purchase communications',
            'email': 'Main email address for sending purchase orders and communications',
            'phone': 'Primary phone number including country code',
            'address': 'Complete business address of the supplier',
            'tax_number': 'Tax identification or VAT registration number',
            'bank_details': 'Banking information for payment processing',
            'payment_terms': 'Default payment terms for this supplier',
            'credit_limit': 'Maximum outstanding amount allowed for this supplier',
            'delivery_lead_time': 'Standard delivery time in days',
            'quality_rating': 'Internal quality rating (0-10 scale)',
            'delivery_rating': 'Internal delivery performance rating (0-10 scale)',
            'is_active': 'Whether this supplier is active for new purchases'
        }

    def clean_registration_certificate(self):
        file = self.cleaned_data.get('registration_certificate')
        if file:
            validate_file_size(file)
        return file

    def clean_tax_certificate(self):
        file = self.cleaned_data.get('tax_certificate')
        if file:
            validate_file_size(file)
        return file

    def clean_quality_certificates(self):
        file = self.cleaned_data.get('quality_certificates')
        if file:
            validate_file_size(file)
        return file

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
    class Meta:
        model = Bill
        fields = [
            'bill_number', 'company', 'supplier', 'purchase_order', 'grn',
            'supplier_invoice_number', 'bill_date', 'due_date', 'notes',
            'supplier_invoice', 'tax_invoice', 'supporting_documents', 'approval_documents'
        ]
        widgets = {
            'bill_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter bill number (e.g., BILL-2025-001)',
                'help_text': 'Unique bill/invoice number'
            }),
            'supplier_invoice_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter supplier invoice number',
                'help_text': 'Invoice number provided by supplier'
            }),
            'bill_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'help_text': 'Date on the supplier invoice'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'help_text': 'Payment due date'
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
                'help_text': 'Upload supplier invoice document (Max 32MB)'
            }),
            'tax_invoice': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png',
                'help_text': 'Upload tax invoice document (Max 32MB)'
            }),
            'supporting_documents': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png',
                'help_text': 'Upload supporting documents like receipts (Max 32MB)'
            }),
            'approval_documents': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx',
                'help_text': 'Upload internal approval documents (Max 32MB)'
            })
        }

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

    def clean_approval_documents(self):
        file = self.cleaned_data.get('approval_documents')
        if file:
            validate_file_size(file)
        return file

class PurchasePaymentForm(forms.ModelForm):
    class Meta:
        model = PurchasePayment
        fields = [
            'payment_number', 'bill', 'supplier', 'amount', 'payment_date',
            'payment_method', 'reference_number', 'notes',
            'payment_receipt', 'bank_statement', 'check_copy', 'wire_transfer_advice'
        ]
        widgets = {
            'payment_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter payment number (e.g., PAY-2025-001)',
                'help_text': 'Unique payment reference number'
            }),
            'bill': forms.Select(attrs={
                'class': 'form-control',
                'help_text': 'Select bill to pay'
            }),
            'supplier': forms.Select(attrs={
                'class': 'form-control',
                'help_text': 'Supplier for this payment'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00',
                'help_text': 'Payment amount'
            }),
            'payment_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'help_text': 'Date when payment was made'
            }),
            'payment_method': forms.Select(attrs={
                'class': 'form-control',
                'help_text': 'Method of payment'
            }),
            'reference_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter payment reference/transaction number',
                'help_text': 'Bank transaction or reference number'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes about this payment',
                'help_text': 'Any special notes about the payment'
            }),
            'payment_receipt': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png',
                'help_text': 'Upload payment receipt document (Max 32MB)'
            }),
            'bank_statement': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.xls,.xlsx',
                'help_text': 'Upload bank statement showing payment (Max 32MB)'
            }),
            'check_copy': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png',
                'help_text': 'Upload copy of check if payment by check (Max 32MB)'
            }),
            'wire_transfer_advice': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx',
                'help_text': 'Upload wire transfer advice document (Max 32MB)'
            })
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        # Filter choices based on company
        if company:
            self.fields['bill'].queryset = Bill.objects.filter(company=company, outstanding_amount__gt=0)
            self.fields['supplier'].queryset = Supplier.objects.filter(company=company, is_active=True)

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
