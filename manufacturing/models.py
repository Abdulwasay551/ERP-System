from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.utils import timezone
from user_auth.models import Company, User
from products.models import Product  # Import centralized Product model
from crm.models import Partner  # Import centralized Partner model
from accounting.models import Account
from inventory.models import Warehouse
from sales.models import SalesOrder

class WorkCenter(models.Model):
    """Work centers/stations where manufacturing operations are performed"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='work_centers')
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True, related_name='work_centers')
    
    # Capacity and costing
    capacity_per_hour = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    cost_per_hour = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    setup_time_minutes = models.IntegerField(default=0)
    cleanup_time_minutes = models.IntegerField(default=0)
    
    # Operating schedules
    operating_hours_per_day = models.DecimalField(max_digits=4, decimal_places=2, default=8)
    operating_days_per_week = models.IntegerField(default=5)
    
    # Resource requirements
    requires_operator = models.BooleanField(default=True)
    max_operators = models.IntegerField(default=1)
    requires_quality_check = models.BooleanField(default=False)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    class Meta:
        unique_together = ['company', 'code']


class BillOfMaterials(models.Model):
    """Enhanced Bill of Materials with routing and operations"""
    MANUFACTURING_TYPE_CHOICES = [
        ('make_to_stock', 'Make to Stock'),
        ('make_to_order', 'Make to Order'),
        ('engineer_to_order', 'Engineer to Order'),
        ('assemble_to_order', 'Assemble to Order'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='boms')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='boms')
    name = models.CharField(max_length=255)
    version = models.CharField(max_length=50, default='1.0')
    revision = models.CharField(max_length=50, blank=True)
    manufacturing_type = models.CharField(max_length=20, choices=MANUFACTURING_TYPE_CHOICES, default='make_to_stock')
    
    # Production details
    lot_size = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    lead_time_days = models.IntegerField(default=1)
    scrap_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    
    # Costing
    material_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    labor_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    overhead_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Routing and operations
    routing_required = models.BooleanField(default=False)
    phantom_bom = models.BooleanField(default=False, help_text="Used for intermediate assemblies")
    
    # Quality requirements
    quality_check_required = models.BooleanField(default=False)
    quality_specification = models.TextField(blank=True)
    
    # Status and lifecycle
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    effective_from = models.DateField(null=True, blank=True)
    effective_to = models.DateField(null=True, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_boms')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Accounting integration
    raw_material_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='boms_raw_material')
    wip_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='boms_wip')
    finished_goods_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='boms_finished_goods')
    overhead_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='boms_overhead')

    def calculate_total_cost(self):
        """Calculate total BOM cost including materials, labor, and overhead"""
        material_cost = sum(item.total_cost for item in self.items.all())
        operation_cost = sum(op.total_cost for op in self.operations.all())
        self.material_cost = material_cost
        self.labor_cost = operation_cost
        self.total_cost = material_cost + operation_cost + self.overhead_cost
        return self.total_cost

    def __str__(self):
        return f"{self.product.name} BOM v{self.version}"
    
    class Meta:
        unique_together = ['company', 'product', 'version']
        ordering = ['-is_default', '-version']

class BillOfMaterialsItem(models.Model):
    """Enhanced BOM items with waste tracking and substitutes"""
    bom = models.ForeignKey(BillOfMaterials, on_delete=models.CASCADE, related_name='items')
    component = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='bom_components')
    quantity = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Waste and efficiency
    waste_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    effective_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Flexibility
    is_optional = models.BooleanField(default=False)
    substitute_products = models.ManyToManyField(Product, blank=True, related_name='substitutable_in_boms')
    
    # Sourcing
    preferred_supplier = models.ForeignKey(Partner, on_delete=models.SET_NULL, null=True, blank=True, related_name='preferred_bom_items')
    
    sequence = models.IntegerField(default=1)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Calculate effective quantity including waste
        waste_factor = 1 + (self.waste_percentage / 100)
        self.effective_quantity = self.quantity * waste_factor
        self.total_cost = self.effective_quantity * self.unit_cost
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.component.name} x {self.quantity}"
    
    class Meta:
        ordering = ['sequence', 'component__name']


class BOMOperation(models.Model):
    """Operations/routing for BOMs"""
    bom = models.ForeignKey(BillOfMaterials, on_delete=models.CASCADE, related_name='operations')
    work_center = models.ForeignKey(WorkCenter, on_delete=models.CASCADE, related_name='bom_operations')
    operation_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    sequence = models.IntegerField(default=1)
    
    # Time requirements
    setup_time_minutes = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    run_time_per_unit_minutes = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    cleanup_time_minutes = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    # Resource requirements
    operators_required = models.IntegerField(default=1)
    skill_level_required = models.CharField(max_length=50, blank=True)
    
    # Quality
    quality_check_required = models.BooleanField(default=False)
    quality_specification = models.TextField(blank=True)
    
    # Costing
    cost_per_hour = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Work instructions
    work_instruction = models.TextField(blank=True)
    safety_notes = models.TextField(blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def calculate_total_time(self, quantity=1):
        """Calculate total time for given quantity"""
        return self.setup_time_minutes + (self.run_time_per_unit_minutes * quantity) + self.cleanup_time_minutes

    def __str__(self):
        return f"{self.bom.product.name} - {self.operation_name}"
    
    class Meta:
        ordering = ['sequence']
        unique_together = ['bom', 'sequence']

class WorkOrder(models.Model):
    """Enhanced Work Order with sales integration and detailed tracking"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('planned', 'Planned'),
        ('released', 'Released'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('on_hold', 'On Hold'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='work_orders')
    bom = models.ForeignKey(BillOfMaterials, on_delete=models.CASCADE, related_name='work_orders')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='work_orders')
    
    # Sales integration
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name='work_orders')
    customer_reference = models.CharField(max_length=255, blank=True)
    
    # Production details
    wo_number = models.CharField(max_length=100, unique=True, blank=True)
    quantity_planned = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    quantity_produced = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    quantity_rejected = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    quantity_remaining = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Status and priority
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    
    # Scheduling
    scheduled_start = models.DateTimeField(null=True, blank=True)
    scheduled_end = models.DateTimeField(null=True, blank=True)
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    
    # Warehouse assignments
    source_warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True, related_name='wo_source')
    destination_warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True, related_name='wo_destination')
    
    # Cost tracking
    planned_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    actual_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    material_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    labor_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    overhead_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Automation flags
    auto_consume_materials = models.BooleanField(default=True)
    backflush_costing = models.BooleanField(default=False)
    
    # Quality
    quality_check_required = models.BooleanField(default=False)
    quality_approved = models.BooleanField(default=False)
    quality_notes = models.TextField(blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_work_orders')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_work_orders')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)
    
    # Accounting integration
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='work_orders')

    def save(self, *args, **kwargs):
        if not self.wo_number:
            # Auto-generate WO number
            from django.utils import timezone
            date_str = timezone.now().strftime('%Y%m%d')
            last_wo = WorkOrder.objects.filter(company=self.company, wo_number__startswith=f'WO{date_str}').order_by('-wo_number').first()
            if last_wo:
                last_num = int(last_wo.wo_number[-3:])
                new_num = last_num + 1
            else:
                new_num = 1
            self.wo_number = f'WO{date_str}{new_num:03d}'
        
        self.quantity_remaining = self.quantity_planned - self.quantity_produced
        super().save(*args, **kwargs)

    def start_production(self):
        """Start work order production"""
        if self.status == 'planned':
            self.status = 'in_progress'
            self.actual_start = timezone.now()
            self.save()

    def complete_production(self):
        """Complete work order production"""
        if self.status == 'in_progress':
            self.status = 'completed'
            self.actual_end = timezone.now()
            self.save()

    def get_progress_percentage(self):
        """Calculate production progress percentage"""
        if self.quantity_planned > 0:
            return round((self.quantity_produced / self.quantity_planned) * 100, 2)
        return 0

    def __str__(self):
        return f"{self.wo_number} - {self.product.name}"
    
    class Meta:
        ordering = ['-created_at']

