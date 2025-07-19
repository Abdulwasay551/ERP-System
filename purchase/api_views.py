from rest_framework import viewsets, permissions
from .models import Supplier, PurchaseOrder, PurchaseOrderItem, Bill, PurchasePayment
from .serializers import SupplierSerializer, PurchaseOrderSerializer, PurchaseOrderItemSerializer, BillSerializer, PurchasePaymentSerializer

class SupplierViewSet(viewsets.ModelViewSet):
    serializer_class = SupplierSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Supplier.objects.filter(company=self.request.user.company)

class PurchaseOrderViewSet(viewsets.ModelViewSet):
    serializer_class = PurchaseOrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return PurchaseOrder.objects.filter(company=self.request.user.company)

class PurchaseOrderItemViewSet(viewsets.ModelViewSet):
    serializer_class = PurchaseOrderItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return PurchaseOrderItem.objects.filter(purchase_order__company=self.request.user.company)

class BillViewSet(viewsets.ModelViewSet):
    serializer_class = BillSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Bill.objects.filter(company=self.request.user.company)

class PurchasePaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PurchasePaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return PurchasePayment.objects.filter(company=self.request.user.company) 