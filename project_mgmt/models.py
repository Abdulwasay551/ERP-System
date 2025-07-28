from django.db import models
from user_auth.models import Company, User
from crm.models import Partner  # Import centralized Partner model
from hr.models import Employee
from accounting.models import Account

# Create your models here.

class Project(models.Model):
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('on_hold', 'On Hold'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='projects')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Link to centralized Partner for client relationship
    client = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name='projects', null=True, blank=True)
    
    # Project details
    project_code = models.CharField(max_length=50, unique=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    budget = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    actual_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='planned')
    priority = models.CharField(max_length=50, default='Medium')
    
    # Management
    project_manager = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_projects')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_projects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='projects')

    def __str__(self):
        return f"{self.project_code} - {self.name}" if self.project_code else self.name

    def save(self, *args, **kwargs):
        # Auto-generate project code if not provided
        if not self.project_code:
            self.project_code = f"PROJ{self.pk or Project.objects.count() + 1:04d}"
        super().save(*args, **kwargs)

class ProjectContractor(models.Model):
    """Link projects to external contractors using centralized Partner"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='contractors')
    contractor = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name='project_contracts')
    role = models.CharField(max_length=255, blank=True, help_text="Role/responsibility in project")
    contract_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.contractor.name} - {self.project.name}"

    def save(self, *args, **kwargs):
        # Ensure partner is marked as vendor/contractor
        if self.contractor:
            self.contractor.is_vendor = True
            self.contractor.save()
        super().save(*args, **kwargs)

class Task(models.Model):
    TASK_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('review', 'Under Review'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Assignment - can be either employee or external contractor
    assigned_to_employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    assigned_to_contractor = models.ForeignKey(Partner, on_delete=models.SET_NULL, null=True, blank=True, related_name='contractor_tasks')
    
    # Task details
    status = models.CharField(max_length=50, choices=TASK_STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=50, default='Medium')
    estimated_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    actual_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.project.name} - {self.name}"

    @property
    def assigned_to(self):
        """Get the assigned person (employee or contractor)"""
        if self.assigned_to_employee:
            return f"Employee: {self.assigned_to_employee}"
        elif self.assigned_to_contractor:
            return f"Contractor: {self.assigned_to_contractor.name}"
        return "Unassigned"

class TimeEntry(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='time_entries')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='time_entries')
    date = models.DateField()
    hours = models.DecimalField(max_digits=5, decimal_places=2)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee} - {self.task} - {self.hours}h"

class ProjectReport(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='reports')
    report_type = models.CharField(max_length=100)
    period_start = models.DateField()
    period_end = models.DateField()
    generated_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.project.name} {self.report_type} ({self.period_start} - {self.period_end})"
