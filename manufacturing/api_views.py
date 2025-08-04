from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction

from .models import (
    WorkCenter, BillOfMaterials, BillOfMaterialsItem, BOMOperation,
    WorkOrder, WorkOrderOperation, OperationLog, QualityCheck,
    MaterialConsumption, MRPPlan, MRPRequirement, ProductionPlan,
    ProductionPlanItem, JobCard, Subcontractor, SubcontractWorkOrder
)
from .serializers import (
    WorkCenterSerializer, BillOfMaterialsSerializer, BillOfMaterialsItemSerializer,
    BOMOperationSerializer, WorkOrderSerializer, WorkOrderOperationSerializer,
    OperationLogSerializer, QualityCheckSerializer, MaterialConsumptionSerializer,
    MRPPlanSerializer, MRPRequirementSerializer, ProductionPlanSerializer,
    ProductionPlanItemSerializer, JobCardSerializer, SubcontractorSerializer,
    SubcontractWorkOrderSerializer
)


class WorkCenterViewSet(viewsets.ModelViewSet):
    serializer_class = WorkCenterSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return WorkCenter.objects.filter(company=self.request.user.company)
    
    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)


class BillOfMaterialsViewSet(viewsets.ModelViewSet):
    serializer_class = BillOfMaterialsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return BillOfMaterials.objects.filter(company=self.request.user.company)
    
    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company, created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Create a duplicate of an existing BOM"""
        bom = self.get_object()
        
        # Create new BOM
        new_bom = BillOfMaterials.objects.create(
            company=bom.company,
            product=bom.product,
            name=f"{bom.name} (Copy)",
            version=f"{bom.version}-copy",
            manufacturing_type=bom.manufacturing_type,
            lot_size=bom.lot_size,
            lead_time_days=bom.lead_time_days,
            scrap_percentage=bom.scrap_percentage,
            routing_required=bom.routing_required,
            phantom_bom=bom.phantom_bom,
            quality_check_required=bom.quality_check_required,
            quality_specification=bom.quality_specification,
            created_by=request.user
        )
        
        # Copy BOM items
        for item in bom.items.all():
            BillOfMaterialsItem.objects.create(
                bom=new_bom,
                component=item.component,
                quantity=item.quantity,
                unit_cost=item.unit_cost,
                waste_percentage=item.waste_percentage,
                is_optional=item.is_optional,
                preferred_supplier=item.preferred_supplier,
                sequence=item.sequence,
                notes=item.notes
            )
        
        # Copy operations
        for operation in bom.operations.all():
            BOMOperation.objects.create(
                bom=new_bom,
                work_center=operation.work_center,
                operation_name=operation.operation_name,
                description=operation.description,
                sequence=operation.sequence,
                setup_time_minutes=operation.setup_time_minutes,
                run_time_per_unit_minutes=operation.run_time_per_unit_minutes,
                cleanup_time_minutes=operation.cleanup_time_minutes,
                operators_required=operation.operators_required,
                skill_level_required=operation.skill_level_required,
                quality_check_required=operation.quality_check_required,
                quality_specification=operation.quality_specification,
                cost_per_hour=operation.cost_per_hour,
                work_instruction=operation.work_instruction,
                safety_notes=operation.safety_notes
            )
        
        serializer = self.get_serializer(new_bom)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class BillOfMaterialsItemViewSet(viewsets.ModelViewSet):
    serializer_class = BillOfMaterialsItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return BillOfMaterialsItem.objects.filter(bom__company=self.request.user.company)


class BOMOperationViewSet(viewsets.ModelViewSet):
    serializer_class = BOMOperationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return BOMOperation.objects.filter(bom__company=self.request.user.company)


class WorkOrderViewSet(viewsets.ModelViewSet):
    serializer_class = WorkOrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return WorkOrder.objects.filter(company=self.request.user.company)
    
    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company, created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Start work order production"""
        work_order = self.get_object()
        work_order.start_production()
        return Response({'status': 'started', 'actual_start': work_order.actual_start})
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Complete work order production"""
        work_order = self.get_object()
        work_order.complete_production()
        return Response({'status': 'completed', 'actual_end': work_order.actual_end})
    
    @action(detail=True, methods=['post'])
    def generate_operations(self, request, pk=None):
        """Generate work order operations from BOM"""
        work_order = self.get_object()
        
        # Delete existing operations
        work_order.operations.all().delete()
        
        # Create operations from BOM
        for bom_operation in work_order.bom.operations.all():
            WorkOrderOperation.objects.create(
                work_order=work_order,
                bom_operation=bom_operation,
                work_center=bom_operation.work_center,
                sequence=bom_operation.sequence,
                quantity_to_produce=work_order.quantity_planned
            )
        
        return Response({'message': 'Operations generated successfully'})


class WorkOrderOperationViewSet(viewsets.ModelViewSet):
    serializer_class = WorkOrderOperationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return WorkOrderOperation.objects.filter(work_order__company=self.request.user.company)


class OperationLogViewSet(viewsets.ModelViewSet):
    serializer_class = OperationLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return OperationLog.objects.filter(work_order_operation__work_order__company=self.request.user.company)
    
    def perform_create(self, serializer):
        serializer.save(operator=self.request.user)


class QualityCheckViewSet(viewsets.ModelViewSet):
    serializer_class = QualityCheckSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return QualityCheck.objects.filter(work_order__company=self.request.user.company)
    
    def perform_create(self, serializer):
        serializer.save(inspector=self.request.user)


class MaterialConsumptionViewSet(viewsets.ModelViewSet):
    serializer_class = MaterialConsumptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return MaterialConsumption.objects.filter(work_order__company=self.request.user.company)
    
    def perform_create(self, serializer):
        serializer.save(consumed_by=self.request.user, consumed_at=timezone.now())


class MRPPlanViewSet(viewsets.ModelViewSet):
    serializer_class = MRPPlanSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return MRPPlan.objects.filter(company=self.request.user.company)
    
    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company, created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def calculate(self, request, pk=None):
        """Run MRP calculation"""
        mrp_plan = self.get_object()
        
        try:
            with transaction.atomic():
                mrp_plan.status = 'calculating'
                mrp_plan.calculation_start = timezone.now()
                mrp_plan.save()
                
                # Clear existing requirements
                mrp_plan.requirements.all().delete()
                
                # TODO: Implement actual MRP calculation logic
                # This is a placeholder for the complex MRP algorithm
                
                mrp_plan.status = 'completed'
                mrp_plan.calculation_end = timezone.now()
                mrp_plan.save()
                
            return Response({'message': 'MRP calculation completed successfully'})
        except Exception as e:
            mrp_plan.status = 'draft'
            mrp_plan.save()
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class MRPRequirementViewSet(viewsets.ModelViewSet):
    serializer_class = MRPRequirementSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return MRPRequirement.objects.filter(mrp_plan__company=self.request.user.company)


class ProductionPlanViewSet(viewsets.ModelViewSet):
    serializer_class = ProductionPlanSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return ProductionPlan.objects.filter(company=self.request.user.company)
    
    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company, created_by=self.request.user)


class ProductionPlanItemViewSet(viewsets.ModelViewSet):
    serializer_class = ProductionPlanItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return ProductionPlanItem.objects.filter(production_plan__company=self.request.user.company)


class JobCardViewSet(viewsets.ModelViewSet):
    serializer_class = JobCardSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return JobCard.objects.filter(work_order__company=self.request.user.company)


class SubcontractorViewSet(viewsets.ModelViewSet):
    serializer_class = SubcontractorSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Subcontractor.objects.filter(company=self.request.user.company)
    
    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)


class SubcontractWorkOrderViewSet(viewsets.ModelViewSet):
    serializer_class = SubcontractWorkOrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return SubcontractWorkOrder.objects.filter(company=self.request.user.company)
    
    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company) 