from rest_framework import serializers
from .models import Project, Task, TimeEntry, ProjectReport, ProjectContractor

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'

class TaskSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    
    class Meta:
        model = Task
        fields = '__all__'

class TimeEntrySerializer(serializers.ModelSerializer):
    task_name = serializers.CharField(source='task.title', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = TimeEntry
        fields = '__all__'

class ProjectReportSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    
    class Meta:
        model = ProjectReport
        fields = '__all__'

class ProjectContractorSerializer(serializers.ModelSerializer):
    contractor_name = serializers.CharField(source='contractor.partner.name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    contractor_email = serializers.CharField(source='contractor.partner.email', read_only=True)
    
    class Meta:
        model = ProjectContractor
        fields = '__all__' 