class WorkOrderOperation(models.Model):
    """Operations within a work order"""
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name='operations')
    bom_operation = models.ForeignKey(BOMOperation, on_delete=models.CASCADE, related_name='work_order_operations')
    work_center = models.ForeignKey(WorkCenter, on_delete=models.CASCADE)
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('skipped', 'Skipped'),
    ]
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sequence = models.IntegerField()
    
    # Time tracking
    planned_start = models.DateTimeField(null=True, blank=True)
    planned_end = models.DateTimeField(null=True, blank=True)
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    
    # Resource assignment
    assigned_operators = models.ManyToManyField(User, blank=True, related_name='assigned_operations')
    
    # Production tracking
    quantity_to_produce = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    quantity_produced = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    quantity_rejected = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Cost tracking
    actual_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.work_order.wo_number} - {self.bom_operation.operation_name}"
    
    class Meta:
        ordering = ['sequence']
        unique_together = ['work_order', 'sequence']


class OperationLog(models.Model):
    """Detailed logs of operation execution"""
    work_order_operation = models.ForeignKey(WorkOrderOperation, on_delete=models.CASCADE, related_name='logs')
    work_center = models.ForeignKey(WorkCenter, on_delete=models.CASCADE)
    operator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='operation_logs')
    
    LOG_TYPE_CHOICES = [
        ('start', 'Start'),
        ('pause', 'Pause'),
        ('resume', 'Resume'),
        ('complete', 'Complete'),
        ('quality_check', 'Quality Check'),
        ('downtime', 'Downtime'),
        ('setup', 'Setup'),
        ('cleanup', 'Cleanup'),
    ]
    
    log_type = models.CharField(max_length=20, choices=LOG_TYPE_CHOICES)
    timestamp = models.DateTimeField(default=timezone.now)
    
    # Production data
    quantity_produced = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    quantity_rejected = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Downtime tracking
    downtime_reason = models.CharField(max_length=255, blank=True)
    downtime_category = models.CharField(max_length=100, blank=True)
    
    # Quality data
    quality_passed = models.BooleanField(null=True, blank=True)
    quality_notes = models.TextField(blank=True)
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.operator.get_full_name()} - {self.log_type} - {self.timestamp}"
    
    class Meta:
        ordering = ['-timestamp']


