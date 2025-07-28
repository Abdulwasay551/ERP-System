from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, F, Q
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.paginator import Paginator

# Import models with try/catch to handle missing models
try:
    from sales.models import SalesOrder
except ImportError:
    SalesOrder = None

try:
    from inventory.models import StockItem
except ImportError:
    StockItem = None

try:
    from accounting.models import Account
except ImportError:
    Account = None

try:
    from hr.models import Employee
except ImportError:
    Employee = None

try:
    from crm.models import Partner
except ImportError:
    Partner = None

# Create your views here.

@login_required
def analytics_dashboard(request):
    """Analytics API endpoint for dashboard data"""
    try:
        company = request.user.company
        
        # Get metrics safely
        total_sales = 0
        total_inventory = 0
        total_accounts = 0
        total_employees = 0
        total_customers = 0
        
        if SalesOrder:
            try:
                total_sales = SalesOrder.objects.filter(company=company).count()
            except:
                total_sales = 0
        
        if StockItem:
            try:
                total_inventory = StockItem.objects.filter(company=company).count()
            except:
                total_inventory = 0
        
        if Account:
            try:
                total_accounts = Account.objects.filter(company=company).count()
            except:
                total_accounts = 0
        
        if Employee:
            try:
                total_employees = Employee.objects.filter(company=company).count()
            except:
                total_employees = 0
        
        if Partner:
            try:
                total_customers = Partner.objects.filter(company=company, is_customer=True).count()
            except:
                total_customers = 0

        # Sales by month (safely)
        sales_by_month = []
        if SalesOrder:
            try:
                sales_by_month = list(
                    SalesOrder.objects.filter(company=company)
                    .extra({'month': "DATE_TRUNC('month', created_at)"})
                    .values('month')
                    .annotate(count=Count('id'))
                    .order_by('month')
                )
            except:
                sales_by_month = []

        data = {
            'total_sales': total_sales,
            'total_inventory': total_inventory,
            'total_accounts': total_accounts,
            'total_employees': total_employees,
            'total_customers': total_customers,
            'sales_by_month': sales_by_month,
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def dashboard_ui(request):
    """Analytics dashboard UI"""
    try:
        company = request.user.company
        
        # Calculate key metrics
        metrics = {
            'total_sales': 0,
            'total_revenue': 0,
            'total_inventory': 0,
            'total_employees': 0,
            'total_customers': 0,
            'total_accounts': 0,
        }
        
        # Sales metrics
        if SalesOrder:
            try:
                sales_orders = SalesOrder.objects.filter(company=company)
                metrics['total_sales'] = sales_orders.count()
                metrics['total_revenue'] = sales_orders.aggregate(
                    total=Sum('total_amount')
                )['total'] or 0
            except:
                pass
        
        # Inventory metrics
        if StockItem:
            try:
                metrics['total_inventory'] = StockItem.objects.filter(company=company).count()
            except:
                pass
        
        # Employee metrics
        if Employee:
            try:
                metrics['total_employees'] = Employee.objects.filter(company=company).count()
            except:
                pass
        
        # Customer metrics
        if Partner:
            try:
                metrics['total_customers'] = Partner.objects.filter(
                    company=company, 
                    is_customer=True
                ).count()
            except:
                pass
        
        # Account metrics
        if Account:
            try:
                metrics['total_accounts'] = Account.objects.filter(company=company).count()
            except:
                pass
        
        # Recent activity (placeholder)
        recent_sales = []
        if SalesOrder:
            try:
                recent_sales = SalesOrder.objects.filter(
                    company=company
                ).order_by('-created_at')[:5]
            except:
                pass
        
        context = {
            **metrics,
            'recent_sales': recent_sales,
        }
        return render(request, 'analytics/dashboard.html', context)
    except Exception as e:
        context = {
            'total_sales': 0,
            'total_revenue': 0,
            'total_inventory': 0,
            'total_employees': 0,
            'total_customers': 0,
            'total_accounts': 0,
            'recent_sales': [],
            'error': str(e)
        }
        return render(request, 'analytics/dashboard.html', context)

@login_required
def sales_reports_ui(request):
    """Sales reports interface"""
    try:
        company = request.user.company
        
        # Get sales data
        sales_data = []
        if SalesOrder:
            try:
                sales_data = SalesOrder.objects.filter(
                    company=company
                ).order_by('-created_at')[:20]
            except:
                pass
        
        context = {
            'sales_data': sales_data,
        }
        return render(request, 'analytics/sales-reports.html', context)
    except Exception as e:
        context = {
            'sales_data': [],
            'error': str(e)
        }
        return render(request, 'analytics/sales-reports.html', context)

@login_required
def financial_reports_ui(request):
    """Financial reports interface"""
    try:
        company = request.user.company
        
        # Get financial data
        accounts_data = []
        if Account:
            try:
                accounts_data = Account.objects.filter(
                    company=company
                ).order_by('code')[:20]
            except:
                pass
        
        context = {
            'accounts_data': accounts_data,
        }
        return render(request, 'analytics/financial-reports.html', context)
    except Exception as e:
        context = {
            'accounts_data': [],
            'error': str(e)
        }
        return render(request, 'analytics/financial-reports.html', context)

@login_required
def inventory_reports_ui(request):
    """Inventory reports interface"""
    try:
        company = request.user.company
        
        # Get inventory data
        inventory_data = []
        if StockItem:
            try:
                inventory_data = StockItem.objects.filter(
                    company=company
                ).order_by('name')[:20]
            except:
                pass
        
        context = {
            'inventory_data': inventory_data,
        }
        return render(request, 'analytics/inventory-reports.html', context)
    except Exception as e:
        context = {
            'inventory_data': [],
            'error': str(e)
        }
        return render(request, 'analytics/inventory-reports.html', context)
