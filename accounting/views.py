from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Account, AccountGroup, AccountCategory, Journal, JournalEntry
from django.views.decorators.http import require_POST
from django.db.models import Count, Sum, Q, F
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.paginator import Paginator

# Create your views here.

@login_required
def accounting_dashboard(request):
    """Accounting module dashboard with key metrics and quick access"""
    try:
        company = request.user.company
        
        # Key metrics
        total_accounts = Account.objects.filter(company=company, is_active=True).count()
        asset_accounts = Account.objects.filter(company=company, type='asset', is_active=True).count()
        liability_accounts = Account.objects.filter(company=company, type='liability', is_active=True).count()
        equity_accounts = Account.objects.filter(company=company, type='equity', is_active=True).count()
        
        # Account groups breakdown with proper company filtering
        account_groups = AccountGroup.objects.filter(company=company).annotate(
            account_count=Count('accounts', filter=Q(accounts__is_active=True))
        ).filter(account_count__gt=0).order_by('-account_count')[:5]
        
        # Recent accounts with balance calculation
        recent_accounts = Account.objects.filter(
            company=company
        ).order_by('-created_at')[:5]
        
        # Add calculated balance for each account
        for account in recent_accounts:
            # Calculate balance from journal items
            total_debit = account.journal_items.aggregate(
                total=Sum('debit')
            )['total'] or 0
            total_credit = account.journal_items.aggregate(
                total=Sum('credit')
            )['total'] or 0
            
            # Calculate balance based on account type
            if account.balance_side == 'debit':
                account.balance = total_debit - total_credit
            else:
                account.balance = total_credit - total_debit
        
        context = {
            'total_accounts': total_accounts,
            'asset_accounts': asset_accounts,
            'liability_accounts': liability_accounts,
            'equity_accounts': equity_accounts,
            'account_groups': account_groups,
            'recent_accounts': recent_accounts,
        }
        return render(request, 'accounting/dashboard.html', context)
    except Exception as e:
        context = {
            'total_accounts': 0,
            'asset_accounts': 0,
            'liability_accounts': 0,
            'equity_accounts': 0,
            'account_groups': [],
            'recent_accounts': [],
            'error': str(e)
        }
        return render(request, 'accounting/dashboard.html', context)

@login_required
def accounts_ui(request):
    """Display accounts with filtering and pagination"""
    try:
        company = request.user.company
        
        # Get filter parameters
        search = request.GET.get('search', '')
        account_type = request.GET.get('type', '')
        status = request.GET.get('status', '')
        group_id = request.GET.get('group', '')
        
        # Build query
        accounts = Account.objects.filter(company=company)
        
        if search:
            accounts = accounts.filter(
                Q(name__icontains=search) | 
                Q(code__icontains=search) |
                Q(description__icontains=search)
            )
        
        if account_type:
            accounts = accounts.filter(type=account_type)
            
        if status == 'active':
            accounts = accounts.filter(is_active=True)
        elif status == 'inactive':
            accounts = accounts.filter(is_active=False)
            
        if group_id:
            accounts = accounts.filter(group_id=group_id)
        
        # Add balance calculation
        for account in accounts:
            total_debit = account.journal_items.aggregate(
                total=Sum('debit')
            )['total'] or 0
            total_credit = account.journal_items.aggregate(
                total=Sum('credit')
            )['total'] or 0
            
            if account.balance_side == 'debit':
                account.balance = total_debit - total_credit
            else:
                account.balance = total_credit - total_debit
        
        # Get account groups for filter dropdown
        account_groups = AccountGroup.objects.filter(company=company, is_active=True)
        
        # Pagination
        paginator = Paginator(accounts.order_by('-created_at'), 20)
        page_number = request.GET.get('page')
        accounts = paginator.get_page(page_number)
        
        context = {
            'accounts': accounts,
            'account_groups': account_groups,
            'search': search,
            'account_type': account_type,
            'status': status,
            'group_id': group_id,
        }
        return render(request, 'accounting/accounts-ui.html', context)
    except Exception as e:
        context = {
            'accounts': [],
            'account_groups': [],
            'error': str(e)
        }
        return render(request, 'accounting/accounts-ui.html', context)

