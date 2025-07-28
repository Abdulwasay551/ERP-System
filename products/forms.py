from django import forms
from django.core.exceptions import ValidationError
from .models import Product, ProductCategory, ProductVariant, ProductTracking, Attribute, AttributeValue, ProductAttribute


class ProductForm(forms.ModelForm):
    """Enhanced Product form with tracking options"""
    
    class Meta:
        model = Product
        fields = [
            'name', 'sku', 'barcode', 'description', 'category', 'product_type',
            'unit_of_measure', 'weight', 'dimensions',
            'cost_price', 'selling_price',
            'is_active', 'is_saleable', 'is_purchasable', 'is_manufacturable', 'is_stockable',
            'tracking_method', 'requires_individual_tracking', 'requires_expiry_tracking', 
            'requires_batch_tracking', 'shelf_life_days',
            'minimum_stock', 'maximum_stock', 'reorder_level',
            'notes', 'image'
        ]
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter product name',
                'help_text': 'Descriptive name for the product'
            }),
            'sku': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter SKU (Stock Keeping Unit)',
                'help_text': 'Unique identifier for this product'
            }),
            'barcode': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter barcode number',
                'help_text': 'Product barcode for scanning'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Detailed product description',
                'help_text': 'Detailed description of the product'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control',
                'help_text': 'Product category classification'
            }),
            'product_type': forms.Select(attrs={
                'class': 'form-control',
                'help_text': 'Type of product for inventory and costing'
            }),
            'unit_of_measure': forms.Select(attrs={
                'class': 'form-control',
                'help_text': 'Base unit for measuring this product'
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'min': '0',
                'placeholder': '0.000',
                'help_text': 'Weight in kilograms'
            }),
            'dimensions': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'L x W x H (e.g., 10cm x 5cm x 2cm)',
                'help_text': 'Physical dimensions'
            }),
            'cost_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'help_text': 'Cost price (purchase/manufacturing cost)'
            }),
            'selling_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'help_text': 'Selling price to customers'
            }),
            
            # Tracking fields
            'tracking_method': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_tracking_method',
                'onchange': 'toggleTrackingOptions(this.value)',
                'help_text': 'How individual units of this product are tracked'
            }),
            'requires_individual_tracking': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'id_requires_individual_tracking',
                'help_text': 'Each unit must be tracked individually (for serial/IMEI/barcode)'
            }),
            'requires_expiry_tracking': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'id_requires_expiry_tracking',
                'help_text': 'Track expiry dates for this product'
            }),
            'requires_batch_tracking': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'id_requires_batch_tracking',
                'help_text': 'Track by batch or lot numbers'
            }),
            'shelf_life_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Enter days',
                'help_text': 'Shelf life in days (for auto-calculating expiry dates)'
            }),
            
            # Stock levels
            'minimum_stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'help_text': 'Minimum stock level for alerts'
            }),
            'maximum_stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'help_text': 'Maximum stock level'
            }),
            'reorder_level': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'help_text': 'Stock level at which to reorder'
            }),
            
            # Boolean fields
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'help_text': 'Whether this product is active'
            }),
            'is_saleable': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'help_text': 'Can be sold to customers'
            }),
            'is_purchasable': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'help_text': 'Can be purchased from suppliers'
            }),
            'is_manufacturable': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'help_text': 'Can be manufactured internally'
            }),
            'is_stockable': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'help_text': 'Tracked in inventory'
            }),
            
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Additional notes about this product',
                'help_text': 'Additional information'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'help_text': 'Product image file'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set initial values based on tracking method
        if self.instance and self.instance.pk:
            self.setup_tracking_fields()

    def setup_tracking_fields(self):
        """Setup tracking fields based on current tracking method"""
        tracking_method = self.instance.tracking_method
        
        # Enable/disable fields based on tracking method
        if tracking_method == 'none':
            self.fields['requires_individual_tracking'].widget.attrs['disabled'] = True
            self.fields['requires_expiry_tracking'].widget.attrs['disabled'] = True
            self.fields['requires_batch_tracking'].widget.attrs['disabled'] = True
            self.fields['shelf_life_days'].widget.attrs['disabled'] = True
        elif tracking_method == 'expiry':
            self.fields['requires_individual_tracking'].widget.attrs['disabled'] = True
            self.fields['requires_batch_tracking'].widget.attrs['disabled'] = True
        elif tracking_method == 'batch':
            self.fields['requires_individual_tracking'].widget.attrs['disabled'] = True
        elif tracking_method in ['serial', 'imei', 'barcode']:
            self.fields['requires_batch_tracking'].widget.attrs['disabled'] = True

    def clean(self):
        cleaned_data = super().clean()
        tracking_method = cleaned_data.get('tracking_method')
        requires_expiry = cleaned_data.get('requires_expiry_tracking')
        shelf_life = cleaned_data.get('shelf_life_days')
        
        # Validate tracking requirements
        if tracking_method == 'expiry' and not requires_expiry:
            raise ValidationError('Products with expiry tracking must have "requires_expiry_tracking" enabled.')
        
        if requires_expiry and not shelf_life:
            raise ValidationError('Products requiring expiry tracking must have shelf life specified.')
        
        return cleaned_data

    def save(self, commit=True):
        product = super().save(commit=False)
        
        # Auto-set tracking flags based on tracking method
        if product.tracking_method == 'expiry':
            product.requires_expiry_tracking = True
            product.requires_individual_tracking = False
            product.requires_batch_tracking = False
        elif product.tracking_method == 'batch':
            product.requires_batch_tracking = True
            product.requires_individual_tracking = False
        elif product.tracking_method in ['serial', 'imei', 'barcode']:
            product.requires_individual_tracking = True
            product.requires_batch_tracking = False
        elif product.tracking_method == 'none':
            product.requires_individual_tracking = False
            product.requires_expiry_tracking = False
            product.requires_batch_tracking = False
        
        if commit:
            product.save()
        return product


