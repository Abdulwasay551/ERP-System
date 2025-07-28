from rest_framework import serializers
from .models import (
    Supplier, TaxChargesTemplate, PurchaseRequisition, PurchaseRequisitionItem,
    RequestForQuotation, RFQItem, SupplierQuotation, SupplierQuotationItem,
    PurchaseOrder, PurchaseOrderItem, PurchaseOrderTaxCharge,
    GoodsReceiptNote, GRNItem, Bill, BillItem, PurchasePayment,
    PurchaseReturn, PurchaseReturnItem, PurchaseApproval
)

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'

class TaxChargesTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxChargesTemplate
        fields = '__all__'

class PurchaseRequisitionItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = PurchaseRequisitionItem
        fields = '__all__'

class PurchaseRequisitionSerializer(serializers.ModelSerializer):
    items = PurchaseRequisitionItemSerializer(many=True, read_only=True)
    requested_by_name = serializers.CharField(source='requested_by.get_full_name', read_only=True)
    
    class Meta:
        model = PurchaseRequisition
        fields = '__all__'

class RFQItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = RFQItem
        fields = '__all__'

class RequestForQuotationSerializer(serializers.ModelSerializer):
    items = RFQItemSerializer(many=True, read_only=True)
    supplier_names = serializers.StringRelatedField(source='suppliers', many=True, read_only=True)
    
    class Meta:
        model = RequestForQuotation
        fields = '__all__'

class SupplierQuotationItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = SupplierQuotationItem
        fields = '__all__'

class SupplierQuotationSerializer(serializers.ModelSerializer):
    items = SupplierQuotationItemSerializer(many=True, read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    
    class Meta:
        model = SupplierQuotation
        fields = '__all__'

class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = PurchaseOrderItem
        fields = '__all__'

class PurchaseOrderTaxChargeSerializer(serializers.ModelSerializer):
    tax_template_name = serializers.CharField(source='tax_template.name', read_only=True)
    
    class Meta:
        model = PurchaseOrderTaxCharge
        fields = '__all__'

class PurchaseOrderSerializer(serializers.ModelSerializer):
    items = PurchaseOrderItemSerializer(many=True, read_only=True)
    tax_charges = PurchaseOrderTaxChargeSerializer(many=True, read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    
    class Meta:
        model = PurchaseOrder
        fields = '__all__'

class GRNItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='po_item.product.name', read_only=True)
    
    class Meta:
        model = GRNItem
        fields = '__all__'

class GoodsReceiptNoteSerializer(serializers.ModelSerializer):
    items = GRNItemSerializer(many=True, read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    po_number = serializers.CharField(source='purchase_order.po_number', read_only=True)
    
    class Meta:
        model = GoodsReceiptNote
        fields = '__all__'

class BillItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = BillItem
        fields = '__all__'

class BillSerializer(serializers.ModelSerializer):
    items = BillItemSerializer(many=True, read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    
    class Meta:
        model = Bill
        fields = '__all__'

class PurchasePaymentSerializer(serializers.ModelSerializer):
    bill_number = serializers.CharField(source='bill.bill_number', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    
    class Meta:
        model = PurchasePayment
        fields = '__all__'

class PurchaseReturnItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = PurchaseReturnItem
        fields = '__all__'

class PurchaseReturnSerializer(serializers.ModelSerializer):
    items = PurchaseReturnItemSerializer(many=True, read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    
    class Meta:
        model = PurchaseReturn
        fields = '__all__'

class PurchaseApprovalSerializer(serializers.ModelSerializer):
    requested_by_name = serializers.CharField(source='requested_by.get_full_name', read_only=True)
    approver_name = serializers.CharField(source='approver.get_full_name', read_only=True)
    
    class Meta:
        model = PurchaseApproval
        fields = '__all__' 