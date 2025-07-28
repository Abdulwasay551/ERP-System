from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from .models import Product, Tax, Quotation, QuotationItem, SalesOrder, SalesOrderItem
from crm.models import Customer
from accounting.models import Account

# Create your views here.

@login_required
def sales_dashboard(request):
    """Sales module dashboard with key metrics and quick access"""
    company = request.user.company
    
    # Key metrics
    total_products = Product.objects.filter(company=company, is_active=True).count()
    total_quotations = Quotation.objects.filter(company=company).count()
    pending_quotations = Quotation.objects.filter(company=company, status='draft').count()
    total_sales_orders = SalesOrder.objects.filter(company=company).count()
    
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
    
    # Recent activities
    recent_quotations = Quotation.objects.filter(company=company).order_by('-created_at')[:5]
    recent_orders = SalesOrder.objects.filter(company=company).order_by('-created_at')[:5]
    
    context = {
        'total_products': total_products,
        'total_quotations': total_quotations,
        'pending_quotations': pending_quotations,
        'total_sales_orders': total_sales_orders,
        'monthly_quotations': monthly_quotations,
        'monthly_sales': monthly_sales,
        'recent_quotations': recent_quotations,
        'recent_orders': recent_orders,
    }
    return render(request, 'sales/dashboard.html', context)

class ProductPageView(LoginRequiredMixin, TemplateView):
    template_name = 'sales/product_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company
        
        # Get all products for the company
        products = Product.objects.filter(company=company).order_by('-created_at')
        
        # Calculate statistics
        total_products = products.count()
        active_products = products.filter(is_active=True).count()
        service_products = products.filter(is_service=True).count()
        
        # Calculate average price
        avg_price = products.aggregate(avg_price=Sum('price'))['avg_price'] or 0
        if total_products > 0:
            avg_price = avg_price / total_products
        
        context.update({
            'products': products,
            'total_products': total_products,
            'active_products': active_products,
            'service_products': service_products,
            'avg_price': avg_price,
        })
        return context

class TaxPageView(LoginRequiredMixin, TemplateView):
    template_name = 'sales/tax_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company
        
        # Get all taxes for the company
        taxes = Tax.objects.filter(company=company).order_by('name')
        
        # Calculate statistics
        total_taxes = taxes.count()
        active_taxes = taxes.filter(is_active=True).count()
        avg_rate = taxes.aggregate(avg_rate=Sum('rate'))['avg_rate'] or 0
        if total_taxes > 0:
            avg_rate = avg_rate / total_taxes
        
        # Get Chart of Accounts for dropdown
        coa_accounts = Account.objects.filter(company=company, account_type__in=['Liability', 'Revenue'])
        
        context.update({
            'taxes': taxes,
            'total_taxes': total_taxes,
            'active_taxes': active_taxes,
            'avg_rate': avg_rate,
            'coa_accounts': coa_accounts,
        })
        return context

class QuotationPageView(LoginRequiredMixin, TemplateView):
    template_name = 'sales/quotation_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company
        
        # Get all quotations for the company
        quotations = Quotation.objects.filter(company=company).select_related('customer', 'created_by').order_by('-created_at')
        
        # Calculate statistics
        total_quotations = quotations.count()
        total_value = quotations.aggregate(total_value=Sum('total'))['total_value'] or 0
        
        # Status breakdown
        draft_count = quotations.filter(status='Draft').count()
        sent_count = quotations.filter(status='Sent').count()
        accepted_count = quotations.filter(status='Accepted').count()
        
        # Get customers and products for dropdowns
        customers = Customer.objects.filter(company=company)
        products = Product.objects.filter(company=company, is_active=True)
        taxes = Tax.objects.filter(company=company, is_active=True)
        
        context.update({
            'quotations': quotations,
            'total_quotations': total_quotations,
            'total_value': total_value,
            'draft_count': draft_count,
            'sent_count': sent_count,
            'accepted_count': accepted_count,
            'customers': customers,
            'products': products,
            'taxes': taxes,
        })
        return context

class SalesOrderPageView(LoginRequiredMixin, TemplateView):
    template_name = 'sales/salesorder_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company
        
        # Get all sales orders for the company
        sales_orders = SalesOrder.objects.filter(company=company).select_related('customer', 'created_by', 'quotation').order_by('-created_at')
        
        # Calculate statistics
        total_orders = sales_orders.count()
        total_value = sales_orders.aggregate(total_value=Sum('total'))['total_value'] or 0
        
        # Status breakdown
        pending_count = sales_orders.filter(status='Pending').count()
        confirmed_count = sales_orders.filter(status='Confirmed').count()
        shipped_count = sales_orders.filter(status='Shipped').count()
        delivered_count = sales_orders.filter(status='Delivered').count()
        
        # Get customers, products, and quotations for dropdowns
        customers = Customer.objects.filter(company=company)
        products = Product.objects.filter(company=company, is_active=True)
        taxes = Tax.objects.filter(company=company, is_active=True)
        quotations = Quotation.objects.filter(company=company, status='Accepted')
        
        context.update({
            'sales_orders': sales_orders,
            'total_orders': total_orders,
            'total_value': total_value,
            'pending_count': pending_count,
            'confirmed_count': confirmed_count,
            'shipped_count': shipped_count,
            'delivered_count': delivered_count,
            'customers': customers,
            'products': products,
            'taxes': taxes,
            'quotations': quotations,
        })
        return context

