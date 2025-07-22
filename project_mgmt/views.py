from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Project
from django.views.decorators.http import require_POST

# Create your views here.

@login_required
def projects_ui(request):
    projects = Project.objects.filter(company=request.user.company)
    return render(request, 'project_mgmt/projects-ui.html', {'projects': projects})

@login_required
@require_POST
def projects_add(request):
    name = request.POST.get('name')
    status = request.POST.get('status')
    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')
    if not name:
        return JsonResponse({'success': False, 'error': 'Name is required.'}, status=400)
    project = Project.objects.create(
        company=request.user.company,
        name=name,
        status=status or '',
        start_date=start_date or None,
        end_date=end_date or None,
        created_by=request.user
    )
    return JsonResponse({
        'success': True,
        'project': {
            'id': project.id,
            'name': project.name,
            'status': project.status,
            'start_date': project.start_date or '',
            'end_date': project.end_date or ''
        }
    })

@login_required
@require_POST
def projects_edit(request, pk):
    project = get_object_or_404(Project, pk=pk, company=request.user.company)
    name = request.POST.get('name')
    status = request.POST.get('status')
    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')
    if not name:
        return JsonResponse({'success': False, 'error': 'Name is required.'}, status=400)
    project.name = name
    project.status = status or ''
    project.start_date = start_date or None
    project.end_date = end_date or None
    project.save()
    return JsonResponse({
        'success': True,
        'project': {
            'id': project.id,
            'name': project.name,
            'status': project.status,
            'start_date': project.start_date or '',
            'end_date': project.end_date or ''
        }
    })

@login_required
@require_POST
def projects_delete(request, pk):
    project = get_object_or_404(Project, pk=pk, company=request.user.company)
    project.delete()
    return JsonResponse({'success': True})