class QualityCheck(models.Model):
    """Quality check records"""
    QUALITY_TYPE_CHOICES = [
        ('incoming', 'Incoming Inspection'),
        ('in_process', 'In-Process'),
        ('final', 'Final Inspection'),
        ('random', 'Random Sampling'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('conditional', 'Conditional Pass'),
    ]
    
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name='quality_checks')
    work_order_operation = models.ForeignKey(WorkOrderOperation, on_delete=models.CASCADE, null=True, blank=True, related_name='quality_checks')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='quality_checks')
    
    quality_type = models.CharField(max_length=20, choices=QUALITY_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Inspection details
    inspector = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quality_inspections')
    inspection_date = models.DateTimeField(default=timezone.now)
    
    # Sample data
    lot_size = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sample_size = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    quantity_passed = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    quantity_failed = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Defect tracking
    defect_description = models.TextField(blank=True)
    corrective_action = models.TextField(blank=True)
    
    # References
    specification = models.TextField(blank=True)
    test_results = models.JSONField(default=dict, blank=True)
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"QC {self.id} - {self.product.name} - {self.status}"
    
    class Meta:
        ordering = ['-inspection_date']


class MaterialConsumption(models.Model):
    """Track material consumption in work orders"""
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name='material_consumptions')
    bom_item = models.ForeignKey(BillOfMaterialsItem, on_delete=models.CASCADE, related_name='consumptions')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='consumptions')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='material_consumptions')
    
    # Consumption details
    planned_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    consumed_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    waste_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Cost tracking
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Tracking
    consumed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='material_consumptions')
    consumed_at = models.DateTimeField(null=True, blank=True)
    
    # Batch/lot tracking
    batch_number = models.CharField(max_length=100, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.total_cost = self.consumed_quantity * self.unit_cost
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.work_order.wo_number} - {self.product.name} x {self.consumed_quantity}"


