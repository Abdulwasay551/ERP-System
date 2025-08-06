# MRP Engine Implementation for Manufacturing Module

from datetime import datetime, timedelta
from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from collections import defaultdict, OrderedDict

from .models import (
    MRPPlan, MRPRequirement, BillOfMaterials, BillOfMaterialsItem,
    WorkOrder, ProductionPlan, ProductionPlanItem
)
from inventory.models import StockItem
from sales.models import SalesOrder, SalesOrderItem
from purchase.models import PurchaseRequest, PurchaseRequestItem
from products.models import Product


class MRPEngine:
    """
    Material Requirements Planning Engine
    Implements the core MRP calculation logic based on:
    - Sales Orders (actual demand)
    - Forecasts (expected demand) 
    - Current inventory levels
    - Bill of Materials
    - Lead times
    - Safety stock and reorder points
    """
    
    def __init__(self, mrp_plan):
        self.mrp_plan = mrp_plan
        self.company = mrp_plan.company
        self.planning_horizon = mrp_plan.planning_horizon_days
        self.end_date = mrp_plan.plan_date + timedelta(days=self.planning_horizon)
        
        # Data structures for calculations
        self.gross_requirements = defaultdict(lambda: defaultdict(Decimal))
        self.scheduled_receipts = defaultdict(lambda: defaultdict(Decimal))
        self.projected_on_hand = defaultdict(lambda: defaultdict(Decimal))
        self.net_requirements = defaultdict(lambda: defaultdict(Decimal))
        self.planned_orders = defaultdict(lambda: defaultdict(Decimal))
        
    def run_mrp_calculation(self):
        """
        Main MRP calculation method
        """
        try:
            with transaction.atomic():
                # Step 1: Clear existing requirements
                self.mrp_plan.requirements.all().delete()
                
                # Step 2: Initialize data
                self._initialize_data()
                
                # Step 3: Calculate gross requirements from demand
                self._calculate_gross_requirements()
                
                # Step 4: Calculate scheduled receipts
                self._calculate_scheduled_receipts()
                
                # Step 5: Run MRP logic for each product
                self._run_mrp_logic()
                
                # Step 6: Create MRP requirements records
                self._create_mrp_requirements()
                
                # Step 7: Generate purchase requests if needed
                if hasattr(self.mrp_plan, 'auto_create_purchase_requests') and self.mrp_plan.auto_create_purchase_requests:
                    self._generate_purchase_requests()
                
                return True
                
        except Exception as e:
            raise Exception(f"MRP Calculation failed: {str(e)}")
    
    def _initialize_data(self):
        """Initialize inventory and product data"""
        # Get all products that have BOMs or are used in BOMs
        products_with_boms = Product.objects.filter(
            company=self.company,
            boms__is_active=True
        ).distinct()
        
        # Get all component products from BOMs
        component_products = Product.objects.filter(
            company=self.company,
            bom_components__bom__company=self.company,
            bom_components__bom__is_active=True
        ).distinct()
        
        # Combine and get unique products
        self.products = (products_with_boms | component_products).distinct()
        
        # Initialize current inventory levels
        for product in self.products:
            try:
                stock_item = StockItem.objects.get(
                    product=product,
                    warehouse__company=self.company
                )
                current_stock = stock_item.available_quantity
                safety_stock = stock_item.safety_stock or Decimal('0')
                
                # Initialize projected on hand with current stock
                self.projected_on_hand[product.id][self.mrp_plan.plan_date] = current_stock
                
                # Store safety stock for later use
                setattr(product, '_safety_stock', safety_stock)
                setattr(product, '_current_stock', current_stock)
                
            except StockItem.DoesNotExist:
                self.projected_on_hand[product.id][self.mrp_plan.plan_date] = Decimal('0')
                setattr(product, '_safety_stock', Decimal('0'))
                setattr(product, '_current_stock', Decimal('0'))
    
    def _calculate_gross_requirements(self):
        """Calculate gross requirements from sales orders and forecasts"""
        
        # 1. From Sales Orders
        sales_orders = SalesOrder.objects.filter(
            company=self.company,
            status__in=['confirmed', 'partial'],
            delivery_date__gte=self.mrp_plan.plan_date,
            delivery_date__lte=self.end_date
        )
        
        for so in sales_orders:
            for item in so.items.all():
                product = item.product
                required_date = so.delivery_date
                quantity = item.quantity - (item.delivered_quantity or Decimal('0'))
                
                if quantity > 0:
                    self.gross_requirements[product.id][required_date] += quantity
        
        # 2. From Production Plans (if any)
        production_plans = ProductionPlan.objects.filter(
            company=self.company,
            status__in=['approved', 'in_progress'],
            start_date__lte=self.end_date,
            end_date__gte=self.mrp_plan.plan_date
        )
        
        for plan in production_plans:
            for item in plan.items.all():
                product = item.product
                required_date = item.planned_end_date
                quantity = item.remaining_quantity
                
                if quantity > 0:
                    self.gross_requirements[product.id][required_date] += quantity
        
        # 3. From Forecasts (placeholder - implement when forecast model exists)
        # TODO: Add forecast-based demand calculation
        
    def _calculate_scheduled_receipts(self):
        """Calculate scheduled receipts from existing orders"""
        
        # 1. From Work Orders
        work_orders = WorkOrder.objects.filter(
            company=self.company,
            status__in=['planned', 'released', 'in_progress'],
            scheduled_end__gte=self.mrp_plan.plan_date,
            scheduled_end__lte=self.end_date
        )
        
        for wo in work_orders:
            product = wo.product
            receipt_date = wo.scheduled_end.date() if wo.scheduled_end else self.mrp_plan.plan_date
            quantity = wo.quantity_remaining
            
            if quantity > 0:
                self.scheduled_receipts[product.id][receipt_date] += quantity
        
        # 2. From Purchase Orders (if integrated)
        # TODO: Add purchase order scheduled receipts
        
    def _run_mrp_logic(self):
        """Run the main MRP logic for each product"""
        
        # Process products in order (finished goods first, then components)
        products_by_level = self._get_products_by_bom_level()
        
        for level in sorted(products_by_level.keys(), reverse=True):
            for product in products_by_level[level]:
                self._calculate_product_requirements(product)
    
    def _get_products_by_bom_level(self):
        """Organize products by BOM level (0=finished goods, higher=components)"""
        products_by_level = defaultdict(list)
        
        for product in self.products:
            # Simple level calculation - can be enhanced
            level = 0
            if product.boms.filter(is_active=True).exists():
                level = 1  # Has BOM, so it's manufactured
            
            # Check if it's used as a component (higher level)
            if product.bom_components.exists():
                level = max(level, 0)  # Component level
            
            products_by_level[level].append(product)
        
        return products_by_level
    
    def _calculate_product_requirements(self, product):
        """Calculate requirements for a specific product using MRP logic"""
        
        # Get all dates we need to consider
        requirement_dates = set()
        requirement_dates.update(self.gross_requirements[product.id].keys())
        requirement_dates.update(self.scheduled_receipts[product.id].keys())
        
        # Sort dates chronologically
        sorted_dates = sorted(requirement_dates) if requirement_dates else []
        
        if not sorted_dates:
            return
        
        # Initialize projected on hand
        current_poh = getattr(product, '_current_stock', Decimal('0'))
        safety_stock = getattr(product, '_safety_stock', Decimal('0'))
        
        for date in sorted_dates:
            # Calculate projected on hand for this period
            gross_req = self.gross_requirements[product.id][date]
            scheduled_receipt = self.scheduled_receipts[product.id][date]
            
            # Previous period's projected on hand
            previous_poh = current_poh
            
            # Calculate new projected on hand
            current_poh = previous_poh + scheduled_receipt - gross_req
            self.projected_on_hand[product.id][date] = current_poh
            
            # Check if net requirement is needed
            if current_poh < safety_stock:
                net_req = safety_stock - current_poh + gross_req
                self.net_requirements[product.id][date] = net_req
                
                # Calculate planned order
                planned_order_qty = net_req
                planned_order_date = self._calculate_planned_order_date(product, date)
                
                self.planned_orders[product.id][planned_order_date] = planned_order_qty
                
                # Add to scheduled receipts for next iteration
                self.scheduled_receipts[product.id][date] += planned_order_qty
                
                # Explode BOM if this is a manufactured item
                self._explode_bom(product, planned_order_qty, planned_order_date)
    
    def _calculate_planned_order_date(self, product, required_date):
        """Calculate when to start the planned order based on lead time"""
        # Get lead time from various sources
        lead_time_days = 0
        
        # From BOM
        bom = product.boms.filter(is_active=True, is_default=True).first()
        if bom:
            lead_time_days = bom.lead_time_days
        
        # From stock item
        try:
            stock_item = StockItem.objects.get(product=product, warehouse__company=self.company)
            if stock_item.lead_time_days:
                lead_time_days = max(lead_time_days, stock_item.lead_time_days)
        except StockItem.DoesNotExist:
            pass
        
        # Calculate planned order date
        planned_date = required_date - timedelta(days=lead_time_days)
        
        # Ensure it's not in the past
        return max(planned_date, self.mrp_plan.plan_date)
    
    def _explode_bom(self, product, quantity, order_date):
        """Explode BOM to create gross requirements for components"""
        
        bom = product.boms.filter(is_active=True, is_default=True).first()
        if not bom:
            return
        
        for bom_item in bom.items.all():
            component = bom_item.component
            component_qty = bom_item.effective_quantity * quantity
            
            # Add to gross requirements for the component
            self.gross_requirements[component.id][order_date] += component_qty
    
    def _create_mrp_requirements(self):
        """Create MRPRequirement records from calculated data"""
        
        for product_id, dates_dict in self.net_requirements.items():
            try:
                product = Product.objects.get(id=product_id)
                
                for required_date, quantity in dates_dict.items():
                    if quantity > 0:
                        # Determine source type
                        source_type = 'purchase'
                        bom = product.boms.filter(is_active=True, is_default=True).first()
                        if bom:
                            source_type = 'manufacture'
                        
                        # Calculate suggested order date
                        if product_id in self.planned_orders:
                            order_dates = [d for d, q in self.planned_orders[product_id].items() if q > 0]
                            suggested_order_date = min(order_dates) if order_dates else required_date
                        else:
                            suggested_order_date = required_date
                        
                        # Get current stock
                        available_qty = getattr(product, '_current_stock', Decimal('0'))
                        
                        MRPRequirement.objects.create(
                            mrp_plan=self.mrp_plan,
                            product=product,
                            required_quantity=quantity,
                            available_quantity=available_qty,
                            shortage_quantity=max(Decimal('0'), quantity - available_qty),
                            required_date=required_date,
                            suggested_order_date=suggested_order_date,
                            source_type=source_type,
                            status='pending'
                        )
                        
            except Product.DoesNotExist:
                continue
    
    def _generate_purchase_requests(self):
        """Generate purchase requests for items that need to be purchased"""
        
        purchase_requirements = self.mrp_plan.requirements.filter(
            source_type='purchase',
            status='pending'
        )
        
        if not purchase_requirements.exists():
            return
        
        # Group by suggested order date
        reqs_by_date = defaultdict(list)
        for req in purchase_requirements:
            reqs_by_date[req.suggested_order_date].append(req)
        
        for order_date, requirements in reqs_by_date.items():
            # Create a purchase request
            pr = PurchaseRequest.objects.create(
                company=self.company,
                title=f"MRP Generated PR - {order_date}",
                description=f"Auto-generated from MRP Plan: {self.mrp_plan.name}",
                priority='normal',
                required_date=order_date,
                created_by=self.mrp_plan.created_by,
                status='draft'
            )
            
            # Add items to purchase request
            for req in requirements:
                PurchaseRequestItem.objects.create(
                    purchase_request=pr,
                    product=req.product,
                    description=req.product.description or req.product.name,
                    quantity=req.shortage_quantity,
                    estimated_cost=Decimal('0'),  # Could be enhanced with product cost
                    priority='normal'
                )
                
                # Link the requirement to the purchase request
                req.status = 'ordered'
                req.notes = f"Purchase Request created: {pr.title}"
                req.save()


