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

    @property
    def total_estimated_hours(self):
        """Calculate total estimated hours for all tasks"""
        return self.tasks.aggregate(total=models.Sum('estimated_hours'))['total'] or 0

    @property
    def total_actual_hours(self):
        """Calculate total actual hours for all tasks"""
        return self.tasks.aggregate(total=models.Sum('actual_hours'))['total'] or 0

    @property
    def completion_percentage(self):
        """Calculate project completion percentage based on tasks"""
        total_tasks = self.tasks.count()
        if total_tasks == 0:
            return 0
        completed_tasks = self.tasks.filter(status='completed').count()
        return round((completed_tasks / total_tasks) * 100, 1)

    @property
    def is_overdue(self):
        """Check if project is overdue"""
        if self.end_date:
            from django.utils import timezone
            return timezone.now().date() > self.end_date and self.status != 'completed'
        return False

    @property
    def total_billable_amount(self):
        """Calculate total billable amount from time entries"""
        total = 0
        for task in self.tasks.all():
            for entry in task.time_entries.filter(is_billable=True):
                total += entry.billable_amount
        return total

    @property
    def profit_margin(self):
        """Calculate profit margin (revenue - costs) / revenue"""
        if self.total_billable_amount > 0:
            profit = self.total_billable_amount - self.actual_cost
            return round((profit / self.total_billable_amount) * 100, 2)
        return 0

    class Meta:
        ordering = ['-created_at']

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

    @property
    def is_overdue(self):
        """Check if task is overdue"""
        if self.due_date:
            from django.utils import timezone
            return timezone.now().date() > self.due_date and self.status != 'completed'
        return False

    @property
    def completion_percentage(self):
        """Calculate task completion percentage based on hours"""
        if self.estimated_hours > 0:
            return min(round((self.actual_hours / self.estimated_hours) * 100, 1), 100)
        return 0 if self.status != 'completed' else 100

    @property
    def can_start(self):
        """Check if task can start (all dependencies completed)"""
        for dependency in self.dependencies.all():
            if dependency.depends_on.status != 'completed':
                return False
        return True

    @property
    def total_subtask_hours(self):
        """Calculate total hours from subtasks"""
        return self.subtasks.aggregate(total=models.Sum('actual_hours'))['total'] or 0

    class Meta:
        ordering = ['due_date', '-created_at']

class Milestone(models.Model):
    """Project milestones for tracking major deliverables"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='milestones')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    target_date = models.DateField()
    completion_date = models.DateField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    percentage_complete = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.project.name} - {self.name}"

    class Meta:
        ordering = ['target_date']

class TaskDependency(models.Model):
    """Task dependencies to manage predecessors"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='dependencies')
    depends_on = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='dependents')
    dependency_type = models.CharField(max_length=50, default='finish_to_start', choices=[
        ('finish_to_start', 'Finish to Start'),
        ('start_to_start', 'Start to Start'),
        ('finish_to_finish', 'Finish to Finish'),
        ('start_to_finish', 'Start to Finish'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.task.name} depends on {self.depends_on.name}"

    class Meta:
        unique_together = ['task', 'depends_on']

class Subtask(models.Model):
    """Subtasks nested under parent tasks"""
    parent_task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='subtasks')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    assigned_to_employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='subtasks')
    status = models.CharField(max_length=50, choices=Task.TASK_STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=50, default='Medium')
    estimated_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    actual_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    due_date = models.DateField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.parent_task.name} > {self.name}"

class ProjectDocument(models.Model):
    """Project documents and file attachments"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='documents')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='project_documents/', null=True, blank=True)
    external_link = models.URLField(blank=True, help_text="Link to external document")
    document_type = models.CharField(max_length=100, choices=[
        ('requirement', 'Requirement'),
        ('design', 'Design Document'),
        ('contract', 'Contract'),
        ('meeting_notes', 'Meeting Notes'),
        ('report', 'Report'),
        ('other', 'Other'),
    ], default='other')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.project.name} - {self.name}"

class ProjectNote(models.Model):
    """Project notes and meeting minutes"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='notes')
    title = models.CharField(max_length=255)
    content = models.TextField()
    note_type = models.CharField(max_length=100, choices=[
        ('meeting', 'Meeting Notes'),
        ('decision', 'Decision Log'),
        ('issue', 'Issue Log'),
        ('general', 'General Note'),
    ], default='general')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.project.name} - {self.title}"

    class Meta:
        ordering = ['-created_at']

class ProjectTemplate(models.Model):
    """Project templates for standardizing project creation"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='project_templates')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    default_budget = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    estimated_duration_days = models.IntegerField(default=30)
    template_tasks = models.JSONField(default=list, help_text="Template tasks structure")
    template_milestones = models.JSONField(default=list, help_text="Template milestones structure")
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class ResourceAllocation(models.Model):
    """Resource allocation for projects"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='resource_allocations')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='project_allocations')
    role = models.CharField(max_length=255, blank=True)
    allocation_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=100.00, help_text="Percentage of time allocated")
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Billing rate per hour")
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_billable = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee} - {self.project.name} ({self.allocation_percentage}%)"

    class Meta:
        unique_together = ['project', 'employee']