class MRPPlan(models.Model):
    """Material Requirements Planning"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='mrp_plans')
    name = models.CharField(max_length=255)
    plan_date = models.DateField(default=timezone.now)
    planning_horizon_days = models.IntegerField(default=90)
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('calculating', 'Calculating'),
        ('completed', 'Completed'),
        ('approved', 'Approved'),
        ('executed', 'Executed'),
    ]
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Planning parameters
    include_safety_stock = models.BooleanField(default=True)
    include_reorder_points = models.BooleanField(default=True)
    consider_lead_times = models.BooleanField(default=True)
    
    # Execution tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_mrp_plans')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_mrp_plans')
    
    calculation_start = models.DateTimeField(null=True, blank=True)
    calculation_end = models.DateTimeField(null=True, blank=True)
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"MRP {self.name} - {self.plan_date}"
    
    class Meta:
        ordering = ['-plan_date']


class MRPRequirement(models.Model):
    """Individual material requirements from MRP calculation"""
    mrp_plan = models.ForeignKey(MRPPlan, on_delete=models.CASCADE, related_name='requirements')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='mrp_requirements')
    
    # Requirement details
    required_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    available_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shortage_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Timing
    required_date = models.DateField()
    suggested_order_date = models.DateField(null=True, blank=True)
    
    # Source
    source_type = models.CharField(max_length=20, choices=[
        ('purchase', 'Purchase'),
        ('manufacture', 'Manufacture'),
        ('transfer', 'Transfer'),
    ])
    
    # References
    sales_orders = models.ManyToManyField(SalesOrder, blank=True, related_name='mrp_requirements')
    work_orders = models.ManyToManyField(WorkOrder, blank=True, related_name='mrp_requirements')
    
    # Status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('ordered', 'Ordered'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled'),
    ]
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - Req: {self.required_quantity} on {self.required_date}"
    
    class Meta:
        ordering = ['required_date', 'product__name']


class Subcontractor(models.Model):
    """Subcontractor model that links to centralized Partner for outsourced manufacturing"""
    # Link to centralized Partner
    partner = models.OneToOneField(Partner, on_delete=models.CASCADE, related_name='subcontractor_profile')
    
    # Subcontractor-specific fields
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='subcontractors')
    specialization = models.CharField(max_length=255, blank=True, help_text="Manufacturing specialization")
    capacity = models.CharField(max_length=255, blank=True, help_text="Production capacity")
    quality_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0, help_text="Quality rating 0-10")
    delivery_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0, help_text="Delivery rating 0-10")
    lead_time_days = models.IntegerField(default=0, help_text="Average lead time in days")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Subcontractor: {self.partner.name}"

    def save(self, *args, **kwargs):
        # Ensure partner is marked as vendor/supplier
        if self.partner:
            self.partner.is_vendor = True
            self.partner.save()
        super().save(*args, **kwargs)

class SubcontractWorkOrder(models.Model):
    """Work orders outsourced to subcontractors"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='subcontract_work_orders')
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name='subcontracts')
    subcontractor = models.ForeignKey(Subcontractor, on_delete=models.CASCADE, related_name='work_orders')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    start_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=50, default='Planned')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.total_cost = self.quantity * self.unit_cost
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Subcontract: {self.product.name} to {self.subcontractor.partner.name}"


