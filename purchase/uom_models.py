# UOM Conversion Models for Purchase Module
# This file extends the purchase models with UOM conversion capabilities

from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from .models import *  # Import existing purchase models

class UnitOfMeasure(models.Model):
    """Master UOM definitions"""
    UOM_TYPE_CHOICES = [
        ('weight', 'Weight'),
        ('volume', 'Volume'), 
        ('length', 'Length'),
        ('area', 'Area'),
        ('quantity', 'Quantity'),
        ('time', 'Time'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='uoms')
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=20)
    uom_type = models.CharField(max_length=50, choices=UOM_TYPE_CHOICES)
    is_base_unit = models.BooleanField(default=False, help_text="Base unit for this UOM type")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['company', 'name']
        ordering = ['uom_type', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.symbol})"

class UOMConversion(models.Model):
    """UOM conversion factors between different units"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='uom_conversions')
    from_uom = models.ForeignKey(UnitOfMeasure, on_delete=models.CASCADE, related_name='conversions_from')
    to_uom = models.ForeignKey(UnitOfMeasure, on_delete=models.CASCADE, related_name='conversions_to')
    conversion_factor = models.DecimalField(
        max_digits=12, 
        decimal_places=6, 
        validators=[MinValueValidator(Decimal('0.000001'))],
        help_text="Multiply by this factor to convert from_uom to to_uom"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['company', 'from_uom', 'to_uom']
    
    def __str__(self):
        return f"1 {self.from_uom.symbol} = {self.conversion_factor} {self.to_uom.symbol}"
    
    def convert(self, quantity):
        """Convert quantity from from_uom to to_uom"""
        return quantity * self.conversion_factor
    
    def reverse_convert(self, quantity):
        """Convert quantity from to_uom to from_uom"""
        return quantity / self.conversion_factor

class ProductUOM(models.Model):
    """Product-specific UOM definitions with conversion rates"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='uoms')
    uom = models.ForeignKey(UnitOfMeasure, on_delete=models.CASCADE)
    is_default = models.BooleanField(default=False, help_text="Default UOM for this product")
    is_purchase_uom = models.BooleanField(default=True, help_text="Can be used for purchasing")
    is_sales_uom = models.BooleanField(default=True, help_text="Can be used for sales")
    conversion_factor = models.DecimalField(
        max_digits=12, 
        decimal_places=6, 
        default=1,
        validators=[MinValueValidator(Decimal('0.000001'))],
        help_text="Conversion factor to base UOM"
    )
    minimum_qty = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['product', 'uom']
    
    def __str__(self):
        return f"{self.product.name} - {self.uom.name}"
    
    def convert_to_base(self, quantity):
        """Convert quantity to base UOM"""
        return quantity * self.conversion_factor
    
    def convert_from_base(self, base_quantity):
        """Convert base quantity to this UOM"""
        return base_quantity / self.conversion_factor

class SupplierProductUOM(models.Model):
    """Supplier-specific UOM and pricing for products"""
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='product_uoms')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='supplier_uoms')
    uom = models.ForeignKey(UnitOfMeasure, on_delete=models.CASCADE)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    minimum_order_qty = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    package_qty = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=1,
        help_text="Quantity of base units in this package (e.g., 10 pieces per packet)"
    )
    lead_time_days = models.IntegerField(default=0)
    is_preferred = models.BooleanField(default=False, help_text="Preferred UOM for this supplier")
    is_active = models.BooleanField(default=True)
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['supplier', 'product', 'uom']
        ordering = ['supplier', 'product', 'is_preferred']
    
    def __str__(self):
        return f"{self.supplier.name} - {self.product.name} ({self.uom.name})"
    
    def get_base_unit_price(self):
        """Calculate price per base unit"""
        if self.package_qty > 0:
            return self.unit_price / self.package_qty
        return self.unit_price
    
    def calculate_total_base_units(self, ordered_qty):
        """Calculate total base units for ordered quantity"""
        return ordered_qty * self.package_qty
