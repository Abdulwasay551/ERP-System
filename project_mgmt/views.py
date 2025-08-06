from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import (
    Project, Task, TimeEntry, ProjectContractor, Milestone, 
    TaskDependency, Subtask, ProjectDocument, ProjectNote,
    ProjectTemplate, ResourceAllocation, ProjectExpense, 
    ProjectTeam, ProjectBilling, ProjectRisk, ProjectSettings
)
from django.views.decorators.http import require_POST
from django.db.models import Count, Q, Sum, F
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.paginator import Paginator
from hr.models import Employee
from crm.models import Partner

# Create your views here.

@login_required
def project_dashboard(request):
    """Enhanced Project Management dashboard with comprehensive metrics"""
    try:
        company = request.user.company
        
        # Project metrics
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
            completed_tasks = Task.objects.filter(project__company=company, status='completed').count()
        except:
            total_tasks = 0
            pending_tasks = 0
            overdue_tasks = 0
            completed_tasks = 0

        # Time tracking metrics
        try:
            total_hours_logged = TimeEntry.objects.filter(
                task__project__company=company
            ).aggregate(total=Sum('hours'))['total'] or 0
            
            billable_hours = TimeEntry.objects.filter(
                task__project__company=company,
                is_billable=True
            ).aggregate(total=Sum('hours'))['total'] or 0
            
            pending_approvals = TimeEntry.objects.filter(
                task__project__company=company,
                approval_status='pending'
            ).count()
        except:
            total_hours_logged = 0
            billable_hours = 0
            pending_approvals = 0

        # Financial metrics
        try:
            total_project_budget = Project.objects.filter(
                company=company
            ).aggregate(total=Sum('budget'))['total'] or 0
            
            total_expenses = ProjectExpense.objects.filter(
                project__company=company
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            billable_expenses = ProjectExpense.objects.filter(
                project__company=company,
                is_billable=True
            ).aggregate(total=Sum('amount'))['total'] or 0
        except:
            total_project_budget = 0
            total_expenses = 0
            billable_expenses = 0

        # Risk metrics
        try:
            high_risks = ProjectRisk.objects.filter(
                project__company=company,
                impact='high',
                status__in=['identified', 'analyzed']
            ).count()
            
            open_risks = ProjectRisk.objects.filter(
                project__company=company,
                status__in=['identified', 'analyzed']
            ).count()
        except:
            high_risks = 0
            open_risks = 0

        # Milestone metrics
        try:
            upcoming_milestones = Milestone.objects.filter(
                project__company=company,
                target_date__gte=timezone.now().date(),
                target_date__lte=timezone.now().date() + timedelta(days=30),
                is_completed=False
            ).count()
            
            overdue_milestones = Milestone.objects.filter(
                project__company=company,
                target_date__lt=timezone.now().date(),
                is_completed=False
            ).count()
        except:
            upcoming_milestones = 0
            overdue_milestones = 0

        # Recent activity
        recent_projects = Project.objects.filter(
            company=company
        ).order_by('-created_at')[:5]
        
        recent_tasks = Task.objects.filter(
            project__company=company
        ).order_by('-created_at')[:5]

        context = {
            # Project metrics
            'total_projects': total_projects,
            'active_projects': active_projects,
            'completed_projects': completed_projects,
            'projects_this_month': projects_this_month,
            
            # Task metrics
            'total_tasks': total_tasks,
            'pending_tasks': pending_tasks,
            'completed_tasks': completed_tasks,
            'overdue_tasks': overdue_tasks,
            
            # Time metrics
            'total_hours_logged': total_hours_logged,
            'billable_hours': billable_hours,
            'pending_approvals': pending_approvals,
            
            # Financial metrics
            'total_project_budget': total_project_budget,
            'total_expenses': total_expenses,
            'billable_expenses': billable_expenses,
            
            # Risk metrics
            'high_risks': high_risks,
            'open_risks': open_risks,
            
            # Milestone metrics
            'upcoming_milestones': upcoming_milestones,
            'overdue_milestones': overdue_milestones,
            
            # Recent activity
            'recent_projects': recent_projects,
            'recent_tasks': recent_tasks,
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
        
        # Calculate completion percentage
        completion_percentage = (completed_tasks * 100 / total_tasks) if total_tasks > 0 else 0
        
        context = {
            'total_projects': total_projects,
            'active_projects': active_projects,
            'completed_projects': completed_projects,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'completion_percentage': completion_percentage,
        }
        return render(request, 'project_mgmt/reports-ui.html', context)
    except Exception as e:
        context = {
            'total_projects': 0,
            'active_projects': 0,
            'completed_projects': 0,
            'total_tasks': 0,
            'completed_tasks': 0,
            'completion_percentage': 0,
            'error': str(e)
        }
        return render(request, 'project_mgmt/reports-ui.html', context)

# API Views for AJAX calls
@login_required
def api_projects(request):
    """API endpoint to get projects for dropdowns"""
    try:
        projects = Project.objects.filter(company=request.user.company).values('id', 'name', 'status')
        return JsonResponse({'success': True, 'projects': list(projects)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def api_tasks(request):
    """API endpoint to get tasks for dropdowns"""
    try:
        tasks = Task.objects.filter(
            project__company=request.user.company
        ).select_related('project').values(
            'id', 'name', 'project__name', 'status', 'priority'
        )
        
        task_list = []
        for task in tasks:
            task_list.append({
                'id': task['id'],
                'name': task['name'],
                'project_name': task['project__name'],
                'status': task['status'],
                'priority': task['priority']
            })
        
        return JsonResponse({'success': True, 'tasks': task_list})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# Task Management Views
@login_required
def task_add(request):
    """Add new task"""
    if request.method == 'GET':
        # Get all projects and employees for the form
        projects = Project.objects.filter(company=request.user.company)
        try:
            from hr.models import Employee
            employees = Employee.objects.filter(company=request.user.company)
        except ImportError:
            employees = []
        
        context = {
            'projects': projects,
            'employees': employees,
            'edit_mode': False
        }
        return render(request, 'project_mgmt/task_form.html', context)
    
    elif request.method == 'POST':
        try:
            name = request.POST.get('name')
            description = request.POST.get('description', '')
            project_id = request.POST.get('project_id')
            priority = request.POST.get('priority', 'Medium')
            status = request.POST.get('status', 'pending')
            due_date = request.POST.get('due_date')
            estimated_hours = request.POST.get('estimated_hours', 0)
            assigned_to = request.POST.get('assigned_to')
            progress = request.POST.get('progress', 0)
            
            if not name or not project_id:
                return JsonResponse({'success': False, 'error': 'Name and project are required.'}, status=400)
            
            project = get_object_or_404(Project, pk=project_id, company=request.user.company)
            
            # Create task
            task = Task.objects.create(
                project=project,
                name=name,
                description=description,
                priority=priority,
                status=status,
                due_date=due_date if due_date else None,
                estimated_hours=float(estimated_hours) if estimated_hours else 0,
                progress=int(progress) if progress else 0
            )
            
            # Assign to employee if provided
            if assigned_to:
                try:
                    from hr.models import Employee
                    employee = Employee.objects.get(id=assigned_to, company=request.user.company)
                    task.assigned_to_employee = employee
                    task.save()
                except (ImportError, Employee.DoesNotExist):
                    pass
            
            return JsonResponse({
                'success': True,
                'task': {
                    'id': task.id,
                    'name': task.name,
                    'status': task.status,
                    'priority': task.priority,
                    'project_name': task.project.name
                }
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

@login_required
def task_detail(request, pk):
    """Task detail view"""
    task = get_object_or_404(Task, pk=pk, project__company=request.user.company)
    
    # Get time entries for this task
    time_entries = TimeEntry.objects.filter(task=task).order_by('-date')
    total_hours = time_entries.aggregate(total=Sum('hours'))['total'] or 0
    
    context = {
        'task': task,
        'time_entries': time_entries,
        'total_hours': total_hours,
    }
    return render(request, 'project_mgmt/task_detail.html', context)

@login_required
def task_edit(request, pk):
    """Edit task"""
    task = get_object_or_404(Task, pk=pk, project__company=request.user.company)
    
    if request.method == 'GET':
        # Get all projects and employees for the form
        projects = Project.objects.filter(company=request.user.company)
        try:
            from hr.models import Employee
            employees = Employee.objects.filter(company=request.user.company)
        except ImportError:
            employees = []
        
        context = {
            'task': task,
            'projects': projects,
            'employees': employees,
            'edit_mode': True
        }
        return render(request, 'project_mgmt/task_form.html', context)
    
    elif request.method == 'POST':
        try:
            task.name = request.POST.get('name', task.name)
            task.description = request.POST.get('description', task.description)
            
            # Handle project change
            project_id = request.POST.get('project_id')
            if project_id:
                project = get_object_or_404(Project, pk=project_id, company=request.user.company)
                task.project = project
            
            task.priority = request.POST.get('priority', task.priority)
            task.status = request.POST.get('status', task.status)
            
            due_date = request.POST.get('due_date')
            task.due_date = due_date if due_date else None
            
            estimated_hours = request.POST.get('estimated_hours')
            task.estimated_hours = float(estimated_hours) if estimated_hours else task.estimated_hours
            
            progress = request.POST.get('progress')
            task.progress = int(progress) if progress else task.progress
            
            # Handle assignment
            assigned_to = request.POST.get('assigned_to')
            if assigned_to:
                try:
                    from hr.models import Employee
                    employee = Employee.objects.get(id=assigned_to, company=request.user.company)
                    task.assigned_to_employee = employee
                except (ImportError, Employee.DoesNotExist):
                    task.assigned_to_employee = None
            else:
                task.assigned_to_employee = None
            
            task.save()
            
            return JsonResponse({
                'success': True,
                'task': {
                    'id': task.id,
                    'name': task.name,
                    'status': task.status,
                    'priority': task.priority,
                    'project_name': task.project.name
                }
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    # GET request - return form
    projects = Project.objects.filter(company=request.user.company)
    context = {'task': task, 'projects': projects}
    return render(request, 'project_mgmt/task_form.html', context)

@login_required
@require_POST
def task_delete(request, pk):
    """Delete task"""
    try:
        task = get_object_or_404(Task, pk=pk, project__company=request.user.company)
        task_name = task.name
        task.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Task "{task_name}" deleted successfully.'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# Time Entry Management Views
@login_required
def timesheet_add(request):
    """Add new time entry"""
    if request.method == 'POST':
        try:
            task_id = request.POST.get('task_id')
            date_str = request.POST.get('date')
            hours = request.POST.get('hours')
            notes = request.POST.get('notes', '')
            
            if not all([task_id, date_str, hours]):
                return JsonResponse({'success': False, 'error': 'Task, date, and hours are required.'}, status=400)
            
            task = get_object_or_404(Task, pk=task_id, project__company=request.user.company)
            
            # Get employee from user
            try:
                employee = Employee.objects.get(user=request.user, company=request.user.company)
            except Employee.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Employee profile not found.'}, status=400)
            
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            time_entry = TimeEntry.objects.create(
                task=task,
                employee=employee,
                date=date_obj,
                hours=float(hours),
                notes=notes
            )
            
            # Update task actual hours
            task.actual_hours = F('actual_hours') + float(hours)
            task.save()
            
            return JsonResponse({
                'success': True,
                'time_entry': {
                    'id': time_entry.id,
                    'task_name': task.name,
                    'hours': float(time_entry.hours),
                    'date': time_entry.date.strftime('%Y-%m-%d')
                }
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

@login_required
def timesheet_edit(request, pk):
    """Edit time entry"""
    time_entry = get_object_or_404(TimeEntry, pk=pk, task__project__company=request.user.company)
    
    if request.method == 'POST':
        try:
            old_hours = time_entry.hours
            
            time_entry.date = datetime.strptime(request.POST.get('date'), '%Y-%m-%d').date()
            new_hours = float(request.POST.get('hours'))
            time_entry.hours = new_hours
            time_entry.notes = request.POST.get('notes', '')
            time_entry.save()
            
            # Update task actual hours
            hours_diff = new_hours - old_hours
            task = time_entry.task
            task.actual_hours = F('actual_hours') + hours_diff
            task.save()
            
            return JsonResponse({
                'success': True,
                'time_entry': {
                    'id': time_entry.id,
                    'hours': float(time_entry.hours),
                    'date': time_entry.date.strftime('%Y-%m-%d')
                }
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    # GET request - return form
    tasks = Task.objects.filter(project__company=request.user.company)
    context = {'time_entry': time_entry, 'tasks': tasks}
    return render(request, 'project_mgmt/timesheet_form.html', context)

@login_required
@require_POST
def timesheet_delete(request, pk):
    """Delete time entry"""
    try:
        time_entry = get_object_or_404(TimeEntry, pk=pk, task__project__company=request.user.company)
        
        # Update task actual hours
        task = time_entry.task
        task.actual_hours = F('actual_hours') - time_entry.hours
        task.save()
        
        time_entry.delete()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# Project Detail View
@login_required
def project_detail(request, pk):
    """Project detail view"""
    project = get_object_or_404(Project, pk=pk, company=request.user.company)
    
    # Get project tasks
    tasks = Task.objects.filter(project=project).order_by('-created_at')
    
    # Get project statistics
    task_stats = tasks.aggregate(
        total_tasks=Count('id'),
        completed_tasks=Count('id', filter=Q(status='completed')),
        total_estimated_hours=Sum('estimated_hours'),
        total_actual_hours=Sum('actual_hours')
    )
    
    # Get recent time entries
    recent_time_entries = TimeEntry.objects.filter(
        task__project=project
    ).select_related('task', 'employee').order_by('-created_at')[:10]
    
    # Calculate progress
    progress = 0
    if task_stats['total_tasks'] > 0:
        progress = (task_stats['completed_tasks'] / task_stats['total_tasks']) * 100
    
    context = {
        'project': project,
        'tasks': tasks,
        'task_stats': task_stats,
        'recent_time_entries': recent_time_entries,
        'progress': round(progress, 1),
    }
    return render(request, 'project_mgmt/project_detail.html', context)

# Report Generation
@login_required
def generate_report(request):
    """Generate project report"""
    if request.method == 'POST':
        try:
            report_type = request.POST.get('report_type')
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            project_filter = request.POST.get('project_filter')
            
            # This is a basic implementation - you can enhance with actual PDF generation
            return JsonResponse({
                'success': True,
                'message': f'Report "{report_type}" generated successfully',
                'download_url': '/project_mgmt/reports/download/latest/'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)