class SupplyDemandAnalyzer:
    """
    Analyzes supply and demand across all products
    Provides insights for planning and decision making
    """
    
    def __init__(self, company, start_date=None, end_date=None):
        self.company = company
        self.start_date = start_date or timezone.now().date()
        self.end_date = end_date or (self.start_date + timedelta(days=90))
    
    def generate_supply_demand_report(self):
        """Generate comprehensive supply-demand analysis"""
        
        report_data = []
        
        products = Product.objects.filter(company=self.company)
        
        for product in products:
            # Current stock
            try:
                stock_item = StockItem.objects.get(
                    product=product,
                    warehouse__company=self.company
                )
                current_stock = stock_item.available_quantity
                safety_stock = stock_item.safety_stock or Decimal('0')
                reorder_point = stock_item.reorder_point or Decimal('0')
            except StockItem.DoesNotExist:
                current_stock = Decimal('0')
                safety_stock = Decimal('0')
                reorder_point = Decimal('0')
            
            # Demand calculation
            demand_qty = self._calculate_total_demand(product)
            
            # Supply calculation  
            supply_qty = self._calculate_total_supply(product)
            
            # Net requirement
            net_qty = demand_qty - supply_qty - current_stock
            
            # Status determination
            status = 'OK'
            if current_stock <= reorder_point:
                status = 'Reorder Required'
            elif current_stock <= safety_stock:
                status = 'Below Safety Stock'
            elif net_qty > 0:
                status = 'Shortage Expected'
            elif current_stock > stock_item.max_stock if hasattr(stock_item, 'max_stock') and stock_item.max_stock > 0 else False:
                status = 'Overstock'
            
            report_data.append({
                'product': product,
                'current_stock': current_stock,
                'safety_stock': safety_stock,
                'reorder_point': reorder_point,
                'total_demand': demand_qty,
                'total_supply': supply_qty,
                'net_requirement': net_qty,
                'status': status,
                'days_of_stock': self._calculate_days_of_stock(current_stock, demand_qty)
            })
        
        return report_data
    
    def _calculate_total_demand(self, product):
        """Calculate total demand for a product in the planning horizon"""
        
        demand = Decimal('0')
        
        # From sales orders
        so_items = SalesOrderItem.objects.filter(
            sales_order__company=self.company,
            product=product,
            sales_order__delivery_date__gte=self.start_date,
            sales_order__delivery_date__lte=self.end_date,
            sales_order__status__in=['confirmed', 'partial']
        )
        
        for item in so_items:
            remaining = item.quantity - (item.delivered_quantity or Decimal('0'))
            demand += max(Decimal('0'), remaining)
        
        # From production requirements (BOM explosion)
        # TODO: Add BOM explosion demand
        
        return demand
    
    def _calculate_total_supply(self, product):
        """Calculate total supply for a product in the planning horizon"""
        
        supply = Decimal('0')
        
        # From work orders
        work_orders = WorkOrder.objects.filter(
            company=self.company,
            product=product,
            status__in=['planned', 'released', 'in_progress'],
            scheduled_end__gte=self.start_date,
            scheduled_end__lte=self.end_date
        )
        
        for wo in work_orders:
            supply += wo.quantity_remaining
        
        # From purchase orders (if integrated)
        # TODO: Add purchase order supply
        
        return supply
    
    def _calculate_days_of_stock(self, current_stock, daily_demand):
        """Calculate how many days current stock will last"""
        
        if daily_demand <= 0:
            return float('inf')
        
        # Estimate daily demand over planning horizon
        planning_days = (self.end_date - self.start_date).days
        if planning_days > 0:
            daily_demand_avg = daily_demand / planning_days
            if daily_demand_avg > 0:
                return float(current_stock / daily_demand_avg)
        
        return float('inf')


