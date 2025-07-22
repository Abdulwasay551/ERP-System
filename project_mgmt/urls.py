from django.urls import path
from .views import projects_ui, projects_add, projects_edit, projects_delete

urlpatterns = [
    path('projects-ui/', projects_ui, name='projectmgmt_projects_ui'),
    path('projects-add/', projects_add, name='projectmgmt_projects_add'),
    path('projects-edit/<int:pk>/', projects_edit, name='projectmgmt_projects_edit'),
    path('projects-delete/<int:pk>/', projects_delete, name='projectmgmt_projects_delete'),
] 