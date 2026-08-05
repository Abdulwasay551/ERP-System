from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import Customer, CustomerLedger, Lead, Opportunity, CommunicationLog
from .serializers import CustomerSerializer, CustomerLedgerSerializer, LeadSerializer, OpportunitySerializer, CommunicationLogSerializer
from user_auth.permissions import RoleIn


class SalesStaff(RoleIn):
    allowed_roles = ['Manager', 'Cashier', 'Salesman']


class CustomerViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerSerializer
    # Customers are created/looked up constantly at checkout - any shop-floor role can
    # manage them (the old required_department='Sales', min_level=2 DepartmentLevelPermission
    # blocked Cashier/Salesman entirely, since they're level 3 and department 'Sales' only
    # matched the retired enterprise 'Sales Manager' role).
    permission_classes = [permissions.IsAuthenticated, SalesStaff]

    def get_queryset(self):
        qs = Customer.objects.filter(company=self.request.user.company)
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(phone__icontains=search) |
                Q(email__icontains=search) |
                Q(cnic__icontains=search)
            )
        return qs.order_by('name')

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company, created_by=self.request.user)

    @action(detail=True, methods=['get'])
    def ledger(self, request, pk=None):
        customer = self.get_object()
        entries = customer.ledger_entries.all().order_by('-transaction_date', '-created_at')
        serializer = CustomerLedgerSerializer(entries, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='outstanding-balance')
    def outstanding_balance(self, request, pk=None):
        customer = self.get_object()
        return Response({'customer_id': customer.id, 'outstanding_balance': str(customer.get_outstanding_balance())})

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