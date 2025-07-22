from django.urls import path
from .views import projects_ui

urlpatterns = [
    path('projects-ui/', projects_ui, name='projectmgmt_projects_ui'),
] 