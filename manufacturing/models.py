from django.db import models
from user_auth.models import Company, User
from sales.models import Product
from accounting.models import Account

class BillOfMaterials(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='boms')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='boms')
    name = models.CharField(max_length=255)
    version = models.CharField(max_length=50, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_boms')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    raw_material_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='boms_raw_material')
    wip_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='boms_wip')
    finished_goods_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='boms_finished_goods')
    overhead_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='boms_overhead')

    def __str__(self):
        return f"{self.product.name} BOM {self.version}"

class BillOfMaterialsItem(models.Model):
    bom = models.ForeignKey(BillOfMaterials, on_delete=models.CASCADE, related_name='items')
    component = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='bom_components')
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.component.name} x {self.quantity}"

class WorkOrder(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='work_orders')
    bom = models.ForeignKey(BillOfMaterials, on_delete=models.CASCADE, related_name='work_orders')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='work_orders')
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=50, default='Planned')
    scheduled_start = models.DateField(null=True, blank=True)
    scheduled_end = models.DateField(null=True, blank=True)
    actual_start = models.DateField(null=True, blank=True)
    actual_end = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_work_orders')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='work_orders')

    def __str__(self):
        return f"WO #{self.id} - {self.product.name}"

class ProductionPlan(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='production_plans')
    name = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=50, default='Planned')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_production_plans')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.start_date} - {self.end_date})"
