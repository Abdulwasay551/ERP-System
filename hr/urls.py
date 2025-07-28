from django.urls import path
from .views import (
    hr_dashboard, employees_ui, employees_add, employees_edit, employees_delete,
    contractors_ui, contractors_add, contractors_edit, contractors_delete,
    attendance_ui, payroll_ui, leaves_ui, reports_ui
)

urlpatterns = [
    path('dashboard/', hr_dashboard, name='hr_dashboard'),
    path('dashboard-ui/', hr_dashboard, name='hr_dashboard_ui'),
    path('employees-ui/', employees_ui, name='hr_employees_ui'),
    path('employees-add/', employees_add, name='hr_employees_add'),
    path('employees-edit/<int:pk>/', employees_edit, name='hr_employees_edit'),
    path('employees-delete/<int:pk>/', employees_delete, name='hr_employees_delete'),
    path('contractors-ui/', contractors_ui, name='hr_contractors_ui'),
    path('contractors-add/', contractors_add, name='hr_contractors_add'),
    path('contractors-edit/<int:pk>/', contractors_edit, name='hr_contractors_edit'),
    path('contractors-delete/<int:pk>/', contractors_delete, name='hr_contractors_delete'),
    path('attendance-ui/', attendance_ui, name='hr_attendance_ui'),
    path('payroll-ui/', payroll_ui, name='hr_payroll_ui'),
    path('leaves-ui/', leaves_ui, name='hr_leaves_ui'),
    path('reports-ui/', reports_ui, name='hr_reports_ui'),
]