class InvoicePageView(LoginRequiredMixin, TemplateView):
    template_name = 'sales/invoice_list.html'

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
@require_POST
def taxes_add(request):
    name = request.POST.get('name')
    rate = request.POST.get('rate')
    is_active = request.POST.get('is_active') == 'on'
    
    if not name or not rate:
        return JsonResponse({'success': False, 'error': 'Name and rate are required.'}, status=400)
    
    try:
        tax = Tax.objects.create(
            company=request.user.company,
            name=name,
            rate=Decimal(rate),
            is_active=is_active
        )
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
def taxes_edit(request, pk):
    tax = get_object_or_404(Tax, pk=pk, company=request.user.company)
    name = request.POST.get('name')
    rate = request.POST.get('rate')
    is_active = request.POST.get('is_active') == 'on'
    
    if not name or not rate:
        return JsonResponse({'success': False, 'error': 'Name and rate are required.'}, status=400)
    
    try:
        tax.name = name
        tax.rate = Decimal(rate)
        tax.is_active = is_active
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
    quotation = get_object_or_404(Quotation, pk=pk, company=request.user.company)
    try:
        quotation.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

# Sales Order CRUD Operations
@login_required
@require_POST
def salesorders_add(request):
    customer_id = request.POST.get('customer_id')
    quotation_id = request.POST.get('quotation_id')
    delivery_date = request.POST.get('delivery_date')
    billing_address = request.POST.get('billing_address', '')
    shipping_address = request.POST.get('shipping_address', '')
    notes = request.POST.get('notes', '')
    
    if not customer_id:
        return JsonResponse({'success': False, 'error': 'Customer is required.'}, status=400)
    
    try:
        customer = get_object_or_404(Customer, pk=customer_id, company=request.user.company)
        quotation = None
        if quotation_id:
            quotation = get_object_or_404(Quotation, pk=quotation_id, company=request.user.company)
        
        sales_order = SalesOrder.objects.create(
            company=request.user.company,
            customer=customer,
            quotation=quotation,
            created_by=request.user,
            delivery_date=delivery_date if delivery_date else None,
            billing_address=billing_address,
            shipping_address=shipping_address,
            notes=notes
        )
        return JsonResponse({
            'success': True,
            'sales_order': {
                'id': sales_order.id,
                'customer_name': sales_order.customer.name,
                'order_date': sales_order.order_date.strftime('%Y-%m-%d'),
                'delivery_date': sales_order.delivery_date.strftime('%Y-%m-%d') if sales_order.delivery_date else '',
                'total': str(sales_order.total),
                'status': sales_order.status,
                'notes': sales_order.notes
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_POST
def salesorders_edit(request, pk):
    sales_order = get_object_or_404(SalesOrder, pk=pk, company=request.user.company)
    customer_id = request.POST.get('customer_id')
    delivery_date = request.POST.get('delivery_date')
    status = request.POST.get('status')
    billing_address = request.POST.get('billing_address', '')
    shipping_address = request.POST.get('shipping_address', '')
    notes = request.POST.get('notes', '')
    
    if not customer_id:
        return JsonResponse({'success': False, 'error': 'Customer is required.'}, status=400)
    
    try:
        customer = get_object_or_404(Customer, pk=customer_id, company=request.user.company)
        sales_order.customer = customer
        sales_order.delivery_date = delivery_date if delivery_date else None
        sales_order.status = status if status else sales_order.status
        sales_order.billing_address = billing_address
        sales_order.shipping_address = shipping_address
        sales_order.notes = notes
        sales_order.save()
        
        return JsonResponse({
            'success': True,
            'sales_order': {
                'id': sales_order.id,
                'customer_name': sales_order.customer.name,
                'order_date': sales_order.order_date.strftime('%Y-%m-%d'),
                'delivery_date': sales_order.delivery_date.strftime('%Y-%m-%d') if sales_order.delivery_date else '',
                'total': str(sales_order.total),
                'status': sales_order.status,
                'notes': sales_order.notes
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_POST
def salesorders_delete(request, pk):
    sales_order = get_object_or_404(SalesOrder, pk=pk, company=request.user.company)
    try:
        sales_order.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

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
