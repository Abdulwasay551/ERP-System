from django.urls import path
from .views import (
    project_dashboard, projects_ui, projects_add, projects_edit, projects_delete,
    tasks_ui, timesheets_ui, reports_ui
)

app_name = 'project_mgmt'

urlpatterns = [
    path('', project_dashboard, name='project_dashboard'),
    path('dashboard/', project_dashboard, name='project_dashboard'),
    path('dashboard-ui/', project_dashboard, name='project_dashboard_ui'),
    path('projects/', projects_ui, name='project_mgmt_projects_ui'),
    path('projects-ui/', projects_ui, name='project_mgmt_projects_ui'),
    path('projects/add/', projects_add, name='project_mgmt_projects_add'),
    path('projects-add/', projects_add, name='project_mgmt_projects_add'),
    path('projects/edit/<int:pk>/', projects_edit, name='project_mgmt_projects_edit'),
    path('projects-edit/<int:pk>/', projects_edit, name='project_mgmt_projects_edit'),
    path('projects/delete/<int:pk>/', projects_delete, name='project_mgmt_projects_delete'),
    path('projects-delete/<int:pk>/', projects_delete, name='project_mgmt_projects_delete'),
    path('tasks/', tasks_ui, name='project_mgmt_tasks_ui'),
    path('tasks-ui/', tasks_ui, name='project_mgmt_tasks_ui'),
    path('milestones/', tasks_ui, name='project_mgmt_milestones_ui'),
    path('milestones-ui/', tasks_ui, name='project_mgmt_milestones_ui'),
    path('resources/', tasks_ui, name='project_mgmt_resources_ui'),
    path('resources-ui/', tasks_ui, name='project_mgmt_resources_ui'),
    path('timetracking/', timesheets_ui, name='project_mgmt_timetracking_ui'),
    path('timetracking-ui/', timesheets_ui, name='project_mgmt_timetracking_ui'),
    path('reports/', reports_ui, name='project_mgmt_reports_ui'),
    path('reports-ui/', reports_ui, name='project_mgmt_reports_ui'),
]