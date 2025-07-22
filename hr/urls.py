from django.urls import path
from .views import employees_ui, employees_add, employees_edit, employees_delete

urlpatterns = [
    path('employees-ui/', employees_ui, name='hr_employees_ui'),
    path('employees-add/', employees_add, name='hr_employees_add'),
    path('employees-edit/<int:pk>/', employees_edit, name='hr_employees_edit'),
    path('employees-delete/<int:pk>/', employees_delete, name='hr_employees_delete'),
] 