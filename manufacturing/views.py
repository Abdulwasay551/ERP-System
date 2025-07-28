from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import BillOfMaterials, WorkOrder, ProductionPlan
from django.views.decorators.http import require_POST
from django.db.models import Count, Q, Sum, F
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.paginator import Paginator

# Create your views here.

@login_required
def manufacturing_dashboard(request):
    """Manufacturing module dashboard with key metrics and quick access"""
    try:
        company = request.user.company
        
        # Key metrics
        total_boms = BillOfMaterials.objects.filter(company=company, is_active=True).count()
        new_boms_this_month = BillOfMaterials.objects.filter(
            company=company, 
            created_at__gte=timezone.now().replace(day=1)
        ).count()
        
        # Work orders metrics
        try:
            active_work_orders = WorkOrder.objects.filter(
                company=company, 
                status__in=['pending', 'in_progress']
            ).count()
        except:
            active_work_orders = 0
        
        # Production metrics
        try:
            production_orders = ProductionPlan.objects.filter(
                company=company,
                status='in_progress'
            ).count()
        except:
            production_orders = 0
        
        # Recent BOMs
        recent_boms = BillOfMaterials.objects.filter(
            company=company
        ).order_by('-created_at')[:5]
        
        context = {
            'total_boms': total_boms,
            'new_boms_this_month': new_boms_this_month,
            'recent_boms': recent_boms,
            'active_work_orders': active_work_orders,
            'production_orders': production_orders,
            'quality_checks': 0,      # Placeholder
        }
        return render(request, 'manufacturing/dashboard.html', context)
    except Exception as e:
        context = {
            'total_boms': 0,
            'new_boms_this_month': 0,
            'recent_boms': [],
            'active_work_orders': 0,
            'production_orders': 0,
            'quality_checks': 0,
            'error': str(e)
        }
        return render(request, 'manufacturing/dashboard.html', context)

@login_required
def boms_ui(request):
    """Display BOMs with filtering and pagination"""
    try:
        company = request.user.company
        
        # Get filter parameters
        search = request.GET.get('search', '')
        status = request.GET.get('status', '')
        
        # Build query
        boms = BillOfMaterials.objects.filter(company=company)
        
        if search:
            boms = boms.filter(
                Q(name__icontains=search) | 
                Q(code__icontains=search) |
                Q(description__icontains=search)
            )
        
        if status == 'active':
            boms = boms.filter(is_active=True)
        elif status == 'inactive':
            boms = boms.filter(is_active=False)
        
        # Pagination
        paginator = Paginator(boms.order_by('-created_at'), 20)
        page_number = request.GET.get('page')
        boms = paginator.get_page(page_number)
        
        context = {
            'boms': boms,
            'search': search,
            'status': status,
        }
        return render(request, 'manufacturing/boms-ui.html', context)
    except Exception as e:
        context = {
            'boms': [],
            'error': str(e)
        }
        return render(request, 'manufacturing/boms-ui.html', context)

@login_required
def boms_add(request):
    """Handle both GET and POST for BOM creation"""
    if request.method == 'GET':
        return render(request, 'manufacturing/bom_form.html')
    
    elif request.method == 'POST':
        try:
            name = request.POST.get('name')
            code = request.POST.get('code')
            description = request.POST.get('description')
            is_active = request.POST.get('is_active') == 'on'
            
            if not name or not code:
                return JsonResponse({'success': False, 'error': 'Name and code are required.'}, status=400)
            
            # Check for duplicate code
            if BillOfMaterials.objects.filter(company=request.user.company, code=code).exists():
                return JsonResponse({'success': False, 'error': 'BOM code already exists.'}, status=400)
            
            bom = BillOfMaterials.objects.create(
                company=request.user.company,
                name=name,
                code=code,
                description=description or '',
                is_active=is_active,
                created_by=request.user
            )
            return JsonResponse({
                'success': True,
                'bom': {
                    'id': bom.id,
                    'name': bom.name,
                    'code': bom.code,
                    'description': bom.description,
                    'is_active': bom.is_active
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def boms_edit(request, pk):
    """Handle both GET and POST for BOM editing"""
    bom = get_object_or_404(BillOfMaterials, pk=pk, company=request.user.company)
    
    if request.method == 'GET':
        return render(request, 'manufacturing/bom_form.html', {
            'bom': bom,
            'edit_mode': True
        })
    
    elif request.method == 'POST':
        try:
            name = request.POST.get('name')
            code = request.POST.get('code')
            description = request.POST.get('description')
            is_active = request.POST.get('is_active') == 'on'
            
            if not name or not code:
                return JsonResponse({'success': False, 'error': 'Name and code are required.'}, status=400)
            
            # Check for duplicate code (excluding current BOM)
            if BillOfMaterials.objects.filter(company=request.user.company, code=code).exclude(pk=pk).exists():
                return JsonResponse({'success': False, 'error': 'BOM code already exists.'}, status=400)
            
            bom.name = name
            bom.code = code
            bom.description = description or ''
            bom.is_active = is_active
            bom.save()
            
            return JsonResponse({
                'success': True,
                'bom': {
                    'id': bom.id,
                    'name': bom.name,
                    'code': bom.code,
                    'description': bom.description,
                    'is_active': bom.is_active
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def boms_delete(request, pk):
    """Handle BOM deletion"""
    if request.method == 'POST':
        try:
            bom = get_object_or_404(BillOfMaterials, pk=pk, company=request.user.company)
            bom_name = bom.name
            bom.delete()
            return JsonResponse({
                'success': True,
                'message': f'BOM "{bom_name}" deleted successfully.'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

@login_required
def workorders_ui(request):
    """Display work orders"""
    try:
        company = request.user.company
        
        # Get work orders if model exists
        try:
            work_orders = WorkOrder.objects.filter(company=company).order_by('-created_at')[:20]
        except:
            work_orders = []
        
        context = {
            'work_orders': work_orders,
        }
        return render(request, 'manufacturing/workorders-ui.html', context)
    except Exception as e:
        context = {
            'work_orders': [],
            'error': str(e)
        }
        return render(request, 'manufacturing/workorders-ui.html', context)

@login_required
def production_ui(request):
    """Display production orders"""
    try:
        company = request.user.company
        
        # Get production orders if model exists
        try:
            production_orders = ProductionPlan.objects.filter(company=company).order_by('-created_at')[:20]
        except:
            production_orders = []
        
        context = {
            'production_orders': production_orders,
        }
        return render(request, 'manufacturing/production-ui.html', context)
    except Exception as e:
        context = {
            'production_orders': [],
            'error': str(e)
        }
        return render(request, 'manufacturing/production-ui.html', context)

@login_required
def quality_ui(request):
    """Display quality control"""
    try:
        context = {
            'quality_checks': [],
        }
        return render(request, 'manufacturing/quality-ui.html', context)
    except Exception as e:
        context = {
            'quality_checks': [],
            'error': str(e)
        }
        return render(request, 'manufacturing/quality-ui.html', context)
