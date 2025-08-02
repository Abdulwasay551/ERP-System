from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib import messages
from django.db.models import Sum, Count, F, Q, Avg, Case, When, FloatField
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
import json
import csv
from user_auth.models import User
from .models import (
    StockItem, Warehouse, WarehouseZone, WarehouseBin, StockMovement,
    StockLot, StockSerial, StockReservation, StockAlert, InventoryLock,
    StockAdjustment, StockAdjustmentItem
)
from .forms import (
    WarehouseForm, StockItemForm, StockMovementForm, StockLotForm,
    InventoryLockForm, QuickStockMovementForm, QuickWarehouseForm
)
from products.models import Product, ProductCategory

# Create your views here.

@login_required
def inventory_dashboard(request):
    """Enhanced inventory module dashboard with purchase integration"""
    company = request.user.company
    
    # Key metrics
    total_stock_items = StockItem.objects.filter(company=company, is_active=True).count()
    total_warehouses = Warehouse.objects.filter(company=company, is_active=True).count()
    total_products = Product.objects.filter(company=company, is_active=True).count()
    low_stock_items = StockItem.objects.filter(company=company, quantity__lte=F('min_stock')).count()
    
    # Enhanced metrics with purchase status
    locked_items = StockItem.objects.filter(
        company=company, 
        stock_status='locked',
        is_active=True
    ).count()
    
    ready_for_sale = StockItem.objects.filter(
        company=company,
        purchase_status='ready_for_use',
        suitable_for_sale=True,
        is_active=True
    ).count()
    
    ready_for_manufacturing = StockItem.objects.filter(
        company=company,
        purchase_status='ready_for_use',
        suitable_for_manufacturing=True,
        is_active=True
    ).count()
    
    # Purchase integration metrics
    try:
        from purchase.models import GRNInventoryLock
        pending_bills_count = GRNInventoryLock.objects.filter(
            grn__company=company,
            lock_reason='pending_invoice',
            is_active=True
        ).values('grn').distinct().count()
        
        total_locked_value = StockItem.objects.filter(
            company=company,
            locked_quantity__gt=0
        ).aggregate(
            total=Sum(F('locked_quantity') * F('average_cost'))
        )['total'] or 0
        
    except ImportError:
        pending_bills_count = 0
        total_locked_value = 0
    
    # Stock movements summary
    total_movements = StockMovement.objects.filter(company=company).count()
    recent_movements = StockMovement.objects.filter(
        company=company
    ).select_related('stock_item__product', 'stock_item__warehouse').order_by('-timestamp')[:5]
    
    # Stock by warehouse
    warehouses_with_stock = Warehouse.objects.filter(
        company=company, is_active=True
    ).annotate(
        total_items=Count('stock_items'),
        total_quantity=Sum('stock_items__quantity'),
        locked_quantity=Sum('stock_items__locked_quantity'),
        available_quantity=Sum('stock_items__available_quantity')
    ).order_by('-total_quantity')[:5]
    
    # Enhanced alerts
    low_stock_alerts = StockItem.objects.filter(
        company=company, 
        quantity__lte=F('min_stock'),
        is_active=True
    ).select_related('product', 'warehouse')[:10]
    
    locked_too_long = StockItem.objects.filter(
        company=company,
        locked_quantity__gt=0,
        last_movement_date__lte=timezone.now() - timedelta(days=7),
        is_active=True
    ).select_related('product', 'warehouse')[:5]
    
    # Recent stock items
    recent_stock_items = StockItem.objects.filter(
        company=company, is_active=True
    ).select_related('product', 'warehouse').order_by('-created_at')[:5]
    
    context = {
        'total_stock_items': total_stock_items,
        'total_warehouses': total_warehouses,
        'total_products': total_products,
        'low_stock_items': low_stock_items,
        'locked_items': locked_items,
        'ready_for_sale': ready_for_sale,
        'ready_for_manufacturing': ready_for_manufacturing,
        'pending_bills_count': pending_bills_count,
        'total_locked_value': total_locked_value,
        'total_movements': total_movements,
        'recent_movements': recent_movements,
        'warehouses_with_stock': warehouses_with_stock,
        'low_stock_alerts': low_stock_alerts,
        'locked_too_long': locked_too_long,
        'recent_stock_items': recent_stock_items,
    }
    return render(request, 'inventory/dashboard.html', context)

@login_required
def stockitems_ui(request):
    """Enhanced stock items view with purchase integration"""
    company = request.user.company
    stockitems = StockItem.objects.filter(
        company=company
    ).select_related('product', 'warehouse', 'category').order_by('-created_at')
    
    # Summary statistics with purchase status
    total_items = stockitems.count()
    active_items = stockitems.filter(is_active=True).count()
    low_stock_count = stockitems.filter(quantity__lte=F('min_stock')).count()
    total_quantity = stockitems.aggregate(total=Sum('quantity'))['total'] or 0
    
    # Enhanced metrics with purchase integration
    locked_items = stockitems.filter(stock_status='locked').count()
    available_items = stockitems.filter(stock_status='available').count()
    ready_for_sale = stockitems.filter(
        purchase_status='ready_for_use',
        suitable_for_sale=True
    ).count()
    
    # Purchase-related metrics
    try:
        from purchase.models import GRNInventoryLock
        items_with_pending_bills = stockitems.filter(
            locked_quantity__gt=0
        ).count()
        
        total_locked_value = stockitems.filter(
            locked_quantity__gt=0
        ).aggregate(
            total=Sum(F('locked_quantity') * F('average_cost'))
        )['total'] or 0
        
    except ImportError:
        items_with_pending_bills = 0
        total_locked_value = 0
    
    context = {
        'stockitems': stockitems,
        'total_items': total_items,
        'active_items': active_items,
        'low_stock_count': low_stock_count,
        'total_quantity': total_quantity,
        'locked_items': locked_items,
        'available_items': available_items,
        'ready_for_sale': ready_for_sale,
        'items_with_pending_bills': items_with_pending_bills,
        'total_locked_value': total_locked_value,
        'warehouses': Warehouse.objects.filter(company=company, is_active=True),
        'categories': ProductCategory.objects.filter(company=company, is_active=True),
        'products': Product.objects.filter(company=company, is_active=True).order_by('name'),
    }
    return render(request, 'inventory/stockitems-ui.html', context)

