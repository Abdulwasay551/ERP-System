from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Project, Task, TimeEntry
from django.views.decorators.http import require_POST
from django.db.models import Count, Q, Sum, F
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.paginator import Paginator

# Create your views here.

@login_required
def project_dashboard(request):
    """Project Management module dashboard with key metrics and quick access"""
    try:
        company = request.user.company
        
        # Key metrics
        total_projects = Project.objects.filter(company=company).count()
        active_projects = Project.objects.filter(company=company, status='active').count()
        completed_projects = Project.objects.filter(company=company, status='completed').count()
        projects_this_month = Project.objects.filter(
            company=company, 
            created_at__gte=timezone.now().replace(day=1)
        ).count()
        
        # Task metrics
        try:
            total_tasks = Task.objects.filter(project__company=company).count()
            pending_tasks = Task.objects.filter(project__company=company, status='pending').count()
            overdue_tasks = Task.objects.filter(
                project__company=company, 
                due_date__lt=timezone.now().date(),
                status__in=['pending', 'in_progress']
            ).count()
        except:
            total_tasks = 0
            pending_tasks = 0
            overdue_tasks = 0
        
        # Recent projects
        recent_projects = Project.objects.filter(
            company=company
        ).order_by('-created_at')[:5]
        
        context = {
            'total_projects': total_projects,
            'active_projects': active_projects,
            'completed_projects': completed_projects,
            'projects_this_month': projects_this_month,
            'recent_projects': recent_projects,
            'total_tasks': total_tasks,
            'pending_tasks': pending_tasks,
            'overdue_tasks': overdue_tasks,
        }
        return render(request, 'project_mgmt/dashboard.html', context)
    except Exception as e:
        context = {
            'total_projects': 0,
            'active_projects': 0,
            'completed_projects': 0,
            'projects_this_month': 0,
            'recent_projects': [],
            'total_tasks': 0,
            'pending_tasks': 0,
            'overdue_tasks': 0,
            'error': str(e)
        }
        return render(request, 'project_mgmt/dashboard.html', context)

@login_required
def projects_ui(request):
    """Display projects with filtering and pagination"""
    try:
        company = request.user.company
        
        # Get filter parameters
        search = request.GET.get('search', '')
        status = request.GET.get('status', '')
        
        # Build query
        projects = Project.objects.filter(company=company)
        
        if search:
            projects = projects.filter(
                Q(name__icontains=search) | 
                Q(description__icontains=search)
            )
        
        if status:
            projects = projects.filter(status=status)
        
        # Pagination
        paginator = Paginator(projects.order_by('-created_at'), 20)
        page_number = request.GET.get('page')
        projects = paginator.get_page(page_number)
        
        context = {
            'projects': projects,
            'search': search,
            'status': status,
        }
        return render(request, 'project_mgmt/projects-ui.html', context)
    except Exception as e:
        context = {
            'projects': [],
            'error': str(e)
        }
        return render(request, 'project_mgmt/projects-ui.html', context)

@login_required
def projects_add(request):
    """Handle both GET and POST for project creation"""
    if request.method == 'GET':
        return render(request, 'project_mgmt/project_form.html')
    
    elif request.method == 'POST':
        try:
            name = request.POST.get('name')
            description = request.POST.get('description', '')
            status = request.POST.get('status', 'active')
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            
            if not name:
                return JsonResponse({'success': False, 'error': 'Name is required.'}, status=400)
            
            project = Project.objects.create(
                company=request.user.company,
                name=name,
                description=description,
                status=status,
                start_date=start_date if start_date else None,
                end_date=end_date if end_date else None,
                created_by=request.user
            )
            return JsonResponse({
                'success': True,
                'project': {
                    'id': project.id,
                    'name': project.name,
                    'status': project.status,
                    'start_date': project.start_date.strftime('%Y-%m-%d') if project.start_date else '',
                    'end_date': project.end_date.strftime('%Y-%m-%d') if project.end_date else ''
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def projects_edit(request, pk):
    """Handle both GET and POST for project editing"""
    project = get_object_or_404(Project, pk=pk, company=request.user.company)
    
    if request.method == 'GET':
        return render(request, 'project_mgmt/project_form.html', {
            'project': project,
            'edit_mode': True
        })
    
    elif request.method == 'POST':
        try:
            name = request.POST.get('name')
            description = request.POST.get('description', '')
            status = request.POST.get('status', 'active')
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            
            if not name:
                return JsonResponse({'success': False, 'error': 'Name is required.'}, status=400)
            
            project.name = name
            project.description = description
            project.status = status
            project.start_date = start_date if start_date else None
            project.end_date = end_date if end_date else None
            project.save()
            
            return JsonResponse({
                'success': True,
                'project': {
                    'id': project.id,
                    'name': project.name,
                    'status': project.status,
                    'start_date': project.start_date.strftime('%Y-%m-%d') if project.start_date else '',
                    'end_date': project.end_date.strftime('%Y-%m-%d') if project.end_date else ''
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def projects_delete(request, pk):
    """Handle project deletion"""
    if request.method == 'POST':
        try:
            project = get_object_or_404(Project, pk=pk, company=request.user.company)
            project_name = project.name
            project.delete()
            return JsonResponse({
                'success': True,
                'message': f'Project "{project_name}" deleted successfully.'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

@login_required
def tasks_ui(request):
    """Display tasks"""
    try:
        company = request.user.company
        
        # Get tasks if model exists
        try:
            tasks = Task.objects.filter(project__company=company).select_related('project').order_by('-created_at')[:20]
        except:
            tasks = []
        
        context = {
            'tasks': tasks,
        }
        return render(request, 'project_mgmt/tasks-ui.html', context)
    except Exception as e:
        context = {
            'tasks': [],
            'error': str(e)
        }
        return render(request, 'project_mgmt/tasks-ui.html', context)

@login_required
def timesheets_ui(request):
    """Display timesheets"""
    try:
        company = request.user.company
        
        # Get time entries if model exists
        try:
            timesheets = TimeEntry.objects.filter(task__project__company=company).select_related('task', 'employee').order_by('-created_at')[:20]
        except:
            timesheets = []
        
        context = {
            'timesheets': timesheets,
        }
        return render(request, 'project_mgmt/timesheets-ui.html', context)
    except Exception as e:
        context = {
            'timesheets': [],
            'error': str(e)
        }
        return render(request, 'project_mgmt/timesheets-ui.html', context)

@login_required
def reports_ui(request):
    """Display project reports"""
    try:
        company = request.user.company
        
        # Project metrics
        total_projects = Project.objects.filter(company=company).count()
        active_projects = Project.objects.filter(company=company, status='active').count()
        completed_projects = Project.objects.filter(company=company, status='completed').count()
        
        # Task metrics if available
        try:
            total_tasks = Task.objects.filter(project__company=company).count()
            completed_tasks = Task.objects.filter(project__company=company, status='completed').count()
        except:
            total_tasks = 0
            completed_tasks = 0
        
        context = {
            'total_projects': total_projects,
            'active_projects': active_projects,
            'completed_projects': completed_projects,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
        }
        return render(request, 'project_mgmt/reports-ui.html', context)
    except Exception as e:
        context = {
            'total_projects': 0,
            'active_projects': 0,
            'completed_projects': 0,
            'total_tasks': 0,
            'completed_tasks': 0,
            'error': str(e)
        }
        return render(request, 'project_mgmt/reports-ui.html', context)
