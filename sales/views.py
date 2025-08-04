from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.db.models import Sum, Count, Q, Avg, Max
from django.utils import timezone
from django.contrib import messages
from django.urls import reverse_lazy
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from user_auth.models import User
from datetime import datetime, timedelta
from decimal import Decimal
import json
from .models import (
    Currency, PriceList, PriceListItem, Tax, Quotation, QuotationItem,
    SalesOrder, SalesOrderItem, DeliveryNote, DeliveryNoteItem,
    Invoice, InvoiceItem, Payment, SalesCommission, CreditNote, LegacyProduct,
    QUOTATION_STATUS_CHOICES, SALES_ORDER_STATUS_CHOICES
)
from products.models import Product
from crm.models import Customer
from accounting.models import Account

# Create your views here.

@login_required
def sales_dashboard(request):
    """Enhanced Sales module dashboard with comprehensive metrics"""
    company = request.user.company
    
    # Key metrics
    total_products = Product.objects.filter(company=company, is_active=True).count()
    total_quotations = Quotation.objects.filter(company=company).count()
    total_sales_orders = SalesOrder.objects.filter(company=company).count()
    total_invoices = Invoice.objects.filter(company=company).count()
    total_delivery_notes = DeliveryNote.objects.filter(company=company).count()
    
    # Status-based counts
    pending_quotations = Quotation.objects.filter(company=company, status='draft').count()
    pending_orders = SalesOrder.objects.filter(company=company, status='pending').count()
    overdue_invoices = Invoice.objects.filter(company=company, status='overdue').count()
    
    # Monthly statistics
    current_month = timezone.now().replace(day=1)
    monthly_quotations = Quotation.objects.filter(
        company=company, 
        created_at__gte=current_month
    ).count()
    
    monthly_sales = SalesOrder.objects.filter(
        company=company, 
        created_at__gte=current_month
    ).aggregate(total=Sum('total'))['total'] or 0
    
    monthly_revenue = Invoice.objects.filter(
        company=company,
        invoice_date__gte=current_month.date(),
        status__in=['paid', 'partially_paid']
    ).aggregate(total=Sum('paid_amount'))['total'] or 0
    
    # Outstanding amounts
    outstanding_invoices = Invoice.objects.filter(
        company=company,
        status__in=['sent', 'partially_paid']
    ).aggregate(
        total_outstanding=Sum('total') - Sum('paid_amount')
    )['total_outstanding'] or 0
    
    # Recent activities
    recent_quotations = Quotation.objects.filter(company=company).select_related('customer').order_by('-created_at')[:5]
    recent_orders = SalesOrder.objects.filter(company=company).select_related('customer').order_by('-created_at')[:5]
    recent_invoices = Invoice.objects.filter(company=company).select_related('customer').order_by('-created_at')[:5]
    
    # Top customers by sales value
    top_customers = Customer.objects.filter(
        company=company,
        invoices__status__in=['paid', 'partially_paid']
    ).annotate(
        total_sales=Sum('invoices__paid_amount')
    ).order_by('-total_sales')[:5]
    
    context = {
        'total_products': total_products,
        'total_quotations': total_quotations,
        'total_sales_orders': total_sales_orders,
        'total_invoices': total_invoices,
        'total_delivery_notes': total_delivery_notes,
        'pending_quotations': pending_quotations,
        'pending_orders': pending_orders,
        'overdue_invoices': overdue_invoices,
        'monthly_quotations': monthly_quotations,
        'monthly_sales': monthly_sales,
        'monthly_revenue': monthly_revenue,
        'outstanding_invoices': outstanding_invoices,
        'recent_quotations': recent_quotations,
        'recent_orders': recent_orders,
        'recent_invoices': recent_invoices,
        'top_customers': top_customers,
    }
    return render(request, 'sales/dashboard.html', context)

# Currency Views
class CurrencyListView(LoginRequiredMixin, ListView):
    model = Currency
    template_name = 'sales/currency_list.html'
    context_object_name = 'currencies'
    
    def get_queryset(self):
        return Currency.objects.filter(company=self.request.user.company).order_by('code')

@login_required
def currency_create(request):
    if request.method == 'POST':
        company = request.user.company
        currency = Currency.objects.create(
            company=company,
            code=request.POST.get('code'),
            name=request.POST.get('name'),
            symbol=request.POST.get('symbol'),
            exchange_rate=request.POST.get('exchange_rate', 1.0000),
            is_base_currency=request.POST.get('is_base_currency') == 'on',
        )
        messages.success(request, f'Currency {currency.code} created successfully!')
        return redirect('sales:currency_list')
    
    context = {'page_title': 'Add Currency'}
    return render(request, 'sales/currency_form.html', context)

# Price List Views
class CurrencyListView(LoginRequiredMixin, TemplateView):
    template_name = 'sales/currency_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company
        
        currencies = Currency.objects.filter(company=company).order_by('-is_base_currency', 'code')
        active_currencies = currencies.filter(is_active=True)
        base_currency = currencies.filter(is_base_currency=True).first()
        
        # Calculate statistics
        active_currencies_count = active_currencies.count()
        average_exchange_rate = currencies.exclude(is_base_currency=True).aggregate(
            avg_rate=Avg('exchange_rate')
        )['avg_rate'] or 0
        
        context.update({
            'currencies': currencies,
            'active_currencies_count': active_currencies_count,
            'base_currency': base_currency,
            'average_exchange_rate': average_exchange_rate,
        })
        return context

