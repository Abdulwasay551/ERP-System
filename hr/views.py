from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Employee
from django.views.decorators.http import require_POST

# Create your views here.

@login_required
def employees_ui(request):
    employees = Employee.objects.filter(company=request.user.company)
    return render(request, 'hr/employees-ui.html', {'employees': employees})

@login_required
@require_POST
def employees_add(request):
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
