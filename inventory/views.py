from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import StockItem, Warehouse, StockMovement
from products.models import Product, ProductCategory
from django.views.decorators.http import require_POST
from django.db.models import Sum, Count, F, Q
from django.utils import timezone
from datetime import datetime, timedelta

# Create your views here.

@login_required
def inventory_dashboard(request):
    """Inventory module dashboard with key metrics and quick access"""
    company = request.user.company
    
    # Key metrics
    total_stock_items = StockItem.objects.filter(company=company, is_active=True).count()
    total_warehouses = Warehouse.objects.filter(company=company, is_active=True).count()
    total_products = Product.objects.filter(company=company, is_active=True).count()
    low_stock_items = StockItem.objects.filter(company=company, quantity__lte=F('min_stock')).count()
    
    # Stock movements summary
    total_movements = StockMovement.objects.filter(company=company).count()
    recent_movements = StockMovement.objects.filter(company=company).order_by('-timestamp')[:5]
    
    # Stock by warehouse
    warehouses_with_stock = Warehouse.objects.filter(
        company=company, is_active=True
    ).annotate(
        total_items=Count('stock_items'),
        total_quantity=Sum('stock_items__quantity')
    ).order_by('-total_quantity')[:5]
    
    # Low stock alerts
    low_stock_alerts = StockItem.objects.filter(
        company=company, 
        quantity__lte=F('min_stock'),
        is_active=True
    ).select_related('product', 'warehouse')[:10]
    
    # Recent stock items
    recent_stock_items = StockItem.objects.filter(
        company=company, is_active=True
    ).select_related('product', 'warehouse').order_by('-created_at')[:5]
    
    context = {
        'total_stock_items': total_stock_items,
        'total_warehouses': total_warehouses,
        'total_products': total_products,
        'low_stock_items': low_stock_items,
        'total_movements': total_movements,
        'recent_movements': recent_movements,
        'warehouses_with_stock': warehouses_with_stock,
        'low_stock_alerts': low_stock_alerts,
        'recent_stock_items': recent_stock_items,
    }
    return render(request, 'inventory/dashboard.html', context)

@login_required
def stockitems_ui(request):
    company = request.user.company
    stockitems = StockItem.objects.filter(
        company=company
    ).select_related('product', 'warehouse', 'category').order_by('-created_at')
    
    # Summary statistics
    total_items = stockitems.count()
    active_items = stockitems.filter(is_active=True).count()
    low_stock_count = stockitems.filter(quantity__lte=F('min_stock')).count()
    total_quantity = stockitems.aggregate(total=Sum('quantity'))['total'] or 0
    
    context = {
        'stockitems': stockitems,
        'total_items': total_items,
        'active_items': active_items,
        'low_stock_count': low_stock_count,
        'total_quantity': total_quantity,
        'warehouses': Warehouse.objects.filter(company=company, is_active=True),
        'categories': ProductCategory.objects.filter(company=company, is_active=True),
    }
    return render(request, 'inventory/stockitems-ui.html', context)

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
    """Warehouses management view"""
    company = request.user.company
    warehouses = Warehouse.objects.filter(company=company).annotate(
        stock_count=Count('stock_items'),
        total_quantity=Sum('stock_items__quantity')
    ).order_by('name')
    
    context = {
        'warehouses': warehouses,
        'total_warehouses': warehouses.count(),
        'active_warehouses': warehouses.filter(is_active=True).count(),
    }
    return render(request, 'inventory/warehouses-ui.html', context)

@login_required
def movements_ui(request):
    """Stock movements view"""
    company = request.user.company
    movements = StockMovement.objects.filter(
        company=company
    ).select_related('stock_item__product', 'from_warehouse', 'to_warehouse', 'performed_by').order_by('-timestamp')[:50]
    
    context = {
        'movements': movements,
        'total_movements': StockMovement.objects.filter(company=company).count(),
        'movements_today': movements.filter(timestamp__date=timezone.now().date()).count(),
    }
    return render(request, 'inventory/movements-ui.html', context)

@login_required
def alerts_ui(request):
    """Stock alerts view"""
    company = request.user.company
    low_stock_items = StockItem.objects.filter(
        company=company,
        quantity__lte=F('min_stock'),
        min_stock__gt=0,
        is_active=True
    ).select_related('product', 'warehouse')
    
    context = {
        'low_stock_items': low_stock_items,
        'alert_count': low_stock_items.count(),
    }
    return render(request, 'inventory/alerts-ui.html', context)

@login_required
def categories_ui(request):
    """Product categories view"""
    company = request.user.company
    categories = ProductCategory.objects.filter(company=company).annotate(
        product_count=Count('products'),
        stock_count=Count('stock_items')
    ).order_by('name')
    
    context = {
        'categories': categories,
        'total_categories': categories.count(),
    }
    return render(request, 'inventory/categories-ui.html', context)

@login_required
def adjustments_ui(request):
    """Stock adjustments view"""
    company = request.user.company
    # Show recent movements as adjustments
    adjustments = StockMovement.objects.filter(
        company=company,
        movement_type__in=['in', 'out']
    ).select_related('stock_item__product', 'from_warehouse', 'to_warehouse', 'performed_by').order_by('-timestamp')[:50]
    
    context = {
        'adjustments': adjustments,
        'total_adjustments': StockMovement.objects.filter(company=company, movement_type__in=['in', 'out']).count(),
    }
    return render(request, 'inventory/adjustments-ui.html', context)

@login_required
def reports_ui(request):
    """Inventory reports view"""
    company = request.user.company
    
    # Report data
    stock_summary = StockItem.objects.filter(company=company, is_active=True).aggregate(
        total_items=Count('id'),
        total_quantity=Sum('quantity'),
        low_stock_count=Count('id', filter=Q(quantity__lte=F('min_stock'), min_stock__gt=0))
    )
    
    # Top categories by stock
    top_categories = ProductCategory.objects.filter(
        company=company
    ).annotate(
        stock_quantity=Sum('stock_items__quantity')
    ).order_by('-stock_quantity')[:10]
    
    context = {
        'stock_summary': stock_summary,
        'top_categories': top_categories,
    }
    return render(request, 'inventory/reports-ui.html', context)
