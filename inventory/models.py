from django.db import models
from user_auth.models import Company, User
from sales.models import Product

class ProductCategory(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='product_categories')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Warehouse(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='warehouses')
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class StockItem(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='stock_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_items')
    category = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_items')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='stock_items')
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    min_stock = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    max_stock = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product.name} @ {self.warehouse.name}"

class StockMovement(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='stock_movements')
    stock_item = models.ForeignKey(StockItem, on_delete=models.CASCADE, related_name='movements')
    from_warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True, related_name='outgoing_movements')
    to_warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True, related_name='incoming_movements')
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    movement_type = models.CharField(max_length=50, choices=[('in', 'Stock In'), ('out', 'Stock Out'), ('transfer', 'Transfer')], default='in')
    reference = models.CharField(max_length=100, blank=True)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_movements')
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.movement_type.title()} {self.quantity} of {self.stock_item.product.name}"

class StockAlert(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='stock_alerts')
    stock_item = models.ForeignKey(StockItem, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=50, choices=[('low', 'Low Stock'), ('high', 'High Stock')], default='low')
    triggered_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.alert_type.title()} for {self.stock_item.product.name} @ {self.stock_item.warehouse.name}"
