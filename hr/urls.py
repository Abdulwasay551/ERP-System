from django.urls import path
from .views import (
    hr_dashboard, employees_ui, employees_add, employees_edit, employees_delete, employee_detail,
    contractors_ui, contractors_add, contractors_edit, contractors_delete, contractor_detail,
    attendance_ui, attendance_mark, attendance_detail, attendance_form,
    payroll_ui, payroll_generate, payroll_detail, payroll_form,
    leaves_ui, leave_apply, leave_approve, leave_detail, leave_form,
    reports_ui, generate_report,
    departments_ui, departments_add, departments_edit, departments_delete, department_detail, department_form,
    designations_ui, designations_add, designations_edit, designations_delete, designation_detail, designation_form,
    contractor_form, performance_ui, training_ui, recruitment_ui, relations_ui, benefits_ui, policies_ui,
    # New CRUD views
    performance_detail, performance_form, performance_delete,
    training_detail, training_form, training_delete,
    recruitment_detail, recruitment_form, recruitment_delete,
    relations_detail, relations_form, relations_delete,
    benefits_detail, benefits_form, benefits_delete,
    policies_detail, policies_form, policies_delete
)

app_name = 'hr'

urlpatterns = [
    # Dashboard
    path('', hr_dashboard, name='dashboard'),
    path('dashboard/', hr_dashboard, name='dashboard'),
    
    # Employee Management
    path('employees/', employees_ui, name='employees_ui'),
    path('employees/add/', employees_add, name='employees_add'),
    path('employees/form/', employees_add, name='employee_form'),
    path('employees/form/<int:pk>/', employees_add, name='employee_form_edit'),
    path('employees/<int:pk>/edit/', employees_edit, name='employees_edit'),
    path('employees-edit/<int:pk>/', employees_edit, name='employees_edit_alt'),
    path('employees/<int:pk>/delete/', employees_delete, name='employees_delete'),
    path('employees/<int:pk>/', employee_detail, name='employee_detail'),
    
    # Contractor Management
    path('contractors/', contractors_ui, name='contractors_ui'),
    path('contractors/add/', contractors_add, name='contractors_add'),
    path('contractors/<int:pk>/edit/', contractors_edit, name='contractors_edit'),
    path('contractors/<int:pk>/delete/', contractors_delete, name='contractors_delete'),
    path('contractors/<int:pk>/', contractor_detail, name='contractor_detail'),
    path('contractors/form/', contractor_form, name='contractor_form'),
    path('contractors/form/<int:pk>/', contractor_form, name='contractor_form_edit'),
    
    # Department Management
    path('departments/', departments_ui, name='departments_ui'),
    path('departments/add/', departments_add, name='departments_add'),
    path('departments/<int:pk>/edit/', departments_edit, name='departments_edit'),
    path('departments/<int:pk>/delete/', departments_delete, name='departments_delete'),
    path('departments/<int:pk>/', department_detail, name='department_detail'),
    path('departments/form/', department_form, name='department_form'),
    path('departments/form/<int:pk>/', department_form, name='department_form_edit'),
    
    # Designation Management
    path('designations/', designations_ui, name='designations_ui'),
    path('designations/add/', designations_add, name='designations_add'),
    path('designations/<int:pk>/edit/', designations_edit, name='designations_edit'),
    path('designations/<int:pk>/delete/', designations_delete, name='designations_delete'),
    path('designations/<int:pk>/', designation_detail, name='designation_detail'),
    path('designations/form/', designation_form, name='designation_form'),
    path('designations/form/<int:pk>/', designation_form, name='designation_form_edit'),
    
    # Attendance Management
    path('attendance/', attendance_ui, name='attendance_ui'),
    path('attendance/mark/', attendance_mark, name='attendance_mark'),
    path('attendance/<int:pk>/', attendance_detail, name='attendance_detail'),
    path('attendance/form/', attendance_form, name='attendance_form'),
    path('attendance/form/<int:pk>/', attendance_form, name='attendance_form_edit'),
    
    # Leave Management
    path('leaves/', leaves_ui, name='leaves_ui'),
    path('leaves/apply/', leave_apply, name='leave_apply'),
    path('leaves/form/', leave_apply, name='leave_apply_form'),
    path('leaves/form/<int:pk>/', leave_apply, name='leave_apply_edit'),
    path('leaves/<int:pk>/approve/', leave_approve, name='leave_approve'),
    path('leaves/<int:pk>/', leave_detail, name='leave_detail'),
    path('leaves/form/', leave_form, name='leave_form'),
    path('leaves/form/<int:pk>/', leave_form, name='leave_form_edit'),
    
    # Payroll Management
    path('payroll/', payroll_ui, name='payroll_ui'),
    path('payroll/generate/', payroll_generate, name='payroll_generate'),
    path('payroll/form/', payroll_form, name='payroll_form'),
    path('payroll/form/<int:pk>/', payroll_form, name='payroll_form_edit'),
    path('payroll/<int:pk>/', payroll_detail, name='payroll_detail'),
    
    # Reports
    path('reports/', reports_ui, name='reports_ui'),
    path('reports/generate/', generate_report, name='generate_report'),
    
    # Performance Management
    path('performance/', performance_ui, name='performance_ui'),
    path('performance/add/', performance_form, name='performance_add'),
    path('performance/<int:pk>/', performance_detail, name='performance_detail'),
    path('performance/<int:pk>/edit/', performance_form, name='performance_edit'),
    path('performance/<int:pk>/delete/', performance_delete, name='performance_delete'),
    
    # Training Management
    path('training/', training_ui, name='training_ui'),
    path('training/add/', training_form, name='training_add'),
    path('training/<int:pk>/', training_detail, name='training_detail'),
    path('training/<int:pk>/edit/', training_form, name='training_edit'),
    path('training/<int:pk>/delete/', training_delete, name='training_delete'),
    
    # Recruitment Management
    path('recruitment/', recruitment_ui, name='recruitment_ui'),
    path('recruitment/add/', recruitment_form, name='recruitment_add'),
    path('recruitment/<int:pk>/', recruitment_detail, name='recruitment_detail'),
    path('recruitment/<int:pk>/edit/', recruitment_form, name='recruitment_edit'),
    path('recruitment/<int:pk>/delete/', recruitment_delete, name='recruitment_delete'),
    
    # Employee Relations
    path('relations/', relations_ui, name='relations_ui'),
    path('relations/add/', relations_form, name='relations_add'),
    path('relations/<int:pk>/', relations_detail, name='relations_detail'),
    path('relations/<int:pk>/edit/', relations_form, name='relations_edit'),
    path('relations/<int:pk>/delete/', relations_delete, name='relations_delete'),
    
    # Benefits Management
    path('benefits/', benefits_ui, name='benefits_ui'),
    path('benefits/add/', benefits_form, name='benefits_add'),
    path('benefits/<int:pk>/', benefits_detail, name='benefits_detail'),
    path('benefits/<int:pk>/edit/', benefits_form, name='benefits_edit'),
    path('benefits/<int:pk>/delete/', benefits_delete, name='benefits_delete'),
    
    # Policies Management
    path('policies/', policies_ui, name='policies_ui'),
    path('policies/add/', policies_form, name='policies_add'),
    path('policies/<int:pk>/', policies_detail, name='policies_detail'),
    path('policies/<int:pk>/edit/', policies_form, name='policies_edit'),
    path('policies/<int:pk>/delete/', policies_delete, name='policies_delete'),
]