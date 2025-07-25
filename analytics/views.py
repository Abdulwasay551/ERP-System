from django.shortcuts import render
from django.http import JsonResponse
from sales.models import SalesOrder
from inventory.models import StockItem
from accounting.models import Account
from hr.models import Employee
from crm.models import Customer
from django.db.models import Count, Sum

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
