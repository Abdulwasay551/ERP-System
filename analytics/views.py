from django.shortcuts import render
from django.http import JsonResponse
from sales.models import SalesOrder
from inventory.models import StockItem
from accounting.models import Account
from hr.models import Employee
from crm.models import Customer
from django.db.models import Count, Sum
from django.contrib.auth.decorators import login_required

# Create your views here.

def analytics_dashboard(request):
    # Example KPIs
    total_sales = SalesOrder.objects.count()
    total_inventory = StockItem.objects.count()
    total_accounts = Account.objects.count()
    total_employees = Employee.objects.count()
    total_customers = Customer.objects.count()

    # Example: sales by month (for chart)
    sales_by_month = (
        SalesOrder.objects.extra({'month': "DATE_TRUNC('month', created_at)"})
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )

    data = {
        'total_sales': total_sales,
        'total_inventory': total_inventory,
        'total_accounts': total_accounts,
        'total_employees': total_employees,
        'total_customers': total_customers,
        'sales_by_month': list(sales_by_month),
    }
    return JsonResponse(data)

@login_required
def dashboard_ui(request):
    return render(request, 'analytics/dashboard-ui.html')

@login_required
def sales_reports_ui(request):
    return render(request, 'analytics/sales-reports-ui.html')

@login_required
def financial_reports_ui(request):
    return render(request, 'analytics/financial-reports-ui.html')

@login_required
def inventory_reports_ui(request):
    return render(request, 'analytics/inventory-reports-ui.html')