@login_required
@require_POST
def currencies_create(request):
    """Create a new currency"""
    try:
        name = request.POST.get('name')
        code = request.POST.get('code', '').upper()
        symbol = request.POST.get('symbol')
        exchange_rate = request.POST.get('exchange_rate')
        country = request.POST.get('country', '')
        description = request.POST.get('description', '')
        is_active = request.POST.get('is_active') == 'on'
        is_base_currency = request.POST.get('is_base_currency') == 'on'
        
        if not all([name, code, symbol, exchange_rate]):
            return JsonResponse({'success': False, 'error': 'Required fields missing'}, status=400)
        
        # Validate currency code uniqueness
        if Currency.objects.filter(company=request.user.company, code=code).exists():
            return JsonResponse({'success': False, 'error': 'Currency code already exists'}, status=400)
        
        # Handle base currency logic
        if is_base_currency:
            # Set current base currency to non-base
            Currency.objects.filter(company=request.user.company, is_base_currency=True).update(
                is_base_currency=False
            )
            exchange_rate = '1.0000'
        
        currency = Currency.objects.create(
            company=request.user.company,
            name=name,
            code=code,
            symbol=symbol,
            exchange_rate=Decimal(exchange_rate),
            country=country,
            description=description,
            is_active=is_active,
            is_base_currency=is_base_currency
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Currency created successfully!',
            'currency': {
                'id': currency.id,
                'name': currency.name,
                'code': currency.code,
                'symbol': currency.symbol,
                'exchange_rate': str(currency.exchange_rate),
                'is_active': currency.is_active,
                'is_base_currency': currency.is_base_currency
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_POST
def currencies_update(request, pk):
    """Update an existing currency"""
    try:
        currency = get_object_or_404(Currency, pk=pk, company=request.user.company)
        
        name = request.POST.get('name')
        code = request.POST.get('code', '').upper()
        symbol = request.POST.get('symbol')
        exchange_rate = request.POST.get('exchange_rate')
        country = request.POST.get('country', '')
        description = request.POST.get('description', '')
        is_active = request.POST.get('is_active') == 'on'
        is_base_currency = request.POST.get('is_base_currency') == 'on'
        
        if not all([name, code, symbol, exchange_rate]):
            return JsonResponse({'success': False, 'error': 'Required fields missing'}, status=400)
        
        # Validate currency code uniqueness (excluding current currency)
        if Currency.objects.filter(
            company=request.user.company, code=code
        ).exclude(pk=pk).exists():
            return JsonResponse({'success': False, 'error': 'Currency code already exists'}, status=400)
        
        # Handle base currency logic
        if is_base_currency and not currency.is_base_currency:
            # Set current base currency to non-base
            Currency.objects.filter(company=request.user.company, is_base_currency=True).update(
                is_base_currency=False
            )
            exchange_rate = '1.0000'
        elif is_base_currency:
            exchange_rate = '1.0000'
        
        # Update currency
        currency.name = name
        currency.code = code
        currency.symbol = symbol
        currency.exchange_rate = Decimal(exchange_rate)
        currency.country = country
        currency.description = description
        currency.is_active = is_active
        currency.is_base_currency = is_base_currency
        currency.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Currency updated successfully!',
            'currency': {
                'id': currency.id,
                'name': currency.name,
                'code': currency.code,
                'symbol': currency.symbol,
                'exchange_rate': str(currency.exchange_rate),
                'is_active': currency.is_active,
                'is_base_currency': currency.is_base_currency
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
def currency_detail(request, pk):
    """Get currency details"""
    try:
        currency = get_object_or_404(Currency, pk=pk, company=request.user.company)
        
        return JsonResponse({
            'success': True,
            'currency': {
                'id': currency.id,
                'name': currency.name,
                'code': currency.code,
                'symbol': currency.symbol,
                'exchange_rate': str(currency.exchange_rate),
                'country': currency.country,
                'description': currency.description,
                'is_active': currency.is_active,
                'is_base_currency': currency.is_base_currency,
                'created_at': currency.created_at.strftime('%Y-%m-%d')
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_POST
def currencies_delete(request, pk):
    """Delete a currency"""
    try:
        currency = get_object_or_404(Currency, pk=pk, company=request.user.company)
        
        # Prevent deletion of base currency
        if currency.is_base_currency:
            return JsonResponse({'success': False, 'error': 'Cannot delete base currency'}, status=400)
        
        # Check if currency is being used in transactions
        if currency.quotations.exists() or currency.sales_orders.exists() or currency.invoices.exists():
            return JsonResponse({
                'success': False, 
                'error': 'Cannot delete currency that is being used in transactions'
            }, status=400)
        
        currency.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Currency deleted successfully!'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

class PriceListView(LoginRequiredMixin, TemplateView):
    template_name = 'sales/pricelist_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company
        
        price_lists = PriceList.objects.filter(company=company).select_related('currency').order_by('-created_at')
        currencies = Currency.objects.filter(company=company, is_active=True)
        
        # Calculate statistics
        total_price_lists = price_lists.count()
        active_price_lists = price_lists.filter(is_active=True).count()
        default_price_list = price_lists.filter(is_default=True).first()
        
        # Get total price list items
        total_items = PriceListItem.objects.filter(price_list__company=company).count()
        
        context.update({
            'price_lists': price_lists,
            'currencies': currencies,
            'total_price_lists': total_price_lists,
            'active_price_lists': active_price_lists,
            'default_price_list': default_price_list,
            'total_items': total_items,
        })
        return context

@login_required
@require_POST
def pricelists_create(request):
    """Create a new price list"""
    try:
        name = request.POST.get('name')
        currency_id = request.POST.get('currency_id')
        valid_from = request.POST.get('valid_from')
        valid_until = request.POST.get('valid_until')
        description = request.POST.get('description', '')
        is_active = request.POST.get('is_active') == 'on'
        is_default = request.POST.get('is_default') == 'on'
        
        if not all([name, currency_id]):
            return JsonResponse({'success': False, 'error': 'Name and currency are required'}, status=400)
        
        currency = get_object_or_404(Currency, pk=currency_id, company=request.user.company)
        
        # Handle default price list logic
        if is_default:
            PriceList.objects.filter(company=request.user.company, is_default=True).update(
                is_default=False
            )
        
        # Parse dates
        valid_from_date = None
        valid_until_date = None
        if valid_from:
            valid_from_date = datetime.strptime(valid_from, '%Y-%m-%d').date()
        if valid_until:
            valid_until_date = datetime.strptime(valid_until, '%Y-%m-%d').date()
        
        price_list = PriceList.objects.create(
            company=request.user.company,
            name=name,
            currency=currency,
            valid_from=valid_from_date,
            valid_until=valid_until_date,
            description=description,
            is_active=is_active,
            is_default=is_default,
            created_by=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Price list created successfully!',
            'price_list': {
                'id': price_list.id,
                'name': price_list.name,
                'currency': price_list.currency.code,
                'is_active': price_list.is_active,
                'is_default': price_list.is_default
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_POST
def pricelists_update(request, pk):
    """Update an existing price list"""
    try:
        price_list = get_object_or_404(PriceList, pk=pk, company=request.user.company)
        
        name = request.POST.get('name')
        currency_id = request.POST.get('currency_id')
        valid_from = request.POST.get('valid_from')
        valid_until = request.POST.get('valid_until')
        description = request.POST.get('description', '')
        is_active = request.POST.get('is_active') == 'on'
        is_default = request.POST.get('is_default') == 'on'
        
        if not all([name, currency_id]):
            return JsonResponse({'success': False, 'error': 'Name and currency are required'}, status=400)
        
        currency = get_object_or_404(Currency, pk=currency_id, company=request.user.company)
        
        # Handle default price list logic
        if is_default and not price_list.is_default:
            PriceList.objects.filter(company=request.user.company, is_default=True).update(
                is_default=False
            )
        
        # Parse dates
        valid_from_date = None
        valid_until_date = None
        if valid_from:
            valid_from_date = datetime.strptime(valid_from, '%Y-%m-%d').date()
        if valid_until:
            valid_until_date = datetime.strptime(valid_until, '%Y-%m-%d').date()
        
        # Update price list
        price_list.name = name
        price_list.currency = currency
        price_list.valid_from = valid_from_date
        price_list.valid_until = valid_until_date
        price_list.description = description
        price_list.is_active = is_active
        price_list.is_default = is_default
        price_list.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Price list updated successfully!',
            'price_list': {
                'id': price_list.id,
                'name': price_list.name,
                'currency': price_list.currency.code,
                'is_active': price_list.is_active,
                'is_default': price_list.is_default
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
def pricelist_detail(request, pk):
    """Get price list details"""
    try:
        price_list = get_object_or_404(PriceList, pk=pk, company=request.user.company)
        
        return JsonResponse({
            'success': True,
            'price_list': {
                'id': price_list.id,
                'name': price_list.name,
                'currency_id': price_list.currency.id,
                'currency_code': price_list.currency.code,
                'valid_from': price_list.valid_from.strftime('%Y-%m-%d') if price_list.valid_from else '',
                'valid_until': price_list.valid_until.strftime('%Y-%m-%d') if price_list.valid_until else '',
                'description': price_list.description,
                'is_active': price_list.is_active,
                'is_default': price_list.is_default,
                'created_at': price_list.created_at.strftime('%Y-%m-%d')
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_POST
def pricelists_delete(request, pk):
    """Delete a price list"""
    try:
        price_list = get_object_or_404(PriceList, pk=pk, company=request.user.company)
        
        # Prevent deletion of default price list if it's the only one
        if price_list.is_default and PriceList.objects.filter(company=request.user.company).count() == 1:
            return JsonResponse({'success': False, 'error': 'Cannot delete the only price list'}, status=400)
        
        price_list.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Price list deleted successfully!'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

class ProductPageView(LoginRequiredMixin, TemplateView):
    template_name = 'sales/product_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company
        
        # Get all products for the company from the centralized products app
        products = Product.objects.filter(company=company).order_by('-created_at')
        
        # Calculate statistics
        total_products = products.count()
        active_products = products.filter(is_active=True).count()
        
        context.update({
            'products': products,
            'total_products': total_products,
            'active_products': active_products,
        })
        return context

class TaxPageView(LoginRequiredMixin, TemplateView):
    template_name = 'sales/tax_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company
        
        # Get all taxes for the company
        taxes = Tax.objects.filter(company=company).select_related('account').order_by('name')
        
        # Calculate statistics
        total_taxes = taxes.count()
        active_taxes_count = taxes.filter(is_active=True).count()
        average_tax_rate = taxes.aggregate(avg_rate=Avg('rate'))['avg_rate'] or 0
        highest_tax_rate = taxes.aggregate(max_rate=Max('rate'))['max_rate'] or 0
        
        # Get Chart of Accounts for tax liability accounts (filtered to liability type)
        from accounting.models import Account
        tax_accounts = Account.objects.filter(
            company=company, 
            account_type__in=['Liability', 'Current Liability']
        ).order_by('code')
        
        # Get companies for dropdown (in case of multi-company setup)
        from user_auth.models import Company
        companies = Company.objects.all()
        
        context.update({
            'taxes': taxes,
            'active_taxes_count': active_taxes_count,
            'average_tax_rate': average_tax_rate,
            'highest_tax_rate': highest_tax_rate,
            'tax_accounts': tax_accounts,
            'companies': companies,
        })
        return context

class CustomerPageView(LoginRequiredMixin, TemplateView):
    template_name = 'sales/customer_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company
        
        # Get all customers for the company
        customers = Customer.objects.filter(company=company).select_related(
            'created_by', 'account', 'partner'
        ).order_by('-created_at')
        
        # Calculate statistics
        total_customers = customers.count()
        active_customers = customers.count()  # All customers are considered active since no is_active field
        
        # Recent customers (last 30 days)
        from django.utils import timezone
        thirty_days_ago = timezone.now() - timedelta(days=30)
        new_customers_count = customers.filter(created_at__gte=thirty_days_ago).count()
        
        # Customers with sales
        customers_with_sales = customers.filter(invoices__isnull=False).distinct().count()
        
        # Sales statistics
        total_sales = customers.aggregate(
            total=Sum('invoices__total')
        )['total'] or 0
        
        # Get Chart of Accounts for customer accounts
        from accounting.models import Account
        customer_accounts = Account.objects.filter(
            company=company, 
            account_type__in=['Receivable', 'Current Asset']
        ).order_by('code')
        
        context.update({
            'customers': customers,
            'total_customers': total_customers,
            'active_customers_count': active_customers,
            'new_customers_count': new_customers_count,
            'customers_with_sales': customers_with_sales,
            'total_customer_sales': total_sales,
            'customer_accounts': customer_accounts,
        })
        return context

class SalesReportPageView(LoginRequiredMixin, TemplateView):
    template_name = 'sales/salesreport_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company
        
        # Date range for reports (default: current month)
        from django.utils import timezone
        today = timezone.now().date()
        first_day_month = today.replace(day=1)
        
        # Get filter parameters
        date_from = self.request.GET.get('date_from', first_day_month.strftime('%Y-%m-%d'))
        date_to = self.request.GET.get('date_to', today.strftime('%Y-%m-%d'))
        customer_filter = self.request.GET.get('customer')
        product_filter = self.request.GET.get('product')
        
        # Parse dates
        try:
            date_from_parsed = datetime.strptime(date_from, '%Y-%m-%d').date()
            date_to_parsed = datetime.strptime(date_to, '%Y-%m-%d').date()
        except ValueError:
            date_from_parsed = first_day_month
            date_to_parsed = today
        
        # Base querysets for the period
        quotations = Quotation.objects.filter(
            company=company,
            date__gte=date_from_parsed,
            date__lte=date_to_parsed
        )
        
        sales_orders = SalesOrder.objects.filter(
            company=company,
            order_date__gte=date_from_parsed,
            order_date__lte=date_to_parsed
        )
        
        invoices = Invoice.objects.filter(
            company=company,
            invoice_date__gte=date_from_parsed,
            invoice_date__lte=date_to_parsed
        )
        
        # Apply filters
        if customer_filter:
            quotations = quotations.filter(customer_id=customer_filter)
            sales_orders = sales_orders.filter(customer_id=customer_filter)
            invoices = invoices.filter(customer_id=customer_filter)
        
        # Sales Performance Metrics
        total_quotations = quotations.count()
        total_quotation_value = quotations.aggregate(total=Sum('total'))['total'] or 0
        
        total_sales_orders = sales_orders.count()
        total_sales_value = sales_orders.aggregate(total=Sum('total'))['total'] or 0
        
        total_invoices = invoices.count()
        total_invoice_value = invoices.aggregate(total=Sum('total'))['total'] or 0
        total_paid_amount = invoices.aggregate(total=Sum('paid_amount'))['total'] or 0
        
        # Conversion rates
        quotation_to_order_rate = (total_sales_orders / total_quotations * 100) if total_quotations > 0 else 0
        order_to_invoice_rate = (total_invoices / total_sales_orders * 100) if total_sales_orders > 0 else 0
        payment_collection_rate = (total_paid_amount / total_invoice_value * 100) if total_invoice_value > 0 else 0
        
        # Top performing customers
        top_customers = Customer.objects.filter(
            company=company,
            invoices__invoice_date__gte=date_from_parsed,
            invoices__invoice_date__lte=date_to_parsed
        ).annotate(
            total_sales=Sum('invoices__total'),
            total_orders=Count('sales_orders', distinct=True),
            total_paid=Sum('invoices__paid_amount')
        ).order_by('-total_sales')[:10]
        
        # Top performing products - fix the annotation
        # We need to aggregate from sales order items for actual sales
        from django.db.models import F
        top_products = Product.objects.filter(
            company=company,
            salesorderitem__sales_order__created_at__gte=date_from_parsed,
            salesorderitem__sales_order__created_at__lte=date_to_parsed
        ).annotate(
            total_sold=Sum('salesorderitem__line_total'),
            order_count=Count('salesorderitem__sales_order', distinct=True)
        ).order_by('-total_sold')[:10]
        
        # Monthly trends (last 12 months)
        monthly_sales = []
        monthly_quotes = []
        for i in range(12):
            month_start = (today.replace(day=1) - timedelta(days=32*i)).replace(day=1)
            month_end = (month_start.replace(month=month_start.month % 12 + 1) - timedelta(days=1)) if month_start.month < 12 else month_start.replace(year=month_start.year + 1, month=1) - timedelta(days=1)
            
            month_sales = SalesOrder.objects.filter(
                company=company,
                order_date__gte=month_start,
                order_date__lte=month_end
            ).aggregate(total=Sum('total'))['total'] or 0
            
            month_quotes = Quotation.objects.filter(
                company=company,
                date__gte=month_start,
                date__lte=month_end
            ).count()
            
            monthly_sales.append({
                'month': month_start.strftime('%b %Y'),
                'sales': float(month_sales),
                'quotes': month_quotes
            })
        
        monthly_sales.reverse()
        
        # Sales by status
        quotation_status_breakdown = {}
        for choice in QUOTATION_STATUS_CHOICES:
            quotation_status_breakdown[choice[1]] = quotations.filter(status=choice[0]).count()
        
        sales_order_status_breakdown = {}
        for choice in SALES_ORDER_STATUS_CHOICES:
            sales_order_status_breakdown[choice[1]] = sales_orders.filter(status=choice[0]).count()
        
        # Outstanding receivables
        outstanding_invoices_data = Invoice.objects.filter(
            company=company,
            status__in=['sent', 'partially_paid']
        ).aggregate(
            total_amount=Sum('total'),
            paid_amount=Sum('paid_amount')
        )
        outstanding_invoices = (outstanding_invoices_data['total_amount'] or 0) - (outstanding_invoices_data['paid_amount'] or 0)
        
        overdue_invoices_data = Invoice.objects.filter(
            company=company,
            due_date__lt=today,
            status__in=['sent', 'partially_paid']
        ).aggregate(
            total_amount=Sum('total'),
            paid_amount=Sum('paid_amount')
        )
        overdue_invoices = (overdue_invoices_data['total_amount'] or 0) - (overdue_invoices_data['paid_amount'] or 0)
        
        # Get dropdown data
        customers = Customer.objects.filter(company=company).order_by('name')
        products = Product.objects.filter(company=company, is_active=True).order_by('name')
        
        context.update({
            # Filters
            'date_from': date_from,
            'date_to': date_to,
            'current_customer': customer_filter,
            'current_product': product_filter,
            'customers': customers,
            'products': products,
            
            # Performance Metrics
            'total_quotations': total_quotations,
            'total_quotation_value': total_quotation_value,
            'total_sales_orders': total_sales_orders,
            'total_sales_value': total_sales_value,
            'total_invoices': total_invoices,
            'total_invoice_value': total_invoice_value,
            'total_paid_amount': total_paid_amount,
            'outstanding_invoices': outstanding_invoices,
            'overdue_invoices': overdue_invoices,
            
            # Conversion Rates
            'quotation_to_order_rate': quotation_to_order_rate,
            'order_to_invoice_rate': order_to_invoice_rate,
            'payment_collection_rate': payment_collection_rate,
            
            # Top Performers
            'top_customers': top_customers,
            'top_products': top_products,
            
            # Trends and Breakdowns
            'monthly_sales': json.dumps(monthly_sales),
            'quotation_status_breakdown': quotation_status_breakdown,
            'sales_order_status_breakdown': sales_order_status_breakdown,
        })
        return context

class QuotationPageView(LoginRequiredMixin, TemplateView):
    template_name = 'sales/quotation_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company
        
        # Start with all quotations for the company
        quotations = Quotation.objects.filter(company=company).select_related(
            'customer', 'created_by', 'currency'
        ).prefetch_related('items__product').order_by('-created_at')
        
        # Apply filters dynamically based on request parameters
        search = self.request.GET.get('search')
        status_filter = self.request.GET.get('status')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        customer_filter = self.request.GET.get('customer')
        
        if search:
            quotations = quotations.filter(
                Q(quotation_number__icontains=search) |
                Q(customer__name__icontains=search) |
                Q(notes__icontains=search)
            )
        
        if status_filter:
            quotations = quotations.filter(status=status_filter)
        
        if date_from:
            quotations = quotations.filter(date__gte=date_from)
        
        if date_to:
            quotations = quotations.filter(date__lte=date_to)
        
        if customer_filter:
            quotations = quotations.filter(customer_id=customer_filter)
        
        # Pagination
        paginator = Paginator(quotations, 20)  # Show 20 quotations per page
        page = self.request.GET.get('page')
        try:
            quotations_page = paginator.page(page)
        except PageNotAnInteger:
            quotations_page = paginator.page(1)
        except EmptyPage:
            quotations_page = paginator.page(paginator.num_pages)
        
        # Calculate statistics dynamically (use filtered queryset for displayed stats)
        total_quotations = quotations.count()
        total_value = quotations.aggregate(total_value=Sum('total'))['total_value'] or 0
        
        # Status breakdown - dynamic calculation
        status_counts = {}
        all_quotations = Quotation.objects.filter(company=company)  # For status counts, use all quotations
        for choice in QUOTATION_STATUS_CHOICES:
            status_counts[choice[0]] = all_quotations.filter(status=choice[0]).count()
        
        # Get customers and related data for dropdowns
        customers = Customer.objects.filter(company=company).order_by('name')
        products = Product.objects.filter(company=company, is_active=True).order_by('name')
        taxes = Tax.objects.filter(company=company, is_active=True).order_by('name')
        currencies = Currency.objects.filter(company=company, is_active=True).order_by('code')
        
        context.update({
            'quotations': quotations,
            'total_quotations': total_quotations,
            'total_quotation_value': total_value,
            'pending_quotations_count': status_counts.get('draft', 0),
            'approved_quotations_count': status_counts.get('accepted', 0),
            'status_counts': status_counts,
            'customers': customers,
            'products': products,
            'taxes': taxes,
            'currencies': currencies,
            # Pass filter values back to template for form persistence
            'current_search': search,
            'current_status': status_filter,
            'current_date_from': date_from,
            'current_date_to': date_to,
            'current_customer': customer_filter,
        })
        return context

@login_required
def quotation_detail(request, pk):
    """Detailed view of a quotation"""
    company = request.user.company
    quotation = get_object_or_404(Quotation, pk=pk, company=company)
    items = quotation.items.select_related('product', 'tax').all()
    
    context = {
        'quotation': quotation,
        'items': items,
    }
    return render(request, 'sales/quotation_detail.html', context)

@login_required
def quotation_form_view(request, pk=None):
    """Create or Edit quotation with form"""
    company = request.user.company
    quotation = None
    
    if pk:
        quotation = get_object_or_404(Quotation, pk=pk, company=company)
    
    if request.method == 'POST':
        return handle_quotation_form_submission(request, quotation)
    
    # GET request - show form
    customers = Customer.objects.filter(company=company)
    products = Product.objects.filter(company=company, is_active=True)
    taxes = Tax.objects.filter(company=company, is_active=True)
    currencies = Currency.objects.filter(company=company, is_active=True)
    
    context = {
        'quotation': quotation,
        'customers': customers,
        'products': products,
        'taxes': taxes,
        'currencies': currencies,
        'today': timezone.now().date(),
    }
    return render(request, 'sales/quotation_form.html', context)

def handle_quotation_form_submission(request, quotation=None):
    """Handle quotation form submission"""
    company = request.user.company
    
    try:
        # Get form data
        customer_id = request.POST.get('customer_id')
        date = request.POST.get('date')
        valid_until = request.POST.get('valid_until')
        currency_id = request.POST.get('currency_id')
        status = request.POST.get('status', 'draft')
        terms_and_conditions = request.POST.get('terms_and_conditions', '')
        notes = request.POST.get('notes', '')
        
        # Validate required fields
        if not customer_id:
            messages.error(request, 'Customer is required.')
            return redirect(request.path)
        
        customer = get_object_or_404(Customer, pk=customer_id, company=company)
        currency = None
        if currency_id:
            currency = get_object_or_404(Currency, pk=currency_id, company=company)
        
        # Create or update quotation
        if quotation:
            quotation.customer = customer
            quotation.date = date if date else quotation.date
            quotation.valid_until = valid_until if valid_until else None
            quotation.currency = currency
            quotation.status = status
            quotation.terms_and_conditions = terms_and_conditions
            quotation.notes = notes
        else:
            quotation = Quotation.objects.create(
                company=company,
                customer=customer,
                created_by=request.user,
                date=date if date else timezone.now().date(),
                valid_until=valid_until if valid_until else None,
                currency=currency,
                status=status,
                terms_and_conditions=terms_and_conditions,
                notes=notes
            )
        
        quotation.save()
        
        # Handle line items
        handle_quotation_line_items(request, quotation)
        
        # Recalculate totals
        recalculate_quotation_totals(quotation)
        
        messages.success(request, f'Quotation {quotation.quotation_number} saved successfully!')
        return redirect('sales:quotations_detail', pk=quotation.pk)
        
    except Exception as e:
        messages.error(request, f'Error saving quotation: {str(e)}')
        return redirect(request.path)

def handle_quotation_line_items(request, quotation):
    """Handle quotation line items from form submission"""
    # Clear existing items if editing
    if quotation.pk:
        quotation.items.all().delete()
    
    # Process new items
    item_count = 0
    while f'items[{item_count}][product_id]' in request.POST:
        product_id = request.POST.get(f'items[{item_count}][product_id]')
        quantity = request.POST.get(f'items[{item_count}][quantity]')
        price = request.POST.get(f'items[{item_count}][price]')
        tax_id = request.POST.get(f'items[{item_count}][tax_id]')
        
        if product_id and quantity and price:
            product = get_object_or_404(Product, pk=product_id, company=quotation.company)
            tax = None
            if tax_id:
                tax = get_object_or_404(Tax, pk=tax_id, company=quotation.company)
            
            quantity = Decimal(quantity)
            price = Decimal(price)
            subtotal = quantity * price
            tax_amount = Decimal('0')
            
            if tax:
                tax_amount = subtotal * (tax.rate / 100)
            
            total = subtotal + tax_amount
            
            QuotationItem.objects.create(
                quotation=quotation,
                product=product,
                quantity=quantity,
                price=price,
                tax=tax,
                total=total
            )
        
        item_count += 1

def recalculate_quotation_totals(quotation):
    """Recalculate quotation totals"""
    items = quotation.items.all()
    subtotal = sum(item.quantity * item.price for item in items)
    tax_amount = sum(item.quantity * item.price * (item.tax.rate / 100 if item.tax else 0) for item in items)
    total = subtotal + tax_amount
    
    quotation.subtotal = subtotal
    quotation.tax_amount = tax_amount
    quotation.total = total
    quotation.save()

@login_required
@require_POST
def quotation_confirm(request, pk):
    """Confirm a quotation and change status to accepted"""
    company = request.user.company
    quotation = get_object_or_404(Quotation, pk=pk, company=company)
    
    try:
        if quotation.status in ['draft', 'sent']:
            quotation.status = 'accepted'
            quotation.save()
            return JsonResponse({
                'success': True, 
                'message': f'Quotation {quotation.quotation_number} confirmed successfully!'
            })
        else:
            return JsonResponse({
                'success': False, 
                'error': f'Cannot confirm quotation with status: {quotation.get_status_display()}'
            })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_POST
def quotation_send(request, pk):
    """Send quotation to customer (change status to sent)"""
    company = request.user.company
    quotation = get_object_or_404(Quotation, pk=pk, company=company)
    
    try:
        if quotation.status == 'draft':
            quotation.status = 'sent'
            quotation.save()
            return JsonResponse({
                'success': True, 
                'message': f'Quotation {quotation.quotation_number} sent successfully!'
            })
        else:
            return JsonResponse({
                'success': False, 
                'error': f'Cannot send quotation with status: {quotation.get_status_display()}'
            })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

class SalesOrderPageView(LoginRequiredMixin, TemplateView):
    template_name = 'sales/salesorder_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company
        
        # Get all sales orders for the company
        sales_orders = SalesOrder.objects.filter(company=company).select_related(
            'customer', 'created_by', 'quotation', 'currency', 'sales_person'
        ).prefetch_related('items__product').order_by('-created_at')
        
        # Apply filters
        search_query = self.request.GET.get('search', '')
        status_filter = self.request.GET.get('status', '')
        customer_filter = self.request.GET.get('customer', '')
        date_from = self.request.GET.get('date_from', '')
        
        if search_query:
            sales_orders = sales_orders.filter(
                Q(customer__name__icontains=search_query) |
                Q(notes__icontains=search_query) |
                Q(id__icontains=search_query)
            )
        
        if status_filter:
            sales_orders = sales_orders.filter(status=status_filter)
        
        if customer_filter:
            sales_orders = sales_orders.filter(customer_id=customer_filter)
        
        if date_from:
            try:
                date_from_parsed = datetime.strptime(date_from, '%Y-%m-%d').date()
                sales_orders = sales_orders.filter(order_date__gte=date_from_parsed)
            except ValueError:
                pass
        
        # Pagination
        paginator = Paginator(sales_orders, 20)  # Show 20 sales orders per page
        page = self.request.GET.get('page')
        try:
            sales_orders_page = paginator.page(page)
        except PageNotAnInteger:
            sales_orders_page = paginator.page(1)
        except EmptyPage:
            sales_orders_page = paginator.page(paginator.num_pages)
        
        # Calculate statistics dynamically (use filtered queryset for displayed stats)
        total_orders = sales_orders.count()
        total_value = sales_orders.aggregate(total_value=Sum('total'))['total_value'] or 0
        
        # Status breakdown
        status_counts = {}
        for choice in SALES_ORDER_STATUS_CHOICES:
            status_counts[choice[0]] = sales_orders.filter(status=choice[0]).count()
        
        # Get related data for dropdowns
        customers = Customer.objects.filter(company=company)
        products = Product.objects.filter(company=company, is_active=True)
        taxes = Tax.objects.filter(company=company, is_active=True)
        quotations = Quotation.objects.filter(company=company, status='accepted')
        currencies = Currency.objects.filter(company=company, is_active=True)
        
        context.update({
            'sales_orders': sales_orders,
            'sales_orders_page': sales_orders_page,
            'total_orders': total_orders,
            'total_value': total_value,
            'status_counts': status_counts,
            'customers': customers,
            'products': products,
            'taxes': taxes,
            'quotations': quotations,
            'currencies': currencies,
            # Filter context for maintaining state
            'current_search': search_query,
            'current_status': status_filter,
            'current_customer': customer_filter,
            'current_date_from': date_from,
        })
        return context

@login_required
def sales_order_detail(request, pk):
    """Detailed view of a sales order - supports both HTML and JSON responses"""
    company = request.user.company
    sales_order = get_object_or_404(SalesOrder, pk=pk, company=company)
    items = sales_order.items.select_related('product', 'tax').all()
    delivery_notes = sales_order.delivery_notes.all()
    
    # Handle AJAX requests
    if request.headers.get('Content-Type') == 'application/json' or request.GET.get('format') == 'json':
        items_data = []
        for item in items:
            items_data.append({
                'id': item.id,
                'product_id': item.product.id,
                'product_name': item.product.name,
                'quantity': str(item.quantity),
                'unit_price': str(item.unit_price),
                'total': str(item.total)
            })
        
        return JsonResponse({
            'success': True,
            'sales_order': {
                'id': sales_order.id,
                'customer_id': sales_order.customer.id,
                'customer_name': sales_order.customer.name,
                'quotation_id': sales_order.quotation.id if sales_order.quotation else None,
                'order_date': sales_order.order_date.strftime('%Y-%m-%d'),
                'delivery_date': sales_order.delivery_date.strftime('%Y-%m-%d') if sales_order.delivery_date else '',
                'status': sales_order.status,
                'currency_id': sales_order.currency.id if sales_order.currency else None,
                'billing_address': sales_order.billing_address or '',
                'shipping_address': sales_order.shipping_address or '',
                'notes': sales_order.notes or '',
                'total': str(sales_order.total),
                'items': items_data
            }
        })
    
    # Regular HTML response
    context = {
        'sales_order': sales_order,
        'items': items,
        'delivery_notes': delivery_notes,
    }
    return render(request, 'sales/salesorder_detail.html', context)

# Delivery Note Views
class DeliveryNotePageView(LoginRequiredMixin, TemplateView):
    template_name = 'sales/deliverynote_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company
        
        delivery_notes = DeliveryNote.objects.filter(company=company).select_related(
            'customer', 'sales_order', 'delivered_by'
        ).prefetch_related('items__product').order_by('-created_at')
        
        # Additional data for template
        customers = Customer.objects.filter(company=company).order_by('name')
        sales_orders = SalesOrder.objects.filter(
            company=company, 
            status__in=['confirmed', 'in_progress']
        ).select_related('customer').order_by('-created_at')
        
        # Statistics
        total_deliveries = delivery_notes.count()
        pending_deliveries = delivery_notes.filter(status='pending').count()
        completed_deliveries = delivery_notes.filter(status='delivered').count()
        
        context.update({
            'delivery_notes': delivery_notes,
            'customers': customers,
            'sales_orders': sales_orders,
            'total_deliveries': total_deliveries,
            'pending_deliveries': pending_deliveries,
            'completed_deliveries': completed_deliveries,
        })
        return context

@login_required
@login_required
def delivery_note_detail(request, pk):
    """Detailed view of a delivery note"""
    company = request.user.company
    delivery_note = get_object_or_404(DeliveryNote, pk=pk, company=company)
    items = delivery_note.items.select_related('product', 'sales_order_item').all()
    
    context = {
        'delivery_note': delivery_note,
        'items': items,
    }
    return render(request, 'sales/deliverynote_detail.html', context)

@login_required
@require_POST
def delivery_notes_create(request):
    """Create a new delivery note"""
    try:
        sales_order_id = request.POST.get('sales_order_id')
        delivery_date = request.POST.get('delivery_date')
        delivery_address = request.POST.get('delivery_address')
        transporter_name = request.POST.get('transporter_name', '')
        vehicle_number = request.POST.get('vehicle_number', '')
        driver_name = request.POST.get('driver_name', '')
        driver_contact = request.POST.get('driver_contact', '')
        notes = request.POST.get('notes', '')
        
        if not all([sales_order_id, delivery_date, delivery_address]):
            return JsonResponse({'success': False, 'error': 'Required fields missing'}, status=400)
        
        sales_order = get_object_or_404(SalesOrder, pk=sales_order_id, company=request.user.company)
        
        # Parse delivery date
        try:
            parsed_delivery_date = datetime.strptime(delivery_date, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Invalid delivery date format'}, status=400)
        
        # Create delivery note
        delivery_note = DeliveryNote.objects.create(
            company=request.user.company,
            sales_order=sales_order,
            customer=sales_order.customer,
            delivery_date=parsed_delivery_date,
            delivery_address=delivery_address,
            transporter_name=transporter_name,
            vehicle_number=vehicle_number,
            driver_name=driver_name,
            driver_contact=driver_contact,
            notes=notes
        )
        
        # Create delivery note items for all sales order items
        for so_item in sales_order.items.all():
            DeliveryNoteItem.objects.create(
                delivery_note=delivery_note,
                sales_order_item=so_item,
                product=so_item.product,
                quantity_ordered=so_item.quantity,
                quantity_delivered=so_item.quantity  # Default to full delivery
            )
        
        return JsonResponse({
            'success': True,
            'message': 'Delivery note created successfully!',
            'delivery_note': {
                'id': delivery_note.id,
                'delivery_number': delivery_note.delivery_number,
                'customer_name': delivery_note.customer.name,
                'delivery_date': delivery_note.delivery_date.strftime('%Y-%m-%d'),
                'status': delivery_note.status
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
def delivery_notes_export(request):
    """Export delivery notes to CSV"""
    import csv
    from django.http import HttpResponse
    
    company = request.user.company
    delivery_notes = DeliveryNote.objects.filter(company=company).select_related(
        'customer', 'sales_order'
    ).order_by('-created_at')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="delivery_notes.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Delivery Number', 'Customer', 'Sales Order', 'Delivery Date',
        'Status', 'Transporter', 'Vehicle Number', 'Driver Name',
        'Tracking Number', 'Created Date'
    ])
    
    for dn in delivery_notes:
        writer.writerow([
            dn.delivery_number,
            dn.customer.name,
            dn.sales_order.order_number if dn.sales_order else 'Direct',
            dn.delivery_date.strftime('%Y-%m-%d'),
            dn.get_status_display(),
            dn.transporter_name,
            dn.vehicle_number,
            dn.driver_name,
            dn.tracking_number,
            dn.created_at.strftime('%Y-%m-%d %H:%M')
        ])
    
    return response

class InvoicePageView(LoginRequiredMixin, TemplateView):
    template_name = 'sales/invoice_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company
        
        # Get all invoices for the company
        invoices = Invoice.objects.filter(company=company).select_related(
            'customer', 'sales_order', 'delivery_note', 'created_by', 'currency'
        ).prefetch_related('items__product', 'payments').order_by('-created_at')
        
        # Apply filters
        search_query = self.request.GET.get('search', '')
        status_filter = self.request.GET.get('status', '')
        customer_filter = self.request.GET.get('customer', '')
        date_from = self.request.GET.get('date_from', '')
        date_to = self.request.GET.get('date_to', '')
        
        if search_query:
            invoices = invoices.filter(
                Q(customer__name__icontains=search_query) |
                Q(invoice_number__icontains=search_query) |
                Q(notes__icontains=search_query) |
                Q(id__icontains=search_query)
            )
        
        if status_filter:
            invoices = invoices.filter(status=status_filter)
        
        if customer_filter:
            invoices = invoices.filter(customer_id=customer_filter)
        
        if date_from:
            try:
                date_from_parsed = datetime.strptime(date_from, '%Y-%m-%d').date()
                invoices = invoices.filter(invoice_date__gte=date_from_parsed)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to_parsed = datetime.strptime(date_to, '%Y-%m-%d').date()
                invoices = invoices.filter(invoice_date__lte=date_to_parsed)
            except ValueError:
                pass
        
        # Pagination
        paginator = Paginator(invoices, 20)  # Show 20 invoices per page
        page = self.request.GET.get('page')
        try:
            invoices_page = paginator.page(page)
        except PageNotAnInteger:
            invoices_page = paginator.page(1)
        except EmptyPage:
            invoices_page = paginator.page(paginator.num_pages)
        
        # Calculate statistics dynamically (use filtered queryset for displayed stats)
        total_invoices = invoices.count()
        total_value = invoices.aggregate(total_value=Sum('total'))['total_value'] or 0
        total_paid = invoices.aggregate(total_paid=Sum('paid_amount'))['total_paid'] or 0
        total_outstanding = total_value - total_paid
        
        # Status breakdown
        status_counts = {}
        for choice_value, choice_label in [
            ('draft', 'Draft'),
            ('sent', 'Sent'),
            ('paid', 'Paid'),
            ('partially_paid', 'Partially Paid'),
            ('overdue', 'Overdue'),
            ('cancelled', 'Cancelled')
        ]:
            status_counts[choice_value] = invoices.filter(status=choice_value).count()
        
        # Overdue invoices
        overdue_count = invoices.filter(status='overdue').count()
        
        # Get related data for dropdowns
        customers = Customer.objects.filter(company=company)
        products = Product.objects.filter(company=company, is_active=True)
        taxes = Tax.objects.filter(company=company, is_active=True)
        sales_orders = SalesOrder.objects.filter(company=company, status__in=['confirmed', 'delivered'])
        currencies = Currency.objects.filter(company=company, is_active=True)
        
        context.update({
            'invoices': invoices,
            'invoices_page': invoices_page,
            'total_invoices': total_invoices,
            'total_value': total_value,
            'total_paid': total_paid,
            'total_outstanding': total_outstanding,
            'status_counts': status_counts,
            'overdue_count': overdue_count,
            'customers': customers,
            'products': products,
            'taxes': taxes,
            'sales_orders': sales_orders,
            'currencies': currencies,
            # Filter context for maintaining state
            'current_search': search_query,
            'current_status': status_filter,
            'current_customer': customer_filter,
            'current_date_from': date_from,
            'current_date_to': date_to,
        })
        return context

@login_required
def invoice_detail(request, pk):
    """Detailed view of an invoice - supports both HTML and JSON responses"""
    company = request.user.company
    invoice = get_object_or_404(Invoice, pk=pk, company=company)
    items = invoice.items.select_related('product', 'tax').all()
    payments = invoice.payments.all().order_by('-payment_date')
    
    # Handle AJAX requests
    if request.headers.get('Content-Type') == 'application/json' or request.GET.get('format') == 'json':
        items_data = []
        for item in items:
            items_data.append({
                'id': item.id,
                'product_id': item.product.id,
                'product_name': item.product.name,
                'quantity': str(item.quantity),
                'unit_price': str(item.unit_price),
                'tax_id': item.tax.id if item.tax else None,
                'total': str(item.total)
            })
        
        payments_data = []
        for payment in payments:
            payments_data.append({
                'id': payment.id,
                'amount': str(payment.amount),
                'payment_date': payment.payment_date.strftime('%Y-%m-%d'),
                'payment_method': payment.payment_method,
                'reference': payment.reference or ''
            })
        
        return JsonResponse({
            'success': True,
            'invoice': {
                'id': invoice.id,
                'customer_id': invoice.customer.id,
                'customer_name': invoice.customer.name,
                'sales_order_id': invoice.sales_order.id if invoice.sales_order else None,
                'invoice_number': invoice.invoice_number or '',
                'invoice_date': invoice.invoice_date.strftime('%Y-%m-%d'),
                'due_date': invoice.due_date.strftime('%Y-%m-%d'),
                'status': invoice.status,
                'currency_id': invoice.currency.id if invoice.currency else None,
                'payment_terms': invoice.payment_terms or '',
                'notes': invoice.notes or '',
                'total': str(invoice.total),
                'paid_amount': str(invoice.paid_amount),
                'items': items_data,
                'payments': payments_data
            }
        })
    
    # Regular HTML response
    context = {
        'invoice': invoice,
        'items': items,
        'payments': payments,
    }
    return render(request, 'sales/invoice_detail.html', context)

# Invoice CRUD Operations
@login_required
@require_POST
def invoices_add(request):
    """Create a new invoice with enhanced line items"""
    try:
        # Basic invoice fields
        customer_id = request.POST.get('customer_id')
        sales_order_id = request.POST.get('sales_order_id')
        invoice_date = request.POST.get('invoice_date')
        due_date = request.POST.get('due_date')
        payment_terms = request.POST.get('payment_terms', '')
        notes = request.POST.get('notes', '')
        currency_id = request.POST.get('currency_id')
        
        # Handle form action
        action = request.POST.get('action', 'save_draft')
        status = 'sent' if action == 'send' else 'draft'
        
        if not customer_id:
            messages.error(request, 'Customer is required.')
            return redirect('sales:invoices')
        
        customer = get_object_or_404(Customer, pk=customer_id, company=request.user.company)
        sales_order = None
        if sales_order_id:
            sales_order = get_object_or_404(SalesOrder, pk=sales_order_id, company=request.user.company)
        
        currency = None
        if currency_id:
            currency = get_object_or_404(Currency, pk=currency_id, company=request.user.company)
        
        # Parse dates
        parsed_invoice_date = timezone.now().date()
        if invoice_date:
            try:
                parsed_invoice_date = datetime.strptime(invoice_date, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        parsed_due_date = parsed_invoice_date + timedelta(days=30)
        if due_date:
            try:
                parsed_due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        # Create invoice
        invoice = Invoice.objects.create(
            company=request.user.company,
            customer=customer,
            sales_order=sales_order,
            created_by=request.user,
            invoice_date=parsed_invoice_date,
            due_date=parsed_due_date,
            payment_terms=payment_terms,
            notes=notes,
            status=status,
            currency=currency
        )
        
        # Process line items with enhanced fields
        total_amount = Decimal('0.00')
        tax_total = Decimal('0.00')
        discount_total = Decimal('0.00')
        items_data = {}
        
        # Collect item data
        for key, value in request.POST.items():
            if key.startswith('items[') and '][' in key:
                item_part = key[6:]  # Remove 'items['
                if '][' in item_part:
                    index_str, field = item_part.split('][', 1)
                    field = field.rstrip(']')
                    try:
                        index = int(index_str)
                        if index not in items_data:
                            items_data[index] = {}
                        items_data[index][field] = value
                    except (ValueError, IndexError):
                        continue
        
        # Create line items with enhanced features
        for index, item_data in items_data.items():
            product_id = item_data.get('product_id')
            quantity = item_data.get('quantity')
            unit_price = item_data.get('unit_price')
            
            if not all([product_id, quantity, unit_price]):
                continue
                
            try:
                product = get_object_or_404(Product, pk=product_id, company=request.user.company)
                quantity = Decimal(str(quantity))
                unit_price = Decimal(str(unit_price))
                
                # Enhanced fields
                description = item_data.get('description', '')
                uom = item_data.get('uom', 'Pcs')
                discount_type = item_data.get('discount_type', 'percent')
                discount_value = Decimal(str(item_data.get('discount_value', 0)))
                tax_id = item_data.get('tax_id')
                tracking_data_str = item_data.get('tracking_data', '[]')
                
                # Parse tracking data
                tracking_data = []
                try:
                    tracking_data = json.loads(tracking_data_str) if tracking_data_str else []
                except json.JSONDecodeError:
                    tracking_data = []
                
                # Get tax object
                tax = None
                if tax_id:
                    try:
                        tax = Tax.objects.get(pk=tax_id, company=request.user.company)
                    except Tax.DoesNotExist:
                        pass
                
                # Create invoice item
                invoice_item = InvoiceItem.objects.create(
                    invoice=invoice,
                    product=product,
                    description=description,
                    quantity=quantity,
                    uom=uom,
                    unit_price=unit_price,
                    discount_type=discount_type,
                    discount_value=discount_value,
                    tax=tax,
                    tracking_data=tracking_data
                )
                
                # Update totals
                total_amount += invoice_item.line_total
                tax_total += invoice_item.tax_amount
                discount_total += invoice_item.discount_amount
                
            except (ValueError, Product.DoesNotExist) as e:
                continue
        
        # Update invoice totals
        invoice.subtotal = total_amount - tax_total + discount_total
        invoice.tax_amount = tax_total
        invoice.discount_amount = discount_total
        invoice.total = total_amount
        invoice.save()
        
        messages.success(request, f'Invoice {invoice.invoice_number} created successfully!')
        
        if action == 'send':
            messages.info(request, f'Invoice {invoice.invoice_number} has been sent to customer.')
        
        return redirect('sales:invoice_detail', pk=invoice.pk)
        
    except Exception as e:
        messages.error(request, f'Error creating invoice: {str(e)}')
        return redirect('sales:invoices')

@login_required
def invoice_form(request, pk=None):
    """Display the invoice form page for creating/editing invoices"""
    company = request.user.company
    
    # Get invoice if editing
    invoice = None
    if pk:
        invoice = get_object_or_404(Invoice, pk=pk, company=company)
    
    # Get form data
    customers = Customer.objects.filter(company=company).order_by('name')
    sales_orders = SalesOrder.objects.filter(company=company, status__in=['confirmed', 'in_progress']).order_by('-order_date')
    currencies = Currency.objects.filter(company=company, is_active=True).order_by('name')
    products = Product.objects.filter(company=company, is_active=True).order_by('name')
    taxes = Tax.objects.filter(company=company, is_active=True).order_by('name')
    
    context = {
        'invoice': invoice,
        'customers': customers,
        'sales_orders': sales_orders,
        'currencies': currencies,
        'products': products,
        'taxes': taxes,
        'today': timezone.now().date(),
    }
    
    # Handle form submission
    if request.method == 'POST':
        if invoice:
            # Update existing invoice
            return invoices_edit(request, pk)
        else:
            # Create new invoice
            return invoices_add(request)
    
    return render(request, 'sales/invoice_form.html', context)

@login_required
def salesorder_form(request, pk=None):
    """Display the sales order form page for creating/editing sales orders"""
    company = request.user.company
    
    # Get sales order if editing
    sales_order = None
    if pk:
        sales_order = get_object_or_404(SalesOrder, pk=pk, company=company)
    
    # Get form data
    customers = Customer.objects.filter(company=company).order_by('name')
    quotations = Quotation.objects.filter(company=company, status='accepted').order_by('-date')
    currencies = Currency.objects.filter(company=company, is_active=True).order_by('name')
    products = Product.objects.filter(company=company, is_active=True).order_by('name')
    taxes = Tax.objects.filter(company=company, is_active=True).order_by('name')
    
    context = {
        'sales_order': sales_order,
        'customers': customers,
        'quotations': quotations,
        'currencies': currencies,
        'products': products,
        'taxes': taxes,
        'today': timezone.now().date(),
    }
    
    # Handle form submission
    if request.method == 'POST':
        if sales_order:
            # Update existing sales order
            return salesorders_edit(request, pk)
        else:
            # Create new sales order
            return salesorders_add(request)
    
    return render(request, 'sales/salesorder_form.html', context)

@login_required
@require_POST
def invoices_edit(request, pk):
    """Update an existing invoice"""
    try:
        invoice = get_object_or_404(Invoice, pk=pk, company=request.user.company)
        
        customer_id = request.POST.get('customer_id')
        sales_order_id = request.POST.get('sales_order_id')
        invoice_date = request.POST.get('invoice_date')
        due_date = request.POST.get('due_date')
        payment_terms = request.POST.get('payment_terms', '')
        notes = request.POST.get('notes', '')
        status = request.POST.get('status', 'draft')
        currency_id = request.POST.get('currency_id')
        
        if not customer_id:
            return JsonResponse({'success': False, 'error': 'Customer is required.'}, status=400)
        
        # Update invoice fields
        customer = get_object_or_404(Customer, pk=customer_id, company=request.user.company)
        invoice.customer = customer
        
        if sales_order_id:
            sales_order = get_object_or_404(SalesOrder, pk=sales_order_id, company=request.user.company)
            invoice.sales_order = sales_order
        
        if currency_id:
            currency = get_object_or_404(Currency, pk=currency_id, company=request.user.company)
            invoice.currency = currency
        
        # Parse dates
        if invoice_date:
            try:
                invoice.invoice_date = datetime.strptime(invoice_date, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        if due_date:
            try:
                invoice.due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        invoice.payment_terms = payment_terms
        invoice.notes = notes
        invoice.status = status
        
        # Clear existing items and add new ones
        invoice.items.all().delete()
        
        # Process line items (same logic as add)
        total_amount = Decimal('0.00')
        items_data = {}
        
        # Collect item data
        for key, value in request.POST.items():
            if key.startswith('items[') and '][' in key:
                item_part = key[6:]
                if '][' in item_part:
                    index_str, field = item_part.split('][', 1)
                    field = field.rstrip(']')
                    try:
                        index = int(index_str)
                        if index not in items_data:
                            items_data[index] = {}
                        items_data[index][field] = value
                    except (ValueError, IndexError):
                        continue
        
        # Create line items
        for index, item_data in items_data.items():
            product_id = item_data.get('product_id')
            quantity = item_data.get('quantity')
            unit_price = item_data.get('unit_price')
            tax_id = item_data.get('tax_id')
            
            if not all([product_id, quantity, unit_price]):
                continue
                
            try:
                product = get_object_or_404(Product, pk=product_id, company=request.user.company)
                quantity = Decimal(str(quantity))
                unit_price = Decimal(str(unit_price))
                
                tax = None
                if tax_id:
                    tax = get_object_or_404(Tax, pk=tax_id, company=request.user.company)
                
                # Calculate tax amount
                subtotal = quantity * unit_price
                tax_amount = Decimal('0.00')
                if tax:
                    tax_amount = subtotal * (tax.rate / 100)
                
                # Create invoice item
                InvoiceItem.objects.create(
                    invoice=invoice,
                    product=product,
                    quantity=quantity,
                    unit_price=unit_price,
                    tax=tax,
                    total=subtotal + tax_amount
                )
                
                total_amount += subtotal + tax_amount
                
            except (ValueError, Product.DoesNotExist):
                continue
        
        # Update invoice total
        invoice.total = total_amount
        invoice.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Invoice updated successfully!',
            'invoice': {
                'id': invoice.id,
                'customer_name': invoice.customer.name,
                'invoice_number': invoice.invoice_number or f'INV-{invoice.id:04d}',
                'invoice_date': invoice.invoice_date.strftime('%Y-%m-%d'),
                'due_date': invoice.due_date.strftime('%Y-%m-%d'),
                'total': str(invoice.total),
                'status': invoice.status,
                'notes': invoice.notes
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_POST
def invoices_delete(request, pk):
    """Delete an invoice"""
    company = request.user.company
    invoice = get_object_or_404(Invoice, pk=pk, company=company)
    
    try:
        invoice_number = invoice.invoice_number or f"INV-{invoice.id:04d}"
        invoice.delete()
        return JsonResponse({
            'success': True, 
            'message': f'Invoice {invoice_number} deleted successfully!'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_POST
def invoices_send(request, pk):
    """Send an invoice (change status from draft to sent)"""
    company = request.user.company
    invoice = get_object_or_404(Invoice, pk=pk, company=company)
    
    try:
        if invoice.status == 'draft':
            invoice.status = 'sent'
            invoice.save()
            
            invoice_number = invoice.invoice_number or f"INV-{invoice.id:04d}"
            return JsonResponse({
                'success': True, 
                'message': f'Invoice {invoice_number} sent successfully!'
            })
        else:
            return JsonResponse({
                'success': False, 
                'error': f'Invoice cannot be sent from {invoice.get_status_display()} status'
            })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_POST
def invoices_mark_paid(request, pk):
    """Mark an invoice as paid"""
    company = request.user.company
    invoice = get_object_or_404(Invoice, pk=pk, company=company)
    
    try:
        if invoice.status in ['sent', 'partially_paid', 'overdue']:
            invoice.status = 'paid'
            invoice.paid_amount = invoice.total
            invoice.save()
            
            invoice_number = invoice.invoice_number or f"INV-{invoice.id:04d}"
            return JsonResponse({
                'success': True, 
                'message': f'Invoice {invoice_number} marked as paid!'
            })
        else:
            return JsonResponse({
                'success': False, 
                'error': f'Invoice cannot be marked as paid from {invoice.get_status_display()} status'
            })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# Payment Views
class PaymentPageView(LoginRequiredMixin, TemplateView):
    template_name = 'sales/payment_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company
        
        payments = Payment.objects.filter(company=company).select_related(
            'customer', 'invoice', 'received_by', 'currency', 'bank_account'
        ).order_by('-created_at')
        
        # Statistics
        total_payments = payments.count()
        total_amount = payments.aggregate(total_amount=Sum('amount'))['total_amount'] or 0
        
        # Method breakdown
        from .models import PAYMENT_METHOD_CHOICES
        method_stats = {}
        for choice in PAYMENT_METHOD_CHOICES:
            method_stats[choice[0]] = payments.filter(method=choice[0]).aggregate(
                count=Count('id'), total=Sum('amount')
            )
        
        # Recent payments
        recent_payments = payments[:10]
        
        context.update({
            'payments': payments,
            'total_payments': total_payments,
            'total_amount': total_amount,
            'method_stats': method_stats,
            'recent_payments': recent_payments,
        })
        return context

@login_required
def payment_receipt(request, pk):
    """Generate payment receipt for printing"""
    company = request.user.company
    payment = get_object_or_404(Payment, pk=pk, company=company)
    
    context = {
        'payment': payment,
    }
    return render(request, 'sales/payment_receipt.html', context)

@login_required
def payment_detail(request, pk):
    """Detailed view of a payment"""
    company = request.user.company
    payment = get_object_or_404(Payment, pk=pk, company=company)
    
    context = {
        'payment': payment,
    }
    return render(request, 'sales/payment_detail.html', context)

@login_required
@require_POST
def payments_create(request):
    """Create a new payment"""
    try:
        customer_id = request.POST.get('customer_id')
        invoice_id = request.POST.get('invoice_id')
        amount = request.POST.get('amount')
        payment_date = request.POST.get('payment_date')
        method = request.POST.get('method')
        reference = request.POST.get('reference', '')
        notes = request.POST.get('notes', '')
        
        if not all([customer_id, amount, payment_date, method]):
            return JsonResponse({'success': False, 'error': 'Required fields missing'}, status=400)
        
        customer = get_object_or_404(Customer, pk=customer_id, company=request.user.company)
        invoice = None
        if invoice_id:
            invoice = get_object_or_404(Invoice, pk=invoice_id, company=request.user.company)
        
        # Parse payment date
        try:
            parsed_payment_date = datetime.strptime(payment_date, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Invalid payment date format'}, status=400)
        
        # Create payment
        payment = Payment.objects.create(
            company=request.user.company,
            customer=customer,
            invoice=invoice,
            amount=Decimal(amount),
            payment_date=parsed_payment_date,
            method=method,
            reference=reference,
            notes=notes,
            received_by=request.user
        )
        
        # Update invoice if provided
        if invoice:
            invoice.paid_amount += payment.amount
            if invoice.paid_amount >= invoice.total:
                invoice.status = 'paid'
            elif invoice.paid_amount > 0:
                invoice.status = 'partially_paid'
            invoice.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Payment recorded successfully!',
            'payment': {
                'id': payment.id,
                'payment_number': payment.payment_number,
                'customer_name': payment.customer.name,
                'amount': float(payment.amount),
                'method': payment.get_method_display()
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_POST
def payments_edit(request, pk):
    """Edit an existing payment"""
    try:
        payment = get_object_or_404(Payment, pk=pk, company=request.user.company)
        
        customer_id = request.POST.get('customer_id')
        invoice_id = request.POST.get('invoice_id')
        amount = request.POST.get('amount')
        payment_date = request.POST.get('payment_date')
        method = request.POST.get('method')
        reference = request.POST.get('reference', '')
        notes = request.POST.get('notes', '')
        
        if not all([customer_id, amount, payment_date, method]):
            return JsonResponse({'success': False, 'error': 'Required fields missing'}, status=400)
        
        customer = get_object_or_404(Customer, pk=customer_id, company=request.user.company)
        
        # Handle invoice change
        old_invoice = payment.invoice
        new_invoice = None
        if invoice_id:
            new_invoice = get_object_or_404(Invoice, pk=invoice_id, company=request.user.company)
        
        # Parse payment date
        try:
            parsed_payment_date = datetime.strptime(payment_date, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Invalid payment date format'}, status=400)
        
        # Store old amount for invoice updates
        old_amount = payment.amount
        
        # Update payment
        payment.customer = customer
        payment.invoice = new_invoice
        payment.amount = Decimal(amount)
        payment.payment_date = parsed_payment_date
        payment.method = method
        payment.reference = reference
        payment.notes = notes
        payment.save()
        
        # Update old invoice if exists
        if old_invoice:
            old_invoice.paid_amount -= old_amount
            if old_invoice.paid_amount <= 0:
                old_invoice.status = 'pending'
            elif old_invoice.paid_amount < old_invoice.total:
                old_invoice.status = 'partially_paid'
            else:
                old_invoice.status = 'paid'
            old_invoice.save()
        
        # Update new invoice if exists
        if new_invoice:
            new_invoice.paid_amount += payment.amount
            if new_invoice.paid_amount >= new_invoice.total:
                new_invoice.status = 'paid'
            elif new_invoice.paid_amount > 0:
                new_invoice.status = 'partially_paid'
            new_invoice.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Payment updated successfully!',
            'payment': {
                'id': payment.id,
                'payment_number': payment.payment_number,
                'customer_name': payment.customer.name,
                'amount': float(payment.amount),
                'method': payment.get_method_display()
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
def payments_export(request):
    """Export payments to CSV"""
    import csv
    from django.http import HttpResponse
    
    company = request.user.company
    payments = Payment.objects.filter(company=company).select_related(
        'customer', 'invoice', 'received_by'
    ).order_by('-created_at')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="payments.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Payment Number', 'Customer', 'Invoice', 'Amount', 'Method',
        'Payment Date', 'Reference', 'Received By', 'Created Date'
    ])
    
    for payment in payments:
        writer.writerow([
            payment.payment_number,
            payment.customer.name if payment.customer else 'N/A',
            payment.invoice.invoice_number if payment.invoice else 'Advance',
            payment.amount,
            payment.get_method_display(),
            payment.payment_date.strftime('%Y-%m-%d'),
            payment.reference,
            payment.received_by.username if payment.received_by else 'N/A',
            payment.created_at.strftime('%Y-%m-%d %H:%M')
        ])
    
    return response

# Credit Note Views
class CreditNotePageView(LoginRequiredMixin, TemplateView):
    template_name = 'sales/creditnote_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company
        
        credit_notes = CreditNote.objects.filter(company=company).select_related(
            'customer', 'invoice', 'created_by', 'currency'
        ).order_by('-created_at')
        
        # Statistics
        total_credit_notes = credit_notes.count()
        total_value = credit_notes.aggregate(total_value=Sum('total'))['total_value'] or 0
        
        # Reason breakdown
        reason_stats = {}
        for choice in credit_notes.model._meta.get_field('reason').choices:
            reason_stats[choice[0]] = credit_notes.filter(reason=choice[0]).count()
        
        context.update({
            'credit_notes': credit_notes,
            'total_credit_notes': total_credit_notes,
            'total_value': total_value,
            'reason_stats': reason_stats,
        })
        return context

# Product CRUD Operations
@login_required
def products_ui(request):
    products = Product.objects.filter(company=request.user.company)
    return render(request, 'sales/products-ui.html', {'products': products})

@login_required
@require_POST
def products_add(request):
    name = request.POST.get('name')
    description = request.POST.get('description', '')
    sku = request.POST.get('sku', '')
    price = request.POST.get('price')
    is_service = request.POST.get('is_service') == 'on'
    is_active = request.POST.get('is_active') == 'on'
    
    if not name or not price:
        return JsonResponse({'success': False, 'error': 'Name and price are required.'}, status=400)
    
    try:
        product = Product.objects.create(
            company=request.user.company,
            name=name,
            description=description,
            sku=sku,
            price=Decimal(price),
            is_service=is_service,
            is_active=is_active
        )
        return JsonResponse({
            'success': True,
            'product': {
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'sku': product.sku,
                'price': str(product.price),
                'is_service': product.is_service,
                'is_active': product.is_active,
                'created_at': product.created_at.strftime('%Y-%m-%d')
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_POST
def products_edit(request, pk):
    product = get_object_or_404(Product, pk=pk, company=request.user.company)
    name = request.POST.get('name')
    description = request.POST.get('description', '')
    sku = request.POST.get('sku', '')
    price = request.POST.get('price')
    is_service = request.POST.get('is_service') == 'on'
    is_active = request.POST.get('is_active') == 'on'
    
    if not name or not price:
        return JsonResponse({'success': False, 'error': 'Name and price are required.'}, status=400)
    
    try:
        product.name = name
        product.description = description
        product.sku = sku
        product.price = Decimal(price)
        product.is_service = is_service
        product.is_active = is_active
        product.save()
        
        return JsonResponse({
            'success': True,
            'product': {
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'sku': product.sku,
                'price': str(product.price),
                'is_service': product.is_service,
                'is_active': product.is_active,
                'created_at': product.created_at.strftime('%Y-%m-%d')
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_POST
def products_delete(request, pk):
    product = get_object_or_404(Product, pk=pk, company=request.user.company)
    try:
        product.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

# Tax CRUD Operations
@login_required
def taxes_detail(request, pk):
    """Get tax details for editing"""
    tax = get_object_or_404(Tax, pk=pk, company=request.user.company)
    return JsonResponse({
        'success': True,
        'tax': {
            'id': tax.id,
            'name': tax.name,
            'rate': str(tax.rate),
            'tax_type': getattr(tax, 'tax_type', 'sales'),  # Default if field doesn't exist
            'description': getattr(tax, 'description', ''),
            'company': tax.company.id if tax.company else '',
            'tax_account': tax.account.id if tax.account else '',
            'is_active': tax.is_active,
            'is_default': getattr(tax, 'is_default', False),
        }
    })

@login_required
@require_POST
def taxes_add(request):
    name = request.POST.get('name')
    rate = request.POST.get('rate')
    is_active = request.POST.get('is_active') == 'on' or request.POST.get('is_active') == 'true'
    description = request.POST.get('description', '')
    tax_account_id = request.POST.get('tax_account')
    
    if not name or not rate:
        return JsonResponse({'success': False, 'error': 'Name and rate are required.'}, status=400)
    
    try:
        # Get account if provided
        account = None
        if tax_account_id:
            from accounting.models import Account
            try:
                account = Account.objects.get(id=tax_account_id, company=request.user.company)
            except Account.DoesNotExist:
                pass
        
        tax = Tax.objects.create(
            company=request.user.company,
            name=name,
            rate=Decimal(rate),
            is_active=is_active,
            account=account
        )
        
        # Set description if the model supports it
        if hasattr(tax, 'description'):
            tax.description = description
            tax.save()
            
        return JsonResponse({
            'success': True,
            'tax': {
                'id': tax.id,
                'name': tax.name,
                'rate': str(tax.rate),
                'is_active': tax.is_active
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
def taxes_detail(request, pk):
    """Get tax details for editing"""
    try:
        tax = get_object_or_404(Tax, pk=pk, company=request.user.company)
        
        return JsonResponse({
            'success': True,
            'tax': {
                'id': tax.id,
                'name': tax.name,
                'rate': str(tax.rate),
                'is_active': tax.is_active,
                'tax_account': tax.account.id if tax.account else None,
                'company': tax.company.id,
                'created_at': tax.created_at.strftime('%Y-%m-%d')
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_POST
def taxes_edit(request, pk):
    tax = get_object_or_404(Tax, pk=pk, company=request.user.company)
    name = request.POST.get('name')
    rate = request.POST.get('rate')
    is_active = request.POST.get('is_active') == 'on' or request.POST.get('is_active') == 'true'
    description = request.POST.get('description', '')
    tax_account_id = request.POST.get('tax_account')
    
    if not name or not rate:
        return JsonResponse({'success': False, 'error': 'Name and rate are required.'}, status=400)
    
    try:
        # Get account if provided
        if tax_account_id:
            from accounting.models import Account
            try:
                account = Account.objects.get(id=tax_account_id, company=request.user.company)
                tax.account = account
            except Account.DoesNotExist:
                pass
        elif tax_account_id == '':
            tax.account = None
            
        tax.name = name
        tax.rate = Decimal(rate)
        tax.is_active = is_active
        
        # Set description if the model supports it
        if hasattr(tax, 'description'):
            tax.description = description
            
        tax.save()
        
        return JsonResponse({
            'success': True,
            'tax': {
                'id': tax.id,
                'name': tax.name,
                'rate': str(tax.rate),
                'is_active': tax.is_active
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_POST
def taxes_delete(request, pk):
    tax = get_object_or_404(Tax, pk=pk, company=request.user.company)
    try:
        tax.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

# Customer CRUD Operations (Sales Module Integration)
@login_required
@require_POST
def customers_add(request):
    """Create a new customer from sales module"""
    try:
        name = request.POST.get('name')
        customer_code = request.POST.get('customer_code', '')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')
        customer_group = request.POST.get('customer_group', '')
        address = request.POST.get('address', '')
        preferred_payment_method = request.POST.get('preferred_payment_method', '')
        loyalty_points = request.POST.get('loyalty_points', 0)
        account_id = request.POST.get('account')
        
        if not name:
            return JsonResponse({'success': False, 'error': 'Customer name is required'}, status=400)
        
        # Get account if provided
        account = None
        if account_id:
            from accounting.models import Account
            try:
                account = Account.objects.get(id=account_id, company=request.user.company)
            except Account.DoesNotExist:
                pass
        
        # Generate customer code if not provided
        if not customer_code:
            last_customer = Customer.objects.filter(company=request.user.company).order_by('-id').first()
            if last_customer and last_customer.customer_code:
                try:
                    last_num = int(last_customer.customer_code.replace('CUST', ''))
                    customer_code = f'CUST{last_num + 1:04d}'
                except:
                    customer_code = f'CUST{Customer.objects.filter(company=request.user.company).count() + 1:04d}'
            else:
                customer_code = f'CUST{Customer.objects.filter(company=request.user.company).count() + 1:04d}'
        
        customer = Customer.objects.create(
            company=request.user.company,
            name=name,
            customer_code=customer_code,
            email=email,
            phone=phone,
            customer_group=customer_group,
            address=address,
            preferred_payment_method=preferred_payment_method,
            loyalty_points=int(loyalty_points) if loyalty_points else 0,
            account=account,
            created_by=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Customer created successfully!',
            'customer': {
                'id': customer.id,
                'name': customer.name,
                'customer_code': customer.customer_code,
                'email': customer.email,
                'phone': customer.phone
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_POST
def customers_edit(request, pk):
    """Update an existing customer"""
    try:
        customer = get_object_or_404(Customer, pk=pk, company=request.user.company)
        
        name = request.POST.get('name')
        customer_code = request.POST.get('customer_code', '')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')
        customer_group = request.POST.get('customer_group', '')
        address = request.POST.get('address', '')
        preferred_payment_method = request.POST.get('preferred_payment_method', '')
        loyalty_points = request.POST.get('loyalty_points', 0)
        account_id = request.POST.get('account')
        
        if not name:
            return JsonResponse({'success': False, 'error': 'Customer name is required'}, status=400)
        
        # Get account if provided
        if account_id:
            from accounting.models import Account
            try:
                account = Account.objects.get(id=account_id, company=request.user.company)
                customer.account = account
            except Account.DoesNotExist:
                pass
        elif account_id == '':
            customer.account = None
        
        customer.name = name
        customer.customer_code = customer_code
        customer.email = email
        customer.phone = phone
        customer.customer_group = customer_group
        customer.address = address
        customer.preferred_payment_method = preferred_payment_method
        customer.loyalty_points = int(loyalty_points) if loyalty_points else 0
        customer.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Customer updated successfully!',
            'customer': {
                'id': customer.id,
                'name': customer.name,
                'customer_code': customer.customer_code,
                'email': customer.email,
                'phone': customer.phone
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
def customers_detail(request, pk):
    """Get customer details"""
    try:
        customer = get_object_or_404(Customer, pk=pk, company=request.user.company)
        
        return JsonResponse({
            'success': True,
            'customer': {
                'id': customer.id,
                'name': customer.name,
                'customer_code': customer.customer_code,
                'email': customer.email,
                'phone': customer.phone,
                'customer_group': customer.customer_group,
                'address': customer.address,
                'preferred_payment_method': customer.preferred_payment_method,
                'loyalty_points': customer.loyalty_points,
                'account': customer.account.id if customer.account else None,
                'created_at': customer.created_at.strftime('%Y-%m-%d')
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_POST
def customers_delete(request, pk):
    """Delete a customer"""
    try:
        customer = get_object_or_404(Customer, pk=pk, company=request.user.company)
        
        # Check if customer has associated transactions
        if (customer.quotations.exists() or customer.sales_orders.exists() or 
            customer.invoices.exists() or customer.delivery_notes.exists()):
            return JsonResponse({
                'success': False, 
                'error': 'Cannot delete customer with existing transactions'
            }, status=400)
        
        customer.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Customer deleted successfully!'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

# Quotation CRUD Operations
@login_required
@require_POST
def quotations_add(request):
    customer_id = request.POST.get('customer_id')
    valid_until = request.POST.get('valid_until')
    notes = request.POST.get('notes', '')
    
    if not customer_id:
        return JsonResponse({'success': False, 'error': 'Customer is required.'}, status=400)
    
    try:
        customer = get_object_or_404(Customer, pk=customer_id, company=request.user.company)
        quotation = Quotation.objects.create(
            company=request.user.company,
            customer=customer,
            created_by=request.user,
            valid_until=valid_until if valid_until else None,
            notes=notes
        )
        return JsonResponse({
            'success': True,
            'quotation': {
                'id': quotation.id,
                'customer_name': quotation.customer.name,
                'date': quotation.date.strftime('%Y-%m-%d'),
                'valid_until': quotation.valid_until.strftime('%Y-%m-%d') if quotation.valid_until else '',
                'total': str(quotation.total),
                'status': quotation.status,
                'notes': quotation.notes
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_POST
def quotations_edit(request, pk):
    quotation = get_object_or_404(Quotation, pk=pk, company=request.user.company)
    customer_id = request.POST.get('customer_id')
    valid_until = request.POST.get('valid_until')
    status = request.POST.get('status')
    notes = request.POST.get('notes', '')
    
    if not customer_id:
        return JsonResponse({'success': False, 'error': 'Customer is required.'}, status=400)
    
    try:
        customer = get_object_or_404(Customer, pk=customer_id, company=request.user.company)
        quotation.customer = customer
        quotation.valid_until = valid_until if valid_until else None
        quotation.status = status if status else quotation.status
        quotation.notes = notes
        quotation.save()
        
        return JsonResponse({
            'success': True,
            'quotation': {
                'id': quotation.id,
                'customer_name': quotation.customer.name,
                'date': quotation.date.strftime('%Y-%m-%d'),
                'valid_until': quotation.valid_until.strftime('%Y-%m-%d') if quotation.valid_until else '',
                'total': str(quotation.total),
                'status': quotation.status,
                'notes': quotation.notes
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_POST
def quotations_delete(request, pk):
    """Delete a quotation"""
    company = request.user.company
    quotation = get_object_or_404(Quotation, pk=pk, company=company)
    
    try:
        quotation_number = quotation.quotation_number
        quotation.delete()
        return JsonResponse({
            'success': True, 
            'message': f'Quotation {quotation_number} deleted successfully!'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# Sales Order CRUD Operations
@login_required
def salesorder_form(request, pk=None):
    """Display the sales order form for creating or editing"""
    company = request.user.company
    
    # Get sales order if editing
    sales_order = None
    if pk:
        sales_order = get_object_or_404(SalesOrder, pk=pk, company=company)
    
    # Handle form submission
    if request.method == 'POST':
        if sales_order:
            # Update existing sales order
            return salesorders_edit(request, pk)
        else:
            # Create new sales order
            return salesorders_add(request)
    
    # GET request - show form
    customers = Customer.objects.filter(company=company).order_by('name')
    products = Product.objects.filter(company=company, is_active=True).order_by('name')
    taxes = Tax.objects.filter(company=company, is_active=True).order_by('name')
    currencies = Currency.objects.filter(company=company, is_active=True).order_by('name')
    quotations = Quotation.objects.filter(company=company, status='accepted').order_by('-date')
    
    context = {
        'sales_order': sales_order,
        'customers': customers,
        'products': products,
        'taxes': taxes,
        'currencies': currencies,
        'quotations': quotations,
        'title': 'Edit Sales Order' if sales_order else 'Create Sales Order',
        'today': timezone.now().date(),
    }
    return render(request, 'sales/salesorder_form.html', context)

@login_required
def salesorders_add(request):
    """Create a new sales order with enhanced tracking and UOM support"""
    try:
        # Basic sales order fields
        customer_id = request.POST.get('customer_id')
        quotation_id = request.POST.get('quotation_id')
        order_date = request.POST.get('order_date')
        delivery_date = request.POST.get('delivery_date')
        billing_address = request.POST.get('billing_address', '')
        shipping_address = request.POST.get('shipping_address', '')
        terms_and_conditions = request.POST.get('terms_and_conditions', '')
        notes = request.POST.get('notes', '')
        currency_id = request.POST.get('currency_id')
        
        # Handle form action
        action = request.POST.get('action', 'save_draft')
        status = 'confirmed' if action == 'confirm' else 'pending'
        
        if not customer_id:
            messages.error(request, 'Customer is required.')
            return redirect('sales:sales_orders')
        
        customer = get_object_or_404(Customer, pk=customer_id, company=request.user.company)
        quotation = None
        if quotation_id:
            quotation = get_object_or_404(Quotation, pk=quotation_id, company=request.user.company)
        
        currency = None
        if currency_id:
            currency = get_object_or_404(Currency, pk=currency_id, company=request.user.company)
        
        # Parse dates
        parsed_order_date = timezone.now().date()
        if order_date:
            try:
                parsed_order_date = datetime.strptime(order_date, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        parsed_delivery_date = None
        if delivery_date:
            try:
                parsed_delivery_date = datetime.strptime(delivery_date, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        # Create sales order
        sales_order = SalesOrder.objects.create(
            company=request.user.company,
            customer=customer,
            quotation=quotation,
            created_by=request.user,
            order_date=parsed_order_date,
            delivery_date=parsed_delivery_date,
            billing_address=billing_address,
            shipping_address=shipping_address,
            terms_and_conditions=terms_and_conditions,
            notes=notes,
            status=status,
            currency=currency
        )
        
        # Process line items with enhanced fields
        total_amount = Decimal('0.00')
        tax_total = Decimal('0.00')
        discount_total = Decimal('0.00')
        items_data = {}
        
        # Collect item data
        for key, value in request.POST.items():
            if key.startswith('items[') and '][' in key:
                item_part = key[6:]  # Remove 'items['
                if '][' in item_part:
                    index_str, field = item_part.split('][', 1)
                    field = field.rstrip(']')
                    try:
                        index = int(index_str)
                        if index not in items_data:
                            items_data[index] = {}
                        items_data[index][field] = value
                    except (ValueError, IndexError):
                        continue
        
        # Create line items with enhanced features
        for index, item_data in items_data.items():
            product_id = item_data.get('product_id')
            quantity = item_data.get('quantity')
            unit_price = item_data.get('unit_price')
            
            if not all([product_id, quantity, unit_price]):
                continue
                
            try:
                product = get_object_or_404(Product, pk=product_id, company=request.user.company)
                quantity = Decimal(str(quantity))
                unit_price = Decimal(str(unit_price))
                
                # Enhanced fields
                description = item_data.get('description', '')
                uom = item_data.get('uom', 'Pcs')
                discount_type = item_data.get('discount_type', 'percent')
                discount_value = Decimal(str(item_data.get('discount_value', 0)))
                tax_id = item_data.get('tax_id')
                tracking_data_str = item_data.get('tracking_data', '[]')
                
                # Parse tracking data
                tracking_data = []
                try:
                    tracking_data = json.loads(tracking_data_str) if tracking_data_str else []
                except json.JSONDecodeError:
                    tracking_data = []
                
                # Get tax object
                tax = None
                if tax_id:
                    try:
                        tax = Tax.objects.get(pk=tax_id, company=request.user.company)
                    except Tax.DoesNotExist:
                        pass
                
                # Create sales order item
                so_item = SalesOrderItem.objects.create(
                    sales_order=sales_order,
                    product=product,
                    description=description,
                    quantity=quantity,
                    uom=uom,
                    unit_price=unit_price,
                    discount_type=discount_type,
                    discount_value=discount_value,
                    tax=tax,
                    tracking_data=tracking_data
                )
                
                # Update totals
                total_amount += so_item.line_total
                tax_total += so_item.tax_amount
                discount_total += so_item.discount_amount
                
            except (ValueError, Product.DoesNotExist) as e:
                continue
        
        # Update sales order totals
        sales_order.subtotal = total_amount - tax_total + discount_total
        sales_order.tax_amount = tax_total
        sales_order.discount_amount = discount_total
        sales_order.total = total_amount
        sales_order.save()
        
        messages.success(request, f'Sales Order {sales_order.order_number} created successfully!')
        
        if action == 'confirm':
            messages.info(request, f'Sales Order {sales_order.order_number} has been confirmed.')
        
        return redirect('sales:sales_orders_detail', pk=sales_order.pk)
        
    except Exception as e:
        messages.error(request, f'Error creating sales order: {str(e)}')
        return redirect('sales:sales_orders')

@login_required
def salesorders_edit(request, pk):
    """Edit an existing sales order"""
    company = request.user.company
    sales_order = get_object_or_404(SalesOrder, pk=pk, company=company)
    
    if request.method == 'POST':
        try:
            # Get form data
            customer_id = request.POST.get('customer_id')
            order_date = request.POST.get('order_date')
            delivery_date = request.POST.get('delivery_date')
            currency_id = request.POST.get('currency_id')
            quotation_id = request.POST.get('quotation_id')
            notes = request.POST.get('notes', '')
            billing_address = request.POST.get('billing_address', '')
            shipping_address = request.POST.get('shipping_address', '')
            action = request.POST.get('action', 'save')
            
            # Validate required fields
            if not customer_id or not order_date:
                messages.error(request, 'Customer and order date are required.')
                return redirect('sales:salesorder_form', pk=pk)
            
            # Update basic sales order fields
            customer = get_object_or_404(Customer, pk=customer_id, company=company)
            sales_order.customer = customer
            sales_order.order_date = order_date
            sales_order.delivery_date = delivery_date if delivery_date else None
            sales_order.notes = notes
            sales_order.billing_address = billing_address
            sales_order.shipping_address = shipping_address
            
            # Update currency if provided
            if currency_id:
                currency = get_object_or_404(Currency, pk=currency_id, company=company)
                sales_order.currency = currency
            
            # Update quotation if provided
            if quotation_id:
                quotation = get_object_or_404(Quotation, pk=quotation_id, company=company)
                sales_order.quotation = quotation
            
            # Update status based on action
            if action == 'confirm':
                sales_order.status = 'confirmed'
            elif action == 'draft':
                sales_order.status = 'draft'
            
            sales_order.save()
            
            # Clear existing items
            sales_order.items.all().delete()
            
            # Process line items
            product_ids = request.POST.getlist('product_id[]')
            quantities = request.POST.getlist('quantity[]')
            unit_prices = request.POST.getlist('unit_price[]')
            discounts = request.POST.getlist('discount[]')
            discount_types = request.POST.getlist('discount_type[]')
            tax_ids = request.POST.getlist('tax_id[]')
            descriptions = request.POST.getlist('description[]')
            uoms = request.POST.getlist('uom[]')
            
            # Tracking data
            serial_numbers = request.POST.getlist('serial_number[]')
            batch_numbers = request.POST.getlist('batch_number[]')
            lot_numbers = request.POST.getlist('lot_number[]')
            expiry_dates = request.POST.getlist('expiry_date[]')
            
            total_amount = Decimal('0.00')
            tax_total = Decimal('0.00')
            discount_total = Decimal('0.00')
            
            for i in range(len(product_ids)):
                if not product_ids[i] or not quantities[i] or not unit_prices[i]:
                    continue
                
                try:
                    product = get_object_or_404(Product, pk=product_ids[i], company=company)
                    quantity = Decimal(quantities[i])
                    unit_price = Decimal(unit_prices[i])
                    discount = Decimal(discounts[i]) if discounts[i] else Decimal('0.00')
                    discount_type = discount_types[i] if i < len(discount_types) else 'percentage'
                    
                    # Calculate line total
                    line_total = quantity * unit_price
                    
                    # Apply discount
                    if discount_type == 'percentage':
                        discount_amount = line_total * (discount / 100)
                    else:  # fixed amount
                        discount_amount = discount
                    
                    line_total_after_discount = line_total - discount_amount
                    discount_total += discount_amount
                    
                    # Calculate tax
                    tax_amount = Decimal('0.00')
                    if i < len(tax_ids) and tax_ids[i]:
                        tax = get_object_or_404(Tax, pk=tax_ids[i], company=company)
                        tax_amount = line_total_after_discount * (tax.percentage / 100)
                        tax_total += tax_amount
                    
                    final_line_total = line_total_after_discount + tax_amount
                    total_amount += final_line_total
                    
                    # Prepare tracking data
                    tracking_data = {}
                    if i < len(serial_numbers) and serial_numbers[i]:
                        tracking_data['serial_number'] = serial_numbers[i]
                    if i < len(batch_numbers) and batch_numbers[i]:
                        tracking_data['batch_number'] = batch_numbers[i]
                    if i < len(lot_numbers) and lot_numbers[i]:
                        tracking_data['lot_number'] = lot_numbers[i]
                    if i < len(expiry_dates) and expiry_dates[i]:
                        tracking_data['expiry_date'] = expiry_dates[i]
                    
                    # Create sales order item
                    SalesOrderItem.objects.create(
                        sales_order=sales_order,
                        product=product,
                        description=descriptions[i] if i < len(descriptions) else product.name,
                        quantity=quantity,
                        uom=uoms[i] if i < len(uoms) else product.uom,
                        unit_price=unit_price,
                        discount_type=discount_type,
                        discount_value=discount,
                        tax=tax if i < len(tax_ids) and tax_ids[i] else None,
                        total=final_line_total,
                        tracking_data=tracking_data if tracking_data else None
                    )
                    
                except (ValueError, Product.DoesNotExist) as e:
                    continue
            
            # Update sales order totals
            sales_order.subtotal = total_amount - tax_total + discount_total
            sales_order.tax_amount = tax_total
            sales_order.discount_amount = discount_total
            sales_order.total = total_amount
            sales_order.save()
            
            messages.success(request, f'Sales Order {sales_order.order_number} updated successfully!')
            
            if action == 'confirm':
                messages.info(request, f'Sales Order {sales_order.order_number} has been confirmed.')
            
            return redirect('sales:sales_orders_detail', pk=sales_order.pk)
            
        except Exception as e:
            messages.error(request, f'Error updating sales order: {str(e)}')
            return redirect('sales:salesorder_form', pk=pk)
    
    # If GET request, redirect to form
    return redirect('sales:salesorder_form', pk=pk)

@login_required
@require_POST
def salesorders_delete(request, pk):
    """Delete a sales order"""
    company = request.user.company
    sales_order = get_object_or_404(SalesOrder, pk=pk, company=company)
    
    try:
        order_number = f"SO-{sales_order.id:04d}"
        sales_order.delete()
        return JsonResponse({
            'success': True, 
            'message': f'Sales order {order_number} deleted successfully!'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_POST
def salesorders_confirm(request, pk):
    """Confirm a sales order (change status from draft/pending to confirmed)"""
    company = request.user.company
    sales_order = get_object_or_404(SalesOrder, pk=pk, company=company)
    
    try:
        if sales_order.status in ['draft', 'pending']:
            sales_order.status = 'confirmed'
            sales_order.save()
            
            order_number = f"SO-{sales_order.id:04d}"
            return JsonResponse({
                'success': True, 
                'message': f'Sales order {order_number} confirmed successfully!'
            })
        else:
            return JsonResponse({
                'success': False, 
                'error': f'Sales order cannot be confirmed from {sales_order.get_status_display()} status'
            })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# Line Item Management Functions

# Quotation Line Items
@login_required
@require_POST
def quotation_items_add(request, quotation_id):
    quotation = get_object_or_404(Quotation, pk=quotation_id, company=request.user.company)
    product_id = request.POST.get('product_id')
    quantity = request.POST.get('quantity')
    price = request.POST.get('price')
    tax_id = request.POST.get('tax_id')
    
    if not product_id or not quantity or not price:
        return JsonResponse({'success': False, 'error': 'Product, quantity, and price are required.'}, status=400)
    
    try:
        product = get_object_or_404(Product, pk=product_id, company=request.user.company)
        tax = None
        if tax_id:
            tax = get_object_or_404(Tax, pk=tax_id, company=request.user.company)
        
        quantity = Decimal(quantity)
        price = Decimal(price)
        total = quantity * price
        
        if tax:
            tax_amount = total * (tax.rate / 100)
            total += tax_amount
        
        item = QuotationItem.objects.create(
            quotation=quotation,
            product=product,
            quantity=quantity,
            price=price,
            tax=tax,
            total=total
        )
        
        # Update quotation total
        quotation.total = sum(item.total for item in quotation.items.all())
        quotation.save()
        
        return JsonResponse({
            'success': True,
            'item': {
                'id': item.id,
                'product_name': item.product.name,
                'quantity': str(item.quantity),
                'price': str(item.price),
                'tax_name': item.tax.name if item.tax else '',
                'total': str(item.total)
            },
            'quotation_total': str(quotation.total)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_POST
def quotation_items_edit(request, quotation_id, item_id):
    quotation = get_object_or_404(Quotation, pk=quotation_id, company=request.user.company)
    item = get_object_or_404(QuotationItem, pk=item_id, quotation=quotation)
    
    product_id = request.POST.get('product_id')
    quantity = request.POST.get('quantity')
    price = request.POST.get('price')
    tax_id = request.POST.get('tax_id')
    
    if not product_id or not quantity or not price:
        return JsonResponse({'success': False, 'error': 'Product, quantity, and price are required.'}, status=400)
    
    try:
        product = get_object_or_404(Product, pk=product_id, company=request.user.company)
        tax = None
        if tax_id:
            tax = get_object_or_404(Tax, pk=tax_id, company=request.user.company)
        
        quantity = Decimal(quantity)
        price = Decimal(price)
        total = quantity * price
        
        if tax:
            tax_amount = total * (tax.rate / 100)
            total += tax_amount
        
        item.product = product
        item.quantity = quantity
        item.price = price
        item.tax = tax
        item.total = total
        item.save()
        
        # Update quotation total
        quotation.total = sum(item.total for item in quotation.items.all())
        quotation.save()
        
        return JsonResponse({
            'success': True,
            'item': {
                'id': item.id,
                'product_name': item.product.name,
                'quantity': str(item.quantity),
                'price': str(item.price),
                'tax_name': item.tax.name if item.tax else '',
                'total': str(item.total)
            },
            'quotation_total': str(quotation.total)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_POST
def quotation_items_delete(request, quotation_id, item_id):
    quotation = get_object_or_404(Quotation, pk=quotation_id, company=request.user.company)
    item = get_object_or_404(QuotationItem, pk=item_id, quotation=quotation)
    
    try:
        item.delete()
        
        # Update quotation total
        quotation.total = sum(item.total for item in quotation.items.all())
        quotation.save()
        
        return JsonResponse({
            'success': True,
            'quotation_total': str(quotation.total)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

# Sales Order Line Items
@login_required
@require_POST
def salesorder_items_add(request, salesorder_id):
    sales_order = get_object_or_404(SalesOrder, pk=salesorder_id, company=request.user.company)
    product_id = request.POST.get('product_id')
    quantity = request.POST.get('quantity')
    price = request.POST.get('price')
    tax_id = request.POST.get('tax_id')
    
    if not product_id or not quantity or not price:
        return JsonResponse({'success': False, 'error': 'Product, quantity, and price are required.'}, status=400)
    
    try:
        product = get_object_or_404(Product, pk=product_id, company=request.user.company)
        tax = None
        if tax_id:
            tax = get_object_or_404(Tax, pk=tax_id, company=request.user.company)
        
        quantity = Decimal(quantity)
        price = Decimal(price)
        total = quantity * price
        
        if tax:
            tax_amount = total * (tax.rate / 100)
            total += tax_amount
        
        item = SalesOrderItem.objects.create(
            sales_order=sales_order,
            product=product,
            quantity=quantity,
            price=price,
            tax=tax,
            total=total
        )
        
        # Update sales order total
        sales_order.total = sum(item.total for item in sales_order.items.all())
        sales_order.save()
        
        return JsonResponse({
            'success': True,
            'item': {
                'id': item.id,
                'product_name': item.product.name,
                'quantity': str(item.quantity),
                'price': str(item.price),
                'tax_name': item.tax.name if item.tax else '',
                'total': str(item.total)
            },
            'salesorder_total': str(sales_order.total)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_POST
def salesorder_items_edit(request, salesorder_id, item_id):
    sales_order = get_object_or_404(SalesOrder, pk=salesorder_id, company=request.user.company)
    item = get_object_or_404(SalesOrderItem, pk=item_id, sales_order=sales_order)
    
    product_id = request.POST.get('product_id')
    quantity = request.POST.get('quantity')
    price = request.POST.get('price')
    tax_id = request.POST.get('tax_id')
    
    if not product_id or not quantity or not price:
        return JsonResponse({'success': False, 'error': 'Product, quantity, and price are required.'}, status=400)
    
    try:
        product = get_object_or_404(Product, pk=product_id, company=request.user.company)
        tax = None
        if tax_id:
            tax = get_object_or_404(Tax, pk=tax_id, company=request.user.company)
        
        quantity = Decimal(quantity)
        price = Decimal(price)
        total = quantity * price
        
        if tax:
            tax_amount = total * (tax.rate / 100)
            total += tax_amount
        
        item.product = product
        item.quantity = quantity
        item.price = price
        item.tax = tax
        item.total = total
        item.save()
        
        # Update sales order total
        sales_order.total = sum(item.total for item in sales_order.items.all())
        sales_order.save()
        
        return JsonResponse({
            'success': True,
            'item': {
                'id': item.id,
                'product_name': item.product.name,
                'quantity': str(item.quantity),
                'price': str(item.price),
                'tax_name': item.tax.name if item.tax else '',
                'total': str(item.total)
            },
            'salesorder_total': str(sales_order.total)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_POST
def salesorder_items_delete(request, salesorder_id, item_id):
    sales_order = get_object_or_404(SalesOrder, pk=salesorder_id, company=request.user.company)
    item = get_object_or_404(SalesOrderItem, pk=item_id, sales_order=sales_order)
    
    try:
        item.delete()
        
        # Update sales order total
        sales_order.total = sum(item.total for item in sales_order.items.all())
        sales_order.save()
        
        return JsonResponse({
            'success': True,
            'salesorder_total': str(sales_order.total)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

# Sales Commission Views
class SalesCommissionListView(LoginRequiredMixin, TemplateView):
    template_name = 'sales/commission_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company
        
        commissions = SalesCommission.objects.filter(company=company).select_related(
            'sales_person', 'invoice', 'paid_by'
        ).order_by('-created_at')
        
        # Calculate statistics
        total_commissions = commissions.count()
        total_commission_amount = commissions.aggregate(
            total=Sum('commission_amount')
        )['total'] or 0
        paid_commissions = commissions.filter(is_paid=True).count()
        pending_commissions = commissions.filter(is_paid=False).count()
        
        # Get sales reps for dropdown
        sales_reps = User.objects.filter(company=company, is_active=True)
        
        # This month commissions
        from django.utils import timezone
        first_day = timezone.now().replace(day=1)
        this_month_amount = commissions.filter(
            created_at__gte=first_day
        ).aggregate(total=Sum('commission_amount'))['total'] or 0
        
        context.update({
            'commissions': commissions,
            'total_commissions': total_commissions,
            'total_commission_amount': total_commission_amount,
            'paid_commissions': paid_commissions,
            'pending_commissions': pending_commissions,
            'sales_reps': sales_reps,
            'this_month_amount': this_month_amount,
        })
        return context

@login_required
@require_POST
def commissions_create(request):
    """Create a new sales commission"""
    try:
        sales_person_id = request.POST.get('sales_person_id')
        invoice_id = request.POST.get('invoice_id')
        commission_rate = request.POST.get('commission_rate')
        commission_amount = request.POST.get('commission_amount')
        calculation_base = request.POST.get('calculation_base')
        notes = request.POST.get('notes', '')
        is_paid = request.POST.get('is_paid') == 'on'
        
        if not all([sales_person_id, invoice_id, commission_rate, commission_amount, calculation_base]):
            return JsonResponse({'success': False, 'error': 'Required fields missing'}, status=400)
        
        sales_person = get_object_or_404(User, pk=sales_person_id)
        invoice = get_object_or_404(Invoice, pk=invoice_id, company=request.user.company)
        
        commission = SalesCommission.objects.create(
            company=request.user.company,
            sales_person=sales_person,
            invoice=invoice,
            commission_rate=Decimal(commission_rate),
            commission_amount=Decimal(commission_amount),
            calculation_base=Decimal(calculation_base),
            notes=notes,
            is_paid=is_paid
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Sales commission created successfully!',
            'commission': {
                'id': commission.id,
                'sales_person': sales_person.get_full_name() or sales_person.username,
                'commission_amount': float(commission.commission_amount),
                'commission_rate': float(commission.commission_rate),
                'is_paid': commission.is_paid
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_POST
def commissions_update(request, pk):
    """Update an existing sales commission"""
    try:
        commission = get_object_or_404(SalesCommission, pk=pk, company=request.user.company)
        
        sales_person_id = request.POST.get('sales_person_id')
        invoice_id = request.POST.get('invoice_id')
        commission_rate = request.POST.get('commission_rate')
        commission_amount = request.POST.get('commission_amount')
        calculation_base = request.POST.get('calculation_base')
        notes = request.POST.get('notes', '')
        is_paid = request.POST.get('is_paid') == 'on'
        
        if not all([sales_person_id, invoice_id, commission_rate, commission_amount, calculation_base]):
            return JsonResponse({'success': False, 'error': 'Required fields missing'}, status=400)
        
        sales_person = get_object_or_404(User, pk=sales_person_id)
        invoice = get_object_or_404(Invoice, pk=invoice_id, company=request.user.company)
        
        # Update commission
        commission.sales_person = sales_person
        commission.invoice = invoice
        commission.commission_rate = Decimal(commission_rate)
        commission.commission_amount = Decimal(commission_amount)
        commission.calculation_base = Decimal(calculation_base)
        commission.notes = notes
        commission.is_paid = is_paid
        commission.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Sales commission updated successfully!',
            'commission': {
                'id': commission.id,
                'sales_person': sales_person.get_full_name() or sales_person.username,
                'commission_amount': float(commission.commission_amount),
                'commission_rate': float(commission.commission_rate),
                'is_paid': commission.is_paid
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
def commission_detail(request, pk):
    """Get commission details"""
    try:
        commission = get_object_or_404(SalesCommission, pk=pk, company=request.user.company)
        
        return JsonResponse({
            'success': True,
            'commission': {
                'id': commission.id,
                'sales_person_id': commission.sales_person.id,
                'sales_person_name': commission.sales_person.get_full_name() or commission.sales_person.username,
                'invoice_id': commission.invoice.id,
                'invoice_number': commission.invoice.invoice_number,
                'commission_rate': str(commission.commission_rate),
                'commission_amount': str(commission.commission_amount),
                'calculation_base': str(commission.calculation_base),
                'notes': commission.notes,
                'is_paid': commission.is_paid,
                'created_at': commission.created_at.strftime('%Y-%m-%d')
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_POST
def commissions_delete(request, pk):
    """Delete a sales commission"""
    try:
        commission = get_object_or_404(SalesCommission, pk=pk, company=request.user.company)
        commission.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Sales commission deleted successfully!'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_POST
def commissions_mark_paid(request, pk):
    """Mark commission as paid"""
    try:
        commission = get_object_or_404(SalesCommission, pk=pk, company=request.user.company)
        commission.is_paid = True
        commission.paid_date = timezone.now().date()
        commission.paid_by = request.user
        commission.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Commission marked as paid!'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

# Credit Note List View (update class name for consistency)
class CreditNoteListView(LoginRequiredMixin, TemplateView):
    template_name = 'sales/creditnote_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company
        
        credit_notes = CreditNote.objects.filter(company=company).select_related(
            'customer', 'invoice', 'created_by', 'currency'
        ).order_by('-created_at')
        
        # Calculate statistics
        total_credit_notes = credit_notes.count()
        total_credit_amount = credit_notes.aggregate(
            total=Sum('total')
        )['total'] or 0
        return_credit_notes = credit_notes.filter(reason='return').count()
        damage_credit_notes = credit_notes.filter(reason='damage').count()
        
        # Get customers for dropdown
        customers = Customer.objects.filter(company=company)
        
        # This month credit notes
        from django.utils import timezone
        first_day = timezone.now().replace(day=1)
        this_month_amount = credit_notes.filter(
            created_at__gte=first_day
        ).aggregate(total=Sum('total'))['total'] or 0
        
        context.update({
            'credit_notes': credit_notes,
            'total_credit_notes': total_credit_notes,
            'total_credit_amount': total_credit_amount,
            'return_credit_notes': return_credit_notes,
            'damage_credit_notes': damage_credit_notes,
            'customers': customers,
            'this_month_amount': this_month_amount,
        })
        return context

@login_required
@require_POST
def creditnotes_create(request):
    """Create a new credit note"""
    try:
        customer_id = request.POST.get('customer_id')
        invoice_id = request.POST.get('invoice_id')
        credit_number = request.POST.get('credit_number')
        credit_date = request.POST.get('credit_date')
        reason = request.POST.get('reason')
        subtotal = request.POST.get('subtotal')
        tax_amount = request.POST.get('tax_amount')
        total = request.POST.get('total')
        notes = request.POST.get('notes', '')
        
        if not all([customer_id, credit_date, reason, subtotal, total]):
            return JsonResponse({'success': False, 'error': 'Required fields missing'}, status=400)
        
        customer = get_object_or_404(Customer, pk=customer_id, company=request.user.company)
        invoice = None
        if invoice_id:
            invoice = get_object_or_404(Invoice, pk=invoice_id, company=request.user.company)
        
        # Parse credit date
        try:
            parsed_credit_date = datetime.strptime(credit_date, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Invalid credit date format'}, status=400)
        
        # Get currency from customer or company default
        currency = customer.currency if hasattr(customer, 'currency') and customer.currency else Currency.objects.filter(company=request.user.company, is_base=True).first()
        if not currency:
            currency = Currency.objects.filter(company=request.user.company).first()
        
        credit_note = CreditNote.objects.create(
            company=request.user.company,
            customer=customer,
            invoice=invoice,
            credit_number=credit_number or '',
            credit_date=parsed_credit_date,
            reason=reason,
            subtotal=Decimal(subtotal),
            tax_amount=Decimal(tax_amount or 0),
            total=Decimal(total),
            currency=currency,
            notes=notes,
            created_by=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Credit note created successfully!',
            'credit_note': {
                'id': credit_note.id,
                'credit_number': credit_note.credit_number,
                'customer_name': customer.name,
                'total': float(credit_note.total),
                'reason': credit_note.reason
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_POST  
def creditnotes_update(request, pk):
    """Update an existing credit note"""
    try:
        credit_note = get_object_or_404(CreditNote, pk=pk, company=request.user.company)
        
        customer_id = request.POST.get('customer_id')
        invoice_id = request.POST.get('invoice_id')
        credit_number = request.POST.get('credit_number')
        credit_date = request.POST.get('credit_date')
        reason = request.POST.get('reason')
        subtotal = request.POST.get('subtotal')
        tax_amount = request.POST.get('tax_amount')
        total = request.POST.get('total')
        notes = request.POST.get('notes', '')
        
        if not all([customer_id, credit_date, reason, subtotal, total]):
            return JsonResponse({'success': False, 'error': 'Required fields missing'}, status=400)
        
        customer = get_object_or_404(Customer, pk=customer_id, company=request.user.company)
        invoice = None
        if invoice_id:
            invoice = get_object_or_404(Invoice, pk=invoice_id, company=request.user.company)
        
        # Parse credit date
        try:
            parsed_credit_date = datetime.strptime(credit_date, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Invalid credit date format'}, status=400)
        
        # Update credit note
        credit_note.customer = customer
        credit_note.invoice = invoice
        credit_note.credit_number = credit_number or credit_note.credit_number
        credit_note.credit_date = parsed_credit_date
        credit_note.reason = reason
        credit_note.subtotal = Decimal(subtotal)
        credit_note.tax_amount = Decimal(tax_amount or 0)
        credit_note.total = Decimal(total)
        credit_note.notes = notes
        credit_note.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Credit note updated successfully!',
            'credit_note': {
                'id': credit_note.id,
                'credit_number': credit_note.credit_number,
                'customer_name': customer.name,
                'total': float(credit_note.total),
                'reason': credit_note.reason
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
def creditnote_detail(request, pk):
    """Get credit note details"""
    try:
        credit_note = get_object_or_404(CreditNote, pk=pk, company=request.user.company)
        
        return JsonResponse({
            'success': True,
            'credit_note': {
                'id': credit_note.id,
                'customer_id': credit_note.customer.id,
                'customer_name': credit_note.customer.name,
                'invoice_id': credit_note.invoice.id if credit_note.invoice else '',
                'invoice_number': credit_note.invoice.invoice_number if credit_note.invoice else '',
                'credit_number': credit_note.credit_number,
                'credit_date': credit_note.credit_date.strftime('%Y-%m-%d'),
                'reason': credit_note.reason,
                'subtotal': str(credit_note.subtotal),
                'tax_amount': str(credit_note.tax_amount),
                'total': str(credit_note.total),
                'notes': credit_note.notes,
                'created_at': credit_note.created_at.strftime('%Y-%m-%d')
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_POST
def creditnotes_delete(request, pk):
    """Delete a credit note"""
    try:
        credit_note = get_object_or_404(CreditNote, pk=pk, company=request.user.company)
        credit_note.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Credit note deleted successfully!'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
        
        context.update({
            'credit_notes': credit_notes,
            'total_credit_notes': total_credit_notes,
            'total_value': total_value,
        })
        return context
