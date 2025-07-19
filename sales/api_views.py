from rest_framework import viewsets, permissions
from .models import Product, Tax, Quotation, SalesOrder, SalesOrderItem, Invoice, Payment
from .serializers import ProductSerializer, TaxSerializer, QuotationSerializer, SalesOrderSerializer, SalesOrderItemSerializer, InvoiceSerializer, PaymentSerializer

class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Product.objects.filter(company=self.request.user.company)

class TaxViewSet(viewsets.ModelViewSet):
    serializer_class = TaxSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Tax.objects.filter(company=self.request.user.company)

class QuotationViewSet(viewsets.ModelViewSet):
    serializer_class = QuotationSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Quotation.objects.filter(company=self.request.user.company)

class SalesOrderViewSet(viewsets.ModelViewSet):
    serializer_class = SalesOrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return SalesOrder.objects.filter(company=self.request.user.company)

class SalesOrderItemViewSet(viewsets.ModelViewSet):
    serializer_class = SalesOrderItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return SalesOrderItem.objects.filter(sales_order__company=self.request.user.company)

class InvoiceViewSet(viewsets.ModelViewSet):
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Invoice.objects.filter(company=self.request.user.company)

class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Payment.objects.filter(company=self.request.user.company) 