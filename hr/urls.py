from django.urls import path
from .views import employees_ui

urlpatterns = [
    path('employees-ui/', employees_ui, name='hr_employees_ui'),
] 