# Utility functions for MRP configuration and automation

def create_automatic_mrp_plan(company, name=None):
    """Create an automatic MRP plan"""
    
    if not name:
        name = f"Auto MRP - {timezone.now().strftime('%Y-%m-%d')}"
    
    mrp_plan = MRPPlan.objects.create(
        company=company,
        name=name,
        plan_date=timezone.now().date(),
        planning_horizon_days=90,
        status='draft',
        include_safety_stock=True,
        include_reorder_points=True,
        consider_lead_times=True
    )
    
    return mrp_plan


def run_automatic_mrp(company):
    """Run automatic MRP for a company"""
    
    try:
        # Create or get today's MRP plan
        today = timezone.now().date()
        mrp_plan, created = MRPPlan.objects.get_or_create(
            company=company,
            plan_date=today,
            defaults={
                'name': f"Auto MRP - {today}",
                'planning_horizon_days': 90,
                'status': 'draft',
                'include_safety_stock': True,
                'include_reorder_points': True,
                'consider_lead_times': True
            }
        )
        
        if mrp_plan.status == 'completed':
            return mrp_plan, "MRP already completed for today"
        
        # Run MRP calculation
        mrp_plan.status = 'calculating'
        mrp_plan.calculation_start = timezone.now()
        mrp_plan.save()
        
        engine = MRPEngine(mrp_plan)
        success = engine.run_mrp_calculation()
        
        if success:
            mrp_plan.status = 'completed'
            mrp_plan.calculation_end = timezone.now()
            mrp_plan.save()
            return mrp_plan, "MRP calculation completed successfully"
        else:
            mrp_plan.status = 'draft'
            mrp_plan.save()
            return mrp_plan, "MRP calculation failed"
            
    except Exception as e:
        if 'mrp_plan' in locals():
            mrp_plan.status = 'draft'
            mrp_plan.save()
        raise Exception(f"Automatic MRP failed: {str(e)}")