class ProductionPlan(models.Model):
    """Enhanced Production Planning"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='production_plans')
    name = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()
    
    PLAN_TYPE_CHOICES = [
        ('forecast', 'Forecast Based'),
        ('sales_order', 'Sales Order Based'),
        ('reorder', 'Reorder Point Based'),
        ('custom', 'Custom Plan'),
    ]
    
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPE_CHOICES, default='forecast')
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Planning parameters
    consider_capacity = models.BooleanField(default=True)
    consider_lead_times = models.BooleanField(default=True)
    auto_create_work_orders = models.BooleanField(default=False)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_production_plans')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_production_plans')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.start_date} - {self.end_date})"
    
    class Meta:
        ordering = ['-start_date']


class ProductionPlanItem(models.Model):
    """Items in production plan"""
    production_plan = models.ForeignKey(ProductionPlan, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='production_plan_items')
    
    # Planning quantities
    planned_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    produced_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    remaining_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Scheduling
    planned_start_date = models.DateField()
    planned_end_date = models.DateField()
    actual_start_date = models.DateField(null=True, blank=True)
    actual_end_date = models.DateField(null=True, blank=True)
    
    # Priority and requirements
    priority = models.CharField(max_length=10, choices=[
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ], default='normal')
    
    # References
    sales_orders = models.ManyToManyField(SalesOrder, blank=True, related_name='production_plan_items')
    work_orders = models.ManyToManyField(WorkOrder, blank=True, related_name='production_plan_items')
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.remaining_quantity = self.planned_quantity - self.produced_quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.production_plan.name} - {self.product.name}"
    
    class Meta:
        ordering = ['planned_start_date', 'priority']


class JobCard(models.Model):
    """Job cards/work instructions for work orders"""
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name='job_cards')
    work_center = models.ForeignKey(WorkCenter, on_delete=models.CASCADE, related_name='job_cards')
    operation = models.ForeignKey(BOMOperation, on_delete=models.CASCADE, related_name='job_cards')
    
    card_number = models.CharField(max_length=100, unique=True, blank=True)
    
    # Instructions
    work_instruction = models.TextField(blank=True)
    safety_instructions = models.TextField(blank=True)
    quality_requirements = models.TextField(blank=True)
    tools_required = models.TextField(blank=True)
    
    # Tracking
    issued_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='issued_job_cards')
    issued_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('issued', 'Issued'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Production tracking
    target_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    actual_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    rejected_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.card_number:
            # Auto-generate job card number
            from django.utils import timezone
            date_str = timezone.now().strftime('%Y%m%d')
            last_card = JobCard.objects.filter(card_number__startswith=f'JC{date_str}').order_by('-card_number').first()
            if last_card:
                last_num = int(last_card.card_number[-3:])
                new_num = last_num + 1
            else:
                new_num = 1
            self.card_number = f'JC{date_str}{new_num:03d}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.card_number} - {self.work_order.wo_number}"
    
    class Meta:
        ordering = ['-created_at']


class DemandForecast(models.Model):
    """Demand forecasting for MRP planning"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='demand_forecasts')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='demand_forecasts')
    
    # Forecast details
    forecast_date = models.DateField()
    forecast_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Forecast metadata
    forecast_type = models.CharField(max_length=20, choices=[
        ('manual', 'Manual'),
        ('historical', 'Historical Based'),
        ('seasonal', 'Seasonal'),
        ('trend', 'Trend Based'),
        ('ai_generated', 'AI Generated'),
    ], default='manual')
    
    confidence_level = models.DecimalField(
        max_digits=5, decimal_places=2, default=50,
        help_text="Confidence level percentage (0-100)"
    )
    
    # Planning parameters
    planning_horizon_days = models.IntegerField(default=30)
    is_active = models.BooleanField(default=True)
    
    # Tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_forecasts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Notes and adjustments
    notes = models.TextField(blank=True)
    manual_adjustment = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    final_forecast = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    def save(self, *args, **kwargs):
        # Calculate final forecast with manual adjustments
        self.final_forecast = self.forecast_quantity + self.manual_adjustment
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.product.name} - {self.forecast_date} - {self.final_forecast}"
    
    class Meta:
        unique_together = ['company', 'product', 'forecast_date']
        ordering = ['forecast_date', 'product__name']


