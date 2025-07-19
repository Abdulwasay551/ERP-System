from rest_framework import serializers
from .models import BillOfMaterials, BillOfMaterialsItem, WorkOrder, ProductionPlan

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