from django.urls import path
from .views import (
    project_dashboard, projects_ui, projects_add, projects_edit, projects_delete,
    tasks_ui, timesheets_ui, reports_ui, project_detail, task_add, task_detail, 
    task_edit, task_delete, timesheet_add, timesheet_edit, timesheet_delete,
    api_projects, api_tasks, generate_report
)
from .additional_views import (
    milestones_ui, milestone_add,
    documents_ui, document_add,
    expenses_ui, expense_add,
    risks_ui, risk_add,
    team_ui, team_add,
    billing_ui, billing_add
)

app_name = 'project_mgmt'

urlpatterns = [
    # Dashboard
    path('', project_dashboard, name='dashboard'),
    path('dashboard/', project_dashboard, name='project_dashboard'),
    path('dashboard-ui/', project_dashboard, name='project_dashboard_ui'),
    
    # Projects
    path('projects/', projects_ui, name='projects_ui'),
    path('projects-ui/', projects_ui, name='projects_ui'),
    path('projects/add/', projects_add, name='projects_add'),
    path('projects-add/', projects_add, name='projects_add'),
    path('projects/<int:pk>/', project_detail, name='project_detail'),
    path('projects/edit/<int:pk>/', projects_edit, name='projects_edit'),
    path('projects-edit/<int:pk>/', projects_edit, name='projects_edit'),
    path('projects/delete/<int:pk>/', projects_delete, name='projects_delete'),
    path('projects-delete/<int:pk>/', projects_delete, name='projects_delete'),
    
    # Tasks
    path('tasks/', tasks_ui, name='tasks_ui'),
    path('tasks-ui/', tasks_ui, name='tasks_ui'),
    path('tasks/add/', task_add, name='task_add'),
    path('tasks/<int:pk>/', task_detail, name='task_detail'),
    path('tasks/edit/<int:pk>/', task_edit, name='task_edit'),
    path('tasks/delete/<int:pk>/', task_delete, name='task_delete'),
    
    # Timesheets
    path('timesheets/', timesheets_ui, name='timesheets_ui'),
    path('timesheets-ui/', timesheets_ui, name='timesheets_ui'),
    path('timetracking/', timesheets_ui, name='timesheets_ui'),
    path('timetracking-ui/', timesheets_ui, name='timesheets_ui'),
    path('timetracking/', timesheets_ui, name='timetracking_ui'),
    path('timetracking-ui/', timesheets_ui, name='timetracking_ui'),
    path('timesheets/add/', timesheet_add, name='timesheet_add'),
    path('timesheets/edit/<int:pk>/', timesheet_edit, name='timesheet_edit'),
    path('timesheets/delete/<int:pk>/', timesheet_delete, name='timesheet_delete'),
    
    # Legacy aliases - now pointing to proper views
    path('milestones/', milestones_ui, name='milestones_ui'),
    path('milestones-ui/', milestones_ui, name='milestones_ui'),
    path('milestones/add/', milestone_add, name='milestone_add'),
    
    # Documents
    path('documents/', documents_ui, name='documents_ui'),
    path('documents-ui/', documents_ui, name='documents_ui'),
    path('documents/add/', document_add, name='document_add'),
    
    # Expenses
    path('expenses/', expenses_ui, name='expenses_ui'),
    path('expenses-ui/', expenses_ui, name='expenses_ui'),
    path('expenses/add/', expense_add, name='expense_add'),
    
    # Risks
    path('risks/', risks_ui, name='risks_ui'),
    path('risks-ui/', risks_ui, name='risks_ui'),
    path('risks/add/', risk_add, name='risk_add'),
    
    # Team Management
    path('team/', team_ui, name='team_ui'),
    path('team-ui/', team_ui, name='team_ui'),
    path('team/add/', team_add, name='team_add'),
    
    # Billing
    path('billing/', billing_ui, name='billing_ui'),
    path('billing-ui/', billing_ui, name='billing_ui'),
    path('billing/add/', billing_add, name='billing_add'),
    
    # Resources (legacy alias)
    path('resources/', team_ui, name='resources_ui'),
    path('resources-ui/', team_ui, name='resources_ui'),
    
    # Reports
    path('reports/', reports_ui, name='reports_ui'),
    path('reports-ui/', reports_ui, name='reports_ui'),
    path('reports/generate/', generate_report, name='generate_report'),
    
    # API endpoints
    path('api/projects/', api_projects, name='api_projects'),
    path('api/tasks/', api_tasks, name='api_tasks'),
]