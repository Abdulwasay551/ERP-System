from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import datetime, timedelta, date
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db import transaction

from .models import (
    Employee, Contractor, Attendance, Leave, Payroll, Payslip, HRReport,
    Department, Designation, SalaryStructure, ShiftType, LeaveType, 
    EmployeeLeaveBalance, PayrollPeriod, PerformanceAppraisal, Training,
    TrainingEnrollment, JobVacancy, JobApplication, EmployeeRelation,
    EmployeeBenefit, EmployeeBenefitEnrollment, HRPolicy
)
from crm.models import Partner

# Create your views here.

@login_required
def hr_dashboard(request):
    """HR module dashboard with key metrics and quick access"""
    company = request.user.company
    
    # Key metrics
    total_employees = Employee.objects.filter(company=company, is_active=True).count()
    total_contractors = Contractor.objects.filter(company=company, is_active=True).count()
    new_employees_this_month = Employee.objects.filter(
        company=company, 
        date_joined__gte=timezone.now().replace(day=1),
        date_joined__lte=timezone.now()
    ).count()
    
    # Present today (employees who have checked in today)
    today = date.today()
    present_today = Attendance.objects.filter(
        employee__company=company,
        date=today,
        status__in=['present', 'late']
    ).count()
    
    # On leave today
    on_leave_today = Leave.objects.filter(
        employee__company=company,
        status='approved',
        start_date__lte=today,
        end_date__gte=today
    ).count()
    
    # Department breakdown
    departments = Employee.objects.filter(
        company=company, 
        is_active=True
    ).values(
        'department__name'
    ).annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    # Format department data for template
    departments_formatted = []
    for dept in departments:
        departments_formatted.append({
            'department': dept['department__name'] or 'Unassigned',
            'count': dept['count']
        })
    
    # Recent employees
    recent_employees = Employee.objects.filter(
        company=company
    ).select_related('department', 'designation').order_by('-date_joined')[:5]
    
    # Recent contractors
    recent_contractors = Contractor.objects.filter(
        company=company
    ).select_related('partner').order_by('-created_at')[:5]
    
    # Pending leave requests
    pending_leaves = Leave.objects.filter(
        employee__company=company,
        status='pending'
    ).count()
    
    context = {
        'total_employees': total_employees,
        'total_contractors': total_contractors,
        'new_employees_this_month': new_employees_this_month,
        'present_today': present_today,
        'on_leave_today': on_leave_today,
        'departments': departments_formatted,
        'recent_employees': recent_employees,
        'recent_contractors': recent_contractors,
        'pending_leaves': pending_leaves,
    }
    return render(request, 'hr/dashboard.html', context)

@login_required
def employees_ui(request):
    """Employee management interface"""
    company = request.user.company
    
    # Get search and filter parameters
    search = request.GET.get('search', '')
    department_filter = request.GET.get('department', '')
    status_filter = request.GET.get('status', '')
    
    # Base queryset
    employees = Employee.objects.filter(company=company).select_related(
        'department', 'designation', 'reporting_manager'
    )
    
    # Apply filters
    if search:
        employees = employees.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(employee_id__icontains=search) |
            Q(email__icontains=search)
        )
    
    if department_filter:
        employees = employees.filter(department_id=department_filter)
    
    if status_filter:
        employees = employees.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(employees.order_by('-created_at'), 25)
    page_number = request.GET.get('page')
    employees_page = paginator.get_page(page_number)
    
    # Get departments for filter dropdown
    departments = Department.objects.filter(company=company, is_active=True)
    
    context = {
        'employees': employees_page,
        'departments': departments,
        'search': search,
        'department_filter': department_filter,
        'status_filter': status_filter,
        'employee_statuses': Employee.STATUS_CHOICES,
    }
    return render(request, 'hr/employees-ui.html', context)

@login_required
def employees_add(request, pk=None):
    """Add new employee or edit existing employee"""
    employee = None
    if pk:
        employee = get_object_or_404(Employee, pk=pk, company=request.user.company)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Basic information
                first_name = request.POST.get('first_name')
                last_name = request.POST.get('last_name')
                email = request.POST.get('email')
                phone = request.POST.get('phone', '')
                address = request.POST.get('address', '')
                
                # Employment details
                department_id = request.POST.get('department')
                designation_id = request.POST.get('designation')
                reporting_manager_id = request.POST.get('reporting_manager')
                employment_type = request.POST.get('employment_type', 'full_time')
                date_joined = request.POST.get('date_joined')
                current_salary = request.POST.get('current_salary', 0)
                status = request.POST.get('status', 'active')
                
                # Personal details
                date_of_birth = request.POST.get('date_of_birth')
                national_id = request.POST.get('national_id', '')
                passport_number = request.POST.get('passport_number', '')
                emergency_contact = request.POST.get('emergency_contact', '')
                emergency_phone = request.POST.get('emergency_phone', '')
                
                # Bank details
                bank_account = request.POST.get('bank_account', '')
                bank_name = request.POST.get('bank_name', '')
                
                # Validation
                if not first_name or not last_name or not email:
                    return JsonResponse({
                        'success': False, 
                        'error': 'First name, last name, and email are required.'
                    }, status=400)
                
                # Prepare employee data
                employee_data = {
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': email,
                    'phone': phone,
                    'address': address,
                    'employment_type': employment_type,
                    'current_salary': float(current_salary) if current_salary else 0,
                    'status': status,
                    'national_id': national_id,
                    'passport_number': passport_number,
                    'emergency_contact': emergency_contact,
                    'emergency_phone': emergency_phone,
                    'bank_account': bank_account,
                    'bank_name': bank_name,
                }
                
                if department_id:
                    employee_data['department_id'] = department_id
                
                if designation_id:
                    employee_data['designation_id'] = designation_id
                
                if reporting_manager_id:
                    employee_data['reporting_manager_id'] = reporting_manager_id
                    
                if date_joined:
                    employee_data['date_joined'] = date_joined
                    
                if date_of_birth:
                    employee_data['date_of_birth'] = date_of_birth
                
                if employee:
                    # Update existing employee
                    for key, value in employee_data.items():
                        setattr(employee, key, value)
                    employee.save()
                    action = 'updated'
                else:
                    # Create new employee
                    employee_data['company'] = request.user.company
                    employee = Employee.objects.create(**employee_data)
                    action = 'created'
                
                # Handle file uploads if present
                if request.FILES.get('profile_picture'):
                    employee.profile_picture = request.FILES['profile_picture']
                    employee.save()
                
                if request.FILES.get('cv_document'):
                    employee.cv_document = request.FILES['cv_document']
                    employee.save()
                
                if request.FILES.get('contract_document'):
                    employee.contract_document = request.FILES['contract_document']
                    employee.save()
                
                return JsonResponse({
                    'success': True,
                    'message': f'Employee {action} successfully',
                    'employee': {
                        'id': employee.id,
                        'employee_id': employee.employee_id,
                        'first_name': employee.first_name,
                        'last_name': employee.last_name,
                        'email': employee.email,
                        'department': employee.department.name if employee.department else '',
                        'designation': employee.designation.title if employee.designation else '',
                    }
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error {action if "action" in locals() else "creating"} employee: {str(e)}'
            }, status=500)
    
    else:
        # GET request - show the form
        departments = Department.objects.filter(company=request.user.company, is_active=True)
        designations = Designation.objects.filter(company=request.user.company, is_active=True)
        managers = Employee.objects.filter(company=request.user.company, is_active=True)
        
        # Exclude current employee from managers list if editing
        if employee:
            managers = managers.exclude(id=employee.id)
        
        context = {
            'employee': employee,
            'departments': departments,
            'designations': designations,
            'managers': managers,
            'employment_types': Employee.EMPLOYMENT_TYPE_CHOICES,
            'status_choices': Employee.STATUS_CHOICES,
        }
        return render(request, 'hr/employee_form.html', context)

