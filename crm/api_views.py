from rest_framework import viewsets, permissions
from .models import Customer, Lead, Opportunity, CommunicationLog
from .serializers import CustomerSerializer, LeadSerializer, OpportunitySerializer, CommunicationLogSerializer
from user_auth.permissions import DepartmentLevelPermission

class CustomerViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated, DepartmentLevelPermission]
    required_department = 'Sales'
    min_level = 2
    def get_queryset(self):
        return Customer.objects.filter(company=self.request.user.company)

class LeadViewSet(viewsets.ModelViewSet):
    serializer_class = LeadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Lead.objects.filter(company=self.request.user.company)

class OpportunityViewSet(viewsets.ModelViewSet):
    serializer_class = OpportunitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Opportunity.objects.filter(company=self.request.user.company)

class CommunicationLogViewSet(viewsets.ModelViewSet):
    serializer_class = CommunicationLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CommunicationLog.objects.filter(company=self.request.user.company) 