@login_required
def accounts_add(request):
    """Handle both GET and POST for account creation"""
    if request.method == 'GET':
        # Show form for creating account
        account_groups = AccountGroup.objects.filter(company=request.user.company, is_active=True)
        return render(request, 'accounting/account_form.html', {'account_groups': account_groups})
    
    elif request.method == 'POST':
        try:
            company = request.user.company
            code = request.POST.get('code')
            name = request.POST.get('name')
            type_ = request.POST.get('type')
            group_id = request.POST.get('group')
            description = request.POST.get('description', '')
            account_type = request.POST.get('account_type', '')
            balance_side = request.POST.get('balance_side', 'debit')
            is_active = request.POST.get('is_active') == 'on'
            
            if not code or not name or not type_:
                return JsonResponse({'success': False, 'error': 'Code, name, and type are required.'}, status=400)
            
            # Get group if specified
            group = None
            if group_id:
                group = AccountGroup.objects.filter(company=company, id=group_id).first()
                if not group:
                    return JsonResponse({'success': False, 'error': 'Group not found.'}, status=400)
            
            # Check for duplicate code
            if Account.objects.filter(company=company, code=code).exists():
                return JsonResponse({'success': False, 'error': 'Account code already exists.'}, status=400)
            
            account = Account.objects.create(
                company=company,
                code=code,
                name=name,
                type=type_,
                group=group,
                description=description,
                account_type=account_type,
                balance_side=balance_side,
                is_active=is_active
            )
            
            return JsonResponse({
                'success': True,
                'account': {
                    'id': account.id,
                    'code': account.code,
                    'name': account.name,
                    'type': account.get_type_display(),
                    'group': account.group.name if account.group else None,
                    'is_active': account.is_active
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def accounts_edit(request, pk):
    """Handle both GET and POST for account editing"""
    account = get_object_or_404(Account, pk=pk, company=request.user.company)
    
    if request.method == 'GET':
        account_groups = AccountGroup.objects.filter(company=request.user.company, is_active=True)
        return render(request, 'accounting/account_form.html', {
            'account': account,
            'account_groups': account_groups,
            'edit_mode': True
        })
    
    elif request.method == 'POST':
        try:
            code = request.POST.get('code')
            name = request.POST.get('name')
            type_ = request.POST.get('type')
            group_id = request.POST.get('group')
            description = request.POST.get('description', '')
            account_type = request.POST.get('account_type', '')
            balance_side = request.POST.get('balance_side', 'debit')
            is_active = request.POST.get('is_active') == 'on'
            
            if not code or not name or not type_:
                return JsonResponse({'success': False, 'error': 'Code, name, and type are required.'}, status=400)
            
            # Check for duplicate code (excluding current account)
            if Account.objects.filter(company=request.user.company, code=code).exclude(pk=pk).exists():
                return JsonResponse({'success': False, 'error': 'Account code already exists.'}, status=400)
            
            # Get group if specified
            group = None
            if group_id:
                group = AccountGroup.objects.filter(company=request.user.company, id=group_id).first()
                if not group:
                    return JsonResponse({'success': False, 'error': 'Group not found.'}, status=400)
            
            account.code = code
            account.name = name
            account.type = type_
            account.group = group
            account.description = description
            account.account_type = account_type
            account.balance_side = balance_side
            account.is_active = is_active
            account.save()
            
            return JsonResponse({
                'success': True,
                'account': {
                    'id': account.id,
                    'code': account.code,
                    'name': account.name,
                    'type': account.get_type_display(),
                    'group': account.group.name if account.group else None,
                    'is_active': account.is_active
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def accounts_delete(request, pk):
    """Handle account deletion with validation"""
    if request.method == 'POST':
        try:
            account = get_object_or_404(Account, pk=pk, company=request.user.company)
            
            # Check if account has journal entries
            if account.journal_items.exists():
                return JsonResponse({
                    'success': False, 
                    'error': 'Cannot delete account with journal entries. Please make it inactive instead.'
                }, status=400)
            
            account_name = account.name
            account.delete()
            return JsonResponse({
                'success': True,
                'message': f'Account "{account_name}" deleted successfully.'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

@login_required
def journals_ui(request):
    """Display journal entries with filtering"""
    try:
        company = request.user.company
        
        # Get journals
        journals = Journal.objects.filter(company=company, is_active=True)
        
        # Get recent journal entries
        recent_entries = JournalEntry.objects.filter(
            company=company
        ).select_related('journal', 'created_by').order_by('-created_at')[:10]
        
        context = {
            'journals': journals,
            'recent_entries': recent_entries,
        }
        return render(request, 'accounting/journals-ui.html', context)
    except Exception as e:
        context = {
            'journals': [],
            'recent_entries': [],
            'error': str(e)
        }
        return render(request, 'accounting/journals-ui.html', context)

@login_required
def ledger_ui(request):
    """Display general ledger"""
    try:
        company = request.user.company
        
        # Get accounts with their balances
        accounts = Account.objects.filter(company=company, is_active=True)
        
        for account in accounts:
            total_debit = account.journal_items.aggregate(
                total=Sum('debit')
            )['total'] or 0
            total_credit = account.journal_items.aggregate(
                total=Sum('credit')
            )['total'] or 0
            
            if account.balance_side == 'debit':
                account.balance = total_debit - total_credit
            else:
                account.balance = total_credit - total_debit
        
        context = {
            'accounts': accounts,
        }
        return render(request, 'accounting/ledger-ui.html', context)
    except Exception as e:
        context = {
            'accounts': [],
            'error': str(e)
        }
        return render(request, 'accounting/ledger-ui.html', context)

@login_required
def trial_balance_ui(request):
    """Display trial balance"""
    try:
        company = request.user.company
        
        # Get all accounts with balances
        accounts = Account.objects.filter(company=company, is_active=True)
        trial_balance_data = []
        total_debits = 0
        total_credits = 0
        
        for account in accounts:
            total_debit = account.journal_items.aggregate(
                total=Sum('debit')
            )['total'] or 0
            total_credit = account.journal_items.aggregate(
                total=Sum('credit')
            )['total'] or 0
            
            debit_balance = 0
            credit_balance = 0
            
            if account.balance_side == 'debit':
                balance = total_debit - total_credit
                if balance > 0:
                    debit_balance = balance
                    total_debits += balance
                elif balance < 0:
                    credit_balance = abs(balance)
                    total_credits += abs(balance)
            else:
                balance = total_credit - total_debit
                if balance > 0:
                    credit_balance = balance
                    total_credits += balance
                elif balance < 0:
                    debit_balance = abs(balance)
                    total_debits += abs(balance)
            
            if debit_balance > 0 or credit_balance > 0:
                trial_balance_data.append({
                    'account': account,
                    'debit_balance': debit_balance,
                    'credit_balance': credit_balance,
                })
        
        context = {
            'trial_balance_data': trial_balance_data,
            'total_debits': total_debits,
            'total_credits': total_credits,
            'is_balanced': abs(total_debits - total_credits) < 0.01,
        }
        return render(request, 'accounting/trial-balance-ui.html', context)
    except Exception as e:
        context = {
            'trial_balance_data': [],
            'total_debits': 0,
            'total_credits': 0,
            'is_balanced': True,
            'error': str(e)
        }
        return render(request, 'accounting/trial-balance-ui.html', context)

@login_required
def reports_ui(request):
    """Display financial reports"""
    try:
        company = request.user.company
        
        # Get key financial metrics
        assets = Account.objects.filter(company=company, type='asset', is_active=True)
        liabilities = Account.objects.filter(company=company, type='liability', is_active=True)
        equity = Account.objects.filter(company=company, type='equity', is_active=True)
        income = Account.objects.filter(company=company, type='income', is_active=True)
        expenses = Account.objects.filter(company=company, type='expense', is_active=True)
        
        # Calculate totals
        def calculate_total_balance(accounts):
            total = 0
            for account in accounts:
                total_debit = account.journal_items.aggregate(total=Sum('debit'))['total'] or 0
                total_credit = account.journal_items.aggregate(total=Sum('credit'))['total'] or 0
                
                if account.balance_side == 'debit':
                    balance = total_debit - total_credit
                else:
                    balance = total_credit - total_debit
                total += balance
            return total
        
        total_assets = calculate_total_balance(assets)
        total_liabilities = calculate_total_balance(liabilities)
        total_equity = calculate_total_balance(equity)
        total_income = calculate_total_balance(income)
        total_expenses = calculate_total_balance(expenses)
        
        net_income = total_income - total_expenses
        
        context = {
            'total_assets': total_assets,
            'total_liabilities': total_liabilities,
            'total_equity': total_equity,
            'total_income': total_income,
            'total_expenses': total_expenses,
            'net_income': net_income,
        }
        return render(request, 'accounting/reports-ui.html', context)
    except Exception as e:
        context = {
            'total_assets': 0,
            'total_liabilities': 0,
            'total_equity': 0,
            'total_income': 0,
            'total_expenses': 0,
            'net_income': 0,
            'error': str(e)
        }
        return render(request, 'accounting/reports-ui.html', context)