@login_required
@require_POST
def employees_edit(request, pk):
    """Edit existing employee"""
    try:
        employee = get_object_or_404(Employee, pk=pk, company=request.user.company)
        
        with transaction.atomic():
            # Basic information
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            phone = request.POST.get('phone', '')
            
            # Employment details
            department_id = request.POST.get('department')
            designation_id = request.POST.get('designation')
            employment_type = request.POST.get('employment_type', employee.employment_type)
            current_salary = request.POST.get('current_salary', employee.current_salary)
            status = request.POST.get('status', employee.status)
            
            # Validation
            if not first_name or not last_name or not email:
                return JsonResponse({
                    'success': False, 
                    'error': 'First name, last name, and email are required.'
                }, status=400)
            
            # Update employee
            employee.first_name = first_name
            employee.last_name = last_name
            employee.email = email
            employee.phone = phone
            employee.employment_type = employment_type
            employee.current_salary = float(current_salary) if current_salary else 0
            employee.status = status
            
            if department_id:
                employee.department_id = department_id
            else:
                employee.department = None
                
            if designation_id:
                employee.designation_id = designation_id
            else:
                employee.designation = None
            
            employee.save()
            
            return JsonResponse({
                'success': True,
                'employee': {
                    'id': employee.id,
                    'employee_id': employee.employee_id,
                    'first_name': employee.first_name,
                    'last_name': employee.last_name,
                    'email': employee.email,
                    'phone': employee.phone,
                    'department': employee.department.name if employee.department else '',
                    'designation': employee.designation.title if employee.designation else '',
                    'status': employee.status,
                }
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error updating employee: {str(e)}'
        }, status=500)

@login_required
@require_POST
def employees_delete(request, pk):
    """Delete employee (soft delete by marking as inactive)"""
    try:
        employee = get_object_or_404(Employee, pk=pk, company=request.user.company)
        employee.is_active = False
        employee.status = 'inactive'
        employee.save()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error deleting employee: {str(e)}'
        }, status=500)

@login_required
def employee_detail(request, pk):
    """Employee detail view"""
    employee = get_object_or_404(Employee, pk=pk, company=request.user.company)
    
    # Get recent attendance
    recent_attendance = Attendance.objects.filter(
        employee=employee
    ).order_by('-date')[:10]
    
    # Get leave balance
    current_year = timezone.now().year
    leave_balances = EmployeeLeaveBalance.objects.filter(
        employee=employee, 
        year=current_year
    ).select_related('leave_type')
    
    # Get recent leaves
    recent_leaves = Leave.objects.filter(
        employee=employee
    ).order_by('-created_at')[:5]
    
    # Get recent payrolls
    recent_payrolls = Payroll.objects.filter(
        employee=employee
    ).order_by('-created_at')[:5]
    
    context = {
        'employee': employee,
        'recent_attendance': recent_attendance,
        'leave_balances': leave_balances,
        'recent_leaves': recent_leaves,
        'recent_payrolls': recent_payrolls,
    }
    return render(request, 'hr/employee_detail.html', context)

@login_required
def attendance_ui(request):
    """Attendance management interface"""
    company = request.user.company
    today = date.today()
    
    # Get filter parameters
    date_filter = request.GET.get('date', today.strftime('%Y-%m-%d'))
    employee_filter = request.GET.get('employee', '')
    
    try:
        filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
    except ValueError:
        filter_date = today
    
    # Get attendance records
    attendances = Attendance.objects.filter(
        employee__company=company,
        date=filter_date
    ).select_related('employee', 'shift_type').order_by('employee__first_name')
    
    if employee_filter:
        attendances = attendances.filter(employee_id=employee_filter)
    
    # Get employees for filter
    employees = Employee.objects.filter(company=company, is_active=True).order_by('first_name')
    
    # Get employees without attendance for today
    employees_with_attendance = attendances.values_list('employee_id', flat=True)
    employees_without_attendance = employees.exclude(id__in=employees_with_attendance)
    
    context = {
        'attendances': attendances,
        'employees': employees,
        'employees_without_attendance': employees_without_attendance,
        'date_filter': date_filter,
        'employee_filter': employee_filter,
        'today': today,
        'filter_date': filter_date,
    }
    return render(request, 'hr/attendance-ui.html', context)

