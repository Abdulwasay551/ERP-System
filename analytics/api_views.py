from datetime import timedelta

from rest_framework import permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Sum, Count, F
from django.utils import timezone

from sales.models import Invoice, InvoiceItem
from inventory.models import StockItem, StockMovement
from crm.models import CustomerLedger
from purchase.models import SupplierLedger, Bill
from products.models import ProductTracking
from accounting.models import Expense

REVENUE_STATUSES = ['sent', 'paid', 'partially_paid']


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_stats(request):
    """Shop-relevant dashboard numbers: today's sales, outstanding balances, low stock,
    pending vendor receipts. Company-scoped."""
    company = request.user.company
    today = timezone.now().date()

    todays_invoices = Invoice.objects.filter(company=company, invoice_date=today, status__in=REVENUE_STATUSES)
    todays_sales_total = todays_invoices.aggregate(total=Sum('total'))['total'] or 0
    todays_sales_count = todays_invoices.count()

    customer_outstanding = CustomerLedger.objects.filter(company=company).aggregate(
        total_debit=Sum('debit_amount'), total_credit=Sum('credit_amount')
    )
    customer_outstanding_total = (customer_outstanding['total_debit'] or 0) - (customer_outstanding['total_credit'] or 0)

    supplier_outstanding = SupplierLedger.objects.filter(company=company).aggregate(
        total_debit=Sum('debit_amount'), total_credit=Sum('credit_amount')
    )
    supplier_outstanding_total = (supplier_outstanding['total_debit'] or 0) - (supplier_outstanding['total_credit'] or 0)

    low_stock_count = StockItem.objects.filter(company=company, available_quantity__lte=F('min_stock')).count()
    available_tracked_units = ProductTracking.objects.filter(product__company=company, status='available').count()
    pending_vendor_receipts = Bill.objects.filter(company=company, goods_received=False).count()

    return Response({
        'todays_sales_total': str(todays_sales_total),
        'todays_sales_count': todays_sales_count,
        'customer_outstanding_total': str(customer_outstanding_total),
        'supplier_outstanding_total': str(supplier_outstanding_total),
        'low_stock_count': low_stock_count,
        'available_tracked_units': available_tracked_units,
        'pending_vendor_receipts': pending_vendor_receipts,
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def profit_report(request):
    """
    Daily revenue/COGS/expenses/profit for the last `days` days (default 30, max 365).
    Revenue is accrual (invoice total on its invoice_date, regardless of payment status
    beyond draft/cancelled) since a shop wants to know what it sold today, not just what
    was collected. COGS comes from StockMovement rows the sale flow already writes
    (movement_type='sale') rather than re-deriving it, so it can never drift from what
    inventory valuation actually used.
    """
    company = request.user.company
    try:
        days = min(max(int(request.query_params.get('days', 30)), 1), 365)
    except ValueError:
        days = 30

    today = timezone.now().date()
    start = today - timedelta(days=days - 1)

    revenue_by_day = {
        row['invoice_date']: row['total'] or 0
        for row in Invoice.objects.filter(
            company=company, invoice_date__gte=start, invoice_date__lte=today, status__in=REVENUE_STATUSES,
        ).values('invoice_date').annotate(total=Sum('total'))
    }
    cogs_by_day = {
        row['day']: row['total'] or 0
        for row in StockMovement.objects.filter(
            company=company, movement_type='sale', timestamp__date__gte=start, timestamp__date__lte=today,
        ).annotate(day=F('timestamp__date')).values('day').annotate(total=Sum('total_cost'))
    }
    expenses_by_day = {
        row['expense_date']: row['total'] or 0
        for row in Expense.objects.filter(
            company=company, expense_date__gte=start, expense_date__lte=today,
        ).values('expense_date').annotate(total=Sum('amount'))
    }

    days_out = []
    totals = {'revenue': 0, 'cogs': 0, 'expenses': 0}
    for i in range(days):
        d = start + timedelta(days=i)
        revenue = revenue_by_day.get(d, 0)
        cogs = cogs_by_day.get(d, 0)
        expenses = expenses_by_day.get(d, 0)
        gross_profit = revenue - cogs
        net_profit = gross_profit - expenses
        totals['revenue'] += revenue
        totals['cogs'] += cogs
        totals['expenses'] += expenses
        days_out.append({
            'date': d.isoformat(),
            'revenue': str(revenue),
            'cogs': str(cogs),
            'gross_profit': str(gross_profit),
            'expenses': str(expenses),
            'net_profit': str(net_profit),
        })

    gross_profit_total = totals['revenue'] - totals['cogs']
    net_profit_total = gross_profit_total - totals['expenses']

    return Response({
        'days': days_out,
        'totals': {
            'revenue': str(totals['revenue']),
            'cogs': str(totals['cogs']),
            'gross_profit': str(gross_profit_total),
            'expenses': str(totals['expenses']),
            'net_profit': str(net_profit_total),
        },
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def top_products(request):
    """Best-selling products by revenue over the last `days` days (default 30)."""
    company = request.user.company
    try:
        days = min(max(int(request.query_params.get('days', 30)), 1), 365)
    except ValueError:
        days = 30
    try:
        limit = min(max(int(request.query_params.get('limit', 5)), 1), 20)
    except ValueError:
        limit = 5

    today = timezone.now().date()
    start = today - timedelta(days=days - 1)

    rows = (
        InvoiceItem.objects.filter(
            invoice__company=company, invoice__invoice_date__gte=start, invoice__invoice_date__lte=today,
            invoice__status__in=REVENUE_STATUSES,
        )
        .values('product__id', 'product__name')
        .annotate(quantity_sold=Sum('quantity'), revenue=Sum(F('quantity') * F('unit_price')))
        .order_by('-revenue')[:limit]
    )
    return Response([
        {
            'product_id': row['product__id'],
            'product_name': row['product__name'],
            'quantity_sold': str(row['quantity_sold']),
            'revenue': str(row['revenue']),
        }
        for row in rows
    ])


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def low_stock_items(request):
    """Untracked-stock products at or below their reorder point, for the dashboard list
    (dashboard_stats only ever returned a count, not which products need restocking)."""
    company = request.user.company
    rows = StockItem.objects.filter(
        company=company, available_quantity__lte=F('min_stock')
    ).select_related('product').order_by('available_quantity')[:20]
    return Response([
        {
            'product_id': row.product_id,
            'product_name': row.product.name,
            'available_quantity': str(row.available_quantity),
            'min_stock': str(row.min_stock),
        }
        for row in rows
    ])
