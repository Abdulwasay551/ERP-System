from rest_framework import serializers
from .models import (
    Supplier, TaxChargesTemplate, PurchaseRequisition, PurchaseRequisitionItem,
    RequestForQuotation, RFQItem, SupplierQuotation, SupplierQuotationItem,
    PurchaseOrder, PurchaseOrderItem, PurchaseOrderTaxCharge,
    GoodsReceiptNote, GRNItem, Bill, BillItem, PurchasePayment, SupplierLedger,
    PurchaseReturn, PurchaseReturnItem, PurchaseApproval
)


class SupplierLedgerSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierLedger
        fields = '__all__'
        read_only_fields = ('balance', 'created_at', 'updated_at')

class SupplierSerializer(serializers.ModelSerializer):
    # name/email/phone/city are @property methods on Supplier (reading through to
    # Partner) - Meta.fields = '__all__' only picks up real model fields, so these must
    # be declared explicitly. Writable here (not read_only) so "Add Vendor" can be a
    # single POST - Supplier.partner is a required OneToOne with no other way to supply
    # one, so create()/update() below manage the linked Partner behind the scenes.
    name = serializers.CharField()
    email = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    city = serializers.CharField(required=False, allow_blank=True)
    outstanding_balance = serializers.SerializerMethodField()

    class Meta:
        model = Supplier
        fields = '__all__'
        read_only_fields = ('company', 'created_by', 'partner', 'supplier_code')

    def get_outstanding_balance(self, obj):
        return str(obj.get_outstanding_balance())

    def create(self, validated_data):
        from crm.models import Partner
        name = validated_data.pop('name')
        email = validated_data.pop('email', '')
        phone = validated_data.pop('phone', '')
        city = validated_data.pop('city', '')
        validated_data['partner'] = Partner.objects.create(
            company=validated_data['company'], name=name, partner_type='company',
            email=email, phone=phone, city=city, is_supplier=True,
            created_by=validated_data.get('created_by'),
        )
        return super().create(validated_data)

    def update(self, instance, validated_data):
        name = validated_data.pop('name', None)
        email = validated_data.pop('email', None)
        phone = validated_data.pop('phone', None)
        city = validated_data.pop('city', None)
        if instance.partner and any(v is not None for v in (name, email, phone, city)):
            if name is not None:
                instance.partner.name = name
            if email is not None:
                instance.partner.email = email
            if phone is not None:
                instance.partner.phone = phone
            if city is not None:
                instance.partner.city = city
            instance.partner.save()
        return super().update(instance, validated_data)

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
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True, default=None)

    class Meta:
        model = Bill
        fields = '__all__'

class PurchasePaymentSerializer(serializers.ModelSerializer):
    bill_number = serializers.CharField(source='bill.bill_number', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)

    class Meta:
        model = PurchasePayment
        fields = '__all__'
        read_only_fields = ('company', 'created_by')

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