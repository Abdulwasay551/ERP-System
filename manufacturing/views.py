from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Count, Q, Sum, F, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from django.core.paginator import Paginator
from django.contrib import messages
from django.db import transaction
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import (
    WorkCenter, BillOfMaterials, BillOfMaterialsItem, BOMOperation,
    WorkOrder, WorkOrderOperation, OperationLog, QualityCheck,
    MaterialConsumption, MRPPlan, MRPRequirement, ProductionPlan,
    ProductionPlanItem, JobCard, Subcontractor, SubcontractWorkOrder,
    DemandForecast, ReorderRule, SupplierLeadTime
)
from .serializers import (
    WorkCenterSerializer, BillOfMaterialsSerializer, WorkOrderSerializer,
    ProductionPlanSerializer, MRPPlanSerializer, QualityCheckSerializer
)
from products.models import Product
from inventory.models import Warehouse, StockMovement
from sales.models import SalesOrder


@login_required
def manufacturing_dashboard(request):
    """Enhanced Manufacturing module dashboard with comprehensive metrics"""
    try:
        company = request.user.company
        
        # Key metrics
        total_boms = BillOfMaterials.objects.filter(company=company, is_active=True).count()
        new_boms_this_month = BillOfMaterials.objects.filter(
            company=company, 
            created_at__gte=timezone.now().replace(day=1)
        ).count()
        
        # Work orders metrics
        active_work_orders = WorkOrder.objects.filter(
            company=company, 
            status__in=['planned', 'released', 'in_progress']
        ).count()
        
        completed_work_orders_this_month = WorkOrder.objects.filter(
            company=company,
            status='completed',
            actual_end__gte=timezone.now().replace(day=1)
        ).count()
        
        # Production metrics
        production_plans = ProductionPlan.objects.filter(
            company=company,
            status__in=['approved', 'in_progress']
        ).count()
        
        # Quality metrics
        quality_checks_pending = QualityCheck.objects.filter(
            work_order__company=company,
            status='pending'
        ).count()
        
        quality_pass_rate = QualityCheck.objects.filter(
            work_order__company=company,
            status='passed',
            inspection_date__gte=timezone.now().replace(day=1)
        ).count()
        
        # Recent activities
        recent_work_orders = WorkOrder.objects.filter(
            company=company
        ).order_by('-created_at')[:5]
        
        recent_boms = BillOfMaterials.objects.filter(
            company=company
        ).order_by('-created_at')[:5]
        
        # Capacity utilization
        work_centers = WorkCenter.objects.filter(company=company, is_active=True)
        
        # MRP alerts
        mrp_requirements = MRPRequirement.objects.filter(
            mrp_plan__company=company,
            status='pending',
            required_date__lte=timezone.now().date() + timedelta(days=7)
        ).count()
        
        context = {
            'total_boms': total_boms,
            'new_boms_this_month': new_boms_this_month,
            'active_work_orders': active_work_orders,
            'completed_work_orders_this_month': completed_work_orders_this_month,
            'production_plans': production_plans,
            'quality_checks_pending': quality_checks_pending,
            'quality_pass_rate': quality_pass_rate,
            'recent_work_orders': recent_work_orders,
            'recent_boms': recent_boms,
            'work_centers_count': work_centers.count(),
            'work_centers': work_centers,  # Add the actual work centers for the template
            'mrp_requirements': mrp_requirements,
        }
        return render(request, 'manufacturing/dashboard.html', context)
    except Exception as e:
        context = {
            'error': str(e),
            'total_boms': 0,
            'active_work_orders': 0,
            'production_plans': 0,
            'quality_checks_pending': 0,
        }
        return render(request, 'manufacturing/dashboard.html', context)

@login_required
def boms_ui(request):
    """Display BOMs with enhanced filtering and pagination"""
    try:
        company = request.user.company
        
        # Get filter parameters
        search = request.GET.get('search', '')
        status = request.GET.get('status', '')
        manufacturing_type = request.GET.get('manufacturing_type', '')
        
        # Build query
        boms = BillOfMaterials.objects.filter(company=company).select_related('product', 'created_by')
        
        if search:
            boms = boms.filter(
                Q(name__icontains=search) | 
                Q(product__name__icontains=search) |
                Q(version__icontains=search)
            )
        
        if status == 'active':
            boms = boms.filter(is_active=True)
        elif status == 'inactive':
            boms = boms.filter(is_active=False)
            
        if manufacturing_type:
            boms = boms.filter(manufacturing_type=manufacturing_type)
        
        # Pagination
        paginator = Paginator(boms.order_by('-created_at'), 20)
        page_number = request.GET.get('page')
        boms = paginator.get_page(page_number)
        
        context = {
            'boms': boms,
            'search': search,
            'status': status,
            'manufacturing_type': manufacturing_type,
            'manufacturing_types': BillOfMaterials.MANUFACTURING_TYPE_CHOICES,
        }
        return render(request, 'manufacturing/boms_list.html', context)
    except Exception as e:
        messages.error(request, f"Error loading BOMs: {str(e)}")
        return render(request, 'manufacturing/boms_list.html', {'boms': []})


@login_required
def work_orders_ui(request):
    """Display Work Orders with comprehensive filtering"""
    try:
        company = request.user.company
        
        # Get filter parameters
        search = request.GET.get('search', '')
        status = request.GET.get('status', '')
        priority = request.GET.get('priority', '')
        
        # Build query
        work_orders = WorkOrder.objects.filter(company=company).select_related('product', 'bom', 'sales_order', 'assigned_to')
        
        if search:
            work_orders = work_orders.filter(
                Q(wo_number__icontains=search) | 
                Q(product__name__icontains=search) |
                Q(customer_reference__icontains=search)
            )
        
        if status:
            work_orders = work_orders.filter(status=status)
            
        if priority:
            work_orders = work_orders.filter(priority=priority)
        
        # Pagination
        paginator = Paginator(work_orders.order_by('-created_at'), 20)
        page_number = request.GET.get('page')
        work_orders = paginator.get_page(page_number)
        
        context = {
            'work_orders': work_orders,
            'search': search,
            'status': status,
            'priority': priority,
            'status_choices': WorkOrder.STATUS_CHOICES,
            'priority_choices': WorkOrder.PRIORITY_CHOICES,
        }
        return render(request, 'manufacturing/work_orders_list.html', context)
    except Exception as e:
        messages.error(request, f"Error loading work orders: {str(e)}")
        return render(request, 'manufacturing/work_orders_list.html', {'work_orders': []})


@login_required
def work_order_detail(request, wo_id):
    """Detailed view of a work order with operations and tracking"""
    try:
        work_order = get_object_or_404(WorkOrder, id=wo_id, company=request.user.company)
        
        # Get related data
        operations = work_order.operations.all().order_by('sequence')
        material_consumptions = work_order.material_consumptions.all()
        quality_checks = work_order.quality_checks.all().order_by('-inspection_date')
        job_cards = work_order.job_cards.all().order_by('-created_at')
        
        context = {
            'work_order': work_order,
            'operations': operations,
            'material_consumptions': material_consumptions,
            'quality_checks': quality_checks,
            'job_cards': job_cards,
            'progress_percentage': work_order.get_progress_percentage(),
        }
        return render(request, 'manufacturing/work_order_detail.html', context)
    except Exception as e:
        messages.error(request, f"Error loading work order: {str(e)}")
        return redirect('manufacturing:work_orders_ui')


