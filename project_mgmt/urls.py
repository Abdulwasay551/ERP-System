from django.urls import path
from .views import (
    projects_ui, projects_add, projects_edit, projects_delete,
    tasks_ui, timesheets_ui, reports_ui
)

urlpatterns = [
    path('projects-ui/', projects_ui, name='projectmgmt_projects_ui'),
    path('projects-add/', projects_add, name='projectmgmt_projects_add'),
    path('projects-edit/<int:pk>/', projects_edit, name='projectmgmt_projects_edit'),
    path('projects-delete/<int:pk>/', projects_delete, name='projectmgmt_projects_delete'),
    path('tasks-ui/', tasks_ui, name='projectmgmt_tasks_ui'),
    path('timesheets-ui/', timesheets_ui, name='projectmgmt_timesheets_ui'),
    path('reports-ui/', reports_ui, name='projectmgmt_reports_ui'),
]