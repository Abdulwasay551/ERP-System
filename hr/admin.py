from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import (
    Employee, Contractor, Attendance, Leave, Payroll, Payslip, HRReport,
    Department, Designation, SalaryStructure, ShiftType, LeaveType, 
    EmployeeLeaveBalance, PayrollPeriod, EmployeeLoan, PerformanceAppraisal,
    Training, TrainingEnrollment, ExitInterview
)

@admin.register(Department)
class DepartmentAdmin(ModelAdmin):
    list_display = ('name', 'code', 'company', 'parent_department', 'department_head', 'is_active')
    search_fields = ('name', 'code', 'description')
    list_filter = ('company', 'is_active', 'parent_department')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'company', 'parent_department')
        }),
        ('Management', {
            'fields': ('department_head', 'budget')
        }),
        ('Additional Information', {
            'fields': ('description', 'is_active')
        })
    )

@admin.register(Designation)
class DesignationAdmin(ModelAdmin):
    list_display = ('title', 'level', 'company', 'salary_range_min', 'salary_range_max', 'is_active')
    search_fields = ('title', 'description', 'responsibilities')
    list_filter = ('company', 'level', 'is_active')
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'level', 'company')
        }),
        ('Salary Range', {
            'fields': ('salary_range_min', 'salary_range_max')
        }),
        ('Job Details', {
            'fields': ('description', 'responsibilities', 'requirements'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        })
    )

@admin.register(SalaryStructure)
class SalaryStructureAdmin(ModelAdmin):
    list_display = ('name', 'designation', 'company', 'basic_salary', 'gross_salary', 'is_active')
    search_fields = ('name', 'designation__title')
    list_filter = ('company', 'designation', 'is_active')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'company', 'designation')
        }),
        ('Salary Components', {
            'fields': ('basic_salary', 'house_allowance', 'transport_allowance', 'medical_allowance', 'other_allowances')
        }),
        ('Deductions', {
            'fields': ('provident_fund_rate', 'tax_rate', 'other_deductions')
        }),
        ('Status', {
            'fields': ('is_active',)
        })
    )

@admin.register(Employee)
class EmployeeAdmin(ModelAdmin):
    list_display = ('employee_id', 'first_name', 'last_name', 'company', 'email', 'phone', 'designation', 'department', 'status', 'is_active')
    search_fields = ('employee_id', 'first_name', 'last_name', 'email', 'phone', 'national_id')
    list_filter = ('company', 'department', 'designation', 'employment_type', 'status', 'is_active')
    fieldsets = (
        ('Basic Information', {
            'fields': ('employee_id', 'first_name', 'last_name', 'email', 'phone', 'address', 'company')
        }),
        ('Employment Details', {
            'fields': ('department', 'designation', 'reporting_manager', 'employment_type', 'date_joined', 'status')
        }),
        ('Personal Information', {
            'fields': ('date_of_birth', 'national_id', 'passport_number', 'emergency_contact', 'emergency_phone'),
            'classes': ('collapse',)
        }),
        ('Salary & Benefits', {
            'fields': ('salary_structure', 'current_salary', 'bank_account', 'bank_name'),
            'classes': ('collapse',)
        }),
        ('User & Partner Links', {
            'fields': ('user', 'partner'),
            'classes': ('collapse',)
        }),
        ('Documents', {
            'fields': ('profile_picture', 'cv_document', 'contract_document'),
            'classes': ('collapse',)
        }),
        ('Exit Information', {
            'fields': ('resignation_date', 'termination_date', 'termination_reason'),
            'classes': ('collapse',)
        })
    )

@admin.register(Contractor)
class ContractorAdmin(ModelAdmin):
    list_display = ('contractor_id', 'partner', 'company', 'contract_type', 'hourly_rate', 'contract_amount', 'is_active')
    search_fields = ('contractor_id', 'partner__name', 'skills')
    list_filter = ('company', 'contract_type', 'is_active')
    fieldsets = (
        ('Basic Information', {
            'fields': ('contractor_id', 'partner', 'company')
        }),
        ('Contract Details', {
            'fields': ('contract_type', 'hourly_rate', 'contract_amount', 'contract_start_date', 'contract_end_date')
        }),
        ('Additional Information', {
            'fields': ('skills', 'is_active'),
            'classes': ('collapse',)
        })
    )

@admin.register(ShiftType)
class ShiftTypeAdmin(ModelAdmin):
    list_display = ('name', 'company', 'start_time', 'end_time', 'working_hours', 'is_active')
    search_fields = ('name',)
    list_filter = ('company', 'is_active')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'company')
        }),
        ('Shift Timing', {
            'fields': ('start_time', 'end_time', 'working_hours', 'break_duration', 'grace_period')
        }),
        ('Status', {
            'fields': ('is_active',)
        })
    )

