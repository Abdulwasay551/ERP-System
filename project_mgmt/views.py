from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Project

# Create your views here.

@login_required
def projects_ui(request):
    projects = Project.objects.filter(company=request.user.company)
    return render(request, 'project_mgmt/projects-ui.html', {'projects': projects})