class ProjectExpense(models.Model):
    """Project-related expenses for cost tracking"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='expenses')
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    expense_type = models.CharField(max_length=100, choices=[
        ('material', 'Material'),
        ('equipment', 'Equipment'),
        ('travel', 'Travel'),
        ('contractor', 'Contractor'),
        ('software', 'Software/License'),
        ('other', 'Other'),
    ], default='other')
    expense_date = models.DateField()
    is_billable = models.BooleanField(default=True)
    receipt = models.FileField(upload_to='project_receipts/', null=True, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.project.name} - {self.description} (${self.amount})"

class TimeEntry(models.Model):
    """Enhanced time tracking with billable hours"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='time_entries')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='time_entries')
    date = models.DateField()
    hours = models.DecimalField(max_digits=5, decimal_places=2)
    is_billable = models.BooleanField(default=True, help_text="Whether this time is billable to client")
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Rate for this time entry")
    notes = models.TextField(blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_time_entries')
    approval_status = models.CharField(max_length=50, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee} - {self.task} - {self.hours}h"

    @property
    def billable_amount(self):
        """Calculate billable amount for this time entry"""
        if self.is_billable and self.hourly_rate:
            return self.hours * self.hourly_rate
        return 0

    class Meta:
        ordering = ['-date', '-created_at']

class ProjectTeam(models.Model):
    """Project team members and their roles"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='team_members')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='project_teams')
    role = models.CharField(max_length=255, choices=[
        ('project_manager', 'Project Manager'),
        ('team_lead', 'Team Lead'),
        ('developer', 'Developer'),
        ('designer', 'Designer'),
        ('analyst', 'Business Analyst'),
        ('tester', 'Quality Assurance'),
        ('consultant', 'Consultant'),
        ('other', 'Other'),
    ], default='other')
    permissions = models.JSONField(default=dict, help_text="Role-based permissions")
    joined_date = models.DateField(auto_now_add=True)
    left_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee} - {self.project.name} ({self.role})"

    class Meta:
        unique_together = ['project', 'employee']

class ProjectBilling(models.Model):
    """Project billing and invoicing tracking"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='billings')
    billing_period_start = models.DateField()
    billing_period_end = models.DateField()
    total_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    billable_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    expenses_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    invoice_number = models.CharField(max_length=100, blank=True)
    invoice_date = models.DateField(null=True, blank=True)
    payment_status = models.CharField(max_length=50, choices=[
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ], default='draft')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.project.name} - {self.billing_period_start} to {self.billing_period_end}"

    class Meta:
        ordering = ['-billing_period_start']

class ProjectRisk(models.Model):
    """Project risk management"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='risks')
    title = models.CharField(max_length=255)
    description = models.TextField()
    risk_type = models.CharField(max_length=100, choices=[
        ('technical', 'Technical'),
        ('resource', 'Resource'),
        ('schedule', 'Schedule'),
        ('budget', 'Budget'),
        ('external', 'External'),
        ('quality', 'Quality'),
        ('other', 'Other'),
    ], default='other')
    probability = models.CharField(max_length=50, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], default='medium')
    impact = models.CharField(max_length=50, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], default='medium')
    status = models.CharField(max_length=50, choices=[
        ('identified', 'Identified'),
        ('analyzed', 'Analyzed'),
        ('mitigated', 'Mitigated'),
        ('closed', 'Closed'),
    ], default='identified')
    mitigation_plan = models.TextField(blank=True)
    owner = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='owned_risks')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.project.name} - {self.title}"

    @property
    def risk_score(self):
        """Calculate risk score based on probability and impact"""
        score_map = {'low': 1, 'medium': 2, 'high': 3}
        prob_score = score_map.get(self.probability.lower(), 2)
        impact_score = score_map.get(self.impact.lower(), 2)
        return prob_score * impact_score

class ProjectSettings(models.Model):
    """Project-specific settings and configurations"""
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name='project_settings')
    default_hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    timesheet_approval_required = models.BooleanField(default=True)
    auto_create_invoices = models.BooleanField(default=False)
    project_code_prefix = models.CharField(max_length=10, default='PROJ')
    task_stages = models.JSONField(default=list, help_text="Custom task stages for projects")
    notification_settings = models.JSONField(default=dict, help_text="Notification preferences")
    billing_frequency = models.CharField(max_length=50, choices=[
        ('weekly', 'Weekly'),
        ('bi_weekly', 'Bi-weekly'),
        ('monthly', 'Monthly'),
        ('milestone', 'On Milestone'),
        ('project_end', 'Project End'),
    ], default='monthly')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Project Settings - {self.company.name}"

    class Meta:
        verbose_name = "Project Settings"
        verbose_name_plural = "Project Settings"

class ProjectReport(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='reports')
    report_type = models.CharField(max_length=100)
    period_start = models.DateField()
    period_end = models.DateField()
    generated_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.project.name} {self.report_type} ({self.period_start} - {self.period_end})"