@login_required
@require_POST
def start_work_order(request, wo_id):
    """Start production for a work order"""
    try:
        work_order = get_object_or_404(WorkOrder, id=wo_id, company=request.user.company)
        
        if work_order.status == 'planned':
            work_order.start_production()
            messages.success(request, f"Work Order {work_order.wo_number} started successfully.")
        else:
            messages.warning(request, f"Work Order {work_order.wo_number} cannot be started from current status.")
        
        return JsonResponse({'success': True, 'status': work_order.status})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_POST
def complete_work_order(request, wo_id):
    """Complete production for a work order"""
    try:
        work_order = get_object_or_404(WorkOrder, id=wo_id, company=request.user.company)
        
        if work_order.status == 'in_progress':
            work_order.complete_production()
            
            # Auto-create inventory movement for finished goods
            if work_order.destination_warehouse and work_order.quantity_produced > 0:
                StockMovement.objects.create(
                    company=work_order.company,
                    product=work_order.product,
                    warehouse=work_order.destination_warehouse,
                    movement_type='receipt',
                    quantity=work_order.quantity_produced,
                    reference_type='work_order',
                    reference_id=work_order.id,
                    notes=f"Production completion for WO {work_order.wo_number}"
                )
            
            messages.success(request, f"Work Order {work_order.wo_number} completed successfully.")
        else:
            messages.warning(request, f"Work Order {work_order.wo_number} cannot be completed from current status.")
        
        return JsonResponse({'success': True, 'status': work_order.status})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def quality_checks_ui(request):
    """Display quality checks with filtering"""
    try:
        company = request.user.company
        
        # Get filter parameters
        status = request.GET.get('status', '')
        quality_type = request.GET.get('quality_type', '')
        
        # Build query
        quality_checks = QualityCheck.objects.filter(
            work_order__company=company
        ).select_related('work_order', 'product', 'inspector')
        
        # Calculate counts before filtering
        total_checks = quality_checks.count()
        pending_checks = quality_checks.filter(status='pending').count()
        passed_checks = quality_checks.filter(status='passed').count()
        failed_checks = quality_checks.filter(status='failed').count()
        
        if status:
            quality_checks = quality_checks.filter(status=status)
            
        if quality_type:
            quality_checks = quality_checks.filter(quality_type=quality_type)
        
        # Pagination
        paginator = Paginator(quality_checks.order_by('-inspection_date'), 20)
        page_number = request.GET.get('page')
        quality_checks = paginator.get_page(page_number)
        
        context = {
            'quality_checks': quality_checks,
            'total_checks': total_checks,
            'pending_checks': pending_checks,
            'passed_checks': passed_checks,
            'failed_checks': failed_checks,
            'status': status,
            'quality_type': quality_type,
            'status_choices': QualityCheck.STATUS_CHOICES,
            'quality_type_choices': QualityCheck.QUALITY_TYPE_CHOICES,
        }
        return render(request, 'manufacturing/quality_checks_list.html', context)
    except Exception as e:
        messages.error(request, f"Error loading quality checks: {str(e)}")
        return render(request, 'manufacturing/quality_checks_list.html', {
            'quality_checks': [],
            'total_checks': 0,
            'pending_checks': 0,
            'passed_checks': 0,
            'failed_checks': 0,
        })


@login_required
def production_plans_ui(request):
    """Display production plans with filtering"""
    try:
        company = request.user.company
        
        # Get filter parameters
        status = request.GET.get('status', '')
        plan_type = request.GET.get('plan_type', '')
        
        # Build query
        production_plans = ProductionPlan.objects.filter(
            company=company
        ).select_related('created_by', 'approved_by')
        
        if status:
            production_plans = production_plans.filter(status=status)
            
        if plan_type:
            production_plans = production_plans.filter(plan_type=plan_type)
        
        # Pagination
        paginator = Paginator(production_plans.order_by('-start_date'), 20)
        page_number = request.GET.get('page')
        production_plans = paginator.get_page(page_number)
        
        context = {
            'production_plans': production_plans,
            'status': status,
            'plan_type': plan_type,
            'status_choices': ProductionPlan.STATUS_CHOICES,
            'plan_type_choices': ProductionPlan.PLAN_TYPE_CHOICES,
        }
        return render(request, 'manufacturing/production_plans_list.html', context)
    except Exception as e:
        messages.error(request, f"Error loading production plans: {str(e)}")
        return render(request, 'manufacturing/production_plans_list.html', {'production_plans': []})


@login_required
def mrp_ui(request):
    """Enhanced Material Requirements Planning interface"""
    try:
        company = request.user.company
        
        # Get latest MRP plans
        mrp_plans = MRPPlan.objects.filter(company=company).order_by('-plan_date')[:10]
        
        # Get pending requirements
        pending_requirements = MRPRequirement.objects.filter(
            mrp_plan__company=company,
            status='pending'
        ).select_related('product', 'mrp_plan').order_by('required_date')[:20]
        
        # Get shortage alerts (requirements due within next 7 days)
        from datetime import timedelta
        shortage_alerts = MRPRequirement.objects.filter(
            mrp_plan__company=company,
            status='pending',
            shortage_quantity__gt=0,
            required_date__lte=timezone.now().date() + timedelta(days=7)
        ).select_related('product', 'mrp_plan').order_by('required_date')
        
        # Get supply-demand summary
        try:
            from .mrp_engine import SupplyDemandAnalyzer
            analyzer = SupplyDemandAnalyzer(company)
            supply_demand_data = analyzer.generate_supply_demand_report()[:10]  # Top 10
        except Exception:
            supply_demand_data = []
        
        # MRP run statistics
        from .models import MRPRunLog
        recent_runs = MRPRunLog.objects.filter(company=company).order_by('-run_timestamp')[:5]
        
        context = {
            'mrp_plans': mrp_plans,
            'pending_requirements': pending_requirements,
            'shortage_alerts': shortage_alerts,
            'supply_demand_data': supply_demand_data,
            'recent_runs': recent_runs,
        }
        return render(request, 'manufacturing/mrp.html', context)
    except Exception as e:
        messages.error(request, f"Error loading MRP data: {str(e)}")
        return render(request, 'manufacturing/mrp.html', {
            'mrp_plans': [], 
            'pending_requirements': [],
            'shortage_alerts': [],
            'supply_demand_data': [],
            'recent_runs': []
        })


