from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from .models import (
    Supplier, TaxChargesTemplate, PurchaseRequisition, PurchaseRequisitionItem,
    RequestForQuotation, RFQItem, SupplierQuotation, SupplierQuotationItem,
    PurchaseOrder, PurchaseOrderItem, PurchaseOrderTaxCharge,
    GoodsReceiptNote, GRNItem, Bill, BillItem, PurchasePayment,
    PurchaseReturn, PurchaseReturnItem, PurchaseApproval
)
from .serializers import (
    SupplierSerializer, TaxChargesTemplateSerializer, PurchaseRequisitionSerializer, 
    PurchaseRequisitionItemSerializer, RequestForQuotationSerializer, RFQItemSerializer,
    SupplierQuotationSerializer, SupplierQuotationItemSerializer, PurchaseOrderSerializer,
    PurchaseOrderItemSerializer, PurchaseOrderTaxChargeSerializer, GoodsReceiptNoteSerializer,
    GRNItemSerializer, BillSerializer, BillItemSerializer, PurchasePaymentSerializer,
    PurchaseReturnSerializer, PurchaseReturnItemSerializer, PurchaseApprovalSerializer
)

class SupplierViewSet(viewsets.ModelViewSet):
    serializer_class = SupplierSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Supplier.objects.filter(company=self.request.user.company)
    
    @action(detail=False, methods=['get'])
    def active_suppliers(self, request):
        suppliers = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(suppliers, many=True)
        return Response(serializer.data)

class TaxChargesTemplateViewSet(viewsets.ModelViewSet):
    serializer_class = TaxChargesTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return TaxChargesTemplate.objects.filter(company=self.request.user.company)

class PurchaseRequisitionViewSet(viewsets.ModelViewSet):
    serializer_class = PurchaseRequisitionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return PurchaseRequisition.objects.filter(company=self.request.user.company)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        requisition = self.get_object()
        requisition.status = 'approved'
        requisition.approved_by = request.user
        requisition.save()
        return Response({'status': 'approved'})
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        requisition = self.get_object()
        requisition.status = 'rejected'
        requisition.rejected_reason = request.data.get('reason', '')
        requisition.save()
        return Response({'status': 'rejected'})

class PurchaseRequisitionItemViewSet(viewsets.ModelViewSet):
    serializer_class = PurchaseRequisitionItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return PurchaseRequisitionItem.objects.filter(purchase_requisition__company=self.request.user.company)

class RequestForQuotationViewSet(viewsets.ModelViewSet):
    serializer_class = RequestForQuotationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return RequestForQuotation.objects.filter(company=self.request.user.company)

class RFQItemViewSet(viewsets.ModelViewSet):
    serializer_class = RFQItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return RFQItem.objects.filter(rfq__company=self.request.user.company)

class SupplierQuotationViewSet(viewsets.ModelViewSet):
    serializer_class = SupplierQuotationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return SupplierQuotation.objects.filter(company=self.request.user.company)
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        quotation = self.get_object()
        quotation.status = 'accepted'
        quotation.save()
        return Response({'status': 'accepted'})

class SupplierQuotationItemViewSet(viewsets.ModelViewSet):
    serializer_class = SupplierQuotationItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return SupplierQuotationItem.objects.filter(quotation__company=self.request.user.company)

class PurchaseOrderViewSet(viewsets.ModelViewSet):
    serializer_class = PurchaseOrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return PurchaseOrder.objects.filter(company=self.request.user.company)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        order = self.get_object()
        order.status = 'approved'
        order.approved_by = request.user
        order.save()
        return Response({'status': 'approved'})
    
    @action(detail=True, methods=['post'])
    def send_to_supplier(self, request, pk=None):
        order = self.get_object()
        order.status = 'sent_to_supplier'
        order.save()
        return Response({'status': 'sent_to_supplier'})

class PurchaseOrderItemViewSet(viewsets.ModelViewSet):
    serializer_class = PurchaseOrderItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return PurchaseOrderItem.objects.filter(purchase_order__company=self.request.user.company)

class PurchaseOrderTaxChargeViewSet(viewsets.ModelViewSet):
    serializer_class = PurchaseOrderTaxChargeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return PurchaseOrderTaxCharge.objects.filter(purchase_order__company=self.request.user.company)

class GoodsReceiptNoteViewSet(viewsets.ModelViewSet):
    serializer_class = GoodsReceiptNoteSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return GoodsReceiptNote.objects.filter(company=self.request.user.company)
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        grn = self.get_object()
        grn.status = 'accepted'
        grn.save()
        # Update inventory here
        return Response({'status': 'accepted'})

class GRNItemViewSet(viewsets.ModelViewSet):
    serializer_class = GRNItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return GRNItem.objects.filter(grn__company=self.request.user.company)

class BillViewSet(viewsets.ModelViewSet):
    serializer_class = BillSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Bill.objects.filter(company=self.request.user.company)
    
    @action(detail=True, methods=['post'])
    def three_way_match(self, request, pk=None):
        bill = self.get_object()
        # Implement 3-way matching logic here
        # Compare PO, GRN, and Invoice
        bill.three_way_match_status = True
        bill.save()
        return Response({'status': 'matched'})

class BillItemViewSet(viewsets.ModelViewSet):
    serializer_class = BillItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return BillItem.objects.filter(bill__company=self.request.user.company)

class PurchasePaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PurchasePaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return PurchasePayment.objects.filter(company=self.request.user.company)

class PurchaseReturnViewSet(viewsets.ModelViewSet):
    serializer_class = PurchaseReturnSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return PurchaseReturn.objects.filter(company=self.request.user.company)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        return_order = self.get_object()
        return_order.status = 'approved'
        return_order.approved_by = request.user
        return_order.save()
        return Response({'status': 'approved'})

class PurchaseReturnItemViewSet(viewsets.ModelViewSet):
    serializer_class = PurchaseReturnItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return PurchaseReturnItem.objects.filter(purchase_return__company=self.request.user.company)

class PurchaseApprovalViewSet(viewsets.ModelViewSet):
    serializer_class = PurchaseApprovalSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return PurchaseApproval.objects.filter(company=self.request.user.company)
    
    @action(detail=False, methods=['get'])
    def pending_approvals(self, request):
        approvals = self.get_queryset().filter(
            Q(approver=request.user) & Q(status='pending')
        )
        serializer = self.get_serializer(approvals, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        approval = self.get_object()
        approval.status = 'approved'
        approval.approved_at = timezone.now()
        approval.comments = request.data.get('comments', '')
        approval.save()
        return Response({'status': 'approved'}) 