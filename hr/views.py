from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Employee

# Create your views here.

@login_required
def employees_ui(request):
    employees = Employee.objects.filter(company=request.user.company)
    return render(request, 'hr/employees-ui.html', {'employees': employees})
