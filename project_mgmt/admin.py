from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Project, Task, TimeEntry, ProjectReport

@admin.register(Project)
class ProjectAdmin(ModelAdmin):
    list_display = ('name', 'company', 'start_date', 'end_date', 'status', 'created_by')
    search_fields = ('name', 'description')
    list_filter = ('company', 'status')

@admin.register(Task)
class TaskAdmin(ModelAdmin):
    list_display = ('name', 'project', 'assigned_to', 'status', 'due_date')
    search_fields = ('name', 'description', 'assigned_to__first_name', 'assigned_to__last_name')
    list_filter = ('project', 'status')

@admin.register(TimeEntry)
class TimeEntryAdmin(ModelAdmin):
    list_display = ('task', 'employee', 'date', 'hours')
    search_fields = ('task__name', 'employee__first_name', 'employee__last_name')
    list_filter = ('employee', 'date')

@admin.register(ProjectReport)
class ProjectReportAdmin(ModelAdmin):
    list_display = ('project', 'report_type', 'period_start', 'period_end', 'generated_at')
    search_fields = ('project__name', 'report_type')
    list_filter = ('project', 'report_type')
