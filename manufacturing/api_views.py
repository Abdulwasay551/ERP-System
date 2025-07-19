from rest_framework import viewsets, permissions
from .models import BillOfMaterials, BillOfMaterialsItem, WorkOrder, ProductionPlan
from .serializers import BillOfMaterialsSerializer, BillOfMaterialsItemSerializer, WorkOrderSerializer, ProductionPlanSerializer

class BillOfMaterialsViewSet(viewsets.ModelViewSet):
    serializer_class = BillOfMaterialsSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return BillOfMaterials.objects.filter(company=self.request.user.company)

class BillOfMaterialsItemViewSet(viewsets.ModelViewSet):
    serializer_class = BillOfMaterialsItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return BillOfMaterialsItem.objects.filter(bom__company=self.request.user.company)

class WorkOrderViewSet(viewsets.ModelViewSet):
    serializer_class = WorkOrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return WorkOrder.objects.filter(company=self.request.user.company)

class ProductionPlanViewSet(viewsets.ModelViewSet):
    serializer_class = ProductionPlanSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return ProductionPlan.objects.filter(company=self.request.user.company) 