@login_required
@require_POST
def attendance_mark(request):
    """Mark attendance for an employee"""
    try:
        employee_id = request.POST.get('employee_id')
        date_str = request.POST.get('date')
        status = request.POST.get('status', 'present')
        check_in = request.POST.get('check_in')
        check_out = request.POST.get('check_out')
        notes = request.POST.get('notes', '')
        
        if not employee_id or not date_str:
            return JsonResponse({
                'success': False,
                'error': 'Employee and date are required.'
            }, status=400)
        
        employee = get_object_or_404(Employee, pk=employee_id, company=request.user.company)
        attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Check if attendance already exists
        attendance, created = Attendance.objects.get_or_create(
            employee=employee,
            date=attendance_date,
            defaults={
                'status': status,
                'notes': notes,
                'check_in': check_in if check_in else None,
                'check_out': check_out if check_out else None,
            }
        )
        
        if not created:
            # Update existing attendance
            attendance.status = status
            attendance.notes = notes
            if check_in:
                attendance.check_in = check_in
            if check_out:
                attendance.check_out = check_out
            attendance.save()
        
        # Calculate working hours if both check_in and check_out are provided
        if attendance.check_in and attendance.check_out:
            attendance.calculate_working_hours()
            attendance.save()
        
        return JsonResponse({
            'success': True,
            'attendance': {
                'id': attendance.id,
                'employee': f"{employee.first_name} {employee.last_name}",
                'date': attendance.date.strftime('%Y-%m-%d'),
                'status': attendance.status,
                'check_in': attendance.check_in.strftime('%H:%M') if attendance.check_in else '',
                'check_out': attendance.check_out.strftime('%H:%M') if attendance.check_out else '',
                'working_hours': float(attendance.working_hours),
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error marking attendance: {str(e)}'
        }, status=500)

@login_required
def payroll_ui(request):
    """Payroll management interface"""
    company = request.user.company
    
    # Get filter parameters
    period_filter = request.GET.get('period', '')
    status_filter = request.GET.get('status', '')
    
    # Get payroll periods
    payroll_periods = PayrollPeriod.objects.filter(company=company).order_by('-created_at')
    
    # Base queryset for payrolls
    payrolls = Payroll.objects.filter(
        employee__company=company
    ).select_related('employee', 'period').order_by('-created_at')
    
    # Apply filters
    if period_filter:
        payrolls = payrolls.filter(period_id=period_filter)
    if status_filter:
        payrolls = payrolls.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(payrolls, 20)
    page_number = request.GET.get('page')
    payrolls_page = paginator.get_page(page_number)
    
    # Summary statistics
    total_payroll = payrolls.aggregate(
        total_gross=Sum('gross_salary'),
        total_deductions=Sum('total_deductions'),
        total_net=Sum('net_salary')
    )
    
    context = {
        'payrolls': payrolls_page,
        'payroll_periods': payroll_periods,
        'period_filter': period_filter,
        'status_filter': status_filter,
        'payroll_statuses': [('draft', 'Draft'), ('approved', 'Approved'), ('paid', 'Paid')],
        'total_payroll': total_payroll,
    }
    return render(request, 'hr/payroll-ui.html', context)

@login_required
@require_POST
def payroll_generate(request):
    """Generate payroll for a period"""
    try:
        period_id = request.POST.get('period_id')
        
        if not period_id:
            return JsonResponse({
                'success': False,
                'error': 'Payroll period is required.'
            }, status=400)
        
        period = get_object_or_404(PayrollPeriod, pk=period_id, company=request.user.company)
        
        # Get active employees
        employees = Employee.objects.filter(company=request.user.company, is_active=True)
        
        generated_count = 0
        
        with transaction.atomic():
            for employee in employees:
                # Check if payroll already exists for this employee and period
                if Payroll.objects.filter(employee=employee, period=period).exists():
                    continue
                
                # Calculate basic salary from salary structure or current salary
                basic_salary = employee.current_salary
                if employee.salary_structure:
                    basic_salary = employee.salary_structure.basic_salary
                
                # Create payroll record
                payroll = Payroll.objects.create(
                    employee=employee,
                    period=period,
                    basic_salary=basic_salary,
                    house_allowance=employee.salary_structure.house_allowance if employee.salary_structure else 0,
                    transport_allowance=employee.salary_structure.transport_allowance if employee.salary_structure else 0,
                    medical_allowance=employee.salary_structure.medical_allowance if employee.salary_structure else 0,
                    other_allowances=employee.salary_structure.other_allowances if employee.salary_structure else 0,
                    provident_fund=basic_salary * (employee.salary_structure.provident_fund_rate / 100) if employee.salary_structure else 0,
                    income_tax=basic_salary * (employee.salary_structure.tax_rate / 100) if employee.salary_structure else 0,
                    other_deductions=employee.salary_structure.other_deductions if employee.salary_structure else 0,
                    working_days=22,  # Default working days
                    present_days=22,  # Should be calculated from attendance
                )
                
                # Calculate totals
                payroll.calculate_totals()
                payroll.save()
                
                generated_count += 1
        
        return JsonResponse({
            'success': True,
            'message': f'Payroll generated for {generated_count} employees.',
            'generated_count': generated_count
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error generating payroll: {str(e)}'
        }, status=500)

@login_required
def payroll_form(request, pk=None):
    """Create or edit payroll record"""
    payroll = None
    if pk:
        payroll = get_object_or_404(Payroll, pk=pk, employee__company=request.user.company)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                employee_id = request.POST.get('employee_id')
                period_id = request.POST.get('period_id')
                
                # Salary components
                basic_salary = request.POST.get('basic_salary', 0)
                house_allowance = request.POST.get('house_allowance', 0)
                transport_allowance = request.POST.get('transport_allowance', 0)
                medical_allowance = request.POST.get('medical_allowance', 0)
                other_allowances = request.POST.get('other_allowances', 0)
                
                # Deductions
                provident_fund = request.POST.get('provident_fund', 0)
                income_tax = request.POST.get('income_tax', 0)
                other_deductions = request.POST.get('other_deductions', 0)
                
                # Attendance
                working_days = request.POST.get('working_days', 22)
                present_days = request.POST.get('present_days', 22)
                overtime_hours = request.POST.get('overtime_hours', 0)
                overtime_amount = float(overtime_hours) * float(request.POST.get('overtime_rate', 0)) if overtime_hours else 0
                
                if not employee_id or not period_id:
                    return JsonResponse({
                        'success': False,
                        'error': 'Employee and payroll period are required.'
                    }, status=400)
                
                employee = get_object_or_404(Employee, pk=employee_id, company=request.user.company)
                period = get_object_or_404(PayrollPeriod, pk=period_id, company=request.user.company)
                
                payroll_data = {
                    'employee': employee,
                    'period': period,
                    'basic_salary': float(basic_salary),
                    'house_allowance': float(house_allowance),
                    'transport_allowance': float(transport_allowance),
                    'medical_allowance': float(medical_allowance),
                    'other_allowances': float(other_allowances),
                    'provident_fund': float(provident_fund),
                    'income_tax': float(income_tax),
                    'other_deductions': float(other_deductions),
                    'working_days': int(working_days),
                    'present_days': int(present_days),
                    'overtime_hours': float(overtime_hours),
                    'overtime_amount': overtime_amount,
                }
                
                if payroll:
                    # Update existing payroll
                    for key, value in payroll_data.items():
                        setattr(payroll, key, value)
                    payroll.calculate_totals()
                    payroll.save()
                    action = 'updated'
                else:
                    # Create new payroll
                    payroll = Payroll.objects.create(**payroll_data)
                    payroll.calculate_totals()
                    payroll.save()
                    action = 'created'
                
                return JsonResponse({
                    'success': True,
                    'message': f'Payroll {action} successfully',
                    'payroll': {
                        'id': payroll.id,
                        'employee': f"{employee.first_name} {employee.last_name}",
                        'period': str(period),
                        'gross_salary': float(payroll.gross_salary),
                        'net_salary': float(payroll.net_salary),
                    }
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error processing payroll: {str(e)}'
            }, status=500)
    
    else:
        # GET request - show form
        employees = Employee.objects.filter(company=request.user.company, is_active=True)
        payroll_periods = PayrollPeriod.objects.filter(company=request.user.company)
        
        context = {
            'payroll': payroll,
            'employees': employees,
            'payroll_periods': payroll_periods,
        }
        return render(request, 'hr/payroll_form.html', context)

@login_required
def leaves_ui(request):
    """Leave management interface"""
    company = request.user.company
    
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    employee_filter = request.GET.get('employee', '')
    leave_type_filter = request.GET.get('leave_type', '')
    
    # Base queryset
    leaves = Leave.objects.filter(
        employee__company=company
    ).select_related('employee', 'leave_type', 'approved_by').order_by('-created_at')
    
    # Apply filters
    if status_filter:
        leaves = leaves.filter(status=status_filter)
    if employee_filter:
        leaves = leaves.filter(employee_id=employee_filter)
    if leave_type_filter:
        leaves = leaves.filter(leave_type_id=leave_type_filter)
    
    # Pagination
    paginator = Paginator(leaves, 20)
    page_number = request.GET.get('page')
    leaves_page = paginator.get_page(page_number)
    
    # Get filter options
    employees = Employee.objects.filter(company=company, is_active=True).order_by('first_name')
    leave_types = LeaveType.objects.filter(company=company, is_active=True)
    
    # Pending leaves for approval
    pending_leaves = Leave.objects.filter(
        employee__company=company,
        status='pending'
    ).select_related('employee', 'leave_type')[:5]
    
    context = {
        'leaves': leaves_page,
        'employees': employees,
        'leave_types': leave_types,
        'pending_leaves': pending_leaves,
        'status_filter': status_filter,
        'employee_filter': employee_filter,
        'leave_type_filter': leave_type_filter,
        'leave_statuses': Leave.STATUS_CHOICES,
    }
    return render(request, 'hr/leaves-ui.html', context)

@login_required
def leave_apply(request, pk=None):
    """Apply for leave or edit existing leave application"""
    leave = None
    if pk:
        leave = get_object_or_404(Leave, pk=pk, employee__company=request.user.company)
    
    if request.method == 'POST':
        try:
            employee_id = request.POST.get('employee_id')
            leave_type_id = request.POST.get('leave_type_id')
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            reason = request.POST.get('reason', '')
            
            if not all([employee_id, leave_type_id, start_date, end_date]):
                return JsonResponse({
                    'success': False,
                    'error': 'All fields are required.'
                }, status=400)
            
            employee = get_object_or_404(Employee, pk=employee_id, company=request.user.company)
            leave_type = get_object_or_404(LeaveType, pk=leave_type_id, company=request.user.company)
            
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            # Calculate days requested
            days_requested = (end_date_obj - start_date_obj).days + 1
            
            if leave:
                # Update existing leave
                leave.employee = employee
                leave.leave_type = leave_type
                leave.start_date = start_date_obj
                leave.end_date = end_date_obj
                leave.days_requested = days_requested
                leave.reason = reason
                leave.save()
                action = 'updated'
            else:
                # Create new leave request
                leave = Leave.objects.create(
                    employee=employee,
                    leave_type=leave_type,
                    start_date=start_date_obj,
                    end_date=end_date_obj,
                    days_requested=days_requested,
                    reason=reason,
                    status='pending'
                )
                action = 'created'
            
            return JsonResponse({
                'success': True,
                'message': f'Leave application {action} successfully',
                'leave': {
                    'id': leave.id,
                    'employee': f"{employee.first_name} {employee.last_name}",
                    'leave_type': leave_type.name,
                    'start_date': leave.start_date.strftime('%Y-%m-%d'),
                    'end_date': leave.end_date.strftime('%Y-%m-%d'),
                    'days_requested': float(leave.days_requested),
                    'status': leave.status,
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error processing leave application: {str(e)}'
            }, status=500)
    
    else:
        # GET request - show form
        employees = Employee.objects.filter(company=request.user.company, is_active=True)
        leave_types = LeaveType.objects.filter(company=request.user.company, is_active=True)
        
        context = {
            'leave': leave,
            'employees': employees,
            'leave_types': leave_types,
        }
        return render(request, 'hr/leave_apply_form.html', context)

@login_required
@require_POST
def leave_approve(request, pk):
    """Approve or reject leave request"""
    try:
        leave = get_object_or_404(Leave, pk=pk, employee__company=request.user.company)
        action = request.POST.get('action')  # 'approve' or 'reject'
        comments = request.POST.get('comments', '')
        
        if action == 'approve':
            leave.status = 'approved'
            leave.approved_by = request.user
            leave.approval_date = timezone.now()
        elif action == 'reject':
            leave.status = 'rejected'
            leave.rejection_reason = comments
        else:
            return JsonResponse({
                'success': False,
                'error': 'Invalid action.'
            }, status=400)
        
        leave.save()
        
        return JsonResponse({
            'success': True,
            'leave': {
                'id': leave.id,
                'status': leave.status,
                'approved_by': leave.approved_by.email if leave.approved_by else '',
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error processing leave request: {str(e)}'
        }, status=500)

@login_required
def reports_ui(request):
    """HR reports interface"""
    company = request.user.company
    
    # Recent reports
    recent_reports = HRReport.objects.filter(company=company).order_by('-generated_at')[:10]
    
    # Report statistics
    total_employees = Employee.objects.filter(company=company, is_active=True).count()
    total_departments = Department.objects.filter(company=company, is_active=True).count()
    pending_leaves = Leave.objects.filter(employee__company=company, status='pending').count()
    
    # Department wise employee count
    dept_stats = Employee.objects.filter(
        company=company, is_active=True
    ).values('department__name').annotate(
        count=Count('id')
    ).order_by('-count')
    
    context = {
        'recent_reports': recent_reports,
        'total_employees': total_employees,
        'total_departments': total_departments,
        'pending_leaves': pending_leaves,
        'dept_stats': dept_stats,
        'report_types': HRReport.REPORT_TYPE_CHOICES,
    }
    return render(request, 'hr/reports-ui.html', context)

@login_required
def generate_report(request):
    """Generate HR report"""
    if request.method == 'POST':
        try:
            report_type = request.POST.get('report_type')
            period_start = request.POST.get('period_start')
            period_end = request.POST.get('period_end')
            title = request.POST.get('title')
            
            if not all([report_type, period_start, period_end, title]):
                return JsonResponse({
                    'success': False,
                    'error': 'All fields are required.'
                }, status=400)
            
            start_date = datetime.strptime(period_start, '%Y-%m-%d').date()
            end_date = datetime.strptime(period_end, '%Y-%m-%d').date()
            
            # Create report record
            report = HRReport.objects.create(
                company=request.user.company,
                report_type=report_type,
                title=title,
                period_start=start_date,
                period_end=end_date,
                generated_by=request.user,
                notes=request.POST.get('notes', '')
            )
            
            return JsonResponse({
                'success': True,
                'report': {
                    'id': report.id,
                    'title': report.title,
                    'report_type': report.get_report_type_display(),
                    'generated_at': report.generated_at.strftime('%Y-%m-%d %H:%M'),
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error generating report: {str(e)}'
            }, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

# Department Management Views
@login_required
def departments_ui(request):
    """Department management interface"""
    departments = Department.objects.filter(company=request.user.company).order_by('name')
    return render(request, 'hr/departments-ui.html', {'departments': departments})

@login_required
@require_POST
def departments_add(request):
    """Add new department"""
    try:
        name = request.POST.get('name')
        code = request.POST.get('code', '')
        description = request.POST.get('description', '')
        budget = request.POST.get('budget', 0)
        
        if not name:
            return JsonResponse({
                'success': False,
                'error': 'Department name is required.'
            }, status=400)
        
        department = Department.objects.create(
            company=request.user.company,
            name=name,
            code=code,
            description=description,
            budget=float(budget) if budget else 0
        )
        
        return JsonResponse({
            'success': True,
            'department': {
                'id': department.id,
                'name': department.name,
                'code': department.code,
                'budget': float(department.budget),
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error creating department: {str(e)}'
        }, status=500)

@login_required
@require_POST
def departments_edit(request, pk):
    """Edit existing department"""
    try:
        department = get_object_or_404(Department, pk=pk, company=request.user.company)
        
        name = request.POST.get('name')
        code = request.POST.get('code', '')
        description = request.POST.get('description', '')
        budget = request.POST.get('budget', department.budget)
        
        if not name:
            return JsonResponse({
                'success': False,
                'error': 'Department name is required.'
            }, status=400)
        
        department.name = name
        department.code = code
        department.description = description
        department.budget = float(budget) if budget else 0
        department.save()
        
        return JsonResponse({
            'success': True,
            'department': {
                'id': department.id,
                'name': department.name,
                'code': department.code,
                'budget': float(department.budget),
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error updating department: {str(e)}'
        }, status=500)

@login_required
@require_POST
def departments_delete(request, pk):
    """Delete department (soft delete)"""
    try:
        department = get_object_or_404(Department, pk=pk, company=request.user.company)
        department.is_active = False
        department.save()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error deleting department: {str(e)}'
        }, status=500)

@login_required
def department_detail(request, pk):
    """Department detail view"""
    department = get_object_or_404(Department, pk=pk, company=request.user.company)
    employees = Employee.objects.filter(department=department, is_active=True)
    
    context = {
        'department': department,
        'employees': employees,
        'employee_count': employees.count(),
    }
    return render(request, 'hr/department_detail.html', context)

# Designation Management Views
@login_required
def designations_ui(request):
    """Designation management interface"""
    designations = Designation.objects.filter(company=request.user.company).order_by('title')
    return render(request, 'hr/designations-ui.html', {'designations': designations})

@login_required
@require_POST
def designations_add(request):
    """Add new designation"""
    try:
        title = request.POST.get('title')
        level = request.POST.get('level', 'entry')
        salary_min = request.POST.get('salary_range_min', 0)
        salary_max = request.POST.get('salary_range_max', 0)
        description = request.POST.get('description', '')
        
        if not title:
            return JsonResponse({
                'success': False,
                'error': 'Designation title is required.'
            }, status=400)
        
        designation = Designation.objects.create(
            company=request.user.company,
            title=title,
            level=level,
            salary_range_min=float(salary_min) if salary_min else 0,
            salary_range_max=float(salary_max) if salary_max else 0,
            description=description
        )
        
        return JsonResponse({
            'success': True,
            'designation': {
                'id': designation.id,
                'title': designation.title,
                'level': designation.level,
                'salary_range_min': float(designation.salary_range_min),
                'salary_range_max': float(designation.salary_range_max),
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error creating designation: {str(e)}'
        }, status=500)

@login_required
@require_POST
def designations_edit(request, pk):
    """Edit existing designation"""
    try:
        designation = get_object_or_404(Designation, pk=pk, company=request.user.company)
        
        title = request.POST.get('title')
        level = request.POST.get('level', designation.level)
        salary_min = request.POST.get('salary_range_min', designation.salary_range_min)
        salary_max = request.POST.get('salary_range_max', designation.salary_range_max)
        description = request.POST.get('description', designation.description)
        
        if not title:
            return JsonResponse({
                'success': False,
                'error': 'Designation title is required.'
            }, status=400)
        
        designation.title = title
        designation.level = level
        designation.salary_range_min = float(salary_min) if salary_min else 0
        designation.salary_range_max = float(salary_max) if salary_max else 0
        designation.description = description
        designation.save()
        
        return JsonResponse({
            'success': True,
            'designation': {
                'id': designation.id,
                'title': designation.title,
                'level': designation.level,
                'salary_range_min': float(designation.salary_range_min),
                'salary_range_max': float(designation.salary_range_max),
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error updating designation: {str(e)}'
        }, status=500)

@login_required
@require_POST
def designations_delete(request, pk):
    """Delete designation (soft delete)"""
    try:
        designation = get_object_or_404(Designation, pk=pk, company=request.user.company)
        designation.is_active = False
        designation.save()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error deleting designation: {str(e)}'
        }, status=500)

@login_required
def designation_detail(request, pk):
    """Designation detail view"""
    designation = get_object_or_404(Designation, pk=pk, company=request.user.company)
    employees = Employee.objects.filter(designation=designation, is_active=True)
    
    context = {
        'designation': designation,
        'employees': employees,
        'employee_count': employees.count(),
    }
    return render(request, 'hr/designation_detail.html', context)

# Contractor Management Views
@login_required
def contractors_add(request):
    partner_id = request.POST.get('partner_id')
    contract_type = request.POST.get('contract_type', 'hourly')
    hourly_rate = request.POST.get('hourly_rate', 0)
    contract_amount = request.POST.get('contract_amount', 0)
    skills = request.POST.get('skills', '')
    
    if not partner_id:
        return JsonResponse({'success': False, 'error': 'Partner is required.'}, status=400)
    
    try:
        partner = Partner.objects.get(id=partner_id, company=request.user.company)
        contractor = Contractor.objects.create(
            company=request.user.company,
            partner=partner,
            contract_type=contract_type,
            hourly_rate=float(hourly_rate) if hourly_rate else 0,
            contract_amount=float(contract_amount) if contract_amount else 0,
            skills=skills
        )
        return JsonResponse({
            'success': True,
            'contractor': {
                'id': contractor.id,
                'contractor_id': contractor.contractor_id,
                'partner_name': contractor.partner.name,
                'contract_type': contractor.contract_type,
                'hourly_rate': str(contractor.hourly_rate),
                'contract_amount': str(contractor.contract_amount),
                'skills': contractor.skills
            }
        })
    except Partner.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Partner not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_POST
def contractors_edit(request, pk):
    contractor = get_object_or_404(Contractor, pk=pk, company=request.user.company)
    
    contract_type = request.POST.get('contract_type', contractor.contract_type)
    hourly_rate = request.POST.get('hourly_rate', contractor.hourly_rate)
    contract_amount = request.POST.get('contract_amount', contractor.contract_amount)
    skills = request.POST.get('skills', contractor.skills)
    
    contractor.contract_type = contract_type
    contractor.hourly_rate = float(hourly_rate) if hourly_rate else 0
    contractor.contract_amount = float(contract_amount) if contract_amount else 0
    contractor.skills = skills
    contractor.save()
    
    return JsonResponse({
        'success': True,
        'contractor': {
            'id': contractor.id,
            'contractor_id': contractor.contractor_id,
            'partner_name': contractor.partner.name,
            'contract_type': contractor.contract_type,
            'hourly_rate': str(contractor.hourly_rate),
            'contract_amount': str(contractor.contract_amount),
            'skills': contractor.skills
        }
    })

@login_required
@require_POST
def contractors_delete(request, pk):
    contractor = get_object_or_404(Contractor, pk=pk, company=request.user.company)
    contractor.delete()
    return JsonResponse({'success': True})

@login_required
def contractor_detail(request, pk):
    """Contractor detail view"""
    contractor = get_object_or_404(Contractor, pk=pk, company=request.user.company)
    
    context = {
        'contractor': contractor,
    }
    return render(request, 'hr/contractor_detail.html', context)

# Additional missing views
@login_required
def contractors_ui(request):
    """Contractors management interface"""
    company = request.user.company
    
    # Get search and filter parameters
    search = request.GET.get('search', '')
    contract_type_filter = request.GET.get('contract_type', '')
    
    # Base queryset
    contractors = Contractor.objects.filter(company=company).select_related('partner')
    
    # Apply filters
    if search:
        contractors = contractors.filter(
            Q(partner__name__icontains=search) |
            Q(contractor_id__icontains=search) |
            Q(skills__icontains=search)
        )
    
    if contract_type_filter:
        contractors = contractors.filter(contract_type=contract_type_filter)
    
    # Pagination
    paginator = Paginator(contractors.order_by('-created_at'), 25)
    page_number = request.GET.get('page')
    contractors_page = paginator.get_page(page_number)
    
    # Get partners for new contractor form
    partners = Partner.objects.filter(company=company, is_vendor=True)
    
    context = {
        'contractors': contractors_page,
        'partners': partners,
        'search': search,
        'contract_type_filter': contract_type_filter,
        'contract_types': Contractor.CONTRACT_TYPE_CHOICES,
    }
    return render(request, 'hr/contractors-ui.html', context)

# Additional detail and form views
@login_required
def payroll_detail(request, pk):
    """Payroll detail view"""
    payroll = get_object_or_404(Payroll, pk=pk, employee__company=request.user.company)
    
    context = {
        'payroll': payroll,
    }
    return render(request, 'hr/payroll_detail.html', context)

@login_required
def leave_detail(request, pk):
    """Leave detail view"""
    leave = get_object_or_404(Leave, pk=pk, employee__company=request.user.company)
    
    context = {
        'leave': leave,
    }
    return render(request, 'hr/leave_detail.html', context)

@login_required
def attendance_detail(request, pk):
    """Attendance detail view"""
    attendance = get_object_or_404(Attendance, pk=pk, employee__company=request.user.company)
    
    context = {
        'attendance': attendance,
    }
    return render(request, 'hr/attendance_detail.html', context)

# Form views for better UX
@login_required
def department_form(request, pk=None):
    """Department form for add/edit"""
    department = None
    if pk:
        department = get_object_or_404(Department, pk=pk, company=request.user.company)
    
    context = {
        'department': department,
    }
    return render(request, 'hr/department_form.html', context)

@login_required
def designation_form(request, pk=None):
    """Designation form for add/edit"""
    designation = None
    if pk:
        designation = get_object_or_404(Designation, pk=pk, company=request.user.company)
    
    context = {
        'designation': designation,
        'levels': Designation._meta.get_field('level').choices,
    }
    return render(request, 'hr/designation_form.html', context)

@login_required
def contractor_form(request, pk=None):
    """Contractor form for add/edit"""
    contractor = None
    if pk:
        contractor = get_object_or_404(Contractor, pk=pk, company=request.user.company)
    
    partners = Partner.objects.filter(company=request.user.company, is_vendor=True)
    
    context = {
        'contractor': contractor,
        'partners': partners,
        'contract_types': Contractor.CONTRACT_TYPE_CHOICES,
    }
    return render(request, 'hr/contractor_form.html', context)

@login_required
def leave_form(request, pk=None):
    """Leave form for add/edit"""
    leave = None
    if pk:
        leave = get_object_or_404(Leave, pk=pk, employee__company=request.user.company)
    
    employees = Employee.objects.filter(company=request.user.company, is_active=True)
    leave_types = LeaveType.objects.filter(company=request.user.company, is_active=True)
    
    context = {
        'leave': leave,
        'employees': employees,
        'leave_types': leave_types,
    }
    return render(request, 'hr/leave_form.html', context)

@login_required
def attendance_form(request, pk=None):
    """Attendance form for add/edit"""
    attendance = None
    if pk:
        attendance = get_object_or_404(Attendance, pk=pk, employee__company=request.user.company)
    
    employees = Employee.objects.filter(company=request.user.company, is_active=True)
    shift_types = ShiftType.objects.filter(company=request.user.company, is_active=True)
    
    context = {
        'attendance': attendance,
        'employees': employees,
        'shift_types': shift_types,
        'attendance_statuses': Attendance.STATUS_CHOICES,
    }
    return render(request, 'hr/attendance_form.html', context)

# Performance Management Views
@login_required
def performance_ui(request):
    """Performance management interface"""
    appraisals = PerformanceAppraisal.objects.filter(
        employee__company=request.user.company
    ).select_related('employee', 'reviewer').order_by('-created_at')
    
    context = {
        'appraisals': appraisals,
        'active_tab': 'performance',
    }
    return render(request, 'hr/performance.html', context)

# Training Management Views
@login_required
def training_ui(request):
    """Training management interface"""
    trainings = Training.objects.filter(
        company=request.user.company
    ).order_by('-start_date')
    
    enrollments = TrainingEnrollment.objects.filter(
        training__company=request.user.company
    ).select_related('training', 'employee')
    
    context = {
        'trainings': trainings,
        'enrollments': enrollments,
        'active_tab': 'training',
    }
    return render(request, 'hr/training.html', context)

# Recruitment Management Views
@login_required
def recruitment_ui(request):
    """Recruitment management interface"""
    vacancies = JobVacancy.objects.filter(
        company=request.user.company
    ).select_related('department', 'designation').order_by('-created_at')
    
    applications = JobApplication.objects.filter(
        vacancy__company=request.user.company
    ).select_related('vacancy').order_by('-created_at')
    
    context = {
        'vacancies': vacancies,
        'applications': applications,
        'active_tab': 'recruitment',
    }
    return render(request, 'hr/recruitment.html', context)

# Employee Relations Views
@login_required
def relations_ui(request):
    """Employee relations management interface"""
    relations = EmployeeRelation.objects.filter(
        employee__company=request.user.company
    ).select_related('employee', 'reported_by', 'assigned_to').order_by('-created_at')
    
    context = {
        'relations': relations,
        'active_tab': 'relations',
    }
    return render(request, 'hr/relations.html', context)

# Benefits Management Views
@login_required
def benefits_ui(request):
    """Benefits management interface"""
    benefits = EmployeeBenefit.objects.filter(
        company=request.user.company
    ).order_by('-created_at')
    
    enrollments = EmployeeBenefitEnrollment.objects.filter(
        benefit__company=request.user.company
    ).select_related('benefit', 'employee')
    
    context = {
        'benefits': benefits,
        'enrollments': enrollments,
        'active_tab': 'benefits',
    }
    return render(request, 'hr/benefits.html', context)

# Policies Management Views
@login_required
def policies_ui(request):
    """HR policies management interface"""
    policies = HRPolicy.objects.filter(
        company=request.user.company
    ).order_by('-created_at')
    
    context = {
        'policies': policies,
        'active_tab': 'policies',
    }
    return render(request, 'hr/policies.html', context)

@login_required
def policies_detail(request, pk):
    """Policy detail view"""
    policy = get_object_or_404(HRPolicy, pk=pk, company=request.user.company)
    context = {
        'policy': policy,
        'active_tab': 'policies',
    }
    return render(request, 'hr/policies_detail.html', context)

@login_required
def policies_form(request, pk=None):
    """Create or edit policy"""
    if pk:
        policy = get_object_or_404(HRPolicy, pk=pk, company=request.user.company)
    else:
        policy = None
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                if policy:
                    # Update existing policy
                    policy.title = request.POST.get('title')
                    policy.policy_type = request.POST.get('policy_type')
                    policy.version = request.POST.get('version')
                    policy.content = request.POST.get('content')
                    policy.effective_date = request.POST.get('effective_date')
                    policy.review_date = request.POST.get('review_date') or None
                    policy.is_active = 'is_active' in request.POST
                    
                    if request.FILES.get('document_file'):
                        policy.document_file = request.FILES['document_file']
                    
                    policy.save()
                    messages.success(request, f'Policy "{policy.title}" updated successfully!')
                else:
                    # Create new policy
                    policy = HRPolicy.objects.create(
                        company=request.user.company,
                        title=request.POST.get('title'),
                        policy_type=request.POST.get('policy_type'),
                        version=request.POST.get('version'),
                        content=request.POST.get('content'),
                        effective_date=request.POST.get('effective_date'),
                        review_date=request.POST.get('review_date') or None,
                        is_active='is_active' in request.POST,
                        document_file=request.FILES.get('document_file')
                    )
                    messages.success(request, f'Policy "{policy.title}" created successfully!')
                
                return redirect('hr:policies_detail', pk=policy.pk)
        except Exception as e:
            messages.error(request, f'Error saving policy: {str(e)}')
    
    context = {
        'policy': policy,
        'policy_types': HRPolicy.POLICY_TYPE_CHOICES,
        'active_tab': 'policies',
    }
    return render(request, 'hr/policies_form.html', context)

@login_required
@require_POST
def policies_delete(request, pk):
    """Delete policy"""
    policy = get_object_or_404(HRPolicy, pk=pk, company=request.user.company)
    policy_name = policy.title
    policy.delete()
    messages.success(request, f'Policy "{policy_name}" deleted successfully!')
    return redirect('hr:policies_ui')

# Benefits Management Views - Extended
@login_required
def benefits_detail(request, pk):
    """Benefit detail view"""
    benefit = get_object_or_404(EmployeeBenefit, pk=pk, company=request.user.company)
    context = {
        'benefit': benefit,
        'active_tab': 'benefits',
    }
    return render(request, 'hr/benefits_detail.html', context)

@login_required
def benefits_form(request, pk=None):
    """Create or edit benefit"""
    if pk:
        benefit = get_object_or_404(EmployeeBenefit, pk=pk, company=request.user.company)
    else:
        benefit = None
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                if benefit:
                    # Update existing benefit
                    benefit.name = request.POST.get('name')
                    benefit.benefit_type = request.POST.get('benefit_type')
                    benefit.description = request.POST.get('description')
                    benefit.cost_to_company = request.POST.get('cost_to_company')
                    benefit.employee_contribution = request.POST.get('employee_contribution')
                    benefit.effective_date = request.POST.get('effective_date')
                    benefit.expiry_date = request.POST.get('expiry_date') or None
                    benefit.eligibility_criteria = request.POST.get('eligibility_criteria')
                    benefit.is_mandatory = 'is_mandatory' in request.POST
                    benefit.is_active = 'is_active' in request.POST
                    benefit.save()
                    messages.success(request, f'Benefit "{benefit.name}" updated successfully!')
                else:
                    # Create new benefit
                    benefit = EmployeeBenefit.objects.create(
                        company=request.user.company,
                        name=request.POST.get('name'),
                        benefit_type=request.POST.get('benefit_type'),
                        description=request.POST.get('description'),
                        cost_to_company=request.POST.get('cost_to_company'),
                        employee_contribution=request.POST.get('employee_contribution'),
                        effective_date=request.POST.get('effective_date'),
                        expiry_date=request.POST.get('expiry_date') or None,
                        eligibility_criteria=request.POST.get('eligibility_criteria'),
                        is_mandatory='is_mandatory' in request.POST,
                        is_active='is_active' in request.POST
                    )
                    messages.success(request, f'Benefit "{benefit.name}" created successfully!')
                
                return redirect('hr:benefits_detail', pk=benefit.pk)
        except Exception as e:
            messages.error(request, f'Error saving benefit: {str(e)}')
    
    context = {
        'benefit': benefit,
        'benefit_types': EmployeeBenefit.BENEFIT_TYPE_CHOICES,
        'active_tab': 'benefits',
    }
    return render(request, 'hr/benefits_form.html', context)

@login_required
@require_POST
def benefits_delete(request, pk):
    """Delete benefit"""
    benefit = get_object_or_404(EmployeeBenefit, pk=pk, company=request.user.company)
    benefit_name = benefit.name
    benefit.delete()
    messages.success(request, f'Benefit "{benefit_name}" deleted successfully!')
    return redirect('hr:benefits_ui')

# Employee Relations Views - Extended
@login_required
def relations_detail(request, pk):
    """Employee relation detail view"""
    relation = get_object_or_404(EmployeeRelation, pk=pk, employee__company=request.user.company)
    context = {
        'relation': relation,
        'active_tab': 'relations',
    }
    return render(request, 'hr/relations_detail.html', context)

@login_required
def relations_form(request, pk=None):
    """Create or edit employee relation"""
    if pk:
        relation = get_object_or_404(EmployeeRelation, pk=pk, employee__company=request.user.company)
    else:
        relation = None
    
    employees = Employee.objects.filter(company=request.user.company, is_active=True)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                if relation:
                    # Update existing relation
                    relation.employee_id = request.POST.get('employee')
                    relation.relation_type = request.POST.get('relation_type')
                    relation.title = request.POST.get('title')
                    relation.description = request.POST.get('description')
                    relation.reported_by_id = request.POST.get('reported_by') or None
                    relation.assigned_to_id = request.POST.get('assigned_to') or None
                    relation.priority = request.POST.get('priority')
                    relation.status = request.POST.get('status')
                    relation.resolution = request.POST.get('resolution')
                    relation.save()
                    messages.success(request, f'Employee relation "{relation.title}" updated successfully!')
                else:
                    # Create new relation
                    relation = EmployeeRelation.objects.create(
                        employee_id=request.POST.get('employee'),
                        relation_type=request.POST.get('relation_type'),
                        title=request.POST.get('title'),
                        description=request.POST.get('description'),
                        reported_by_id=request.POST.get('reported_by') or None,
                        assigned_to_id=request.POST.get('assigned_to') or None,
                        priority=request.POST.get('priority'),
                        status=request.POST.get('status'),
                        resolution=request.POST.get('resolution')
                    )
                    messages.success(request, f'Employee relation "{relation.title}" created successfully!')
                
                return redirect('hr:relations_detail', pk=relation.pk)
        except Exception as e:
            messages.error(request, f'Error saving employee relation: {str(e)}')
    
    context = {
        'relation': relation,
        'employees': employees,
        'relation_types': EmployeeRelation.RELATION_TYPE_CHOICES,
        'priority_choices': EmployeeRelation.PRIORITY_CHOICES,
        'status_choices': EmployeeRelation.STATUS_CHOICES,
        'active_tab': 'relations',
    }
    return render(request, 'hr/relations_form.html', context)

@login_required
@require_POST
def relations_delete(request, pk):
    """Delete employee relation"""
    relation = get_object_or_404(EmployeeRelation, pk=pk, employee__company=request.user.company)
    relation_title = relation.title
    relation.delete()
    messages.success(request, f'Employee relation "{relation_title}" deleted successfully!')
    return redirect('hr:relations_ui')

# Recruitment Views - Extended
@login_required
def recruitment_detail(request, pk):
    """Job vacancy detail view"""
    vacancy = get_object_or_404(JobVacancy, pk=pk, company=request.user.company)
    applications = JobApplication.objects.filter(vacancy=vacancy).order_by('-created_at')
    context = {
        'vacancy': vacancy,
        'applications': applications,
        'active_tab': 'recruitment',
    }
    return render(request, 'hr/recruitment_detail.html', context)

@login_required
def recruitment_form(request, pk=None):
    """Create or edit job vacancy"""
    if pk:
        vacancy = get_object_or_404(JobVacancy, pk=pk, company=request.user.company)
    else:
        vacancy = None
    
    departments = Department.objects.filter(company=request.user.company)
    designations = Designation.objects.filter(company=request.user.company)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                if vacancy:
                    # Update existing vacancy
                    vacancy.title = request.POST.get('title')
                    vacancy.department_id = request.POST.get('department')
                    vacancy.designation_id = request.POST.get('designation') or None
                    vacancy.description = request.POST.get('description')
                    vacancy.requirements = request.POST.get('requirements')
                    vacancy.experience_required = request.POST.get('experience_required')
                    vacancy.qualification_required = request.POST.get('qualification_required')
                    vacancy.salary_range = request.POST.get('salary_range')
                    vacancy.employment_type = request.POST.get('employment_type')
                    vacancy.location = request.POST.get('location')
                    vacancy.application_deadline = request.POST.get('application_deadline') or None
                    vacancy.is_active = 'is_active' in request.POST
                    vacancy.save()
                    messages.success(request, f'Job vacancy "{vacancy.title}" updated successfully!')
                else:
                    # Create new vacancy
                    vacancy = JobVacancy.objects.create(
                        company=request.user.company,
                        title=request.POST.get('title'),
                        department_id=request.POST.get('department'),
                        designation_id=request.POST.get('designation') or None,
                        description=request.POST.get('description'),
                        requirements=request.POST.get('requirements'),
                        experience_required=request.POST.get('experience_required'),
                        qualification_required=request.POST.get('qualification_required'),
                        salary_range=request.POST.get('salary_range'),
                        employment_type=request.POST.get('employment_type'),
                        location=request.POST.get('location'),
                        application_deadline=request.POST.get('application_deadline') or None,
                        is_active='is_active' in request.POST
                    )
                    messages.success(request, f'Job vacancy "{vacancy.title}" created successfully!')
                
                return redirect('hr:recruitment_detail', pk=vacancy.pk)
        except Exception as e:
            messages.error(request, f'Error saving job vacancy: {str(e)}')
    
    context = {
        'vacancy': vacancy,
        'departments': departments,
        'designations': designations,
        'employment_types': JobVacancy.EMPLOYMENT_TYPE_CHOICES,
        'active_tab': 'recruitment',
    }
    return render(request, 'hr/recruitment_form.html', context)

@login_required
@require_POST
def recruitment_delete(request, pk):
    """Delete job vacancy"""
    vacancy = get_object_or_404(JobVacancy, pk=pk, company=request.user.company)
    vacancy_title = vacancy.title
    vacancy.delete()
    messages.success(request, f'Job vacancy "{vacancy_title}" deleted successfully!')
    return redirect('hr:recruitment_ui')

# Training Views - Extended
@login_required
def training_detail(request, pk):
    """Training detail view"""
    training = get_object_or_404(Training, pk=pk, company=request.user.company)
    enrollments = TrainingEnrollment.objects.filter(training=training).select_related('employee')
    context = {
        'training': training,
        'enrollments': enrollments,
        'active_tab': 'training',
    }
    return render(request, 'hr/training_detail.html', context)

@login_required
def training_form(request, pk=None):
    """Create or edit training"""
    if pk:
        training = get_object_or_404(Training, pk=pk, company=request.user.company)
    else:
        training = None
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                if training:
                    # Update existing training
                    training.title = request.POST.get('title')
                    training.description = request.POST.get('description')
                    training.training_type = request.POST.get('training_type')
                    training.duration_hours = request.POST.get('duration_hours')
                    training.start_date = request.POST.get('start_date')
                    training.end_date = request.POST.get('end_date') or None
                    training.location = request.POST.get('location')
                    training.instructor = request.POST.get('instructor')
                    training.cost = request.POST.get('cost') or 0
                    training.max_participants = request.POST.get('max_participants') or None
                    training.is_active = 'is_active' in request.POST
                    training.save()
                    messages.success(request, f'Training "{training.title}" updated successfully!')
                else:
                    # Create new training
                    training = Training.objects.create(
                        company=request.user.company,
                        title=request.POST.get('title'),
                        description=request.POST.get('description'),
                        training_type=request.POST.get('training_type'),
                        duration_hours=request.POST.get('duration_hours'),
                        start_date=request.POST.get('start_date'),
                        end_date=request.POST.get('end_date') or None,
                        location=request.POST.get('location'),
                        instructor=request.POST.get('instructor'),
                        cost=request.POST.get('cost') or 0,
                        max_participants=request.POST.get('max_participants') or None,
                        is_active='is_active' in request.POST
                    )
                    messages.success(request, f'Training "{training.title}" created successfully!')
                
                return redirect('hr:training_detail', pk=training.pk)
        except Exception as e:
            messages.error(request, f'Error saving training: {str(e)}')
    
    context = {
        'training': training,
        'training_types': Training.TRAINING_TYPE_CHOICES,
        'active_tab': 'training',
    }
    return render(request, 'hr/training_form.html', context)

@login_required
@require_POST
def training_delete(request, pk):
    """Delete training"""
    training = get_object_or_404(Training, pk=pk, company=request.user.company)
    training_title = training.title
    training.delete()
    messages.success(request, f'Training "{training_title}" deleted successfully!')
    return redirect('hr:training_ui')

# Performance Views - Extended
@login_required
def performance_detail(request, pk):
    """Performance appraisal detail view"""
    appraisal = get_object_or_404(PerformanceAppraisal, pk=pk, employee__company=request.user.company)
    context = {
        'appraisal': appraisal,
        'active_tab': 'performance',
    }
    return render(request, 'hr/performance_detail.html', context)

@login_required
def performance_form(request, pk=None):
    """Create or edit performance appraisal"""
    if pk:
        appraisal = get_object_or_404(PerformanceAppraisal, pk=pk, employee__company=request.user.company)
    else:
        appraisal = None
    
    employees = Employee.objects.filter(company=request.user.company, is_active=True)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                if appraisal:
                    # Update existing appraisal
                    appraisal.employee_id = request.POST.get('employee')
                    appraisal.period_start = request.POST.get('period_start')
                    appraisal.period_end = request.POST.get('period_end')
                    appraisal.reviewer_id = request.POST.get('reviewer') or None
                    appraisal.manager_goals_achievement = request.POST.get('goals_achievements')
                    appraisal.manager_strengths = request.POST.get('strengths')
                    appraisal.manager_areas_improvement = request.POST.get('areas_for_improvement')
                    appraisal.manager_rating = request.POST.get('overall_rating')
                    appraisal.manager_comments = request.POST.get('recommendations')
                    appraisal.status = request.POST.get('status')
                    appraisal.save()
                    messages.success(request, f'Performance appraisal for "{appraisal.employee}" updated successfully!')
                else:
                    # Create new appraisal
                    appraisal = PerformanceAppraisal.objects.create(
                        employee_id=request.POST.get('employee'),
                        period_start=request.POST.get('period_start'),
                        period_end=request.POST.get('period_end'),
                        reviewer_id=request.POST.get('reviewer') or None,
                        manager_goals_achievement=request.POST.get('goals_achievements'),
                        manager_strengths=request.POST.get('strengths'),
                        manager_areas_improvement=request.POST.get('areas_for_improvement'),
                        manager_rating=request.POST.get('overall_rating'),
                        manager_comments=request.POST.get('recommendations'),
                        status=request.POST.get('status')
                    )
                    messages.success(request, f'Performance appraisal for "{appraisal.employee}" created successfully!')
                
                return redirect('hr:performance_detail', pk=appraisal.pk)
        except Exception as e:
            messages.error(request, f'Error saving performance appraisal: {str(e)}')
    
    context = {
        'appraisal': appraisal,
        'employees': employees,
        'rating_choices': PerformanceAppraisal.RATING_CHOICES,
        'status_choices': PerformanceAppraisal.STATUS_CHOICES,
        'active_tab': 'performance',
    }
    return render(request, 'hr/performance_form.html', context)

@login_required
@require_POST
def performance_delete(request, pk):
    """Delete performance appraisal"""
    appraisal = get_object_or_404(PerformanceAppraisal, pk=pk, employee__company=request.user.company)
    employee_name = str(appraisal.employee)
    appraisal.delete()
    messages.success(request, f'Performance appraisal for "{employee_name}" deleted successfully!')
    return redirect('hr:performance_ui')
