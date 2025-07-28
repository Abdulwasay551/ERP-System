from rest_framework import viewsets, permissions
from .models import Project, Task, TimeEntry, ProjectReport, ProjectContractor
from .serializers import ProjectSerializer, TaskSerializer, TimeEntrySerializer, ProjectReportSerializer, ProjectContractorSerializer

class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Project.objects.filter(company=self.request.user.company)

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Task.objects.filter(project__company=self.request.user.company)

class TimeEntryViewSet(viewsets.ModelViewSet):
    serializer_class = TimeEntrySerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return TimeEntry.objects.filter(task__project__company=self.request.user.company)

class ProjectReportViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return ProjectReport.objects.filter(project__company=self.request.user.company)

class ProjectContractorViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectContractorSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return ProjectContractor.objects.filter(company=self.request.user.company) 