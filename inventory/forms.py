from django import forms
from django.core.exceptions import ValidationError
from .models import (
    Warehouse, WarehouseZone, WarehouseBin, StockItem, StockMovement, 
    StockLot, StockSerial, StockReservation, StockAlert, InventoryLock,
    StockAdjustment, StockAdjustmentItem
)
from products.models import Product, ProductCategory
from user_auth.models import User, Company
from accounting.models import Account
from django.utils import timezone
from decimal import Decimal


class WarehouseForm(forms.ModelForm):
    """Form for creating and editing warehouses"""
    
    class Meta:
        model = Warehouse
        fields = [
            'name', 'code', 'location', 'address', 'warehouse_type',
            'parent_warehouse', 'location_type', 'latitude', 'longitude',
            'default_for_raw_material', 'default_for_finished_goods', 'default_for_wip',
            'max_capacity_weight', 'max_capacity_volume', 'temperature_controlled',
            'min_temperature', 'max_temperature', 'restricted_access',
            'requires_approval', 'manager', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter warehouse name'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., KHI-RAW-01'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City or area'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Full address'
            }),
            'warehouse_type': forms.Select(attrs={'class': 'form-control'}),
            'parent_warehouse': forms.Select(attrs={'class': 'form-control'}),
            'location_type': forms.Select(attrs={'class': 'form-control'}),
            'latitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.00000001'
            }),
            'longitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.00000001'
            }),
            'max_capacity_weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'max_capacity_volume': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'min_temperature': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'max_temperature': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'manager': forms.Select(attrs={'class': 'form-control select2'}),
            'default_for_raw_material': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'default_for_finished_goods': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'default_for_wip': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'temperature_controlled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'restricted_access': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'requires_approval': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        if self.company:
            # Filter parent warehouses by company
            self.fields['parent_warehouse'].queryset = Warehouse.objects.filter(
                company=self.company, is_active=True
            ).exclude(id=self.instance.id if self.instance.pk else None)
            
            # Filter managers by company
            self.fields['manager'].queryset = User.objects.filter(
                company=self.company, is_active=True
            )

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if code and self.company:
            existing = Warehouse.objects.filter(
                company=self.company, code=code
            ).exclude(id=self.instance.id if self.instance.pk else None)
            if existing.exists():
                raise ValidationError("Warehouse code must be unique within your company.")
        return code

    def clean(self):
        cleaned_data = super().clean()
        parent = cleaned_data.get('parent_warehouse')
        
        # Prevent circular reference
        if parent and self.instance.pk:
            if parent.id == self.instance.id:
                raise ValidationError("A warehouse cannot be its own parent.")
        
        # Temperature validation
        temp_controlled = cleaned_data.get('temperature_controlled')
        min_temp = cleaned_data.get('min_temperature')
        max_temp = cleaned_data.get('max_temperature')
        
        if temp_controlled and min_temp is not None and max_temp is not None:
            if min_temp >= max_temp:
                raise ValidationError("Minimum temperature must be less than maximum temperature.")
        
        return cleaned_data


