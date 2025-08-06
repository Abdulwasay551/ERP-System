# Additional views for new project management models

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Sum
from django.utils import timezone
from .models import (
    Project, Milestone, ProjectDocument, ProjectExpense, 
    ProjectRisk, ProjectTeam, ProjectBilling
)
from hr.models import Employee

# ===================== MILESTONE VIEWS =====================

@login_required
def milestones_ui(request):
    """Display project milestones"""
    try:
        company = request.user.company
        project_id = request.GET.get('project')
        
        milestones = Milestone.objects.filter(project__company=company)
        
        if project_id:
            milestones = milestones.filter(project_id=project_id)
        
        milestones = milestones.select_related('project').order_by('target_date')
        
        # Get projects for filter
        projects = Project.objects.filter(company=company)
        
        context = {
            'milestones': milestones,
            'projects': projects,
            'selected_project': project_id
        }
        return render(request, 'project_mgmt/milestones-ui.html', context)
    except Exception as e:
        return render(request, 'project_mgmt/milestones-ui.html', {'error': str(e)})

@login_required
def milestone_add(request):
    """Add new milestone"""
    if request.method == 'POST':
        try:
            project_id = request.POST.get('project')
            project = get_object_or_404(Project, pk=project_id, company=request.user.company)
            
            milestone = Milestone.objects.create(
                project=project,
                name=request.POST.get('name'),
                description=request.POST.get('description', ''),
                target_date=request.POST.get('target_date'),
                percentage_complete=float(request.POST.get('percentage_complete', 0))
            )
            
            return JsonResponse({
                'success': True,
                'milestone': {
                    'id': milestone.id,
                    'name': milestone.name,
                    'project': milestone.project.name,
                    'target_date': milestone.target_date.strftime('%Y-%m-%d'),
                    'percentage_complete': float(milestone.percentage_complete)
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    # GET request
    projects = Project.objects.filter(company=request.user.company)
    return render(request, 'project_mgmt/milestone_form.html', {'projects': projects})

# ===================== PROJECT DOCUMENT VIEWS =====================

@login_required
def documents_ui(request):
    """Display project documents"""
    try:
        company = request.user.company
        project_id = request.GET.get('project')
        
        documents = ProjectDocument.objects.filter(project__company=company)
        
        if project_id:
            documents = documents.filter(project_id=project_id)
        
        documents = documents.select_related('project', 'uploaded_by').order_by('-created_at')
        
        projects = Project.objects.filter(company=company)
        
        context = {
            'documents': documents,
            'projects': projects,
            'selected_project': project_id
        }
        return render(request, 'project_mgmt/documents-ui.html', context)
    except Exception as e:
        return render(request, 'project_mgmt/documents-ui.html', {'error': str(e)})

@login_required
def document_add(request):
    """Add new document"""
    if request.method == 'POST':
        try:
            project_id = request.POST.get('project')
            project = get_object_or_404(Project, pk=project_id, company=request.user.company)
            
            document = ProjectDocument.objects.create(
                project=project,
                name=request.POST.get('name'),
                description=request.POST.get('description', ''),
                document_type=request.POST.get('document_type', 'other'),
                external_link=request.POST.get('external_link', ''),
                uploaded_by=request.user
            )
            
            if 'file' in request.FILES:
                document.file = request.FILES['file']
                document.save()
            
            return JsonResponse({
                'success': True,
                'document': {
                    'id': document.id,
                    'name': document.name,
                    'project': document.project.name,
                    'document_type': document.document_type
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    projects = Project.objects.filter(company=request.user.company)
    return render(request, 'project_mgmt/document_form.html', {'projects': projects})

# ===================== PROJECT EXPENSE VIEWS =====================

@login_required
def expenses_ui(request):
    """Display project expenses"""
    try:
        company = request.user.company
        project_id = request.GET.get('project')
        
        expenses = ProjectExpense.objects.filter(project__company=company)
        
        if project_id:
            expenses = expenses.filter(project_id=project_id)
        
        expenses = expenses.select_related('project', 'created_by').order_by('-expense_date')
        
        # Calculate totals
        total_amount = expenses.aggregate(total=Sum('amount'))['total'] or 0
        billable_amount = expenses.filter(is_billable=True).aggregate(total=Sum('amount'))['total'] or 0
        
        projects = Project.objects.filter(company=company)
        
        context = {
            'expenses': expenses,
            'projects': projects,
            'selected_project': project_id,
            'total_amount': total_amount,
            'billable_amount': billable_amount
        }
        return render(request, 'project_mgmt/expenses-ui.html', context)
    except Exception as e:
        return render(request, 'project_mgmt/expenses-ui.html', {'error': str(e)})

@login_required
def expense_add(request):
    """Add new expense"""
    if request.method == 'POST':
        try:
            project_id = request.POST.get('project')
            project = get_object_or_404(Project, pk=project_id, company=request.user.company)
            
            expense = ProjectExpense.objects.create(
                project=project,
                description=request.POST.get('description'),
                amount=float(request.POST.get('amount')),
                expense_type=request.POST.get('expense_type', 'other'),
                expense_date=request.POST.get('expense_date'),
                is_billable=request.POST.get('is_billable') == 'on',
                notes=request.POST.get('notes', ''),
                created_by=request.user
            )
            
            if 'receipt' in request.FILES:
                expense.receipt = request.FILES['receipt']
                expense.save()
            
            return JsonResponse({
                'success': True,
                'expense': {
                    'id': expense.id,
                    'description': expense.description,
                    'amount': float(expense.amount),
                    'expense_type': expense.expense_type,
                    'is_billable': expense.is_billable
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    projects = Project.objects.filter(company=request.user.company)
    return render(request, 'project_mgmt/expense_form.html', {'projects': projects})

# ===================== PROJECT RISK VIEWS =====================

@login_required
def risks_ui(request):
    """Display project risks"""
    try:
        company = request.user.company
        project_id = request.GET.get('project')
        
        risks = ProjectRisk.objects.filter(project__company=company)
        
        if project_id:
            risks = risks.filter(project_id=project_id)
        
        risks = risks.select_related('project', 'owner', 'created_by').order_by('-created_at')
        
        projects = Project.objects.filter(company=company)
        
        context = {
            'risks': risks,
            'projects': projects,
            'selected_project': project_id
        }
        return render(request, 'project_mgmt/risks-ui.html', context)
    except Exception as e:
        return render(request, 'project_mgmt/risks-ui.html', {'error': str(e)})

@login_required
def risk_add(request):
    """Add new risk"""
    if request.method == 'POST':
        try:
            project_id = request.POST.get('project')
            project = get_object_or_404(Project, pk=project_id, company=request.user.company)
            
            owner_id = request.POST.get('owner')
            owner = None
            if owner_id:
                owner = get_object_or_404(Employee, pk=owner_id, company=request.user.company)
            
            risk = ProjectRisk.objects.create(
                project=project,
                title=request.POST.get('title'),
                description=request.POST.get('description'),
                risk_type=request.POST.get('risk_type', 'other'),
                probability=request.POST.get('probability', 'medium'),
                impact=request.POST.get('impact', 'medium'),
                status=request.POST.get('status', 'identified'),
                mitigation_plan=request.POST.get('mitigation_plan', ''),
                owner=owner,
                created_by=request.user
            )
            
            return JsonResponse({
                'success': True,
                'risk': {
                    'id': risk.id,
                    'title': risk.title,
                    'risk_type': risk.risk_type,
                    'probability': risk.probability,
                    'impact': risk.impact,
                    'status': risk.status
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    projects = Project.objects.filter(company=request.user.company)
    employees = Employee.objects.filter(company=request.user.company)
    return render(request, 'project_mgmt/risk_form.html', {
        'projects': projects,
        'employees': employees
    })

# ===================== PROJECT TEAM VIEWS =====================

@login_required
def team_ui(request):
    """Display project team members"""
    try:
        company = request.user.company
        project_id = request.GET.get('project')
        
        team_members = ProjectTeam.objects.filter(project__company=company)
        
        if project_id:
            team_members = team_members.filter(project_id=project_id)
        
        team_members = team_members.select_related('project', 'employee').order_by('project__name', 'role')
        
        projects = Project.objects.filter(company=company)
        
        context = {
            'team_members': team_members,
            'projects': projects,
            'selected_project': project_id
        }
        return render(request, 'project_mgmt/team-ui.html', context)
    except Exception as e:
        return render(request, 'project_mgmt/team-ui.html', {'error': str(e)})

@login_required
def team_add(request):
    """Add team member to project"""
    if request.method == 'POST':
        try:
            project_id = request.POST.get('project')
            project = get_object_or_404(Project, pk=project_id, company=request.user.company)
            
            employee_id = request.POST.get('employee')
            employee = get_object_or_404(Employee, pk=employee_id, company=request.user.company)
            
            # Check if already exists
            if ProjectTeam.objects.filter(project=project, employee=employee).exists():
                return JsonResponse({'success': False, 'error': 'Employee already in project team'}, status=400)
            
            team_member = ProjectTeam.objects.create(
                project=project,
                employee=employee,
                role=request.POST.get('role', 'other'),
                permissions={}  # You can enhance this with actual permissions
            )
            
            return JsonResponse({
                'success': True,
                'team_member': {
                    'id': team_member.id,
                    'employee_name': f"{employee.first_name} {employee.last_name}",
                    'role': team_member.role,
                    'project': project.name
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    projects = Project.objects.filter(company=request.user.company)
    employees = Employee.objects.filter(company=request.user.company)
    return render(request, 'project_mgmt/team_form.html', {
        'projects': projects,
        'employees': employees
    })

# ===================== PROJECT BILLING VIEWS =====================

@login_required
def billing_ui(request):
    """Display project billing"""
    try:
        company = request.user.company
        project_id = request.GET.get('project')
        
        billings = ProjectBilling.objects.filter(project__company=company)
        
        if project_id:
            billings = billings.filter(project_id=project_id)
        
        billings = billings.select_related('project', 'created_by').order_by('-billing_period_start')
        
        projects = Project.objects.filter(company=company)
        
        # Calculate totals
        total_billed = billings.aggregate(total=Sum('total_amount'))['total'] or 0
        paid_amount = billings.filter(payment_status='paid').aggregate(total=Sum('total_amount'))['total'] or 0
        
        context = {
            'billings': billings,
            'projects': projects,
            'selected_project': project_id,
            'total_billed': total_billed,
            'paid_amount': paid_amount
        }
        return render(request, 'project_mgmt/billing-ui.html', context)
    except Exception as e:
        return render(request, 'project_mgmt/billing-ui.html', {'error': str(e)})

@login_required
def billing_add(request):
    """Add billing record"""
    if request.method == 'POST':
        try:
            project_id = request.POST.get('project')
            project = get_object_or_404(Project, pk=project_id, company=request.user.company)
            
            billing = ProjectBilling.objects.create(
                project=project,
                billing_period_start=request.POST.get('billing_period_start'),
                billing_period_end=request.POST.get('billing_period_end'),
                total_hours=float(request.POST.get('total_hours', 0)),
                billable_hours=float(request.POST.get('billable_hours', 0)),
                total_amount=float(request.POST.get('total_amount', 0)),
                expenses_amount=float(request.POST.get('expenses_amount', 0)),
                invoice_number=request.POST.get('invoice_number', ''),
                payment_status=request.POST.get('payment_status', 'draft'),
                notes=request.POST.get('notes', ''),
                created_by=request.user
            )
            
            if request.POST.get('invoice_date'):
                billing.invoice_date = request.POST.get('invoice_date')
                billing.save()
            
            return JsonResponse({
                'success': True,
                'billing': {
                    'id': billing.id,
                    'project': project.name,
                    'total_amount': float(billing.total_amount),
                    'payment_status': billing.payment_status
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    projects = Project.objects.filter(company=request.user.company)
    return render(request, 'project_mgmt/billing_form.html', {'projects': projects})
