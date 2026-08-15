from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.http import HttpResponse
from .models import Customer, CustomerLedger, CustomerLedgerAdjustment, Lead, Opportunity, CommunicationLog
from .serializers import (
    CustomerSerializer, CustomerLedgerSerializer, CustomerLedgerAdjustmentSerializer,
    LeadSerializer, OpportunitySerializer, CommunicationLogSerializer,
)
from user_auth.permissions import RoleIn, IsOwnerOrManager
from core.pdf_utils import build_ledger_pdf
from core.mixins import SoftDeleteViewSetMixin
from core.idempotency import IdempotentCreateMixin
from core.pk_conflict import PkConflictReportingMixin, save_with_pk_fallback


class SalesStaff(RoleIn):
    allowed_roles = ['Manager', 'Cashier', 'Salesman']


class CustomerViewSet(IdempotentCreateMixin, PkConflictReportingMixin, SoftDeleteViewSetMixin, viewsets.ModelViewSet):
    serializer_class = CustomerSerializer
    # Customers are created/looked up constantly at checkout - any shop-floor role can
    # manage them (the old required_department='Sales', min_level=2 DepartmentLevelPermission
    # blocked Cashier/Salesman entirely, since they're level 3 and department 'Sales' only
    # matched the retired enterprise 'Sales Manager' role).
    permission_classes = [permissions.IsAuthenticated, SalesStaff]
    filterset_fields = ['customer_group']
    ordering_fields = ['name', 'customer_code', 'created_at']

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
        from core.device_registry import validated_desktop_pk, validated_desktop_number
        company = self.request.user.company
        explicit_id = validated_desktop_pk(self.request.data, 'customer', company)
        extra = {}
        explicit_code = validated_desktop_number(self.request.data, 'customer_code', company)
        if explicit_code:
            extra['customer_code'] = explicit_code
        conflict = save_with_pk_fallback(serializer, explicit_id, company=company, created_by=self.request.user, **extra)
        if conflict:
            self._pk_conflicts = [{'model': 'crm.Customer', **conflict}]

    @action(detail=True, methods=['get'])
    def ledger(self, request, pk=None):
        customer = self.get_object()
        entries = customer.ledger_entries.all().order_by('-transaction_date', '-created_at')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        if date_from:
            entries = entries.filter(transaction_date__gte=date_from)
        if date_to:
            entries = entries.filter(transaction_date__lte=date_to)

        try:
            page = max(int(request.query_params.get('page', 1)), 1)
            page_size = min(max(int(request.query_params.get('page_size', 25)), 1), 200)
        except ValueError:
            page = 1
            page_size = 25

        count = entries.count()
        start = (page - 1) * page_size
        page_entries = entries[start:start + page_size]
        return Response({
            'count': count,
            'page': page,
            'page_size': page_size,
            'total_pages': (count + page_size - 1) // page_size if count else 1,
            'results': CustomerLedgerSerializer(page_entries, many=True).data,
        })

    @action(detail=True, methods=['get'], url_path='ledger/pdf')
    def ledger_pdf(self, request, pk=None):
        customer = self.get_object()
        entries = customer.ledger_entries.all().order_by('transaction_date', 'created_at')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        if date_from:
            entries = entries.filter(transaction_date__gte=date_from)
        if date_to:
            entries = entries.filter(transaction_date__lte=date_to)
        entries = list(entries)
        closing_balance = entries[-1].balance if entries else customer.get_outstanding_balance()
        buf = build_ledger_pdf(customer.name, 'Customer', entries, date_from, date_to, closing_balance)
        response = HttpResponse(buf.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{customer.name}-ledger.pdf"'
        return response

    @action(detail=True, methods=['get'], url_path='outstanding-balance')
    def outstanding_balance(self, request, pk=None):
        customer = self.get_object()
        return Response({'customer_id': customer.id, 'outstanding_balance': str(customer.get_outstanding_balance())})


class CustomerLedgerAdjustmentViewSet(IdempotentCreateMixin, SoftDeleteViewSetMixin, viewsets.ModelViewSet):
    """Manual debit/credit against a customer's ledger - not tied to an invoice/payment.
    Owner/Manager only (not SalesStaff like CustomerViewSet): this directly manipulates a
    customer's balance with no invoice/bill paper trail behind it."""
    serializer_class = CustomerLedgerAdjustmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]
    filterset_fields = ['customer', 'entry_type']
    ordering_fields = ['transaction_date', 'amount', 'created_at']

    def get_queryset(self):
        return CustomerLedgerAdjustment.objects.filter(company=self.request.user.company)

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company, created_by=self.request.user)


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