class ProductTrackingForm(forms.ModelForm):
    """Form for creating individual tracking units"""
    
    class Meta:
        model = ProductTracking
        fields = [
            'product', 'variant', 'serial_number', 'imei_number', 'barcode', 'batch_number',
            'manufacturing_date', 'expiry_date', 'supplier_batch_reference',
            'current_warehouse', 'location_notes', 'purchase_price', 'warranty_expiry',
            'notes'
        ]
        
        widgets = {
            'product': forms.Select(attrs={
                'class': 'form-control',
                'onchange': 'updateTrackingFields(this.value)',
                'help_text': 'Select the product to track'
            }),
            'variant': forms.Select(attrs={
                'class': 'form-control',
                'help_text': 'Product variant (if applicable)'
            }),
            'serial_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter serial number',
                'help_text': 'Unique serial number'
            }),
            'imei_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter IMEI number',
                'help_text': 'IMEI number for mobile devices'
            }),
            'barcode': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter or scan barcode',
                'help_text': 'Product barcode'
            }),
            'batch_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter batch/lot number',
                'help_text': 'Batch or lot identification'
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
            'supplier_batch_reference': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Supplier batch reference',
                'help_text': 'Supplier\'s batch reference number'
            }),
            'current_warehouse': forms.Select(attrs={
                'class': 'form-control',
                'help_text': 'Current storage location'
            }),
            'location_notes': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Specific location within warehouse',
                'help_text': 'Bin, rack, or specific location'
            }),
            'purchase_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'help_text': 'Purchase price for this unit'
            }),
            'warranty_expiry': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'help_text': 'Warranty expiry date'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes',
                'help_text': 'Any additional information'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Show only relevant tracking fields based on product
        if self.instance and self.instance.product:
            self.setup_tracking_fields_for_product(self.instance.product)

    def setup_tracking_fields_for_product(self, product):
        """Show only relevant tracking fields based on product tracking method"""
        if product.tracking_method == 'none':
            # Hide all tracking fields
            for field in ['serial_number', 'imei_number', 'barcode', 'batch_number']:
                self.fields[field].widget = forms.HiddenInput()
        elif product.tracking_method == 'serial':
            # Show only serial number
            for field in ['imei_number', 'barcode', 'batch_number']:
                self.fields[field].widget = forms.HiddenInput()
        elif product.tracking_method == 'imei':
            # Show only IMEI
            for field in ['serial_number', 'barcode', 'batch_number']:
                self.fields[field].widget = forms.HiddenInput()
        elif product.tracking_method == 'barcode':
            # Show only barcode
            for field in ['serial_number', 'imei_number', 'batch_number']:
                self.fields[field].widget = forms.HiddenInput()
        elif product.tracking_method == 'batch':
            # Show only batch number
            for field in ['serial_number', 'imei_number', 'barcode']:
                self.fields[field].widget = forms.HiddenInput()

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        
        if product:
            # Validate tracking fields based on product tracking method
            tracking_value = None
            
            if product.tracking_method == 'serial':
                tracking_value = cleaned_data.get('serial_number')
            elif product.tracking_method == 'imei':
                tracking_value = cleaned_data.get('imei_number')
            elif product.tracking_method == 'barcode':
                tracking_value = cleaned_data.get('barcode')
            elif product.tracking_method == 'batch':
                tracking_value = cleaned_data.get('batch_number')
            
            if product.tracking_method != 'none' and not tracking_value:
                raise ValidationError(f'This product requires {product.get_tracking_method_display()} tracking.')
            
            # Auto-calculate expiry date if manufacturing date is provided and product has shelf life
            manufacturing_date = cleaned_data.get('manufacturing_date')
            expiry_date = cleaned_data.get('expiry_date')
            
            if (manufacturing_date and not expiry_date and 
                product.shelf_life_days and product.requires_expiry_tracking):
                from datetime import timedelta
                cleaned_data['expiry_date'] = manufacturing_date + timedelta(days=product.shelf_life_days)
        
        return cleaned_data