class WarehouseZoneForm(forms.ModelForm):
    """Form for warehouse zones"""
    
    class Meta:
        model = WarehouseZone
        fields = [
            'warehouse', 'name', 'code', 'description', 'zone_type',
            'temperature_controlled', 'min_temperature', 'max_temperature',
            'is_active'
        ]
        widgets = {
            'warehouse': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'zone_type': forms.Select(attrs={'class': 'form-control'}),
            'min_temperature': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_temperature': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'temperature_controlled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        if self.company:
            self.fields['warehouse'].queryset = Warehouse.objects.filter(
                company=self.company, is_active=True
            )


class StockItemForm(forms.ModelForm):
    """Form for creating and editing stock items"""
    
    class Meta:
        model = StockItem
        fields = [
            'product', 'warehouse', 'zone', 'bin_location', 'specific_location',
            'min_stock', 'max_stock', 'reorder_point', 'safety_stock', 'reorder_quantity',
            'valuation_method', 'standard_cost', 'tracking_type',
            'requires_quality_check', 'has_expiry', 'shelf_life_days', 'expiry_alert_days',
            'suitable_for_sale', 'suitable_for_manufacturing', 'consumable_item',
            'lead_time_days', 'preferred_supplier',
            'weight_per_unit', 'volume_per_unit', 'dimensions_length', 'dimensions_width', 'dimensions_height',
            'barcode', 'qr_code', 'rfid_tag',
            'restricted_access', 'requires_approval_for_issue', 'temperature_sensitive', 'hazardous_material',
            'is_active', 'account'
        ]
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control select2'}),
            'warehouse': forms.Select(attrs={'class': 'form-control select2'}),
            'zone': forms.Select(attrs={'class': 'form-control'}),
            'bin_location': forms.Select(attrs={'class': 'form-control'}),
            'specific_location': forms.TextInput(attrs={'class': 'form-control'}),
            'min_stock': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_stock': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'reorder_point': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'safety_stock': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'reorder_quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'valuation_method': forms.Select(attrs={'class': 'form-control'}),
            'standard_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tracking_type': forms.Select(attrs={'class': 'form-control'}),
            'shelf_life_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'expiry_alert_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'lead_time_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'weight_per_unit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'volume_per_unit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'dimensions_length': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'dimensions_width': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'dimensions_height': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'barcode': forms.TextInput(attrs={'class': 'form-control'}),
            'qr_code': forms.TextInput(attrs={'class': 'form-control'}),
            'rfid_tag': forms.TextInput(attrs={'class': 'form-control'}),
            'account': forms.Select(attrs={'class': 'form-control select2'}),
            # Checkboxes
            'requires_quality_check': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'has_expiry': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'suitable_for_sale': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'suitable_for_manufacturing': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'consumable_item': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'restricted_access': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'requires_approval_for_issue': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'temperature_sensitive': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'hazardous_material': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        if self.company:
            self.fields['product'].queryset = Product.objects.filter(
                company=self.company, is_active=True
            )
            self.fields['warehouse'].queryset = Warehouse.objects.filter(
                company=self.company, is_active=True
            )
            self.fields['account'].queryset = Account.objects.filter(
                company=self.company, is_active=True
            )
            
        # Initially empty zones and bins (will be populated via AJAX)
        self.fields['zone'].queryset = WarehouseZone.objects.none()
        self.fields['bin_location'].queryset = WarehouseBin.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        min_stock = cleaned_data.get('min_stock', 0)
        max_stock = cleaned_data.get('max_stock', 0)
        reorder_point = cleaned_data.get('reorder_point', 0)
        
        if max_stock and min_stock and max_stock <= min_stock:
            raise ValidationError("Maximum stock must be greater than minimum stock.")
        
        if reorder_point and min_stock and reorder_point < min_stock:
            raise ValidationError("Reorder point should not be less than minimum stock level.")
        
        return cleaned_data


class StockMovementForm(forms.ModelForm):
    """Form for stock movements"""
    
    class Meta:
        model = StockMovement
        fields = [
            'stock_item', 'movement_type', 'quantity', 'unit_cost',
            'from_warehouse', 'to_warehouse', 'from_bin', 'to_bin',
            'reference_type', 'reference_number', 'tracking_number',
            'batch_number', 'lot_number', 'serial_number',
            'expiry_date', 'manufacturing_date', 'notes'
        ]
        widgets = {
            'stock_item': forms.Select(attrs={'class': 'form-control select2'}),
            'movement_type': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'unit_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'from_warehouse': forms.Select(attrs={'class': 'form-control'}),
            'to_warehouse': forms.Select(attrs={'class': 'form-control'}),
            'from_bin': forms.Select(attrs={'class': 'form-control'}),
            'to_bin': forms.Select(attrs={'class': 'form-control'}),
            'reference_type': forms.Select(attrs={'class': 'form-control'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control'}),
            'tracking_number': forms.TextInput(attrs={'class': 'form-control'}),
            'batch_number': forms.TextInput(attrs={'class': 'form-control'}),
            'lot_number': forms.TextInput(attrs={'class': 'form-control'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'manufacturing_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        if self.company:
            self.fields['stock_item'].queryset = StockItem.objects.filter(
                company=self.company, is_active=True
            )
            self.fields['from_warehouse'].queryset = Warehouse.objects.filter(
                company=self.company, is_active=True
            )
            self.fields['to_warehouse'].queryset = Warehouse.objects.filter(
                company=self.company, is_active=True
            )

    def clean(self):
        cleaned_data = super().clean()
        movement_type = cleaned_data.get('movement_type')
        from_warehouse = cleaned_data.get('from_warehouse')
        to_warehouse = cleaned_data.get('to_warehouse')
        quantity = cleaned_data.get('quantity')
        stock_item = cleaned_data.get('stock_item')
        
        # Validate warehouse requirements based on movement type
        if movement_type in ['transfer_in', 'transfer_out', 'inter_warehouse_transfer']:
            if not from_warehouse or not to_warehouse:
                raise ValidationError("Both source and destination warehouses are required for transfers.")
            if from_warehouse == to_warehouse:
                raise ValidationError("Source and destination warehouses cannot be the same.")
        
        # Validate quantity against available stock for outgoing movements
        if movement_type in ['sale', 'transfer_out', 'adjustment_out', 'production_out', 'material_issue']:
            if stock_item and quantity:
                if quantity > stock_item.available_quantity:
                    raise ValidationError(f"Cannot move {quantity} units. Only {stock_item.available_quantity} units available.")
        
        return cleaned_data


class StockAdjustmentForm(forms.ModelForm):
    """Form for stock adjustments"""
    
    class Meta:
        model = StockAdjustment
        fields = [
            'adjustment_number', 'adjustment_date', 'adjustment_type',
            'reason', 'notes', 'reference_document'
        ]
        widgets = {
            'adjustment_number': forms.TextInput(attrs={'class': 'form-control'}),
            'adjustment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'adjustment_type': forms.Select(attrs={'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'reference_document': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        # Auto-generate adjustment number if not provided
        if not self.instance.pk and not self.initial.get('adjustment_number'):
            last_adjustment = StockAdjustment.objects.filter(
                company=self.company
            ).order_by('-id').first()
            
            if last_adjustment:
                try:
                    last_num = int(last_adjustment.adjustment_number.split('-')[-1])
                    new_num = last_num + 1
                except:
                    new_num = 1
            else:
                new_num = 1
                
            self.initial['adjustment_number'] = f"ADJ-{new_num:06d}"


class StockLotForm(forms.ModelForm):
    """Form for lot/batch tracking"""
    
    class Meta:
        model = StockLot
        fields = [
            'stock_item', 'lot_number', 'batch_number', 'quantity',
            'unit_cost', 'expiry_date', 'manufacturing_date', 'best_before_date',
            'quality_certificate', 'supplier_lot_number', 'country_of_origin',
            'certification_details'
        ]
        widgets = {
            'stock_item': forms.Select(attrs={'class': 'form-control select2'}),
            'lot_number': forms.TextInput(attrs={'class': 'form-control'}),
            'batch_number': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'unit_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'manufacturing_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'best_before_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'quality_certificate': forms.TextInput(attrs={'class': 'form-control'}),
            'supplier_lot_number': forms.TextInput(attrs={'class': 'form-control'}),
            'country_of_origin': forms.TextInput(attrs={'class': 'form-control'}),
            'certification_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        if self.company:
            self.fields['stock_item'].queryset = StockItem.objects.filter(
                company=self.company, is_active=True
            )

    def clean(self):
        cleaned_data = super().clean()
        mfg_date = cleaned_data.get('manufacturing_date')
        exp_date = cleaned_data.get('expiry_date')
        best_before = cleaned_data.get('best_before_date')
        
        if mfg_date and exp_date:
            if exp_date <= mfg_date:
                raise ValidationError("Expiry date must be after manufacturing date.")
        
        if mfg_date and best_before:
            if best_before <= mfg_date:
                raise ValidationError("Best before date must be after manufacturing date.")
        
        return cleaned_data


class InventoryLockForm(forms.ModelForm):
    """Form for inventory locks"""
    
    class Meta:
        model = InventoryLock
        fields = [
            'stock_item', 'locked_quantity', 'lock_type', 'reference_type',
            'reference_number', 'expires_at', 'auto_unlock_on_bill',
            'auto_unlock_on_quality_pass', 'requires_approval_to_unlock',
            'priority', 'reason', 'notes'
        ]
        widgets = {
            'stock_item': forms.Select(attrs={'class': 'form-control select2'}),
            'locked_quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'lock_type': forms.Select(attrs={'class': 'form-control'}),
            'reference_type': forms.Select(attrs={'class': 'form-control'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control'}),
            'expires_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'priority': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '10'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'auto_unlock_on_bill': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'auto_unlock_on_quality_pass': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'requires_approval_to_unlock': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        if self.company:
            self.fields['stock_item'].queryset = StockItem.objects.filter(
                company=self.company, is_active=True
            )

    def clean(self):
        cleaned_data = super().clean()
        stock_item = cleaned_data.get('stock_item')
        locked_quantity = cleaned_data.get('locked_quantity')
        
        if stock_item and locked_quantity:
            if locked_quantity > stock_item.available_quantity:
                raise ValidationError(f"Cannot lock {locked_quantity} units. Only {stock_item.available_quantity} units available.")
        
        return cleaned_data


# Quick action forms for modals
class QuickStockMovementForm(forms.Form):
    """Simplified form for quick stock movements"""
    stock_item = forms.ModelChoiceField(
        queryset=StockItem.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control select2'}),
        label="Product"
    )
    movement_type = forms.ChoiceField(
        choices=[
            ('adjustment_in', 'Stock In (Increase)'),
            ('adjustment_out', 'Stock Out (Decrease)'),
            ('transfer_in', 'Transfer In'),
            ('transfer_out', 'Transfer Out'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Movement Type"
    )
    quantity = forms.DecimalField(
        max_digits=12, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
        label="Quantity"
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label="Notes/Reason"
    )

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        if company:
            self.fields['stock_item'].queryset = StockItem.objects.filter(
                company=company, is_active=True
            )


class QuickWarehouseForm(forms.Form):
    """Simplified form for quick warehouse creation"""
    name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Warehouse name'}),
        label="Warehouse Name"
    )
    code = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., KHI-RAW-01'}),
        label="Warehouse Code"
    )
    location = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City or area'}),
        label="Location"
    )
    warehouse_type = forms.ChoiceField(
        choices=Warehouse._meta.get_field('warehouse_type').choices,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Warehouse Type"
    )
