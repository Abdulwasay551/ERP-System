from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import (
    Project, ProjectContractor, Task, TimeEntry, ProjectReport,
    Milestone, TaskDependency, Subtask, ProjectDocument, ProjectNote,
    ProjectTemplate, ResourceAllocation, ProjectExpense, ProjectTeam,
    ProjectBilling, ProjectRisk, ProjectSettings
)

@admin.register(Project)
class ProjectAdmin(ModelAdmin):
    list_display = ('project_code', 'name', 'client', 'company', 'status', 'start_date', 'end_date', 'budget', 'actual_cost')
    search_fields = ('project_code', 'name', 'client__name', 'description')
    list_filter = ('company', 'status', 'priority', 'client')
    fieldsets = (
        ('Basic Information', {
            'fields': ('project_code', 'name', 'description', 'company', 'client')
        }),
        ('Project Details', {
            'fields': ('start_date', 'end_date', 'budget', 'actual_cost', 'status', 'priority')
        }),
        ('Management', {
            'fields': ('project_manager', 'created_by', 'account'),
            'classes': ('collapse',)
        })
    )

@admin.register(ProjectContractor)
class ProjectContractorAdmin(ModelAdmin):
    list_display = ('project', 'contractor', 'role', 'contract_amount', 'start_date', 'end_date', 'is_active')
    search_fields = ('project__name', 'contractor__name', 'role')
    list_filter = ('project', 'is_active')
    fieldsets = (
        ('Basic Information', {
            'fields': ('project', 'contractor', 'role')
        }),
        ('Contract Details', {
            'fields': ('contract_amount', 'start_date', 'end_date', 'is_active')
        })
    )

@admin.register(Task)
class TaskAdmin(ModelAdmin):
    list_display = ('name', 'project', 'assigned_to', 'status', 'priority', 'estimated_hours', 'actual_hours', 'due_date')
    search_fields = ('name', 'description')
    list_filter = ('project', 'status', 'priority')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'project')
        }),
        ('Assignment', {
            'fields': ('assigned_to_employee', 'assigned_to_contractor')
        }),
        ('Task Details', {
            'fields': ('status', 'priority', 'estimated_hours', 'actual_hours', 'due_date')
        })
    )

    def assigned_to(self, obj):
        """Display who is assigned to the task"""
        return obj.assigned_to
    assigned_to.short_description = 'Assigned To'

@admin.register(TimeEntry)
class TimeEntryAdmin(ModelAdmin):
    list_display = ('task', 'employee', 'date', 'hours', 'is_billable', 'approval_status', 'billable_amount')
    search_fields = ('task__name', 'employee__first_name', 'employee__last_name', 'notes')
    list_filter = ('task', 'employee', 'is_billable', 'approval_status', 'date')
    
    def billable_amount(self, obj):
        return f"${obj.billable_amount:.2f}"
    billable_amount.short_description = 'Billable Amount'

@admin.register(ProjectReport)
class ProjectReportAdmin(ModelAdmin):
    list_display = ('project', 'report_type', 'period_start', 'period_end', 'generated_at')
    search_fields = ('project__name', 'report_type')
    list_filter = ('project', 'report_type')

@admin.register(Milestone)
class MilestoneAdmin(ModelAdmin):
    list_display = ('name', 'project', 'target_date', 'is_completed', 'percentage_complete')
    search_fields = ('name', 'description')
    list_filter = ('project', 'is_completed', 'target_date')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'project')
        }),
        ('Timeline', {
            'fields': ('target_date', 'completion_date', 'is_completed', 'percentage_complete')
        })
    )

@admin.register(TaskDependency)
class TaskDependencyAdmin(ModelAdmin):
    list_display = ('task', 'depends_on', 'dependency_type', 'created_at')
    search_fields = ('task__name', 'depends_on__name')
    list_filter = ('dependency_type', 'created_at')

@admin.register(Subtask)
class SubtaskAdmin(ModelAdmin):
    list_display = ('name', 'parent_task', 'assigned_to', 'status', 'estimated_hours')
    search_fields = ('name', 'description')
    list_filter = ('parent_task', 'status', 'assigned_to_employee')
    
    def assigned_to(self, obj):
        return obj.assigned_to_employee
    assigned_to.short_description = 'Assigned To'

@admin.register(ProjectDocument)
class ProjectDocumentAdmin(ModelAdmin):
    list_display = ('name', 'project', 'uploaded_by', 'created_at', 'document_type')
    search_fields = ('name', 'description')
    list_filter = ('project', 'uploaded_by', 'document_type', 'created_at')

@admin.register(ProjectNote)
class ProjectNoteAdmin(ModelAdmin):
    list_display = ('project', 'title', 'note_type', 'created_by', 'created_at', 'content_preview')
    search_fields = ('title', 'content')
    list_filter = ('project', 'note_type', 'created_by', 'created_at')
    
    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content Preview'

@admin.register(ProjectTemplate)
class ProjectTemplateAdmin(ModelAdmin):
    list_display = ('name', 'created_by', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    list_filter = ('created_by', 'is_active', 'created_at')

@admin.register(ResourceAllocation)
class ResourceAllocationAdmin(ModelAdmin):
    list_display = ('project', 'employee', 'allocation_percentage', 'start_date', 'end_date')
    search_fields = ('project__name', 'employee__first_name', 'employee__last_name')
    list_filter = ('project', 'employee', 'start_date')

@admin.register(ProjectExpense)
class ProjectExpenseAdmin(ModelAdmin):
    list_display = ('project', 'description', 'expense_type', 'amount', 'expense_date', 'is_billable')
    search_fields = ('description', 'notes')
    list_filter = ('project', 'expense_type', 'is_billable', 'expense_date')

@admin.register(ProjectTeam)
class ProjectTeamAdmin(ModelAdmin):
    list_display = ('project', 'employee', 'role', 'joined_date', 'is_active')
    search_fields = ('project__name', 'employee__first_name', 'employee__last_name', 'role')
    list_filter = ('project', 'role', 'is_active', 'joined_date')

@admin.register(ProjectBilling)
class ProjectBillingAdmin(ModelAdmin):
    list_display = ('project', 'billing_period_start', 'billing_period_end', 'total_amount', 'invoice_date', 'payment_status')
    search_fields = ('project__name', 'invoice_number')
    list_filter = ('payment_status', 'invoice_date', 'billing_period_start')

@admin.register(ProjectRisk)
class ProjectRiskAdmin(ModelAdmin):
    list_display = ('project', 'title', 'risk_type', 'probability', 'impact', 'status')
    search_fields = ('title', 'description', 'mitigation_plan')
    list_filter = ('project', 'risk_type', 'probability', 'impact', 'status')

@admin.register(ProjectSettings)
class ProjectSettingsAdmin(ModelAdmin):
    list_display = ('company', 'default_hourly_rate', 'timesheet_approval_required', 'billing_frequency')
    search_fields = ('company__name',)
    list_filter = ('timesheet_approval_required', 'auto_create_invoices', 'billing_frequency')