@admin.register(Attendance)
class AttendanceAdmin(ModelAdmin):
    list_display = ('employee', 'date', 'shift_type', 'check_in', 'check_out', 'status', 'working_hours', 'overtime_hours')
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__employee_id')
    list_filter = ('status', 'shift_type', 'date')
    fieldsets = (
        ('Employee & Date', {
            'fields': ('employee', 'date', 'shift_type')
        }),
        ('Timing', {
            'fields': ('check_in', 'check_out', 'break_start', 'break_end')
        }),
        ('Hours & Status', {
            'fields': ('status', 'working_hours', 'overtime_hours', 'location')
        }),
        ('Notes & Approval', {
            'fields': ('notes', 'approved_by'),
            'classes': ('collapse',)
        })
    )

@admin.register(LeaveType)
class LeaveTypeAdmin(ModelAdmin):
    list_display = ('name', 'code', 'company', 'annual_entitlement', 'is_paid', 'requires_approval', 'is_active')
    search_fields = ('name', 'code', 'description')
    list_filter = ('company', 'is_paid', 'requires_approval', 'carry_forward_allowed', 'encashment_allowed', 'is_active')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'company', 'description')
        }),
        ('Entitlement', {
            'fields': ('annual_entitlement', 'carry_forward_allowed', 'max_carry_forward', 'encashment_allowed')
        }),
        ('Approval Process', {
            'fields': ('requires_approval', 'advance_notice_days', 'is_paid')
        }),
        ('Status', {
            'fields': ('is_active',)
        })
    )

@admin.register(EmployeeLeaveBalance)
class EmployeeLeaveBalanceAdmin(ModelAdmin):
    list_display = ('employee', 'leave_type', 'year', 'entitled_days', 'used_days', 'carry_forward_days', 'available_days')
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__employee_id')
    list_filter = ('leave_type', 'year')

@admin.register(Leave)
class LeaveAdmin(ModelAdmin):
    list_display = ('employee', 'leave_type', 'start_date', 'end_date', 'days_requested', 'status', 'approved_by')
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__employee_id', 'reason')
    list_filter = ('leave_type', 'status', 'start_date')
    fieldsets = (
        ('Leave Details', {
            'fields': ('employee', 'leave_type', 'start_date', 'end_date', 'days_requested', 'reason')
        }),
        ('Approval', {
            'fields': ('status', 'approved_by', 'approval_date', 'rejection_reason')
        }),
        ('Additional Information', {
            'fields': ('covering_employee', 'emergency_contact'),
            'classes': ('collapse',)
        })
    )

@admin.register(PayrollPeriod)
class PayrollPeriodAdmin(ModelAdmin):
    list_display = ('name', 'company', 'start_date', 'end_date', 'pay_date', 'status', 'created_by')
    search_fields = ('name',)
    list_filter = ('company', 'status', 'start_date')
    fieldsets = (
        ('Period Information', {
            'fields': ('name', 'company', 'start_date', 'end_date', 'pay_date')
        }),
        ('Status & Creator', {
            'fields': ('status', 'created_by')
        })
    )

@admin.register(Payroll)
class PayrollAdmin(ModelAdmin):
    list_display = ('employee', 'period', 'basic_salary', 'gross_salary', 'total_deductions', 'net_salary', 'status')
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__employee_id')
    list_filter = ('status', 'period', 'salary_account', 'benefits_account', 'liability_account')
    fieldsets = (
        ('Basic Information', {
            'fields': ('employee', 'period', 'status')
        }),
        ('Salary Components', {
            'fields': ('basic_salary', 'house_allowance', 'transport_allowance', 'medical_allowance', 'other_allowances', 'overtime_amount', 'bonus')
        }),
        ('Deductions', {
            'fields': ('provident_fund', 'income_tax', 'loan_deduction', 'advance_deduction', 'other_deductions')
        }),
        ('Totals', {
            'fields': ('gross_salary', 'total_deductions', 'net_salary')
        }),
        ('Working Days & Hours', {
            'fields': ('working_days', 'present_days', 'overtime_hours'),
            'classes': ('collapse',)
        }),
        ('Accounting', {
            'fields': ('salary_account', 'benefits_account', 'liability_account'),
            'classes': ('collapse',)
        }),
        ('Approval', {
            'fields': ('approved_by',),
            'classes': ('collapse',)
        })
    )

@admin.register(Payslip)
class PayslipAdmin(ModelAdmin):
    list_display = ('payroll', 'generated_at', 'generated_by', 'pdf_file')
    search_fields = ('payroll__employee__first_name', 'payroll__employee__last_name', 'payroll__employee__employee_id')
    list_filter = ('generated_at', 'generated_by')