@login_required
@require_POST
def run_mrp_calculation(request):
    """Run MRP calculation"""
    try:
        from .mrp_engine import run_automatic_mrp
        
        company = request.user.company
        mrp_plan, message = run_automatic_mrp(company)
        
        messages.success(request, f"MRP calculation completed: {message}")
        return JsonResponse({
            'success': True,
            'message': message,
            'mrp_plan_id': mrp_plan.id,
            'requirements_count': mrp_plan.requirements.count()
        })
        
    except Exception as e:
        messages.error(request, f"MRP calculation failed: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
def supply_demand_report(request):
    """Supply-Demand Analysis Report"""
    try:
        company = request.user.company
        
        # Get date range from request
        from datetime import timedelta
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            start_date = timezone.now().date()
            
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            end_date = start_date + timedelta(days=90)
        
        # Generate report
        from .mrp_engine import SupplyDemandAnalyzer
        analyzer = SupplyDemandAnalyzer(company, start_date, end_date)
        report_data = analyzer.generate_supply_demand_report()
        
        # Filter and pagination
        search = request.GET.get('search', '')
        if search:
            report_data = [
                item for item in report_data 
                if search.lower() in item['product'].name.lower()
            ]
        
        # Add percentage calculations for template
        for item in report_data:
            if item.get('reorder_point', 0) > 0:
                item['stock_percentage'] = min(100, (item['current_stock'] / item['reorder_point']) * 100)
            else:
                item['stock_percentage'] = 100
        
        # Group by status for summary
        status_summary = {}
        for item in report_data:
            status = item['status']
            # Convert status to template-friendly keys
            status_key = status.replace(' ', '_').replace('-', '_').lower()
            if status_key not in status_summary:
                status_summary[status_key] = 0
            status_summary[status_key] += 1
        
        context = {
            'report_data': report_data,
            'status_summary': status_summary,
            'start_date': start_date,
            'end_date': end_date,
            'search': search
        }
        
        return render(request, 'manufacturing/supply_demand_report.html', context)
        
    except Exception as e:
        messages.error(request, f"Error generating supply-demand report: {str(e)}")
        return render(request, 'manufacturing/supply_demand_report.html', {
            'report_data': [],
            'status_summary': {},
            'start_date': timezone.now().date(),
            'end_date': timezone.now().date() + timedelta(days=90)
        })


@login_required
def mrp_planning_dashboard(request):
    """Advanced MRP Planning Dashboard with enhanced analytics"""
    try:
        company = request.user.company
        
        # Get comprehensive MRP data
        mrp_plans = MRPPlan.objects.filter(company=company).order_by('-plan_date')[:10]
        
        # Get pending requirements with detailed analysis
        pending_requirements = MRPRequirement.objects.filter(
            mrp_plan__company=company,
            status='pending'
        ).select_related('product', 'mrp_plan').order_by('required_date')[:50]
        
        # Get critical shortage alerts (due within next 7 days)
        from datetime import timedelta
        critical_date = timezone.now().date() + timedelta(days=7)
        shortage_alerts = MRPRequirement.objects.filter(
            mrp_plan__company=company,
            status='pending',
            shortage_quantity__gt=0,
            required_date__lte=critical_date
        ).select_related('product', 'mrp_plan').order_by('required_date')
        
        # Get supply-demand analytics
        try:
            from .mrp_engine import SupplyDemandAnalyzer
            analyzer = SupplyDemandAnalyzer(company)
            supply_demand_data = analyzer.generate_supply_demand_report()
            
            # Calculate summary statistics
            total_products = len(supply_demand_data)
            critical_products = len([item for item in supply_demand_data 
                                   if item['status'] in ['Reorder Required', 'Below Safety Stock', 'Shortage Expected']])
            
        except Exception as e:
            supply_demand_data = []
            total_products = 0
            critical_products = 0
        
        # MRP run statistics with performance metrics
        from .models import MRPRunLog
        recent_runs = MRPRunLog.objects.filter(company=company).order_by('-run_timestamp')[:10]
        
        # Calculate planning metrics
        planning_metrics = {
            'total_requirements': pending_requirements.count(),
            'critical_items': shortage_alerts.count(),
            'purchase_requirements': pending_requirements.filter(source_type='purchase').count(),
            'manufacture_requirements': pending_requirements.filter(source_type='manufacture').count(),
            'total_value': sum([float(req.shortage_quantity) * 10 for req in pending_requirements]),  # Placeholder calculation
            'planning_efficiency': 85,  # Placeholder metric
            'forecast_accuracy': 92,   # Placeholder metric
            'on_time_delivery': 88,    # Placeholder metric
        }
        
        context = {
            'mrp_plans': mrp_plans,
            'pending_requirements': pending_requirements,
            'shortage_alerts': shortage_alerts,
            'supply_demand_data': supply_demand_data,
            'recent_runs': recent_runs,
            'planning_metrics': planning_metrics,
            'total_products': total_products,
            'critical_products': critical_products,
        }
        
        return render(request, 'manufacturing/mrp_planning_dashboard.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading MRP planning dashboard: {str(e)}")
        return render(request, 'manufacturing/mrp_planning_dashboard.html', {
            'mrp_plans': [], 
            'pending_requirements': [],
            'shortage_alerts': [],
            'supply_demand_data': [],
            'recent_runs': [],
            'planning_metrics': {},
            'total_products': 0,
            'critical_products': 0,
        })


@login_required
def work_centers_ui(request):
    """Display work centers with utilization metrics"""
    try:
        company = request.user.company
        
        # Get work centers with related data
        work_centers = WorkCenter.objects.filter(company=company).prefetch_related('work_order_operations')
        
        # Filter by status if provided
        status_filter = request.GET.get('status')
        if status_filter:
            work_centers = work_centers.filter(status=status_filter)
        
        # Filter by department if provided  
        department_filter = request.GET.get('department')
        if department_filter:
            work_centers = work_centers.filter(department__icontains=department_filter)
        
        # Calculate metrics
        active_centers = work_centers.filter(status='active').count()
        
        # Calculate utilization for each work center
        total_utilization = 0
        total_capacity = 0
        for wc in work_centers:
            # Get active operations
            active_ops = wc.work_order_operations.filter(status='in_progress').count()
            wc.active_operations = active_ops
            
            # Calculate efficiency (placeholder - can be enhanced)
            wc.efficiency = 85  # Placeholder percentage
            
            # Calculate utilization percentage
            if hasattr(wc, 'capacity_per_hour') and wc.capacity_per_hour:
                utilization = min((active_ops * 10), 100)  # Simple calculation
                wc.utilization_percentage = utilization
                total_utilization += utilization
                total_capacity += wc.capacity_per_hour or 0
            else:
                wc.utilization_percentage = 0
        
        avg_utilization = total_utilization / len(work_centers) if work_centers else 0
        
        # Get all departments for filter dropdown
        departments = work_centers.values_list('department', flat=True).distinct()
        departments = [dept for dept in departments if dept]
        
        # Pagination
        paginator = Paginator(work_centers, 10)
        page_number = request.GET.get('page')
        work_centers_page = paginator.get_page(page_number)
        
        context = {
            'work_centers': work_centers_page,
            'active_centers': active_centers,
            'avg_utilization': round(avg_utilization, 1),
            'total_capacity': total_capacity,
            'departments': departments,
        }
        return render(request, 'manufacturing/work_centers_list.html', context)
    except Exception as e:
        messages.error(request, f"Error loading work centers: {str(e)}")
        return render(request, 'manufacturing/work_centers_list.html', {'work_centers': []})


# API Views for integration with other modules

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_work_order_from_sales(request):
    """Create work order from sales order"""
    try:
        sales_order_id = request.data.get('sales_order_id')
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity')
        
        sales_order = get_object_or_404(SalesOrder, id=sales_order_id, company=request.user.company)
        product = get_object_or_404(Product, id=product_id, company=request.user.company)
        
        # Find active BOM for the product
        bom = BillOfMaterials.objects.filter(
            company=request.user.company,
            product=product,
            is_active=True,
            is_default=True
        ).first()
        
        if not bom:
            return Response({'error': 'No active BOM found for this product'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create work order
        work_order = WorkOrder.objects.create(
            company=request.user.company,
            bom=bom,
            product=product,
            sales_order=sales_order,
            quantity_planned=quantity,
            status='planned',
            created_by=request.user,
            customer_reference=sales_order.customer_reference
        )
        
        # Create work order operations from BOM
        for bom_op in bom.operations.all():
            WorkOrderOperation.objects.create(
                work_order=work_order,
                bom_operation=bom_op,
                work_center=bom_op.work_center,
                sequence=bom_op.sequence,
                quantity_to_produce=quantity
            )
        
        serializer = WorkOrderSerializer(work_order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def consume_materials(request, wo_id):
    """Record material consumption for a work order"""
    try:
        work_order = get_object_or_404(WorkOrder, id=wo_id, company=request.user.company)
        
        consumptions = request.data.get('consumptions', [])
        
        with transaction.atomic():
            for consumption_data in consumptions:
                product_id = consumption_data.get('product_id')
                warehouse_id = consumption_data.get('warehouse_id')
                consumed_quantity = consumption_data.get('consumed_quantity')
                
                product = get_object_or_404(Product, id=product_id)
                warehouse = get_object_or_404(Warehouse, id=warehouse_id)
                
                # Find corresponding BOM item
                bom_item = work_order.bom.items.filter(component=product).first()
                
                # Create material consumption record
                MaterialConsumption.objects.create(
                    work_order=work_order,
                    bom_item=bom_item,
                    product=product,
                    warehouse=warehouse,
                    consumed_quantity=consumed_quantity,
                    consumed_by=request.user,
                    consumed_at=timezone.now()
                )
                
                # Create stock movement (issue)
                StockMovement.objects.create(
                    company=work_order.company,
                    product=product,
                    warehouse=warehouse,
                    movement_type='issue',
                    quantity=consumed_quantity,
                    reference_type='work_order',
                    reference_id=work_order.id,
                    notes=f"Material consumption for WO {work_order.wo_number}"
                )
        
        return Response({'success': True, 'message': 'Materials consumed successfully'})
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def manufacturing_reports(request):
    """Generate manufacturing reports and analytics"""
    try:
        company = request.user.company
        report_type = request.GET.get('type', 'overview')
        
        if report_type == 'overview':
            # Production overview
            data = {
                'total_work_orders': WorkOrder.objects.filter(company=company).count(),
                'completed_this_month': WorkOrder.objects.filter(
                    company=company,
                    status='completed',
                    actual_end__gte=timezone.now().replace(day=1)
                ).count(),
                'quality_pass_rate': _calculate_quality_pass_rate(company),
                'top_products': _get_top_produced_products(company),
                'work_center_utilization': _get_work_center_utilization(company),
            }
        elif report_type == 'efficiency':
            # Efficiency metrics
            data = {
                'on_time_delivery': _calculate_on_time_delivery(company),
                'capacity_utilization': _calculate_capacity_utilization(company),
                'scrap_rate': _calculate_scrap_rate(company),
            }
        else:
            data = {'error': 'Invalid report type'}
        
        return Response(data)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


def _calculate_quality_pass_rate(company):
    """Calculate quality pass rate for the company"""
    try:
        total_checks = QualityCheck.objects.filter(
            work_order__company=company,
            inspection_date__gte=timezone.now().replace(day=1)
        ).count()
        
        passed_checks = QualityCheck.objects.filter(
            work_order__company=company,
            status='passed',
            inspection_date__gte=timezone.now().replace(day=1)
        ).count()
        
        if total_checks > 0:
            return round((passed_checks / total_checks) * 100, 2)
        return 0
    except:
        return 0


def _get_top_produced_products(company, limit=5):
    """Get top produced products"""
    try:
        return list(WorkOrder.objects.filter(
            company=company,
            status='completed',
            actual_end__gte=timezone.now().replace(day=1)
        ).values('product__name').annotate(
            total_quantity=Sum('quantity_produced')
        ).order_by('-total_quantity')[:limit])
    except:
        return []


def _get_work_center_utilization(company):
    """Calculate work center utilization"""
    try:
        work_centers = WorkCenter.objects.filter(company=company, is_active=True)
        utilization_data = []
        
        for wc in work_centers:
            total_operations = wc.work_order_operations.count()
            active_operations = wc.work_order_operations.filter(status='in_progress').count()
            
            utilization = (active_operations / max(1, wc.max_operators)) * 100 if wc.max_operators else 0
            
            utilization_data.append({
                'work_center': wc.name,
                'utilization': round(utilization, 2),
                'active_operations': active_operations,
                'total_operations': total_operations
            })
        
        return utilization_data
    except:
        return []


def _calculate_on_time_delivery(company):
    """Calculate on-time delivery percentage"""
    try:
        completed_orders = WorkOrder.objects.filter(
            company=company,
            status='completed',
            actual_end__isnull=False,
            scheduled_end__isnull=False
        )
        
        total_orders = completed_orders.count()
        on_time_orders = completed_orders.filter(actual_end__lte=F('scheduled_end')).count()
        
        if total_orders > 0:
            return round((on_time_orders / total_orders) * 100, 2)
        return 0
    except:
        return 0


def _calculate_capacity_utilization(company):
    """Calculate overall capacity utilization"""
    try:
        work_centers = WorkCenter.objects.filter(company=company, is_active=True)
        total_capacity = sum(wc.capacity_per_hour * wc.operating_hours_per_day for wc in work_centers)
        
        # This is a simplified calculation - in reality, you'd track actual hours used
        active_operations = WorkOrderOperation.objects.filter(
            work_center__company=company,
            status='in_progress'
        ).count()
        
        if total_capacity > 0:
            return round((active_operations / total_capacity) * 100, 2)
        return 0
    except:
        return 0


def _calculate_scrap_rate(company):
    """Calculate scrap rate"""
    try:
        total_produced = WorkOrder.objects.filter(
            company=company,
            status='completed'
        ).aggregate(total=Sum('quantity_produced'))['total'] or 0
        
        total_rejected = WorkOrder.objects.filter(
            company=company,
            status='completed'
        ).aggregate(total=Sum('quantity_rejected'))['total'] or 0
        
        if total_produced > 0:
            return round((total_rejected / (total_produced + total_rejected)) * 100, 2)
        return 0
    except:
        return 0

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
        
        # Get production plans
        try:
            production_plans = ProductionPlan.objects.filter(company=company).order_by('-created_at')[:20]
        except:
            production_plans = []
        
        # Get work orders for Gantt chart
        try:
            work_orders = WorkOrder.objects.filter(company=company).order_by('-created_at')[:20]
        except:
            work_orders = []
        
        # Get work centers with utilization
        try:
            work_centers = WorkCenter.objects.filter(company=company)
            # Add utilization calculation if needed
            for center in work_centers:
                if not hasattr(center, 'utilization_percentage'):
                    center.utilization_percentage = 75  # Default value
        except:
            work_centers = []
        
        context = {
            'production_plans': production_plans,
            'work_orders': work_orders,
            'work_centers': work_centers,
        }
        return render(request, 'manufacturing/production-ui.html', context)
    except Exception as e:
        context = {
            'production_plans': [],
            'work_orders': [],
            'work_centers': [],
            'error': str(e)
        }
        return render(request, 'manufacturing/production-ui.html', context)

@login_required
def quality_ui(request):
    """Display quality control"""
    try:
        company = request.user.company
        
        # Get recent quality checks
        try:
            recent_quality_checks = QualityCheck.objects.filter(
                work_order__company=company
            ).select_related('work_order', 'inspector').order_by('-created_at')[:10]
        except:
            recent_quality_checks = []
        
        # Calculate quality statistics
        try:
            all_checks = QualityCheck.objects.filter(work_order__company=company)
            total_checks = all_checks.count()
            
            if total_checks > 0:
                passed_checks = all_checks.filter(status='passed').count()
                failed_checks = all_checks.filter(status='failed').count()
                
                pass_rate = (passed_checks / total_checks) * 100
                critical_defects = all_checks.filter(defect_level='critical').count()
                major_defects = all_checks.filter(defect_level='major').count()
                minor_defects = all_checks.filter(defect_level='minor').count()
                
                quality_stats = {
                    'pass_rate_percentage': round(pass_rate, 1),
                    'critical_defect_rate': round((critical_defects / total_checks) * 100, 1),
                    'major_defect_rate': round((major_defects / total_checks) * 100, 1),
                    'minor_defect_rate': round((minor_defects / total_checks) * 100, 1),
                }
            else:
                quality_stats = {
                    'pass_rate_percentage': 0,
                    'critical_defect_rate': 0,
                    'major_defect_rate': 0,
                    'minor_defect_rate': 0,
                }
        except:
            quality_stats = {
                'pass_rate_percentage': 0,
                'critical_defect_rate': 0,
                'major_defect_rate': 0,
                'minor_defect_rate': 0,
            }
        
        context = {
            'recent_quality_checks': recent_quality_checks,
            'quality_stats': quality_stats,
        }
        return render(request, 'manufacturing/quality-ui.html', context)
    except Exception as e:
        context = {
            'recent_quality_checks': [],
            'quality_stats': {
                'pass_rate_percentage': 0,
                'critical_defect_rate': 0,
                'major_defect_rate': 0,
                'minor_defect_rate': 0,
            },
            'error': str(e)
        }
        return render(request, 'manufacturing/quality-ui.html', context)

@login_required
def material_tracking_ui(request):
    """Display material tracking/consumption"""
    try:
        company = request.user.company
        
        # Get material consumptions if model exists
        try:
            material_consumptions = MaterialConsumption.objects.filter(
                work_order__company=company
            ).select_related('work_order', 'product', 'warehouse', 'consumed_by').order_by('-consumed_at')[:20]
        except:
            material_consumptions = []
        
        # Get work orders for filter
        try:
            work_orders = WorkOrder.objects.filter(company=company).order_by('-created_at')[:50]
        except:
            work_orders = []
        
        # Get products for filter
        try:
            from products.models import Product
            products = Product.objects.filter(company=company, is_active=True)[:50]
        except:
            products = []
        
        context = {
            'material_consumptions': material_consumptions,
            'work_orders': work_orders,
            'products': products,
        }
        return render(request, 'manufacturing/material_tracking.html', context)
    except Exception as e:
        context = {
            'material_consumptions': [],
            'work_orders': [],
            'products': [],
            'error': str(e)
        }
        return render(request, 'manufacturing/material_tracking.html', context)

@login_required
def job_cards_ui(request):
    """Display job cards"""
    try:
        company = request.user.company
        
        # Get job cards if model exists
        try:
            job_cards = JobCard.objects.filter(
                work_order__company=company
            ).select_related('work_order', 'employee', 'work_center').order_by('-created_at')
            
            # Apply filters
            search = request.GET.get('search')
            status = request.GET.get('status')
            employee = request.GET.get('employee')
            work_center = request.GET.get('work_center')
            
            if search:
                job_cards = job_cards.filter(
                    Q(job_card_number__icontains=search) |
                    Q(work_order__wo_number__icontains=search)
                )
            if status:
                job_cards = job_cards.filter(status=status)
            if employee:
                job_cards = job_cards.filter(employee_id=employee)
            if work_center:
                job_cards = job_cards.filter(work_center_id=work_center)
            
            # Calculate metrics
            total_cards = job_cards.count()
            in_progress_count = job_cards.filter(status='in_progress').count()
            completed_today = job_cards.filter(
                status='completed',
                end_time__date=timezone.now().date()
            ).count()
            active_employees = job_cards.filter(status='in_progress').values('employee').distinct().count()
            
            # Pagination
            from django.core.paginator import Paginator
            paginator = Paginator(job_cards, 10)
            page_number = request.GET.get('page')
            job_cards_page = paginator.get_page(page_number)
            
        except Exception as e:
            job_cards_page = []
            total_cards = in_progress_count = completed_today = active_employees = 0
        
        # Get employees for filter
        try:
            from hr.models import Employee
            employees = Employee.objects.filter(company=company, is_active=True)
        except:
            employees = []
        
        # Get work centers for filter
        try:
            work_centers = WorkCenter.objects.filter(company=company, is_active=True)
        except:
            work_centers = []
        
        context = {
            'job_cards': job_cards_page,
            'employees': employees,
            'work_centers': work_centers,
            'in_progress_count': in_progress_count,
            'completed_today': completed_today,
            'active_employees': active_employees,
        }
        return render(request, 'manufacturing/job_cards.html', context)
    except Exception as e:
        context = {
            'job_cards': [],
            'employees': [],
            'work_centers': [],
            'error': str(e)
        }
        return render(request, 'manufacturing/job_cards.html', context)

@login_required
def subcontracting_ui(request):
    """Display subcontracting orders"""
    try:
        company = request.user.company
        
        # Get subcontract work orders if model exists
        try:
            subcontract_orders = SubcontractWorkOrder.objects.filter(
                work_order__company=company
            ).select_related('work_order', 'subcontractor').order_by('-created_at')[:20]
            
            # Calculate due this week count
            from datetime import timedelta
            week_from_now = timezone.now().date() + timedelta(days=7)
            due_this_week_count = SubcontractWorkOrder.objects.filter(
                work_order__company=company,
                due_date__lte=week_from_now,
                status__in=['pending', 'in_progress']
            ).count()
        except:
            subcontract_orders = []
            due_this_week_count = 0
        
        context = {
            'subcontract_orders': subcontract_orders,
            'due_this_week_count': due_this_week_count,
        }
        return render(request, 'manufacturing/subcontracting.html', context)
    except Exception as e:
        context = {
            'subcontract_orders': [],
            'due_this_week_count': 0,
            'error': str(e)
        }
        return render(request, 'manufacturing/subcontracting.html', context)

@login_required
def reports_ui(request):
    """Display manufacturing reports and analytics"""
    try:
        company = request.user.company
        
        # Calculate basic manufacturing metrics
        total_work_orders = WorkOrder.objects.filter(company=company).count()
        completed_work_orders = WorkOrder.objects.filter(company=company, status='completed').count()
        active_work_orders = WorkOrder.objects.filter(company=company, status__in=['planned', 'released', 'in_progress']).count()
        
        # Calculate completion rate
        completion_rate = (completed_work_orders / max(1, total_work_orders)) * 100
        
        # Recent production data (sample)
        production_data = {
            'daily_production': [120, 135, 98, 156, 143, 167, 145],
            'efficiency_trend': [87, 89, 85, 91, 88, 93, 90],
            'quality_rates': [94, 96, 93, 97, 95, 98, 96]
        }
        
        context = {
            'total_work_orders': total_work_orders,
            'completed_work_orders': completed_work_orders,
            'active_work_orders': active_work_orders,
            'completion_rate': round(completion_rate, 1),
            'production_data': production_data,
        }
        return render(request, 'manufacturing/reports.html', context)
    except Exception as e:
        context = {
            'total_work_orders': 0,
            'completed_work_orders': 0,
            'active_work_orders': 0,
            'completion_rate': 0,
            'production_data': {},
            'error': str(e)
        }
        return render(request, 'manufacturing/reports.html', context)

@login_required
def settings_ui(request):
    """Display manufacturing settings"""
    try:
        company = request.user.company
        
        # Get work centers for settings dropdowns
        try:
            work_centers = WorkCenter.objects.filter(company=company)
            work_centers_count = work_centers.count()
        except:
            work_centers = []
            work_centers_count = 0
        
        context = {
            'work_centers_count': work_centers_count,
            'work_centers': work_centers,
        }
        return render(request, 'manufacturing/settings.html', context)
    except Exception as e:
        context = {
            'work_centers_count': 0,
            'work_centers': [],
            'error': str(e)
        }
        return render(request, 'manufacturing/settings.html', context)

@login_required
def work_center_create(request):
    """Create a new work center"""
    if request.method == 'POST':
        try:
            company = request.user.company
            
            # Get form data
            name = request.POST.get('name')
            location = request.POST.get('location', '')
            capacity_per_hour = request.POST.get('capacity_per_hour', 1)
            operating_hours_per_day = request.POST.get('operating_hours_per_day', 8)
            description = request.POST.get('description', '')
            
            # Generate unique code
            code = f"WC-{WorkCenter.objects.filter(company=company).count() + 1:03d}"
            
            # Create work center
            work_center = WorkCenter.objects.create(
                company=company,
                name=name,
                code=code,
                description=description,
                capacity_per_hour=capacity_per_hour,
                operating_hours_per_day=operating_hours_per_day
            )
            
            # Add location as custom field if provided
            if location:
                work_center.location = location
                work_center.save()
            
            messages.success(request, f'Work Center "{name}" created successfully!')
            return redirect('manufacturing:work_centers_ui')
            
        except Exception as e:
            messages.error(request, f'Error creating work center: {str(e)}')
            return redirect('manufacturing:work_centers_ui')
    
    return redirect('manufacturing:work_centers_ui')

@login_required
def work_center_detail(request, pk):
    """View work center details"""
    try:
        company = request.user.company
        work_center = get_object_or_404(WorkCenter, pk=pk, company=company)
        
        # Get related data
        active_operations = work_center.work_order_operations.filter(status='in_progress')
        recent_operations = work_center.work_order_operations.order_by('-created_at')[:10]
        
        context = {
            'work_center': work_center,
            'active_operations': active_operations,
            'recent_operations': recent_operations,
        }
        return render(request, 'manufacturing/work_center_detail.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading work center: {str(e)}')
        return redirect('manufacturing:work_centers_ui')

@login_required
def work_center_edit(request, pk):
    """Edit work center"""
    try:
        company = request.user.company
        work_center = get_object_or_404(WorkCenter, pk=pk, company=company)
        
        if request.method == 'POST':
            # Update work center
            work_center.name = request.POST.get('name', work_center.name)
            work_center.description = request.POST.get('description', work_center.description)
            work_center.capacity_per_hour = request.POST.get('capacity_per_hour', work_center.capacity_per_hour)
            work_center.operating_hours_per_day = request.POST.get('operating_hours_per_day', work_center.operating_hours_per_day)
            work_center.save()
            
            messages.success(request, f'Work Center "{work_center.name}" updated successfully!')
            return redirect('manufacturing:work_center_detail', pk=work_center.pk)
        
        context = {
            'work_center': work_center,
        }
        return render(request, 'manufacturing/work_center_edit.html', context)
        
    except Exception as e:
        messages.error(request, f'Error editing work center: {str(e)}')
        return redirect('manufacturing:work_centers_ui')

@login_required
def work_center_manage(request, pk):
    """Manage work center operations and scheduling"""
    try:
        company = request.user.company
        work_center = get_object_or_404(WorkCenter, pk=pk, company=company)
        
        # Get current operations and scheduling data
        active_operations = work_center.work_order_operations.filter(status='in_progress')
        pending_operations = work_center.work_order_operations.filter(status='pending')
        
        context = {
            'work_center': work_center,
            'active_operations': active_operations,
            'pending_operations': pending_operations,
        }
        return render(request, 'manufacturing/work_center_manage.html', context)
        
    except Exception as e:
        messages.error(request, f'Error managing work center: {str(e)}')
        return redirect('manufacturing:work_centers_ui')

@login_required
def work_order_create(request):
    """Create a new work order"""
    if request.method == 'POST':
        try:
            company = request.user.company
            
            # Get form data
            product_id = request.POST.get('product')
            quantity = request.POST.get('quantity')
            priority = request.POST.get('priority', 'medium')
            planned_start = request.POST.get('planned_start')
            planned_end = request.POST.get('planned_end')
            description = request.POST.get('description', '')
            
            # Validate required fields
            if not product_id or not quantity:
                messages.error(request, 'Product and quantity are required')
                return redirect('manufacturing:work_order_create')
            
            # Get product
            from products.models import Product
            product = get_object_or_404(Product, id=product_id, company=company)
            
            # Generate work order number
            wo_count = WorkOrder.objects.filter(company=company).count()
            wo_number = f"WO-{timezone.now().year}-{wo_count + 1:03d}"
            
            # Create work order
            work_order = WorkOrder.objects.create(
                company=company,
                wo_number=wo_number,
                product=product,
                quantity=quantity,
                priority=priority,
                planned_start=planned_start if planned_start else None,
                planned_end=planned_end if planned_end else None,
                description=description,
                status='planned'
            )
            
            messages.success(request, f'Work Order {wo_number} created successfully!')
            return redirect('manufacturing:work_order_detail', wo_id=work_order.id)
            
        except Exception as e:
            messages.error(request, f'Error creating work order: {str(e)}')
    
    try:
        company = request.user.company
        from products.models import Product
        products = Product.objects.filter(company=company, is_active=True)
        
        context = {
            'products': products,
        }
        return render(request, 'manufacturing/work_order_create.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading form: {str(e)}')
        return redirect('manufacturing:work_orders_ui')

@login_required  
def work_order_edit(request, wo_id):
    """Edit a work order"""
    try:
        company = request.user.company
        work_order = get_object_or_404(WorkOrder, id=wo_id, company=company)
        
        if request.method == 'POST':
            # Update work order
            product_id = request.POST.get('product')
            if product_id:
                from products.models import Product
                product = get_object_or_404(Product, id=product_id, company=company)
                work_order.product = product
            
            work_order.quantity = request.POST.get('quantity', work_order.quantity)
            work_order.priority = request.POST.get('priority', work_order.priority)
            work_order.planned_start = request.POST.get('planned_start') or work_order.planned_start
            work_order.planned_end = request.POST.get('planned_end') or work_order.planned_end
            work_order.description = request.POST.get('description', work_order.description)
            work_order.save()
            
            messages.success(request, f'Work Order {work_order.wo_number} updated successfully!')
            return redirect('manufacturing:work_order_detail', wo_id=work_order.id)
        
        try:
            from products.models import Product
            products = Product.objects.filter(company=company, is_active=True)
        except:
            products = []
        
        context = {
            'work_order': work_order,
            'products': products,
        }
        return render(request, 'manufacturing/work_order_edit.html', context)
        
    except Exception as e:
        messages.error(request, f'Error editing work order: {str(e)}')
        return redirect('manufacturing:work_orders_ui')


@login_required
def production_plan_create(request):
    """Create a new production plan"""
    try:
        company = request.user.company
        
        if request.method == 'POST':
            name = request.POST.get('name')
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            plan_type = request.POST.get('plan_type', 'forecast')
            consider_capacity = request.POST.get('consider_capacity') == 'on'
            consider_lead_times = request.POST.get('consider_lead_times') == 'on'
            auto_create_work_orders = request.POST.get('auto_create_work_orders') == 'on'
            notes = request.POST.get('notes', '')
            
            if not all([name, start_date, end_date]):
                messages.error(request, 'Please fill in all required fields.')
                return redirect('manufacturing:production_plan_create')
            
            production_plan = ProductionPlan.objects.create(
                company=company,
                name=name,
                start_date=start_date,
                end_date=end_date,
                plan_type=plan_type,
                consider_capacity=consider_capacity,
                consider_lead_times=consider_lead_times,
                auto_create_work_orders=auto_create_work_orders,
                notes=notes,
                created_by=request.user
            )
            
            messages.success(request, f'Production Plan "{name}" created successfully!')
            return redirect('manufacturing:production_plan_detail', plan_id=production_plan.id)
        
        context = {
            'plan_types': ProductionPlan.PLAN_TYPE_CHOICES,
        }
        return render(request, 'manufacturing/production_plan_create.html', context)
        
    except Exception as e:
        messages.error(request, f'Error creating production plan: {str(e)}')
        return redirect('manufacturing:production_plans_ui')


@login_required
def production_plan_edit(request, plan_id):
    """Edit an existing production plan"""
    try:
        company = request.user.company
        production_plan = get_object_or_404(ProductionPlan, id=plan_id, company=company)
        
        if request.method == 'POST':
            production_plan.name = request.POST.get('name', production_plan.name)
            production_plan.start_date = request.POST.get('start_date') or production_plan.start_date
            production_plan.end_date = request.POST.get('end_date') or production_plan.end_date
            production_plan.plan_type = request.POST.get('plan_type', production_plan.plan_type)
            production_plan.status = request.POST.get('status', production_plan.status)
            production_plan.consider_capacity = request.POST.get('consider_capacity') == 'on'
            production_plan.consider_lead_times = request.POST.get('consider_lead_times') == 'on'
            production_plan.auto_create_work_orders = request.POST.get('auto_create_work_orders') == 'on'
            production_plan.notes = request.POST.get('notes', production_plan.notes)
            production_plan.save()
            
            messages.success(request, f'Production Plan "{production_plan.name}" updated successfully!')
            return redirect('manufacturing:production_plan_detail', plan_id=production_plan.id)
        
        context = {
            'production_plan': production_plan,
            'plan_types': ProductionPlan.PLAN_TYPE_CHOICES,
            'status_choices': ProductionPlan.STATUS_CHOICES,
        }
        return render(request, 'manufacturing/production_plan_edit.html', context)
        
    except Exception as e:
        messages.error(request, f'Error editing production plan: {str(e)}')
        return redirect('manufacturing:production_plans_ui')


@login_required  
def production_plan_detail(request, plan_id):
    """View production plan details"""
    try:
        company = request.user.company
        production_plan = get_object_or_404(ProductionPlan, id=plan_id, company=company)
        
        # Get plan items with related data
        plan_items = production_plan.items.select_related('product').all()
        
        # Calculate summary statistics
        total_items = plan_items.count()
        total_planned_quantity = plan_items.aggregate(Sum('planned_quantity'))['planned_quantity__sum'] or 0
        total_produced_quantity = plan_items.aggregate(Sum('produced_quantity'))['produced_quantity__sum'] or 0
        
        context = {
            'production_plan': production_plan,
            'plan_items': plan_items,
            'total_items': total_items,
            'total_planned_quantity': total_planned_quantity,
            'total_produced_quantity': total_produced_quantity,
            'completion_percentage': (total_produced_quantity / total_planned_quantity * 100) if total_planned_quantity > 0 else 0,
        }
        return render(request, 'manufacturing/production_plan_detail.html', context)
        
    except Exception as e:
        messages.error(request, f'Error viewing production plan: {str(e)}')
        return redirect('manufacturing:production_plans_ui')


# MRP Views
@login_required
def mrp_plan_list(request):
    """List all MRP plans"""
    try:
        company = request.user.company
        plans = MRPPlan.objects.filter(company=company).order_by('-created_at')
        
        # Pagination
        paginator = Paginator(plans, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'plans': page_obj,
            'total_plans': plans.count(),
        }
        return render(request, 'manufacturing/mrp_plan_list.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading MRP plans: {str(e)}')
        return redirect('manufacturing:mrp_ui')


@login_required
def mrp_plan_create(request):
    """Create a new MRP plan"""
    if request.method == 'POST':
        try:
            company = request.user.company
            
            # Create MRP plan
            plan = MRPPlan.objects.create(
                company=company,
                name=request.POST.get('name'),
                plan_date=request.POST.get('plan_date') or timezone.now().date(),
                planning_horizon_days=int(request.POST.get('planning_horizon_days', 90)),
                include_safety_stock=request.POST.get('include_safety_stock') == 'on',
                include_reorder_points=request.POST.get('include_reorder_points') == 'on',
                consider_lead_times=request.POST.get('consider_lead_times') == 'on',
                auto_create_purchase_requests=request.POST.get('auto_create_purchase_requests') == 'on',
                description=request.POST.get('description', ''),
                created_by=request.user,
                status='draft'
            )
            
            messages.success(request, f'MRP Plan "{plan.name}" created successfully!')
            return redirect('manufacturing:mrp_plan_detail', plan_id=plan.id)
            
        except Exception as e:
            messages.error(request, f'Error creating MRP plan: {str(e)}')
    
    context = {
        'today': timezone.now().date(),
    }
    return render(request, 'manufacturing/mrp_plan_create.html', context)


@login_required
def mrp_plan_detail(request, plan_id):
    """View MRP plan details"""
    try:
        company = request.user.company
        plan = get_object_or_404(MRPPlan, id=plan_id, company=company)
        
        # Get requirements
        requirements = plan.requirements.select_related('product').order_by('required_date', 'product__name')
        
        # Summary statistics
        total_requirements = requirements.count()
        total_shortage_value = requirements.aggregate(
            total=Sum('shortage_quantity')
        )['total'] or Decimal('0')
        
        pending_requirements = requirements.filter(status='pending').count()
        
        context = {
            'plan': plan,
            'requirements': requirements,
            'total_requirements': total_requirements,
            'total_shortage_value': total_shortage_value,
            'pending_requirements': pending_requirements,
        }
        return render(request, 'manufacturing/mrp_plan_detail.html', context)
        
    except Exception as e:
        messages.error(request, f'Error viewing MRP plan: {str(e)}')
        return redirect('manufacturing:mrp_plan_list')


@login_required
def mrp_requirement_list(request):
    """List all MRP requirements"""
    try:
        company = request.user.company
        
        # Get latest MRP plan or filter by plan_id
        plan_id = request.GET.get('plan_id')
        if plan_id:
            requirements = MRPRequirement.objects.filter(
                mrp_plan__company=company,
                mrp_plan_id=plan_id
            ).select_related('product', 'mrp_plan')
        else:
            # Get requirements from the latest plan
            latest_plan = MRPPlan.objects.filter(
                company=company,
                status='completed'
            ).order_by('-created_at').first()
            
            if latest_plan:
                requirements = latest_plan.requirements.select_related('product')
            else:
                requirements = MRPRequirement.objects.none()
        
        # Filter options
        status_filter = request.GET.get('status')
        if status_filter:
            requirements = requirements.filter(status=status_filter)
        
        source_type_filter = request.GET.get('source_type')
        if source_type_filter:
            requirements = requirements.filter(source_type=source_type_filter)
        
        # Pagination
        paginator = Paginator(requirements, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Get available plans for filter
        available_plans = MRPPlan.objects.filter(company=company).order_by('-created_at')[:10]
        
        context = {
            'requirements': page_obj,
            'available_plans': available_plans,
            'current_plan_id': plan_id,
            'status_filter': status_filter,
            'source_type_filter': source_type_filter,
        }
        return render(request, 'manufacturing/mrp_requirement_list.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading MRP requirements: {str(e)}')
        return redirect('manufacturing:mrp_ui')


@login_required
def demand_forecast_list(request):
    """List demand forecasts"""
    try:
        company = request.user.company
        forecasts = DemandForecast.objects.filter(company=company).select_related('product').order_by('-forecast_date')
        
        # Filter by product
        product_filter = request.GET.get('product')
        if product_filter:
            forecasts = forecasts.filter(product_id=product_filter)
        
        # Filter by date range
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        if start_date:
            forecasts = forecasts.filter(forecast_date__gte=start_date)
        if end_date:
            forecasts = forecasts.filter(forecast_date__lte=end_date)
        
        # Pagination
        paginator = Paginator(forecasts, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Get products for filter
        products = Product.objects.filter(company=company).order_by('name')
        
        context = {
            'forecasts': page_obj,
            'products': products,
            'product_filter': product_filter,
            'start_date': start_date,
            'end_date': end_date,
        }
        return render(request, 'manufacturing/demand_forecast_list.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading demand forecasts: {str(e)}')
        return redirect('manufacturing:mrp_ui')


@login_required
def supplier_lead_time_list(request):
    """List supplier lead times"""
    try:
        company = request.user.company
        lead_times = SupplierLeadTime.objects.filter(company=company).select_related('product', 'supplier').order_by('product__name')
        
        # Filter by product
        product_filter = request.GET.get('product')
        if product_filter:
            lead_times = lead_times.filter(product_id=product_filter)
        
        # Filter by supplier
        supplier_filter = request.GET.get('supplier')
        if supplier_filter:
            lead_times = lead_times.filter(supplier_id=supplier_filter)
        
        # Pagination
        paginator = Paginator(lead_times, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Get products and suppliers for filters
        products = Product.objects.filter(company=company).order_by('name')
        from crm.models import Partner
        suppliers = Partner.objects.filter(company=company, is_supplier=True).order_by('name')
        
        context = {
            'lead_times': page_obj,
            'products': products,
            'suppliers': suppliers,
            'product_filter': product_filter,
            'supplier_filter': supplier_filter,
        }
        return render(request, 'manufacturing/supplier_lead_time_list.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading supplier lead times: {str(e)}')
        return redirect('manufacturing:mrp_ui')


@login_required
def reorder_rules_list(request):
    """List reorder rules"""
    try:
        company = request.user.company
        reorder_rules = ReorderRule.objects.filter(company=company).select_related('product', 'warehouse').order_by('product__name')
        
        # Filter by product
        product_filter = request.GET.get('product')
        if product_filter:
            reorder_rules = reorder_rules.filter(product_id=product_filter)
        
        # Filter by warehouse
        warehouse_filter = request.GET.get('warehouse')
        if warehouse_filter:
            reorder_rules = reorder_rules.filter(warehouse_id=warehouse_filter)
        
        # Filter by active status
        active_filter = request.GET.get('active')
        if active_filter:
            reorder_rules = reorder_rules.filter(is_active=active_filter == 'true')
        
        # Pagination
        paginator = Paginator(reorder_rules, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Get products and warehouses for filters
        products = Product.objects.filter(company=company).order_by('name')
        warehouses = Warehouse.objects.filter(company=company).order_by('name')
        
        context = {
            'reorder_rules': page_obj,
            'products': products,
            'warehouses': warehouses,
            'product_filter': product_filter,
            'warehouse_filter': warehouse_filter,
            'active_filter': active_filter,
        }
        return render(request, 'manufacturing/reorder_rules_list.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading reorder rules: {str(e)}')
        return redirect('manufacturing:mrp_ui')
