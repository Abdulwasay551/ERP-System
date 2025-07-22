from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Product
from django.views.decorators.http import require_POST

# Create your views here.

class ProductPageView(LoginRequiredMixin, TemplateView):
    template_name = 'sales/product_list.html'

class TaxPageView(LoginRequiredMixin, TemplateView):
    template_name = 'sales/tax_list.html'

class QuotationPageView(LoginRequiredMixin, TemplateView):
    template_name = 'sales/quotation_list.html'

class SalesOrderPageView(LoginRequiredMixin, TemplateView):
    template_name = 'sales/salesorder_list.html'

@login_required
def products_ui(request):
    products = Product.objects.filter(company=request.user.company)
    return render(request, 'sales/products-ui.html', {'products': products})

@login_required
@require_POST
def products_add(request):
    name = request.POST.get('name')
    sku = request.POST.get('sku')
    price = request.POST.get('price')
    is_active = request.POST.get('is_active') == 'on'
    if not name or not price:
        return JsonResponse({'success': False, 'error': 'Name and price are required.'}, status=400)
    product = Product.objects.create(
        company=request.user.company,
        name=name,
        sku=sku or '',
        price=price,
        is_active=is_active
    )
    return JsonResponse({
        'success': True,
        'product': {
            'id': product.id,
            'name': product.name,
            'sku': product.sku,
            'price': str(product.price),
            'is_active': product.is_active
        }
    })

@login_required
@require_POST
def products_edit(request, pk):
    product = get_object_or_404(Product, pk=pk, company=request.user.company)
    name = request.POST.get('name')
    sku = request.POST.get('sku')
    price = request.POST.get('price')
    is_active = request.POST.get('is_active') == 'on'
    if not name or not price:
        return JsonResponse({'success': False, 'error': 'Name and price are required.'}, status=400)
    product.name = name
    product.sku = sku or ''
    product.price = price
    product.is_active = is_active
    product.save()
    return JsonResponse({
        'success': True,
        'product': {
            'id': product.id,
            'name': product.name,
            'sku': product.sku,
            'price': str(product.price),
            'is_active': product.is_active
        }
    })

@login_required
@require_POST
def products_delete(request, pk):
    product = get_object_or_404(Product, pk=pk, company=request.user.company)
    product.delete()
    return JsonResponse({'success': True})
