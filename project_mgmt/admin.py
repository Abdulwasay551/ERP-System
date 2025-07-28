from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Project, ProjectContractor, Task, TimeEntry, ProjectReport

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
    list_display = ('task', 'employee', 'date', 'hours')
    search_fields = ('task__name', 'employee__first_name', 'employee__last_name')
    list_filter = ('task', 'employee')

@admin.register(ProjectReport)
class ProjectReportAdmin(ModelAdmin):
    list_display = ('project', 'report_type', 'period_start', 'period_end', 'generated_at')
    search_fields = ('project__name', 'report_type')
    list_filter = ('project', 'report_type')
