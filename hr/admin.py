from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Employee, Attendance, Leave, Payroll, Payslip, HRReport

@admin.register(Employee)
class EmployeeAdmin(ModelAdmin):
    list_display = ('first_name', 'last_name', 'company', 'email', 'phone', 'position', 'department', 'is_active')
    search_fields = ('first_name', 'last_name', 'email', 'phone', 'position', 'department')
    list_filter = ('company', 'department', 'is_active')

@admin.register(Attendance)
class AttendanceAdmin(ModelAdmin):
    list_display = ('employee', 'date', 'check_in', 'check_out', 'status')
    search_fields = ('employee__first_name', 'employee__last_name', 'status')
    list_filter = ('status',)

@admin.register(Leave)
class LeaveAdmin(ModelAdmin):
    list_display = ('employee', 'leave_type', 'start_date', 'end_date', 'status', 'approved_by')
    search_fields = ('employee__first_name', 'employee__last_name', 'leave_type', 'status')
    list_filter = ('leave_type', 'status')

@admin.register(Payroll)
class PayrollAdmin(ModelAdmin):
    list_display = ('employee', 'period_start', 'period_end', 'basic_salary', 'deductions', 'bonuses', 'net_salary', 'status')
    search_fields = ('employee__first_name', 'employee__last_name', 'status')
    list_filter = ('status',)

@admin.register(Payslip)
class PayslipAdmin(ModelAdmin):
    list_display = ('payroll', 'pdf_file', 'generated_at')
    search_fields = ('payroll__employee__first_name', 'payroll__employee__last_name')

@admin.register(HRReport)
class HRReportAdmin(ModelAdmin):
    list_display = ('report_type', 'company', 'period_start', 'period_end', 'generated_at')
    search_fields = ('report_type',)
    list_filter = ('company', 'report_type')
