from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from django.db import models
from django.http import JsonResponse, HttpResponse
import csv
from .models import ProductCategory, StockItem, StockMovement, Warehouse, StockAlert, StockAdjustment, StockAdjustmentItem
from .serializers import ProductCategorySerializer, StockItemSerializer, StockMovementSerializer, WarehouseSerializer, StockAlertSerializer

class ProductCategoryViewSet(viewsets.ModelViewSet):
    serializer_class = ProductCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return ProductCategory.objects.filter(company=self.request.user.company)

class WarehouseViewSet(viewsets.ModelViewSet):
    serializer_class = WarehouseSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Warehouse.objects.filter(company=self.request.user.company)

class StockItemViewSet(viewsets.ModelViewSet):
    serializer_class = StockItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return StockItem.objects.filter(company=self.request.user.company)

class StockMovementViewSet(viewsets.ModelViewSet):
    serializer_class = StockMovementSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return StockMovement.objects.filter(company=self.request.user.company)

class StockAlertViewSet(viewsets.ModelViewSet):
    serializer_class = StockAlertSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return StockAlert.objects.filter(company=self.request.user.company)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def quick_restock(request, item_id):
    """Quick restock functionality for stock alerts"""
    try:
        stock_item = get_object_or_404(StockItem, id=item_id, company=request.user.company)
        quantity = float(request.POST.get('quantity', 0))
        reason = request.POST.get('reason', 'Quick restock from alerts')
        
        if quantity <= 0:
            return JsonResponse({'error': 'Invalid quantity'}, status=400)
        
        with transaction.atomic():
            # Create stock adjustment
            adjustment = StockAdjustment.objects.create(
                company=request.user.company,
                reference=f"QR-{timezone.now().strftime('%Y%m%d-%H%M%S')}",
                adjustment_type='increase',
                reason=reason,
                created_by=request.user,
                status='posted'
            )
            
            # Create adjustment item
            StockAdjustmentItem.objects.create(
                adjustment=adjustment,
                stock_item=stock_item,
                quantity_before=stock_item.quantity,
                adjustment_quantity=quantity,
                quantity_after=stock_item.quantity + quantity,
                reason=reason
            )
            
            # Update stock item
            stock_item.quantity += quantity
            stock_item.last_updated = timezone.now()
            stock_item.updated_by = request.user
            stock_item.save()
            
            # Create stock movement
            StockMovement.objects.create(
                company=request.user.company,
                stock_item=stock_item,
                movement_type='adjustment',
                quantity=quantity,
                reference=adjustment.reference,
                notes=reason,
                created_by=request.user
            )
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully added {quantity} units to {stock_item.product.name}',
            'new_quantity': stock_item.quantity
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def alerts_export(request):
    """Export alerts data to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="stock_alerts.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Alert Type', 'Product', 'SKU', 'Warehouse', 'Current Stock', 'Min Stock', 'Max Stock', 'Status', 'Created Date'])
    
    # Get critical stock items
    critical_items = StockItem.objects.filter(
        company=request.user.company,
        quantity__lte=0
    ).select_related('product', 'warehouse')
    
    for item in critical_items:
        writer.writerow([
            'Critical Stock',
            item.product.name,
            item.product.sku,
            item.warehouse.name,
            item.quantity,
            item.min_stock or 'Not set',
            item.max_stock or 'Not set',
            'Critical',
            item.created_at.strftime('%Y-%m-%d %H:%M')
        ])
    
    # Get low stock items
    low_stock_items = StockItem.objects.filter(
        company=request.user.company,
        min_stock__isnull=False,
        quantity__gt=0,
        quantity__lte=models.F('min_stock')
    ).select_related('product', 'warehouse')
    
    for item in low_stock_items:
        writer.writerow([
            'Low Stock',
            item.product.name,
            item.product.sku,
            item.warehouse.name,
            item.quantity,
            item.min_stock,
            item.max_stock or 'Not set',
            'Low',
            item.created_at.strftime('%Y-%m-%d %H:%M')
        ])
    
    return response 