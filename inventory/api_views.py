from rest_framework import viewsets, permissions
from .models import ProductCategory, StockItem, StockMovement, Warehouse, StockAlert
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