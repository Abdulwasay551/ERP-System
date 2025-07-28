from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count
from .models import Product, ProductCategory, ProductVariant, ProductTracking, Attribute, AttributeValue, ProductAttribute
from .serializers import (
    ProductSerializer, ProductCategorySerializer, ProductVariantSerializer, 
    ProductTrackingSerializer, AttributeSerializer, AttributeValueSerializer,
    ProductAttributeSerializer, ProductListSerializer, ProductDetailSerializer
)
from .filters import ProductFilter


class ProductCategoryViewSet(viewsets.ModelViewSet):
    serializer_class = ProductCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        queryset = ProductCategory.objects.filter(company=self.request.user.company)
        
        # Simple filtering
        parent = self.request.query_params.get('parent')
        if parent:
            queryset = queryset.filter(parent_id=parent)
        
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)

    @action(detail=False, methods=['get'])
    def hierarchy(self, request):
        """Get categories in hierarchical structure"""
        categories = self.get_queryset().filter(parent=None).prefetch_related('subcategories')
        serializer = self.get_serializer(categories, many=True)
        return Response(serializer.data)


class ProductViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['name', 'sku', 'description']
    ordering_fields = ['name', 'sku', 'created_at', 'selling_price']
    ordering = ['name']

    def get_queryset(self):
        queryset = Product.objects.filter(company=self.request.user.company).select_related(
            'category', 'created_by', 'updated_by'
        ).prefetch_related('variants', 'tracking_units')
        
        # Apply custom filtering
        filter_instance = ProductFilter(queryset, self.request.query_params)
        return filter_instance.filter_queryset()

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        elif self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductSerializer

    def perform_create(self, serializer):
        serializer.save(
            company=self.request.user.company,
            created_by=self.request.user
        )

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """Get dashboard statistics for products"""
        queryset = self.get_queryset()
        stats = {
            'total_products': queryset.count(),
            'active_products': queryset.filter(is_active=True).count(),
            'inactive_products': queryset.filter(is_active=False).count(),
            'saleable_products': queryset.filter(is_saleable=True, is_active=True).count(),
            'purchasable_products': queryset.filter(is_purchasable=True, is_active=True).count(),
            'manufacturable_products': queryset.filter(is_manufacturable=True, is_active=True).count(),
            'stockable_products': queryset.filter(is_stockable=True, is_active=True).count(),
            'products_with_variants': queryset.filter(is_variant=True, is_active=True).count(),
            'products_by_category': queryset.values('category__name').annotate(
                count=Count('id')
            ).order_by('-count')[:10],
            'products_by_type': queryset.values('product_type').annotate(
                count=Count('id')
            ).order_by('-count'),
            'tracking_methods': queryset.values('tracking_method').annotate(
                count=Count('id')
            ).order_by('-count'),
        }
        return Response(stats)

    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Get products with low stock levels"""
        # This would typically integrate with inventory module
        # For now, return products that might need attention
        queryset = self.get_queryset().filter(
            is_stockable=True,
            is_active=True,
            minimum_stock__gt=0
        )
        serializer = ProductListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Toggle product active status"""
        product = self.get_object()
        product.is_active = not product.is_active
        product.updated_by = request.user
        product.save()
        
        serializer = self.get_serializer(product)
        return Response({
            'message': f'Product {"activated" if product.is_active else "deactivated"} successfully',
            'product': serializer.data
        })

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Duplicate a product"""
        original_product = self.get_object()
        
        # Create a copy
        new_product = Product.objects.create(
            company=original_product.company,
            name=f"{original_product.name} (Copy)",
            sku=f"{original_product.sku}-COPY",
            description=original_product.description,
            category=original_product.category,
            product_type=original_product.product_type,
            unit_of_measure=original_product.unit_of_measure,
            weight=original_product.weight,
            dimensions=original_product.dimensions,
            cost_price=original_product.cost_price,
            selling_price=original_product.selling_price,
            is_saleable=original_product.is_saleable,
            is_purchasable=original_product.is_purchasable,
            is_manufacturable=original_product.is_manufacturable,
            is_stockable=original_product.is_stockable,
            is_variant=original_product.is_variant,
            tracking_method=original_product.tracking_method,
            minimum_stock=original_product.minimum_stock,
            maximum_stock=original_product.maximum_stock,
            reorder_level=original_product.reorder_level,
            notes=original_product.notes,
            created_by=request.user,
            is_active=False  # Start as inactive
        )
        
        serializer = self.get_serializer(new_product)
        return Response({
            'message': 'Product duplicated successfully',
            'product': serializer.data
        }, status=status.HTTP_201_CREATED)


class ProductVariantViewSet(viewsets.ModelViewSet):
    serializer_class = ProductVariantSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['name', 'sku', 'color', 'size', 'material']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        queryset = ProductVariant.objects.filter(
            product__company=self.request.user.company
        ).select_related('product')
        
        # Simple filtering
        product = self.request.query_params.get('product')
        if product:
            queryset = queryset.filter(product_id=product)
        
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset

    @action(detail=False, methods=['get'])
    def by_product(self, request):
        """Get variants for a specific product"""
        product_id = request.query_params.get('product_id')
        if not product_id:
            return Response({'error': 'product_id parameter is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        variants = self.get_queryset().filter(product_id=product_id)
        serializer = self.get_serializer(variants, many=True)
        return Response(serializer.data)


class ProductTrackingViewSet(viewsets.ModelViewSet):
    serializer_class = ProductTrackingSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['serial_number', 'imei_number', 'barcode']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = ProductTracking.objects.filter(
            product__company=self.request.user.company
        ).select_related('product', 'variant', 'created_by')
        
        # Simple filtering
        product = self.request.query_params.get('product')
        if product:
            queryset = queryset.filter(product_id=product)
        
        variant = self.request.query_params.get('variant')
        if variant:
            queryset = queryset.filter(variant_id=variant)
        
        is_available = self.request.query_params.get('is_available')
        if is_available is not None:
            queryset = queryset.filter(is_available=is_available.lower() == 'true')
        
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def by_product(self, request):
        """Get tracking units for a specific product"""
        product_id = request.query_params.get('product_id')
        if not product_id:
            return Response({'error': 'product_id parameter is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        tracking_units = self.get_queryset().filter(product_id=product_id)
        serializer = self.get_serializer(tracking_units, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def validate_identifier(self, request):
        """Validate if a tracking identifier is unique"""
        identifier_type = request.data.get('type')  # 'serial', 'imei', 'barcode'
        identifier_value = request.data.get('value')
        product_id = request.data.get('product_id')
        
        if not all([identifier_type, identifier_value, product_id]):
            return Response({'error': 'type, value, and product_id are required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Check if identifier exists
        filter_kwargs = {
            f'{identifier_type}_number' if identifier_type != 'barcode' else identifier_type: identifier_value,
            'product_id': product_id
        }
        
        exists = self.get_queryset().filter(**filter_kwargs).exists()
        return Response({
            'exists': exists,
            'message': f'{identifier_type.title()} {"already exists" if exists else "is available"}'
        })


class AttributeViewSet(viewsets.ModelViewSet):
    serializer_class = AttributeSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        queryset = Attribute.objects.filter(company=self.request.user.company)
        
        # Simple filtering
        data_type = self.request.query_params.get('data_type')
        if data_type:
            queryset = queryset.filter(data_type=data_type)
        
        is_required = self.request.query_params.get('is_required')
        if is_required is not None:
            queryset = queryset.filter(is_required=is_required.lower() == 'true')
        
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)


class AttributeValueViewSet(viewsets.ModelViewSet):
    serializer_class = AttributeValueSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['value']
    ordering_fields = ['value', 'created_at']
    ordering = ['value']

    def get_queryset(self):
        queryset = AttributeValue.objects.filter(
            attribute__company=self.request.user.company
        ).select_related('attribute')
        
        # Simple filtering
        attribute = self.request.query_params.get('attribute')
        if attribute:
            queryset = queryset.filter(attribute_id=attribute)
        
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset

    @action(detail=False, methods=['get'])
    def by_attribute(self, request):
        """Get values for a specific attribute"""
        attribute_id = request.query_params.get('attribute_id')
        if not attribute_id:
            return Response({'error': 'attribute_id parameter is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        values = self.get_queryset().filter(attribute_id=attribute_id)
        serializer = self.get_serializer(values, many=True)
        return Response(serializer.data)


class ProductAttributeViewSet(viewsets.ModelViewSet):
    serializer_class = ProductAttributeSerializer
    permission_classes = [permissions.IsAuthenticated]
    ordering_fields = ['created_at']
    ordering = ['attribute__name']

    def get_queryset(self):
        queryset = ProductAttribute.objects.filter(
            product__company=self.request.user.company
        ).select_related('product', 'attribute')
        
        # Simple filtering
        product = self.request.query_params.get('product')
        if product:
            queryset = queryset.filter(product_id=product)
        
        attribute = self.request.query_params.get('attribute')
        if attribute:
            queryset = queryset.filter(attribute_id=attribute)
        
        return queryset

    @action(detail=False, methods=['get'])
    def by_product(self, request):
        """Get attributes for a specific product"""
        product_id = request.query_params.get('product_id')
        if not product_id:
            return Response({'error': 'product_id parameter is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        attributes = self.get_queryset().filter(product_id=product_id)
        serializer = self.get_serializer(attributes, many=True)
        return Response(serializer.data)
