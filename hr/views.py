from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Employee, Contractor
from crm.models import Partner
from django.views.decorators.http import require_POST
from django.db.models import Count
from django.utils import timezone
from datetime import datetime, timedelta

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
        date_joined__gte=timezone.now().replace(day=1)
    ).count()
    
    # Department breakdown
    departments = Employee.objects.filter(
        company=company, 
        is_active=True
    ).values('department').annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    # Recent employees
    recent_employees = Employee.objects.filter(
        company=company
    ).order_by('-date_joined')[:5]
    
    # Recent contractors
    recent_contractors = Contractor.objects.filter(
        company=company
    ).order_by('-created_at')[:5]
    
    context = {
        'total_employees': total_employees,
        'total_contractors': total_contractors,
        'new_employees_this_month': new_employees_this_month,
        'departments': departments,
        'recent_employees': recent_employees,
        'recent_contractors': recent_contractors,
    }
    return render(request, 'hr/dashboard.html', context)

@login_required
def employees_ui(request):
    employees = Employee.objects.filter(company=request.user.company)
    return render(request, 'hr/employees-ui.html', {'employees': employees})

@login_required
def employees_add(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        department = request.POST.get('department')
        if not first_name or not last_name or not email:
            return JsonResponse({'success': False, 'error': 'First name, last name, and email are required.'}, status=400)
        employee = Employee.objects.create(
            company=request.user.company,
            first_name=first_name,
            last_name=last_name,
            email=email,
            department=department or ''
        )
        return JsonResponse({
            'success': True,
            'employee': {
                'id': employee.id,
                'first_name': employee.first_name,
                'last_name': employee.last_name,
                'email': employee.email,
                'department': employee.department
            }
        })
    else:
        # GET request - show the form
        return render(request, 'hr/employee_form.html')

@login_required
@require_POST
def employees_edit(request, pk):
    employee = get_object_or_404(Employee, pk=pk, company=request.user.company)
    first_name = request.POST.get('first_name')
    last_name = request.POST.get('last_name')
    email = request.POST.get('email')
    department = request.POST.get('department')
    if not first_name or not last_name or not email:
        return JsonResponse({'success': False, 'error': 'First name, last name, and email are required.'}, status=400)
    employee.first_name = first_name
    employee.last_name = last_name
    employee.email = email
    employee.department = department or ''
    employee.save()
    return JsonResponse({
        'success': True,
        'employee': {
            'id': employee.id,
            'first_name': employee.first_name,
            'last_name': employee.last_name,
            'email': employee.email,
            'department': employee.department
        }
    })

@login_required
@require_POST
def employees_delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk, company=request.user.company)
    employee.delete()
    return JsonResponse({'success': True})

@login_required
def attendance_ui(request):
    return render(request, 'hr/attendance-ui.html')

@login_required
def payroll_ui(request):
    return render(request, 'hr/payroll-ui.html')

@login_required
def leaves_ui(request):
    return render(request, 'hr/leaves-ui.html')

@login_required
def reports_ui(request):
    return render(request, 'hr/reports-ui.html')

# Contractor Management Views
@login_required
def contractors_ui(request):
    contractors = Contractor.objects.filter(company=request.user.company)
    return render(request, 'hr/contractors-ui.html', {'contractors': contractors})

@login_required
@require_POST
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
