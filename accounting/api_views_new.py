from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Sum
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from .models import (
    Account, AccountCategory, AccountGroup, Journal, JournalEntry, JournalItem,
    AccountPayable, AccountReceivable, BankAccount, BankReconciliation, TaxConfig, 
    Currency, FinancialStatement, AccountingAuditLog, RecurringJournal
)
from .serializers import (
    AccountSerializer, JournalSerializer, JournalEntrySerializer, JournalItemSerializer,
    AccountPayableSerializer, AccountReceivableSerializer, BankAccountSerializer,
    BankReconciliationSerializer, TaxConfigSerializer, CurrencySerializer,
    FinancialStatementSerializer, AccountingAuditLogSerializer, RecurringJournalSerializer
)


class AccountViewSet(viewsets.ModelViewSet):
    serializer_class = AccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Account.objects.filter(company=self.request.user.company).order_by('code')

    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get accounts filtered by type"""
        account_type = request.query_params.get('type')
        if account_type:
            accounts = self.get_queryset().filter(type=account_type)
            serializer = self.get_serializer(accounts, many=True)
            return Response(serializer.data)
        return Response({'error': 'Type parameter is required'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def chart_of_accounts(self, request):
        """Get complete chart of accounts in hierarchical format"""
        try:
            categories = AccountCategory.objects.filter(company=request.user.company).prefetch_related(
                'groups__accounts'
            ).order_by('code')
            
            coa_data = []
            for category in categories:
                category_data = {
                    'id': category.id,
                    'code': category.code,
                    'name': category.name,
                    'type': 'category',
                    'groups': []
                }
                
                for group in category.groups.all().order_by('code'):
                    group_data = {
                        'id': group.id,
                        'code': group.code,
                        'name': group.name,
                        'type': 'group',
                        'accounts': []
                    }
                    
                    for account in group.accounts.all().order_by('code'):
                        account_data = {
                            'id': account.id,
                            'code': account.code,
                            'name': account.name,
                            'type': 'account',
                            'account_type': account.account_type,
                            'balance_side': account.balance_side,
                            'is_active': account.is_active
                        }
                        group_data['accounts'].append(account_data)
                    
                    category_data['groups'].append(group_data)
                
                coa_data.append(category_data)
            
            return Response(coa_data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def balance(self, request, pk=None):
        """Get account balance"""
        account = self.get_object()
        
        # Calculate balance from journal items
        journal_items = JournalItem.objects.filter(account=account)
        total_debit = journal_items.aggregate(Sum('debit'))['debit__sum'] or Decimal('0.00')
        total_credit = journal_items.aggregate(Sum('credit'))['credit__sum'] or Decimal('0.00')
        
        # Calculate balance based on account's normal balance side
        if account.balance_side == 'debit':
            balance = total_debit - total_credit
        else:
            balance = total_credit - total_debit
        
        return Response({
            'account_id': account.id,
            'account_code': account.code,
            'account_name': account.name,
            'balance_side': account.balance_side,
            'total_debit': total_debit,
            'total_credit': total_credit,
            'balance': balance
        })


class JournalViewSet(viewsets.ModelViewSet):
    serializer_class = JournalSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Journal.objects.filter(company=self.request.user.company)


class JournalEntryViewSet(viewsets.ModelViewSet):
    serializer_class = JournalEntrySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return JournalEntry.objects.filter(company=self.request.user.company).order_by('-date', '-id')

    @action(detail=False, methods=['get'])
    def trial_balance(self, request):
        """Generate trial balance report"""
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        try:
            # Filter journal entries by date range if provided
            entries_filter = Q(company=request.user.company)
            if date_from:
                entries_filter &= Q(date__gte=date_from)
            if date_to:
                entries_filter &= Q(date__lte=date_to)
            
            # Get all accounts with their balances
            accounts = Account.objects.filter(company=request.user.company, is_active=True).order_by('code')
            trial_balance_data = []
            total_debit = Decimal('0.00')
            total_credit = Decimal('0.00')
            
            for account in accounts:
                # Get journal items for this account
                items = JournalItem.objects.filter(
                    account=account,
                    entry__in=JournalEntry.objects.filter(entries_filter)
                )
                
                account_debit = items.aggregate(Sum('debit'))['debit__sum'] or Decimal('0.00')
                account_credit = items.aggregate(Sum('credit'))['credit__sum'] or Decimal('0.00')
                
                # Calculate balance
                if account.balance_side == 'debit':
                    balance = account_debit - account_credit
                    if balance > 0:
                        debit_balance = balance
                        credit_balance = Decimal('0.00')
                    else:
                        debit_balance = Decimal('0.00')
                        credit_balance = abs(balance)
                else:
                    balance = account_credit - account_debit
                    if balance > 0:
                        credit_balance = balance
                        debit_balance = Decimal('0.00')
                    else:
                        credit_balance = Decimal('0.00')
                        debit_balance = abs(balance)
                
                # Only include accounts with non-zero balances
                if debit_balance > 0 or credit_balance > 0:
                    trial_balance_data.append({
                        'account_code': account.code,
                        'account_name': account.name,
                        'debit_balance': debit_balance,
                        'credit_balance': credit_balance
                    })
                    
                    total_debit += debit_balance
                    total_credit += credit_balance
            
            return Response({
                'trial_balance': trial_balance_data,
                'total_debit': total_debit,
                'total_credit': total_credit,
                'is_balanced': total_debit == total_credit,
                'date_from': date_from,
                'date_to': date_to
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class JournalItemViewSet(viewsets.ModelViewSet):
    serializer_class = JournalItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return JournalItem.objects.filter(entry__company=self.request.user.company)


class AccountPayableViewSet(viewsets.ModelViewSet):
    serializer_class = AccountPayableSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return AccountPayable.objects.filter(company=self.request.user.company)


class AccountReceivableViewSet(viewsets.ModelViewSet):
    serializer_class = AccountReceivableSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return AccountReceivable.objects.filter(company=self.request.user.company)


class BankAccountViewSet(viewsets.ModelViewSet):
    serializer_class = BankAccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return BankAccount.objects.filter(company=self.request.user.company)


class BankReconciliationViewSet(viewsets.ModelViewSet):
    serializer_class = BankReconciliationSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return BankReconciliation.objects.filter(company=self.request.user.company)


class TaxConfigViewSet(viewsets.ModelViewSet):
    serializer_class = TaxConfigSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return TaxConfig.objects.filter(company=self.request.user.company)


class CurrencyViewSet(viewsets.ModelViewSet):
    serializer_class = CurrencySerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Currency.objects.all()


class FinancialStatementViewSet(viewsets.ModelViewSet):
    serializer_class = FinancialStatementSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return FinancialStatement.objects.filter(company=self.request.user.company)


class AccountingAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AccountingAuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return AccountingAuditLog.objects.all()


class RecurringJournalViewSet(viewsets.ModelViewSet):
    serializer_class = RecurringJournalSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return RecurringJournal.objects.filter(journal__company=self.request.user.company)