class ProductCategoryForm(forms.ModelForm):
    """Form for managing product categories"""
    
    class Meta:
        model = ProductCategory
        fields = ['name', 'code', 'description', 'parent', 'is_active']
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Category name',
                'help_text': 'Name of the product category'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Category code',
                'help_text': 'Short code for the category'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Category description',
                'help_text': 'Detailed description of the category'
            }),
            'parent': forms.Select(attrs={
                'class': 'form-control',
                'help_text': 'Parent category (for subcategories)'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'help_text': 'Whether this category is active'
            })
        }


class BulkTrackingImportForm(forms.Form):
    """Form for bulk importing tracking data"""
    
    product = forms.ModelChoiceField(
        queryset=Product.objects.none(),
        widget=forms.Select(attrs={
            'class': 'form-control',
            'help_text': 'Product to import tracking data for'
        })
    )
    
    tracking_data = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 10,
            'placeholder': 'Enter tracking numbers, one per line',
            'help_text': 'Enter one tracking number per line'
        }),
        help_text='Enter tracking numbers (serial, IMEI, barcode, etc.) one per line'
    )
    
    warehouse = forms.ModelChoiceField(
        queryset=None,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'help_text': 'Default warehouse for all items'
        })
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter products to those that require tracking
        self.fields['product'].queryset = Product.objects.filter(
            company=user.company,
            tracking_method__in=['serial', 'imei', 'barcode', 'batch'],
            is_active=True
        )
        
        # Set warehouse queryset
        from inventory.models import Warehouse
        self.fields['warehouse'].queryset = Warehouse.objects.filter(
            company=user.company,
            is_active=True
        )

    def clean_tracking_data(self):
        tracking_data = self.cleaned_data['tracking_data']
        lines = [line.strip() for line in tracking_data.splitlines() if line.strip()]
        
        if not lines:
            raise ValidationError('At least one tracking number must be provided.')
        
        return lines
