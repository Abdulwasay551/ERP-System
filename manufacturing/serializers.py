from rest_framework import serializers
from .models import BillOfMaterials, BillOfMaterialsItem, WorkOrder, ProductionPlan, Subcontractor, SubcontractWorkOrder

class BillOfMaterialsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillOfMaterials
        fields = '__all__'

class BillOfMaterialsItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillOfMaterialsItem
        fields = '__all__'

class WorkOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkOrder
        fields = '__all__'

class ProductionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionPlan
        fields = '__all__'

class SubcontractorSerializer(serializers.ModelSerializer):
    partner_name = serializers.CharField(source='partner.name', read_only=True)
    partner_email = serializers.CharField(source='partner.email', read_only=True)
    partner_phone = serializers.CharField(source='partner.phone', read_only=True)
    
    class Meta:
        model = Subcontractor
        fields = '__all__'

class SubcontractWorkOrderSerializer(serializers.ModelSerializer):
    subcontractor_name = serializers.CharField(source='subcontractor.partner.name', read_only=True)
    work_order_reference = serializers.CharField(source='work_order.work_order_number', read_only=True)
    
    class Meta:
        model = SubcontractWorkOrder
        fields = '__all__' 