@login_required
def stockitem_detail(request, pk):
    """Enhanced stock item detail view with purchase integration"""
    company = request.user.company
    stockitem = get_object_or_404(StockItem, pk=pk, company=company)
    
    # Recent movements
    movements = StockMovement.objects.filter(
        stock_item=stockitem
    ).order_by('-timestamp')[:20]
    
    # Purchase-related information
    purchase_info = {}
    try:
        from purchase.models import GRNInventoryLock, GRNItem
        
        # Current locks - fix the field reference
        current_locks = GRNInventoryLock.objects.filter(
            grn_item__product=stockitem.product,
            is_active=True
        ).select_related('grn')
        
        # GRN items that contributed to this stock
        grn_items = GRNItem.objects.filter(
            product=stockitem.product,
            grn__company=company
        ).select_related('grn__purchase_order').order_by('-grn__received_date')[:10]
        
        purchase_info = {
            'current_locks': current_locks,
            'grn_history': grn_items,
            'has_locked_quantity': stockitem.locked_quantity > 0,
            'available_for_use': stockitem.available_quantity,
        }
        
    except ImportError:
        pass
    
    context = {
        'stockitem': stockitem,
        'movements': movements,
        'purchase_info': purchase_info,
        'locked_percentage': (stockitem.locked_quantity / stockitem.quantity * 100) if stockitem.quantity > 0 else 0,
        'available_percentage': (stockitem.available_quantity / stockitem.quantity * 100) if stockitem.quantity > 0 else 0,
    }
    
    return render(request, 'inventory/stockitem_detail.html', context)

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
def stockitems_edit(request, pk):
    stockitem = get_object_or_404(StockItem, pk=pk, company=request.user.company)
    
    if request.method == 'GET':
        # Return stock item data for form population
        return JsonResponse({
            'success': True,
            'stockitem': {
                'id': stockitem.id,
                'product_name': stockitem.product.name,
                'warehouse_name': stockitem.warehouse.name,
                'quantity': str(stockitem.quantity),
                'is_active': stockitem.is_active
            }
        })
    
    # POST request - update stock item
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
@login_required
@require_POST
def stock_movement_add(request):
    """Add stock movement"""
    stock_item_id = request.POST.get('stock_item')
    movement_type = request.POST.get('movement_type')
    quantity = request.POST.get('quantity')
    unit_cost = request.POST.get('unit_cost')
    from_warehouse_id = request.POST.get('from_warehouse')
    to_warehouse_id = request.POST.get('to_warehouse')
    reference = request.POST.get('reference')
    notes = request.POST.get('notes')
    
    if not stock_item_id or not movement_type or not quantity:
        return JsonResponse({'success': False, 'error': 'Stock item, movement type, and quantity are required.'}, status=400)
    
    try:
        stock_item = StockItem.objects.get(id=stock_item_id, company=request.user.company)
        quantity = Decimal(str(quantity))
        unit_cost = Decimal(str(unit_cost)) if unit_cost else stock_item.average_cost if hasattr(stock_item, 'average_cost') else Decimal('0')
        
        # Prepare movement data
        movement_data = {
            'company': request.user.company,
            'stock_item': stock_item,
            'movement_type': movement_type,
            'quantity': quantity,
            'unit_cost': unit_cost,
            'notes': notes,
            'performed_by': request.user,
            'reference_number': reference,
        }
        
        # Add warehouse fields if provided
        if from_warehouse_id:
            try:
                from_warehouse = Warehouse.objects.get(id=from_warehouse_id, company=request.user.company)
                movement_data['from_warehouse'] = from_warehouse
            except Warehouse.DoesNotExist:
                pass
        
        if to_warehouse_id:
            try:
                to_warehouse = Warehouse.objects.get(id=to_warehouse_id, company=request.user.company)
                movement_data['to_warehouse'] = to_warehouse
            except Warehouse.DoesNotExist:
                pass
        
        # Create the movement
        movement = StockMovement.objects.create(**movement_data)
        
        return JsonResponse({
            'success': True,
            'movement': {
                'id': movement.id,
                'movement_type': movement.get_movement_type_display(),
                'quantity': str(movement.quantity),
                'total_cost': str(movement.total_cost),
                'timestamp': movement.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            }
        })
        
    except StockItem.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Stock item not found.'}, status=404)
    except (ValueError, TypeError, InvalidOperation):
        return JsonResponse({'success': False, 'error': 'Invalid quantity or cost value.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

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
    all_movements = StockMovement.objects.filter(
        company=company
    ).select_related('stock_item__product', 'from_warehouse', 'to_warehouse', 'performed_by')
    
    # Calculate today's movements before slicing
    movements_today_count = all_movements.filter(timestamp__date=timezone.now().date()).count()
    
    # Get recent movements (limited to 50)
    movements = all_movements.order_by('-timestamp')[:50]
    
    # Get stock items and warehouses for the movement form
    stock_items = StockItem.objects.filter(
        company=company,
        is_active=True
    ).select_related('product', 'warehouse').order_by('product__name')
    
    warehouses = Warehouse.objects.filter(
        company=company,
        is_active=True
    ).order_by('name')
    
    context = {
        'movements': movements,
        'stock_items': stock_items,
        'warehouses': warehouses,
        'total_movements': StockMovement.objects.filter(company=company).count(),
        'movements_today_count': movements_today_count,
    }
    return render(request, 'inventory/movements-ui.html', context)

@login_required
def alerts_ui(request):
    """Enhanced stock alerts view with comprehensive alert management"""
    company = request.user.company
    
    # Low stock alerts
    low_stock_items = StockItem.objects.filter(
        company=company,
        quantity__lte=F('min_stock'),
        min_stock__gt=0,
        is_active=True
    ).select_related('product', 'warehouse')
    
    # Critical stock alerts (zero or negative stock)
    critical_stock_items = StockItem.objects.filter(
        company=company,
        quantity__lte=0,
        is_active=True
    ).select_related('product', 'warehouse')
    
    # Overstock alerts (items with excessive stock)
    overstock_items = StockItem.objects.filter(
        company=company,
        quantity__gte=F('max_stock'),
        max_stock__gt=0,
        is_active=True
    ).select_related('product', 'warehouse')
    
    # Expiring items (if expiry tracking is available)
    current_date = timezone.now().date()
    month_from_now = current_date + timedelta(days=30)
    
    expiring_lots = StockLot.objects.filter(
        stock_item__company=company,
        expiry_date__isnull=False,
        expiry_date__lte=month_from_now,
        expiry_date__gt=current_date,
        is_active=True
    ).select_related('stock_item__product', 'stock_item__warehouse')
    
    # Long-locked items
    week_ago = timezone.now() - timedelta(days=7)
    long_locked_items = StockItem.objects.filter(
        company=company,
        locked_quantity__gt=0,
        last_movement_date__lte=week_ago,
        is_active=True
    ).select_related('product', 'warehouse')
    
    # Inactive products with stock
    inactive_products_with_stock = StockItem.objects.filter(
        company=company,
        product__is_active=False,
        quantity__gt=0
    ).select_related('product', 'warehouse')
    
    # Alert statistics
    total_alerts = (
        low_stock_items.count() + 
        critical_stock_items.count() + 
        overstock_items.count() + 
        expiring_lots.count() +
        long_locked_items.count() +
        inactive_products_with_stock.count()
    )
    
    # Stock value at risk
    critical_value = critical_stock_items.aggregate(
        total=Sum(F('quantity') * F('average_cost'))
    )['total'] or 0
    
    low_stock_value = low_stock_items.aggregate(
        total=Sum(F('quantity') * F('average_cost'))
    )['total'] or 0
    
    # Get warehouses and categories for filtering
    warehouses = Warehouse.objects.filter(company=company, is_active=True)
    categories = ProductCategory.objects.filter(company=company, is_active=True)
    
    context = {
        'low_stock_items': low_stock_items,
        'critical_stock_items': critical_stock_items,
        'overstock_items': overstock_items,
        'expiring_lots': expiring_lots,
        'long_locked_items': long_locked_items,
        'inactive_products_with_stock': inactive_products_with_stock,
        'warehouses': warehouses,
        'categories': categories,
        
        # Statistics
        'total_alerts': total_alerts,
        'critical_alerts': critical_stock_items.count(),
        'low_stock_alerts': low_stock_items.count(),
        'overstock_alerts': overstock_items.count(),
        'expiring_alerts': expiring_lots.count(),
        'locked_alerts': long_locked_items.count(),
        'inactive_alerts': inactive_products_with_stock.count(),
        
        # Values
        'critical_value': critical_value,
        'low_stock_value': low_stock_value,
        
        # Dates
        'current_date': current_date,
        'month_from_now': month_from_now,
    }
    return render(request, 'inventory/alerts-ui-enhanced.html', context)

@login_required
def categories_ui(request):
    """Enhanced Product categories management view with full CRUD operations"""
    company = request.user.company
    categories = ProductCategory.objects.filter(company=company).annotate(
        product_count=Count('products'),
        total_stock_value=Sum(F('products__stock_items__quantity') * F('products__stock_items__average_cost'), default=0),
        active_products=Count('products', filter=Q(products__is_active=True))
    ).order_by('name')
    
    # Calculate statistics
    total_categories = categories.count()
    active_categories = categories.filter(is_active=True).count()
    categories_with_products = categories.filter(product_count__gt=0).count()
    
    # Get parent categories for hierarchy
    parent_categories = categories.filter(parent__isnull=True)
    
    context = {
        'categories': categories,
        'parent_categories': parent_categories,
        'total_categories': total_categories,
        'active_categories': active_categories,
        'categories_with_products': categories_with_products,
        'page_title': 'Item Categories Management',
    }
    return render(request, 'inventory/categories-ui-enhanced.html', context)

@login_required
@require_POST
def category_create(request):
    """Create new product category"""
    try:
        name = request.POST.get('name', '').strip()
        code = request.POST.get('code', '').strip()
        description = request.POST.get('description', '').strip()
        parent_id = request.POST.get('parent_id')
        
        if not name:
            return JsonResponse({'success': False, 'error': 'Category name is required'})
        
        # Check if category with same name exists
        if ProductCategory.objects.filter(company=request.user.company, name=name).exists():
            return JsonResponse({'success': False, 'error': 'Category with this name already exists'})
        
        # Check if code is unique (if provided)
        if code and ProductCategory.objects.filter(company=request.user.company, code=code).exists():
            return JsonResponse({'success': False, 'error': 'Category with this code already exists'})
        
        parent = None
        if parent_id:
            parent = get_object_or_404(ProductCategory, id=parent_id, company=request.user.company)
        
        category = ProductCategory.objects.create(
            company=request.user.company,
            name=name,
            code=code,
            description=description,
            parent=parent,
            is_active=True
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Category "{name}" created successfully',
            'category': {
                'id': category.id,
                'name': category.name,
                'code': category.code,
                'description': category.description,
                'parent': category.parent.name if category.parent else None,
                'is_active': category.is_active,
                'created_at': category.created_at.strftime('%Y-%m-%d %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_POST 
def category_update(request, category_id):
    """Update existing product category"""
    try:
        category = get_object_or_404(ProductCategory, id=category_id, company=request.user.company)
        
        name = request.POST.get('name', '').strip()
        code = request.POST.get('code', '').strip()
        description = request.POST.get('description', '').strip()
        parent_id = request.POST.get('parent_id')
        is_active = request.POST.get('is_active') == 'true'
        
        if not name:
            return JsonResponse({'success': False, 'error': 'Category name is required'})
        
        # Check if category with same name exists (excluding current)
        if ProductCategory.objects.filter(company=request.user.company, name=name).exclude(id=category_id).exists():
            return JsonResponse({'success': False, 'error': 'Category with this name already exists'})
        
        # Check if code is unique (if provided, excluding current)
        if code and ProductCategory.objects.filter(company=request.user.company, code=code).exclude(id=category_id).exists():
            return JsonResponse({'success': False, 'error': 'Category with this code already exists'})
        
        parent = None
        if parent_id and parent_id != str(category_id):  # Prevent self-reference
            parent = get_object_or_404(ProductCategory, id=parent_id, company=request.user.company)
        
        category.name = name
        category.code = code
        category.description = description
        category.parent = parent
        category.is_active = is_active
        category.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Category "{name}" updated successfully',
            'category': {
                'id': category.id,
                'name': category.name,
                'code': category.code,
                'description': category.description,
                'parent': category.parent.name if category.parent else None,
                'is_active': category.is_active,
                'updated_at': category.updated_at.strftime('%Y-%m-%d %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_POST
def category_delete(request, category_id):
    """Delete product category"""
    try:
        category = get_object_or_404(ProductCategory, id=category_id, company=request.user.company)
        
        # Check if category has products
        if category.products.exists():
            return JsonResponse({
                'success': False, 
                'error': f'Cannot delete category "{category.name}" because it has {category.products.count()} products. Move or delete products first.'
            })
        
        # Check if category has subcategories
        if category.subcategories.exists():
            return JsonResponse({
                'success': False,
                'error': f'Cannot delete category "{category.name}" because it has {category.subcategories.count()} subcategories. Delete subcategories first.'
            })
        
        category_name = category.name
        category.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Category "{category_name}" deleted successfully'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def category_detail(request, category_id):
    """Get category details with products and stock information"""
    try:
        category = get_object_or_404(ProductCategory, id=category_id, company=request.user.company)
        
        # Get products in this category
        products = category.products.filter(is_active=True).annotate(
            stock_quantity=Sum('stockitem__quantity', default=0),
            stock_value=Sum('stockitem__quantity', default=0) * F('cost_price')
        )
        
        # Get subcategories
        subcategories = category.subcategories.filter(is_active=True).annotate(
            product_count=Count('products')
        )
        
        return JsonResponse({
            'success': True,
            'category': {
                'id': category.id,
                'name': category.name,
                'code': category.code,
                'description': category.description,
                'parent': category.parent.name if category.parent else None,
                'is_active': category.is_active,
                'created_at': category.created_at.strftime('%Y-%m-%d %H:%M'),
                'product_count': products.count(),
                'subcategory_count': subcategories.count(),
                'total_stock_value': sum(p.stock_value or 0 for p in products),
            },
            'products': [
                {
                    'id': p.id,
                    'name': p.name,
                    'sku': p.sku,
                    'stock_quantity': p.stock_quantity,
                    'cost_price': float(p.cost_price) if p.cost_price else 0,
                    'selling_price': float(p.selling_price) if p.selling_price else 0,
                }
                for p in products[:10]  # Limit to first 10 products
            ],
            'subcategories': [
                {
                    'id': sc.id,
                    'name': sc.name,
                    'code': sc.code,
                    'product_count': sc.product_count,
                    'is_active': sc.is_active,
                }
                for sc in subcategories
            ]
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def adjustments_ui(request):
    """Enhanced Stock adjustments management view with comprehensive functionality"""
    company = request.user.company
    
    # Get all stock adjustments (use the proper model, not movements)
    adjustments = StockAdjustment.objects.filter(
        company=company
    ).select_related(
        'created_by', 'approved_by', 'posted_by'
    ).prefetch_related('items__stock_item__product').order_by('-created_at')
    
    # Calculate statistics
    total_adjustments = adjustments.count()
    pending_adjustments = adjustments.filter(status='pending_approval').count()
    draft_adjustments = adjustments.filter(status='draft').count()
    posted_adjustments = adjustments.filter(status='posted').count()
    
    # Today's adjustments
    today_adjustments = adjustments.filter(created_at__date=timezone.now().date()).count()
    
    # Calculate total value impact
    value_increase = adjustments.filter(
        status='posted',
        adjustment_type='increase'
    ).aggregate(total=Sum('total_adjustment_value'))['total'] or 0
    
    value_decrease = adjustments.filter(
        status='posted',
        adjustment_type='decrease'
    ).aggregate(total=Sum('total_adjustment_value'))['total'] or 0
    
    net_value_impact = value_increase - abs(value_decrease)
    
    # Get warehouses and products for filters
    warehouses = Warehouse.objects.filter(company=company, is_active=True)
    products = Product.objects.filter(company=company, is_active=True)
    
    # Recent 50 adjustments for display
    recent_adjustments = adjustments[:50]
    
    context = {
        'adjustments': recent_adjustments,
        'warehouses': warehouses,
        'products': products,
        'total_adjustments': total_adjustments,
        'pending_adjustments': pending_adjustments,
        'draft_adjustments': draft_adjustments,
        'posted_adjustments': posted_adjustments,
        'today_adjustments': today_adjustments,
        'value_increase': value_increase,
        'value_decrease': value_decrease,
        'net_value_impact': net_value_impact,
    }
    return render(request, 'inventory/adjustments-ui-enhanced.html', context)

@login_required
def reports_ui(request):
    """Enhanced Inventory reports and analytics view"""
    company = request.user.company
    
    # Basic stock summary
    stock_items = StockItem.objects.filter(company=company, is_active=True)
    
    # Calculate total value as float to avoid Decimal arithmetic issues
    total_stock_value = float(sum((item.quantity * item.average_cost) for item in stock_items))
    
    stock_summary = {
        'total_items': stock_items.count(),
        'total_value': total_stock_value,
        'low_stock_items': stock_items.filter(quantity__lte=F('min_stock'), min_stock__gt=0).count(),
        'out_of_stock_items': stock_items.filter(quantity=0).count(),
        'total_warehouses': Warehouse.objects.filter(company=company, is_active=True).count(),
        'total_categories': ProductCategory.objects.filter(company=company, is_active=True).count(),
        'top_products': Product.objects.filter(company=company, is_active=True)[:10]
    }
    
    # Warehouse analytics
    warehouse_analytics = []
    for warehouse in Warehouse.objects.filter(company=company, is_active=True):
        warehouse_stock = stock_items.filter(warehouse=warehouse)
        warehouse_analytics.append({
            'name': warehouse.name,
            'total_items': warehouse_stock.count(),
            'total_value': float(sum((item.quantity * item.average_cost) for item in warehouse_stock)),
            'utilization': 85.0  # Mock utilization percentage
        })
    
    # Category analytics
    category_analytics = []
    for category in ProductCategory.objects.filter(company=company, is_active=True)[:10]:
        category_products = Product.objects.filter(category=category, company=company)
        category_stock = stock_items.filter(product__in=category_products)
        category_analytics.append({
            'name': category.name,
            'total_items': category_stock.count(),
            'total_value': float(sum((item.quantity * item.average_cost) for item in category_stock))
        })
    
    # Movement analytics (simplified)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_movements = StockMovement.objects.filter(
        company=company, 
        timestamp__gte=thirty_days_ago
    )
    
    movement_analytics = []
    for movement_type in ['in', 'out', 'transfer', 'adjustment']:
        count = recent_movements.filter(movement_type=movement_type).count()
        if count > 0:
            movement_analytics.append({
                'movement_type': movement_type,
                'count': count,
                'total_quantity': sum(m.quantity for m in recent_movements.filter(movement_type=movement_type))
            })
    
    # ABC Analysis (simplified)
    total_stock_value = stock_summary['total_value']
    abc_analysis = {
        'A': {'count': 20, 'value': total_stock_value * 0.7, 'percentage': 20},
        'B': {'count': 30, 'value': total_stock_value * 0.2, 'percentage': 30},
        'C': {'count': 50, 'value': total_stock_value * 0.1, 'percentage': 50}
    }
    
    # Aging analysis (simplified)
    aging_analysis = [
        {'label': '0-30 days', 'count': 45, 'value': total_stock_value * 0.4, 'percentage': 40},
        {'label': '31-60 days', 'count': 30, 'value': total_stock_value * 0.3, 'percentage': 30},
        {'label': '61-90 days', 'count': 20, 'value': total_stock_value * 0.2, 'percentage': 20},
        {'label': '90+ days', 'count': 15, 'value': total_stock_value * 0.1, 'percentage': 10}
    ]
    
    # Turnover analysis (simplified)
    turnover_analysis = []
    for product in Product.objects.filter(company=company, is_active=True)[:10]:
        stock_item = stock_items.filter(product=product).first()
        if stock_item:
            turnover_analysis.append({
                'product_name': product.name,
                'avg_inventory': stock_item.quantity,
                'cogs': float(stock_item.quantity * stock_item.average_cost),
                'turnover_ratio': 4.5,  # Mock ratio
                'days_in_inventory': 80,  # Mock days
                'performance': 'Good'  # Mock performance
            })
    
    context = {
        'stock_summary': stock_summary,
        'warehouse_analytics': warehouse_analytics,
        'category_analytics': category_analytics,
        'movement_analytics': movement_analytics,
        'abc_analysis': abc_analysis,
        'aging_analysis': aging_analysis,
        'turnover_analysis': turnover_analysis,
        'report_date': timezone.now(),
    }
    return render(request, 'inventory/reports-ui-enhanced.html', context)

# New Warehouse Management Views
@login_required
def warehouse_add(request):
    """Add new warehouse"""
    if request.method == 'POST':
        form = WarehouseForm(request.POST, company=request.user.company)
        if form.is_valid():
            warehouse = form.save(commit=False)
            warehouse.company = request.user.company
            warehouse.save()
            messages.success(request, f'Warehouse "{warehouse.name}" created successfully!')
            return JsonResponse({
                'success': True,
                'warehouse': {
                    'id': warehouse.id,
                    'name': warehouse.name,
                    'location': warehouse.location,
                    'is_active': warehouse.is_active,
                    'warehouse_type': warehouse.get_warehouse_type_display(),
                    'stock_count': 0,
                    'total_quantity': 0
                }
            })
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def warehouse_edit(request, pk):
    """Edit existing warehouse"""
    warehouse = get_object_or_404(Warehouse, pk=pk, company=request.user.company)
    
    if request.method == 'POST':
        form = WarehouseForm(request.POST, instance=warehouse, company=request.user.company)
        if form.is_valid():
            warehouse = form.save()
            messages.success(request, f'Warehouse "{warehouse.name}" updated successfully!')
            return JsonResponse({
                'success': True,
                'warehouse': {
                    'id': warehouse.id,
                    'name': warehouse.name,
                    'location': warehouse.location,
                    'is_active': warehouse.is_active,
                    'warehouse_type': warehouse.get_warehouse_type_display(),
                    'stock_count': warehouse.stock_items.count(),
                    'total_quantity': warehouse.stock_items.aggregate(total=Sum('quantity'))['total'] or 0
                }
            })
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    
    # GET request - return warehouse data for form population
    return JsonResponse({
        'success': True,
        'warehouse': {
            'id': warehouse.id,
            'name': warehouse.name,
            'location': warehouse.location,
            'warehouse_type': warehouse.warehouse_type,
            'is_active': warehouse.is_active,
            'address': warehouse.address,
            'code': getattr(warehouse, 'code', ''),
        }
    })

@login_required
@require_POST
def warehouse_delete(request, pk):
    """Delete warehouse"""
    warehouse = get_object_or_404(Warehouse, pk=pk, company=request.user.company)
    
    # Check if warehouse has stock items
    stock_count = warehouse.stock_items.filter(is_active=True).count()
    if stock_count > 0:
        return JsonResponse({
            'success': False, 
            'error': f'Cannot delete warehouse with {stock_count} active stock items. Please move or remove stock first.'
        })
    
    warehouse_name = warehouse.name
    warehouse.delete()
    messages.success(request, f'Warehouse "{warehouse_name}" deleted successfully!')
    
    return JsonResponse({'success': True})

@login_required
def warehouse_detail(request, pk):
    """Warehouse detail view"""
    warehouse = get_object_or_404(Warehouse, pk=pk, company=request.user.company)
    
    # Get stock items in this warehouse
    stock_items = StockItem.objects.filter(
        warehouse=warehouse,
        company=request.user.company
    ).select_related('product', 'category').order_by('-created_at')
    
    # Get recent movements for this warehouse
    recent_movements = StockMovement.objects.filter(
        Q(from_warehouse=warehouse) | Q(to_warehouse=warehouse),
        company=request.user.company
    ).select_related('stock_item__product', 'performed_by').order_by('-timestamp')[:10]
    
    # Calculate statistics
    total_items = stock_items.count()
    total_quantity = stock_items.aggregate(total=Sum('quantity'))['total'] or 0
    total_value = stock_items.aggregate(
        total=Sum(F('quantity') * F('average_cost'))
    )['total'] or 0
    
    context = {
        'warehouse': warehouse,
        'stock_items': stock_items,
        'recent_movements': recent_movements,
        'total_items': total_items,
        'total_quantity': total_quantity,
        'total_value': total_value,
    }
    return render(request, 'inventory/warehouse_detail.html', context)

# New Template Views
@login_required
def transfers_ui(request):
    """Stock transfers management view"""
    company = request.user.company
    
    # Get transfer-related movements
    all_transfers = StockMovement.objects.filter(
        company=company,
        movement_type__in=['transfer_out', 'transfer_in', 'inter_warehouse_transfer']
    ).select_related(
        'stock_item__product', 
        'from_warehouse', 
        'to_warehouse', 
        'performed_by'
    ).order_by('-timestamp')
    
    # Calculate statistics
    transfers_today_count = all_transfers.filter(timestamp__date=timezone.now().date()).count()
    pending_transfers = all_transfers.filter(movement_type='transfer_out').count()
    in_transit = all_transfers.filter(movement_type='transfer_out').count()
    
    # Get recent transfers (limited to 50)
    transfers = all_transfers[:50]
    
    # Get warehouses and stock items for the form
    warehouses = Warehouse.objects.filter(company=company, is_active=True).order_by('name')
    stock_items = StockItem.objects.filter(
        company=company,
        is_active=True,
        quantity__gt=0
    ).select_related('product', 'warehouse').order_by('product__name')
    
    context = {
        'transfers': transfers,
        'warehouses': warehouses,
        'stock_items': stock_items,
        'total_transfers': all_transfers.count(),
        'transfers_today': transfers_today_count,
        'pending_transfers': pending_transfers,
        'in_transit': in_transit,
    }
    return render(request, 'inventory/transfers-ui.html', context)

@login_required
def lots_ui(request):
    """Stock lots management view"""
    company = request.user.company
    lots = StockLot.objects.filter(
        stock_item__company=company
    ).select_related('stock_item__product', 'stock_item__warehouse').order_by('-received_date')
    
    # Get stock items for the dropdown in add lot modal
    stock_items = StockItem.objects.filter(
        company=company
    ).select_related('product', 'warehouse').order_by('product__name')
    
    # Get products for filtering
    products = Product.objects.filter(company=company).order_by('name')
    
    # Calculate statistics
    current_date = timezone.now().date()
    expiring_soon_lots = lots.filter(
        expiry_date__isnull=False,
        expiry_date__lte=current_date + timezone.timedelta(days=30),
        expiry_date__gt=current_date
    )
    
    context = {
        'lots': lots,
        'stock_items': stock_items,
        'products': products,
        'total_lots': lots.count(),
        'active_lots': lots.filter(is_active=True, remaining_quantity__gt=0).count(),
        'expiring_lots': expiring_soon_lots.count(),
        'expired_lots': lots.filter(expiry_date__lt=current_date).count() if lots.filter(expiry_date__isnull=False).exists() else 0,
        'quarantined_lots': lots.filter(is_quarantined=True).count(),
    }
    return render(request, 'inventory/lots-ui.html', context)

@login_required
@require_POST
def lot_add(request):
    """Add new lot via AJAX"""
    try:
        import json
        data = json.loads(request.body)
        
        stock_item = get_object_or_404(StockItem, id=data['stock_item'], company=request.user.company)
        
        lot = StockLot.objects.create(
            stock_item=stock_item,
            lot_number=data['lot_number'],
            batch_number=data.get('batch_number', ''),
            quantity=Decimal(data['quantity']),
            remaining_quantity=Decimal(data['quantity']),
            unit_cost=Decimal(data.get('unit_cost', 0)),
            manufacturing_date=data.get('manufacturing_date') if data.get('manufacturing_date') else None,
            expiry_date=data.get('expiry_date') if data.get('expiry_date') else None,
            supplier_lot_number=data.get('supplier_lot_number', ''),
            is_active=True
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Lot created successfully',
            'lot_id': lot.id
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

@login_required
def lot_details(request, lot_id):
    """Get lot details via AJAX"""
    try:
        lot = get_object_or_404(StockLot, id=lot_id, stock_item__company=request.user.company)
        
        data = {
            'lot_number': lot.lot_number,
            'batch_number': lot.batch_number,
            'product_name': lot.stock_item.product.name,
            'quantity': str(lot.quantity),
            'remaining_quantity': str(lot.remaining_quantity),
            'received_date': lot.received_date.strftime('%b %d, %Y'),
            'expiry_date': lot.expiry_date.strftime('%b %d, %Y') if lot.expiry_date else None,
            'quality_status': 'Approved' if lot.quality_approved else 'Pending',
            'is_quarantined': lot.is_quarantined,
            'is_expired': lot.is_expired
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
@require_POST
def lot_approve_quality(request, lot_id):
    """Approve quality for a lot"""
    try:
        lot = get_object_or_404(StockLot, id=lot_id, stock_item__company=request.user.company)
        
        lot.quality_approved = True
        lot.quality_approved_by = request.user
        lot.quality_approved_date = timezone.now()
        lot.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Quality approved successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

@login_required
@require_POST
def lot_quarantine(request, lot_id):
    """Quarantine a lot"""
    try:
        import json
        data = json.loads(request.body)
        
        lot = get_object_or_404(StockLot, id=lot_id, stock_item__company=request.user.company)
        
        lot.is_quarantined = True
        lot.quarantine_reason = data.get('reason', '')
        lot.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Lot quarantined successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

@login_required
def export_expiring_lots(request):
    """Export expiring lots as CSV"""
    import csv
    from django.http import HttpResponse
    
    try:
        company = request.user.company
        current_date = timezone.now().date()
        expiring_lots = StockLot.objects.filter(
            stock_item__company=company,
            expiry_date__isnull=False,
            expiry_date__lte=current_date + timezone.timedelta(days=30),
            expiry_date__gt=current_date
        ).select_related('stock_item__product')
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="expiring-lots-{current_date}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Lot Number', 'Product', 'Quantity', 'Remaining', 'Expiry Date', 'Days Until Expiry'])
        
        for lot in expiring_lots:
            days_until_expiry = (lot.expiry_date - current_date).days
            writer.writerow([
                lot.lot_number,
                lot.stock_item.product.name,
                lot.quantity,
                lot.remaining_quantity,
                lot.expiry_date.strftime('%Y-%m-%d'),
                days_until_expiry
            ])
        
        return response
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def locks_ui(request):
    """Enhanced inventory locks management view"""
    company = request.user.company
    
    # Get all locks with related data
    locks = InventoryLock.objects.filter(
        stock_item__company=company
    ).select_related(
        'stock_item__product', 
        'stock_item__warehouse',
        'locked_by',
        'unlocked_by'
    ).order_by('-locked_at')
    
    # Calculate statistics
    from django.db.models import Count, Case, When, IntegerField, Sum, F
    from datetime import datetime, timedelta
    
    today = timezone.now().date()
    week_from_now = today + timedelta(days=7)
    
    stats = locks.aggregate(
        active_locks=Count(Case(When(is_active=True, then=1), output_field=IntegerField())),
        grn_pending_count=Count(Case(When(lock_type='grn_pending_bill', is_active=True, then=1), output_field=IntegerField())),
        quality_holds_count=Count(Case(When(lock_type__in=['quality_inspection', 'quality_failed'], is_active=True, then=1), output_field=IntegerField())),
        expired_locks=Count(Case(When(expires_at__lt=timezone.now(), is_active=True, then=1), output_field=IntegerField())),
    )
    
    # Calculate total locked value
    total_locked_value = locks.filter(is_active=True).aggregate(
        total=Sum(F('locked_quantity') * F('stock_item__average_cost'))
    )['total'] or 0
    
    # Get filter options
    locked_by_users = User.objects.filter(
        inventory_locks__stock_item__company=company
    ).distinct().order_by('first_name', 'last_name', 'email')
    
    # Get stock items for the create form
    stock_items = StockItem.objects.filter(
        company=company,
        is_active=True,
        available_quantity__gt=0
    ).select_related('product', 'warehouse').order_by('product__name')
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(locks, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'locks': page_obj,
        'page_obj': page_obj,
        'locked_by_users': locked_by_users,
        'stock_items': stock_items,
        'today': today,
        'week_from_now': week_from_now,
        **stats,
        'total_locked_value': total_locked_value,
    }
    return render(request, 'inventory/locks-ui-enhanced.html', context)


@login_required
@require_POST
def locks_create(request):
    """Create a new inventory lock"""
    try:
        import json
        
        stock_item_id = request.POST.get('stock_item')
        locked_quantity = Decimal(request.POST.get('locked_quantity', '0'))
        lock_type = request.POST.get('lock_type')
        priority = int(request.POST.get('priority', '5'))
        reference_type = request.POST.get('reference_type', '')
        reference_number = request.POST.get('reference_number', '')
        expires_at = request.POST.get('expires_at')
        reason = request.POST.get('reason', '')
        requires_approval = request.POST.get('requires_approval_to_unlock') == 'on'
        
        # Validate inputs
        if not stock_item_id or locked_quantity <= 0 or not lock_type:
            return JsonResponse({
                'success': False,
                'error': 'Stock item, quantity, and lock type are required'
            }, status=400)
        
        stock_item = get_object_or_404(StockItem, id=stock_item_id, company=request.user.company)
        
        # Check available quantity
        if stock_item.available_quantity < locked_quantity:
            return JsonResponse({
                'success': False,
                'error': f'Insufficient available quantity. Available: {stock_item.available_quantity}'
            }, status=400)
        
        # Parse expiry date
        expires_at_parsed = None
        if expires_at:
            try:
                expires_at_parsed = timezone.datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            except ValueError:
                pass
        
        # Create the lock
        lock = InventoryLock.objects.create(
            stock_item=stock_item,
            locked_quantity=locked_quantity,
            lock_type=lock_type,
            priority=priority,
            reference_type=reference_type,
            reference_number=reference_number,
            expires_at=expires_at_parsed,
            reason=reason,
            requires_approval_to_unlock=requires_approval,
            locked_by=request.user
        )
        
        # Update stock item locked quantity
        stock_item.locked_quantity += locked_quantity
        stock_item.save()
        
        # Create stock movement for audit trail
        StockMovement.objects.create(
            stock_item=stock_item,
            movement_type='lock',
            quantity=locked_quantity,
            reference=f"Lock-{lock.id}",
            notes=f"Inventory locked: {reason}",
            performed_by=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Inventory lock created successfully',
            'lock_id': lock.id
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_POST
def locks_unlock(request, lock_id):
    """Unlock inventory"""
    try:
        import json
        
        lock = get_object_or_404(InventoryLock, id=lock_id, stock_item__company=request.user.company)
        unlock_reason = request.POST.get('unlock_reason', '')
        
        if not unlock_reason:
            return JsonResponse({
                'success': False,
                'error': 'Unlock reason is required'
            }, status=400)
        
        # Check if approval is required
        if lock.requires_approval_to_unlock:
            # For now, assume the current user has approval rights
            # In a more complex system, you'd check user permissions here
            pass
        
        # Unlock the inventory
        success, message = lock.unlock(request.user, unlock_reason)
        
        if success:
            # Create stock movement for audit trail
            StockMovement.objects.create(
                stock_item=lock.stock_item,
                movement_type='unlock',
                quantity=lock.locked_quantity,
                reference=f"Unlock-{lock.id}",
                notes=f"Inventory unlocked: {unlock_reason}",
                performed_by=request.user
            )
            
            return JsonResponse({
                'success': True,
                'message': message
            })
        else:
            return JsonResponse({
                'success': False,
                'error': message
            }, status=400)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_POST  
def locks_bulk_unlock(request):
    """Bulk unlock multiple inventory locks"""
    try:
        import json
        
        lock_ids_json = request.POST.get('lock_ids')
        bulk_unlock_reason = request.POST.get('bulk_unlock_reason', '')
        
        if not lock_ids_json or not bulk_unlock_reason:
            return JsonResponse({
                'success': False,
                'error': 'Lock IDs and unlock reason are required'
            }, status=400)
        
        lock_ids = json.loads(lock_ids_json)
        
        locks = InventoryLock.objects.filter(
            id__in=lock_ids,
            stock_item__company=request.user.company,
            is_active=True
        )
        
        unlocked_count = 0
        failed_locks = []
        
        for lock in locks:
            success, message = lock.unlock(request.user, bulk_unlock_reason)
            if success:
                unlocked_count += 1
                
                # Create stock movement for audit trail
                StockMovement.objects.create(
                    stock_item=lock.stock_item,
                    movement_type='unlock',
                    quantity=lock.locked_quantity,
                    reference=f"BulkUnlock-{lock.id}",
                    notes=f"Bulk unlock: {bulk_unlock_reason}",
                    performed_by=request.user
                )
            else:
                failed_locks.append({
                    'lock_id': lock.id,
                    'product': lock.stock_item.product.name,
                    'error': message
                })
        
        return JsonResponse({
            'success': True,
            'unlocked_count': unlocked_count,
            'failed_locks': failed_locks,
            'message': f'{unlocked_count} locks unlocked successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def locks_details(request, lock_id):
    """Get lock details for modal display"""
    try:
        lock = get_object_or_404(InventoryLock, id=lock_id, stock_item__company=request.user.company)
        
        return JsonResponse({
            'success': True,
            'product_name': lock.stock_item.product.name,
            'warehouse_name': lock.stock_item.warehouse.name,
            'locked_quantity': str(lock.locked_quantity),
            'lock_type_display': lock.get_lock_type_display(),
            'reference_number': lock.reference_number or '',
            'locked_by': lock.locked_by.get_full_name() or lock.locked_by.email,
            'locked_at': lock.locked_at.isoformat(),
            'reason': lock.reason
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def locks_status(request):
    """Get current lock status for auto-refresh"""
    try:
        company = request.user.company
        locks = InventoryLock.objects.filter(stock_item__company=company)
        
        from django.db.models import Count, Case, When, IntegerField, Sum, F
        
        stats = locks.aggregate(
            active_locks=Count(Case(When(is_active=True, then=1), output_field=IntegerField())),
            grn_pending_count=Count(Case(When(lock_type='grn_pending_bill', is_active=True, then=1), output_field=IntegerField())),
            quality_holds_count=Count(Case(When(lock_type__in=['quality_inspection', 'quality_failed'], is_active=True, then=1), output_field=IntegerField())),
            expired_locks=Count(Case(When(expires_at__lt=timezone.now(), is_active=True, then=1), output_field=IntegerField())),
        )
        
        total_locked_value = locks.filter(is_active=True).aggregate(
            total=Sum(F('locked_quantity') * F('stock_item__average_cost'))
        )['total'] or 0
        
        return JsonResponse({
            **stats,
            'total_locked_value': float(total_locked_value)
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)

@login_required
def physical_count_ui(request):
    """Physical count management view"""
    company = request.user.company
    
    # Get stock adjustments for physical counting
    adjustments = StockAdjustment.objects.filter(
        company=company
    ).select_related(
        'created_by', 'approved_by', 'posted_by'
    ).prefetch_related('items').order_by('-created_at')[:50]
    
    # Calculate statistics
    active_counts = StockAdjustment.objects.filter(
        company=company,
        status__in=['draft', 'pending_approval']
    ).count()
    
    adjustments_today = StockAdjustment.objects.filter(
        company=company,
        created_at__date=timezone.now().date()
    ).count()
    
    pending_approval = StockAdjustment.objects.filter(
        company=company,
        status='pending_approval'
    ).count()
    
    # Calculate total value impact
    total_value_impact = StockAdjustment.objects.filter(
        company=company,
        status='posted'
    ).aggregate(
        total=Sum('total_adjustment_value')
    )['total'] or 0
    
    # Get warehouses for filtering
    warehouses = Warehouse.objects.filter(company=company, is_active=True)
    
    context = {
        'adjustments': adjustments,
        'warehouses': warehouses,
        'active_counts': active_counts,
        'adjustments_today': adjustments_today,
        'pending_approval': pending_approval,
        'total_value_impact': total_value_impact,
        'today': timezone.now().date(),
    }
    return render(request, 'inventory/physical-count-enhanced.html', context)

@login_required
@require_POST
def create_adjustment_api(request):
    """API to create new stock adjustment"""
    try:
        company = request.user.company
        
        # Generate adjustment number
        last_adjustment = StockAdjustment.objects.filter(
            company=company
        ).order_by('-id').first()
        
        if last_adjustment:
            # Extract number from last adjustment and increment
            try:
                last_num = int(last_adjustment.adjustment_number.split('-')[-1])
                new_num = last_num + 1
            except (ValueError, IndexError):
                new_num = 1
        else:
            new_num = 1
        
        adjustment_number = f"ADJ-{timezone.now().year}-{new_num:06d}"
        
        # Create adjustment
        adjustment = StockAdjustment.objects.create(
            company=company,
            adjustment_number=adjustment_number,
            adjustment_type=request.POST.get('adjustment_type', 'physical_count'),
            adjustment_date=request.POST.get('adjustment_date'),
            reason=request.POST.get('reason', ''),
            reference_document=request.POST.get('reference_document', ''),
            created_by=request.user
        )
        
        return JsonResponse({
            'success': True,
            'id': adjustment.id,
            'adjustment_number': adjustment.adjustment_number
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_POST
def approve_adjustment_api(request, adjustment_id):
    """API to approve stock adjustment"""
    try:
        adjustment = get_object_or_404(
            StockAdjustment, 
            id=adjustment_id, 
            company=request.user.company
        )
        
        success, message = adjustment.approve(request.user)
        
        return JsonResponse({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_POST
def post_adjustment_api(request, adjustment_id):
    """API to post stock adjustment"""
    try:
        adjustment = get_object_or_404(
            StockAdjustment, 
            id=adjustment_id, 
            company=request.user.company
        )
        
        success, message = adjustment.post(request.user)
        
        return JsonResponse({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

# API Views for Dynamic Loading
@login_required
def warehouse_zones_api(request, warehouse_id):
    """API to get zones for a specific warehouse"""
    try:
        warehouse = get_object_or_404(Warehouse, pk=warehouse_id, company=request.user.company)
        zones = WarehouseZone.objects.filter(warehouse=warehouse, is_active=True).values('id', 'name', 'description')
        return JsonResponse({'success': True, 'zones': list(zones)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def warehouse_bins_api(request, zone_id):
    """API to get bins for a specific zone"""
    try:
        zone = get_object_or_404(WarehouseZone, pk=zone_id, warehouse__company=request.user.company)
        bins = WarehouseBin.objects.filter(zone=zone, is_active=True).values('id', 'name', 'capacity', 'current_stock')
        return JsonResponse({'success': True, 'bins': list(bins)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def adjustment_detail(request, adjustment_id):
    """View adjustment details"""
    adjustment = get_object_or_404(
        StockAdjustment, 
        id=adjustment_id, 
        company=request.user.company
    )
    
    context = {
        'adjustment': adjustment,
        'items': adjustment.items.select_related(
            'stock_item__product',
            'stock_item__warehouse',
            'counted_by'
        ).all(),
        'can_edit': adjustment.status == 'draft',
        'can_approve': adjustment.status == 'pending_approval',
        'can_post': adjustment.status == 'approved',
    }
    
    return render(request, 'inventory/adjustment-detail.html', context)

@login_required
def adjustment_edit(request, adjustment_id):
    """Edit adjustment and its items"""
    adjustment = get_object_or_404(
        StockAdjustment, 
        id=adjustment_id, 
        company=request.user.company
    )
    
    if adjustment.status != 'draft':
        messages.error(request, 'Only draft adjustments can be edited.')
        return redirect('inventory:adjustment_detail', adjustment_id=adjustment_id)
    
    if request.method == 'POST':
        # Handle form submission
        adjustment.reason = request.POST.get('reason', '')
        adjustment.reference_document = request.POST.get('reference_document', '')
        adjustment.save()
        
        # Handle item updates
        for key, value in request.POST.items():
            if key.startswith('physical_qty_'):
                item_id = key.replace('physical_qty_', '')
                try:
                    item = adjustment.items.get(id=item_id)
                    item.physical_quantity = Decimal(value)
                    item.save()
                except (StockAdjustmentItem.DoesNotExist, InvalidOperation):
                    continue
        
        messages.success(request, 'Adjustment updated successfully.')
        return redirect('inventory:adjustment_detail', adjustment_id=adjustment_id)
    
    # Get stock items for this warehouse if specified
    stock_items = StockItem.objects.filter(
        company=request.user.company,
        quantity__gt=0
    ).select_related('product', 'warehouse')
    
    context = {
        'adjustment': adjustment,
        'items': adjustment.items.select_related(
            'stock_item__product',
            'stock_item__warehouse'
        ).all(),
        'stock_items': stock_items,
    }
    
    return render(request, 'inventory/adjustment-edit.html', context)

@login_required
def locks_export(request):
    """Export inventory locks to CSV"""
    import csv
    from django.http import HttpResponse
    
    try:
        company = request.user.company
        
        # Get all locks with filters if provided
        locks = InventoryLock.objects.filter(
            stock_item__company=company
        ).select_related(
            'stock_item__product',
            'stock_item__warehouse',
            'locked_by',
            'unlocked_by'
        ).order_by('-locked_at')
        
        # Apply filters from GET parameters
        status_filter = request.GET.get('status')
        if status_filter == 'active':
            locks = locks.filter(is_active=True)
        elif status_filter == 'inactive':
            locks = locks.filter(is_active=False)
        
        lock_type_filter = request.GET.get('lock_type')
        if lock_type_filter:
            locks = locks.filter(lock_type=lock_type_filter)
        
        date_from = request.GET.get('date_from')
        if date_from:
            try:
                from datetime import datetime
                date_from_parsed = datetime.strptime(date_from, '%Y-%m-%d').date()
                locks = locks.filter(locked_at__date__gte=date_from_parsed)
            except ValueError:
                pass
        
        date_to = request.GET.get('date_to')
        if date_to:
            try:
                from datetime import datetime
                date_to_parsed = datetime.strptime(date_to, '%Y-%m-%d').date()
                locks = locks.filter(locked_at__date__lte=date_to_parsed)
            except ValueError:
                pass
        
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        current_date = timezone.now().strftime('%Y-%m-%d')
        response['Content-Disposition'] = f'attachment; filename="inventory-locks-{current_date}.csv"'
        
        writer = csv.writer(response)
        
        # Write header
        writer.writerow([
            'Lock ID',
            'Product',
            'SKU',
            'Warehouse',
            'Locked Quantity',
            'Lock Type',
            'Priority',
            'Status',
            'Reference Type',
            'Reference Number',
            'Reason',
            'Locked By',
            'Locked At',
            'Expires At',
            'Unlocked By',
            'Unlocked At',
            'Unlock Reason',
            'Unit Cost',
            'Total Value'
        ])
        
        # Write data rows
        for lock in locks:
            unit_cost = lock.stock_item.average_cost or 0
            total_value = lock.locked_quantity * unit_cost
            
            writer.writerow([
                lock.id,
                lock.stock_item.product.name,
                lock.stock_item.product.sku,
                lock.stock_item.warehouse.name,
                lock.locked_quantity,
                lock.get_lock_type_display(),
                lock.priority,
                'Active' if lock.is_active else 'Inactive',
                lock.reference_type,
                lock.reference_number,
                lock.reason,
                lock.locked_by.get_full_name() or lock.locked_by.email,
                lock.locked_at.strftime('%Y-%m-%d %H:%M:%S'),
                lock.expires_at.strftime('%Y-%m-%d %H:%M:%S') if lock.expires_at else '',
                (lock.unlocked_by.get_full_name() or lock.unlocked_by.email) if lock.unlocked_by else '',
                lock.unlocked_at.strftime('%Y-%m-%d %H:%M:%S') if lock.unlocked_at else '',
                lock.unlock_reason or '',
                unit_cost,
                total_value
            ])
        
        return response
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