@admin.register(EmployeeLoan)
class EmployeeLoanAdmin(ModelAdmin):
    list_display = ('employee', 'loan_type', 'amount', 'installment_amount', 'paid_installments', 'total_installments', 'balance_amount', 'status')
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__employee_id', 'purpose')
    list_filter = ('loan_type', 'status', 'start_date')
    fieldsets = (
        ('Loan Information', {
            'fields': ('employee', 'loan_type', 'amount', 'interest_rate', 'purpose')
        }),
        ('Repayment', {
            'fields': ('installment_amount', 'total_installments', 'paid_installments', 'balance_amount', 'start_date')
        }),
        ('Status & Approval', {
            'fields': ('status', 'approved_by')
        })
    )

@admin.register(PerformanceAppraisal)
class PerformanceAppraisalAdmin(ModelAdmin):
    list_display = ('employee', 'period_start', 'period_end', 'reviewer', 'self_rating', 'manager_rating', 'final_rating', 'status')
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__employee_id')
    list_filter = ('status', 'final_rating', 'promotion_recommended', 'period_start')
    fieldsets = (
        ('Appraisal Period', {
            'fields': ('employee', 'period_start', 'period_end', 'reviewer', 'status')
        }),
        ('Self Assessment', {
            'fields': ('self_goals_achievement', 'self_strengths', 'self_areas_improvement', 'self_rating'),
            'classes': ('collapse',)
        }),
        ('Manager Assessment', {
            'fields': ('manager_goals_achievement', 'manager_strengths', 'manager_areas_improvement', 'manager_rating', 'manager_comments'),
            'classes': ('collapse',)
        }),
        ('Final Review', {
            'fields': ('final_rating', 'promotion_recommended', 'increment_recommended', 'training_recommendations', 'completed_at')
        })
    )

@admin.register(Training)
class TrainingAdmin(ModelAdmin):
    list_display = ('title', 'company', 'instructor', 'duration_hours', 'start_date', 'end_date', 'is_mandatory', 'is_active')
    search_fields = ('title', 'description', 'instructor')
    list_filter = ('company', 'is_mandatory', 'certificate_issued', 'is_active', 'start_date')
    fieldsets = (
        ('Training Information', {
            'fields': ('title', 'description', 'company', 'instructor')
        }),
        ('Schedule & Capacity', {
            'fields': ('start_date', 'end_date', 'duration_hours', 'location', 'max_participants')
        }),
        ('Settings', {
            'fields': ('cost_per_participant', 'is_mandatory', 'certificate_issued', 'is_active')
        })
    )

@admin.register(TrainingEnrollment)
class TrainingEnrollmentAdmin(ModelAdmin):
    list_display = ('training', 'employee', 'enrollment_date', 'completion_date', 'status', 'score')
    search_fields = ('training__title', 'employee__first_name', 'employee__last_name', 'employee__employee_id')
    list_filter = ('status', 'training', 'enrollment_date')
    fieldsets = (
        ('Enrollment Information', {
            'fields': ('training', 'employee', 'enrollment_date', 'status')
        }),
        ('Completion Details', {
            'fields': ('completion_date', 'score', 'feedback', 'certificate_path'),
            'classes': ('collapse',)
        })
    )

@admin.register(ExitInterview)
class ExitInterviewAdmin(ModelAdmin):
    list_display = ('employee', 'interviewer', 'interview_date', 'job_satisfaction_rating', 'would_recommend_company', 'assets_returned')
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__employee_id', 'reason_for_leaving')
    list_filter = ('interview_date', 'job_satisfaction_rating', 'would_recommend_company', 'assets_returned')
    fieldsets = (
        ('Interview Details', {
            'fields': ('employee', 'interviewer', 'interview_date')
        }),
        ('Feedback', {
            'fields': ('reason_for_leaving', 'job_satisfaction_rating', 'would_recommend_company', 'suggestions')
        }),
        ('Settlement', {
            'fields': ('assets_returned', 'final_settlement_amount')
        })
    )

@admin.register(HRReport)
class HRReportAdmin(ModelAdmin):
    list_display = ('title', 'report_type', 'company', 'period_start', 'period_end', 'generated_by', 'generated_at')
    search_fields = ('title', 'notes')
    list_filter = ('company', 'report_type', 'generated_at')
    fieldsets = (
        ('Report Information', {
            'fields': ('title', 'report_type', 'company')
        }),
        ('Period', {
            'fields': ('period_start', 'period_end')
        }),
        ('Generation Details', {
            'fields': ('generated_by', 'file_path', 'notes')
        })
    )