class SupplierLeadTime(models.Model):
    """Lead time matrix for supplier-product combinations"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='supplier_lead_times')
    supplier = models.ForeignKey('crm.Partner', on_delete=models.CASCADE, related_name='lead_times')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='supplier_lead_times')
    
    # Lead time details
    lead_time_days = models.IntegerField(default=0, help_text="Average lead time in days")
    min_lead_time_days = models.IntegerField(default=0, help_text="Minimum lead time")
    max_lead_time_days = models.IntegerField(default=0, help_text="Maximum lead time")
    
    # Quality and reliability metrics
    on_time_delivery_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=100,
        help_text="On-time delivery percentage (0-100)"
    )
    
    quality_rating = models.DecimalField(
        max_digits=3, decimal_places=2, default=5,
        help_text="Quality rating (1-10)"
    )
    
    # Pricing and terms
    price_per_unit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    minimum_order_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    
    # Status and validity
    is_preferred = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)
    
    # Tracking
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Performance tracking
    actual_deliveries = models.IntegerField(default=0)
    late_deliveries = models.IntegerField(default=0)
    
    def get_reliability_score(self):
        """Calculate overall reliability score"""
        if self.actual_deliveries == 0:
            return 0
        
        delivery_score = self.on_time_delivery_rate / 100
        quality_score = self.quality_rating / 10
        
        # Weighted average: 60% delivery, 40% quality
        return (delivery_score * 0.6 + quality_score * 0.4) * 100
    
    def __str__(self):
        return f"{self.supplier.name} - {self.product.name} - {self.lead_time_days} days"
    
    class Meta:
        unique_together = ['company', 'supplier', 'product']
        ordering = ['supplier__name', 'product__name']


class MRPRunLog(models.Model):
    """Log of MRP runs for audit and tracking"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='mrp_run_logs')
    mrp_plan = models.ForeignKey(MRPPlan, on_delete=models.CASCADE, related_name='run_logs')
    
    # Run details
    run_timestamp = models.DateTimeField(default=timezone.now)
    trigger_source = models.CharField(max_length=20, choices=[
        ('manual', 'Manual'),
        ('scheduled', 'Scheduled'),
        ('auto', 'Automatic'),
        ('api', 'API'),
    ], default='manual')
    
    # Execution details
    execution_time_seconds = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    products_processed = models.IntegerField(default=0)
    requirements_generated = models.IntegerField(default=0)
    purchase_requests_created = models.IntegerField(default=0)
    
    # Status and results
    status = models.CharField(max_length=20, choices=[
        ('success', 'Success'),
        ('error', 'Error'),
        ('partial', 'Partial Success'),
        ('cancelled', 'Cancelled'),
    ], default='success')
    
    error_message = models.TextField(blank=True)
    warnings = models.TextField(blank=True)
    
    # Configuration snapshot
    configuration_snapshot = models.JSONField(default=dict, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"MRP Run - {self.run_timestamp} - {self.status}"
    
    class Meta:
        ordering = ['-run_timestamp']


class ReorderRule(models.Model):
    """Reorder rules and policies for inventory planning"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='reorder_rules')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reorder_rules')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='reorder_rules')
    
    # Reorder logic
    reorder_method = models.CharField(max_length=20, choices=[
        ('min_max', 'Min-Max'),
        ('reorder_point', 'Reorder Point'),
        ('lot_for_lot', 'Lot for Lot'),
        ('fixed_quantity', 'Fixed Quantity'),
        ('period_of_supply', 'Period of Supply'),
    ], default='reorder_point')
    
    # Quantities
    minimum_stock = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    maximum_stock = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reorder_point = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    safety_stock = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    economic_order_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Lead time and demand
    lead_time_days = models.IntegerField(default=0)
    average_daily_demand = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    demand_variability = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Auto-execution settings
    auto_create_purchase_request = models.BooleanField(default=False)
    auto_create_work_order = models.BooleanField(default=False)
    
    # Status
    is_active = models.BooleanField(default=True)
    last_triggered = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def calculate_reorder_point(self):
        """Calculate reorder point based on lead time and demand"""
        reorder_point = (self.average_daily_demand * self.lead_time_days) + self.safety_stock
        return max(reorder_point, self.minimum_stock)
    
    def should_reorder(self, current_stock):
        """Check if reorder is needed based on current stock"""
        if self.reorder_method == 'reorder_point':
            return current_stock <= self.reorder_point
        elif self.reorder_method == 'min_max':
            return current_stock <= self.minimum_stock
        return False
    
    def calculate_order_quantity(self, current_stock):
        """Calculate how much to order"""
        if self.reorder_method == 'min_max':
            return self.maximum_stock - current_stock
        elif self.reorder_method == 'fixed_quantity':
            return self.economic_order_quantity
        elif self.reorder_method == 'lot_for_lot':
            # Calculate based on future demand
            return self.average_daily_demand * self.lead_time_days
        else:
            return self.economic_order_quantity
    
    def __str__(self):
        return f"{self.product.name} - {self.warehouse.name} - {self.reorder_method}"
    
    class Meta:
        unique_together = ['company', 'product', 'warehouse']
        ordering = ['product__name', 'warehouse__name']


class CapacityPlan(models.Model):
    """Work center capacity planning"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='capacity_plans')
    work_center = models.ForeignKey(WorkCenter, on_delete=models.CASCADE, related_name='capacity_plans')
    
    # Planning period
    plan_date = models.DateField()
    planning_horizon_days = models.IntegerField(default=30)
    
    # Capacity details
    available_hours = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    planned_hours = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    actual_hours = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Utilization metrics
    utilization_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    efficiency_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Constraints and issues
    is_overloaded = models.BooleanField(default=False)
    capacity_issues = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def calculate_utilization(self):
        """Calculate capacity utilization"""
        if self.available_hours > 0:
            self.utilization_percentage = (self.planned_hours / self.available_hours) * 100
            self.is_overloaded = self.utilization_percentage > 100
        else:
            self.utilization_percentage = 0
            self.is_overloaded = False
    
    def __str__(self):
        return f"{self.work_center.name} - {self.plan_date} - {self.utilization_percentage}%"
    
    class Meta:
        unique_together = ['company', 'work_center', 'plan_date']
        ordering = ['plan_date', 'work_center__name']
