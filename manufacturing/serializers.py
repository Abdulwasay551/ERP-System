from rest_framework import serializers
from .models import (
    WorkCenter, BillOfMaterials, BillOfMaterialsItem, BOMOperation,
    WorkOrder, WorkOrderOperation, OperationLog, QualityCheck,
    MaterialConsumption, MRPPlan, MRPRequirement, ProductionPlan,
    ProductionPlanItem, JobCard, Subcontractor, SubcontractWorkOrder,
    DemandForecast, SupplierLeadTime, MRPRunLog, ReorderRule, CapacityPlan
)


class WorkCenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkCenter
        fields = '__all__'


class BOMOperationSerializer(serializers.ModelSerializer):
    work_center_name = serializers.CharField(source='work_center.name', read_only=True)
    
    class Meta:
        model = BOMOperation
        fields = '__all__'


class BillOfMaterialsItemSerializer(serializers.ModelSerializer):
    component_name = serializers.CharField(source='component.name', read_only=True)
    substitute_products_names = serializers.StringRelatedField(source='substitute_products', many=True, read_only=True)
    
    class Meta:
        model = BillOfMaterialsItem
        fields = '__all__'


class BillOfMaterialsSerializer(serializers.ModelSerializer):
    items = BillOfMaterialsItemSerializer(many=True, read_only=True)
    operations = BOMOperationSerializer(many=True, read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = BillOfMaterials
        fields = '__all__'


class WorkOrderOperationSerializer(serializers.ModelSerializer):
    bom_operation_name = serializers.CharField(source='bom_operation.operation_name', read_only=True)
    work_center_name = serializers.CharField(source='work_center.name', read_only=True)
    assigned_operators_names = serializers.StringRelatedField(source='assigned_operators', many=True, read_only=True)
    
    class Meta:
        model = WorkOrderOperation
        fields = '__all__'


class OperationLogSerializer(serializers.ModelSerializer):
    operator_name = serializers.CharField(source='operator.get_full_name', read_only=True)
    work_center_name = serializers.CharField(source='work_center.name', read_only=True)
    
    class Meta:
        model = OperationLog
        fields = '__all__'


class QualityCheckSerializer(serializers.ModelSerializer):
    inspector_name = serializers.CharField(source='inspector.get_full_name', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    work_order_number = serializers.CharField(source='work_order.wo_number', read_only=True)
    
    class Meta:
        model = QualityCheck
        fields = '__all__'


class MaterialConsumptionSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    work_order_number = serializers.CharField(source='work_order.wo_number', read_only=True)
    consumed_by_name = serializers.CharField(source='consumed_by.get_full_name', read_only=True)
    
    class Meta:
        model = MaterialConsumption
        fields = '__all__'


class WorkOrderSerializer(serializers.ModelSerializer):
    operations = WorkOrderOperationSerializer(many=True, read_only=True)
    material_consumptions = MaterialConsumptionSerializer(many=True, read_only=True)
    quality_checks = QualityCheckSerializer(many=True, read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    bom_name = serializers.CharField(source='bom.name', read_only=True)
    sales_order_number = serializers.CharField(source='sales_order.order_number', read_only=True)
    progress_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = WorkOrder
        fields = '__all__'
    
    def get_progress_percentage(self, obj):
        return obj.get_progress_percentage()


class MRPRequirementSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    mrp_plan_name = serializers.CharField(source='mrp_plan.name', read_only=True)
    
    class Meta:
        model = MRPRequirement
        fields = '__all__'


class MRPPlanSerializer(serializers.ModelSerializer):
    requirements = MRPRequirementSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    
    class Meta:
        model = MRPPlan
        fields = '__all__'


class ProductionPlanItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    sales_orders_numbers = serializers.SerializerMethodField()
    work_orders_numbers = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductionPlanItem
        fields = '__all__'
    
    def get_sales_orders_numbers(self, obj):
        return [so.order_number for so in obj.sales_orders.all()]
    
    def get_work_orders_numbers(self, obj):
        return [wo.wo_number for wo in obj.work_orders.all()]


class ProductionPlanSerializer(serializers.ModelSerializer):
    items = ProductionPlanItemSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    
    class Meta:
        model = ProductionPlan
        fields = '__all__'


class JobCardSerializer(serializers.ModelSerializer):
    work_order_number = serializers.CharField(source='work_order.wo_number', read_only=True)
    work_center_name = serializers.CharField(source='work_center.name', read_only=True)
    operation_name = serializers.CharField(source='operation.operation_name', read_only=True)
    issued_to_name = serializers.CharField(source='issued_to.get_full_name', read_only=True)
    
    class Meta:
        model = JobCard
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
    work_order_number = serializers.CharField(source='work_order.wo_number', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = SubcontractWorkOrder
        fields = '__all__'


class DemandForecastSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = DemandForecast
        fields = '__all__'


class SupplierLeadTimeSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    reliability_score = serializers.SerializerMethodField()
    
    def get_reliability_score(self, obj):
        return obj.get_reliability_score()
    
    class Meta:
        model = SupplierLeadTime
        fields = '__all__'


class MRPRunLogSerializer(serializers.ModelSerializer):
    mrp_plan_name = serializers.CharField(source='mrp_plan.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = MRPRunLog
        fields = '__all__'


class ReorderRuleSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    calculated_reorder_point = serializers.SerializerMethodField()
    
    def get_calculated_reorder_point(self, obj):
        return obj.calculate_reorder_point()
    
    class Meta:
        model = ReorderRule
        fields = '__all__'


class CapacityPlanSerializer(serializers.ModelSerializer):
    work_center_name = serializers.CharField(source='work_center.name', read_only=True)
    work_center_code = serializers.CharField(source='work_center.code', read_only=True)
    
    class Meta:
        model = CapacityPlan
        fields = '__all__' 