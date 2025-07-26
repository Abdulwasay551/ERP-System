from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import StockItem, Product, Warehouse
from django.views.decorators.http import require_POST

# Create your views here.

@login_required
def stockitems_ui(request):
    stockitems = StockItem.objects.filter(company=request.user.company)
    return render(request, 'inventory/stockitems-ui.html', {'stockitems': stockitems})

@login_required
@require_POST
def stockitems_add(request):
    product_name = request.POST.get('product')
    warehouse_name = request.POST.get('warehouse')
    quantity = request.POST.get('quantity')
    is_active = request.POST.get('is_active') == 'on'
    if not product_name or not warehouse_name or not quantity:
        return JsonResponse({'success': False, 'error': 'Product, warehouse, and quantity are required.'}, status=400)
    product = Product.objects.filter(company=request.user.company, name=product_name).first()
    warehouse = Warehouse.objects.filter(company=request.user.company, name=warehouse_name).first()
    if not product or not warehouse:
        return JsonResponse({'success': False, 'error': 'Product or warehouse not found.'}, status=400)
    stockitem = StockItem.objects.create(
        company=request.user.company,
        product=product,
        warehouse=warehouse,
        quantity=quantity,
        is_active=is_active
    )
    return JsonResponse({
        'success': True,
        'stockitem': {
            'id': stockitem.id,
            'product': stockitem.product.name,
            'warehouse': stockitem.warehouse.name,
            'quantity': str(stockitem.quantity),
            'is_active': stockitem.is_active
        }
    })

@login_required
@require_POST
def stockitems_edit(request, pk):
    stockitem = get_object_or_404(StockItem, pk=pk, company=request.user.company)
    product_name = request.POST.get('product')
    warehouse_name = request.POST.get('warehouse')
    quantity = request.POST.get('quantity')
    is_active = request.POST.get('is_active') == 'on'
    if not product_name or not warehouse_name or not quantity:
        return JsonResponse({'success': False, 'error': 'Product, warehouse, and quantity are required.'}, status=400)
    product = Product.objects.filter(company=request.user.company, name=product_name).first()
    warehouse = Warehouse.objects.filter(company=request.user.company, name=warehouse_name).first()
    if not product or not warehouse:
        return JsonResponse({'success': False, 'error': 'Product or warehouse not found.'}, status=400)
    stockitem.product = product
    stockitem.warehouse = warehouse
    stockitem.quantity = quantity
    stockitem.is_active = is_active
    stockitem.save()
    return JsonResponse({
        'success': True,
        'stockitem': {
            'id': stockitem.id,
            'product': stockitem.product.name,
            'warehouse': stockitem.warehouse.name,
            'quantity': str(stockitem.quantity),
            'is_active': stockitem.is_active
        }
    })

@login_required
@require_POST
def stockitems_delete(request, pk):
    stockitem = get_object_or_404(StockItem, pk=pk, company=request.user.company)
    stockitem.delete()
    return JsonResponse({'success': True})

@login_required
def warehouses_ui(request):
    warehouses = Warehouse.objects.filter(company=request.user.company)
    return render(request, 'inventory/warehouses-ui.html', {'warehouses': warehouses})

@login_required
def movements_ui(request):
    # For now, just return a simple template
    return render(request, 'inventory/movements-ui.html')

@login_required
def alerts_ui(request):
    # For now, just return a simple template
    return render(request, 'inventory/alerts-ui.html')

@login_required
def categories_ui(request):
    # For now, just return a simple template
    return render(request, 'inventory/categories-ui.html')
