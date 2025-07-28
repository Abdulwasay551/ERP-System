from django.db.models import Q
from .models import Product, ProductCategory


class ProductFilter:
    """Simple filtering for products without django-filter dependency"""
    
    def __init__(self, queryset, data=None):
        self.queryset = queryset
        self.data = data or {}
    
    def filter_queryset(self):
        """Apply filters to the queryset"""
        queryset = self.queryset
        
        # Text search
        search = self.data.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(sku__icontains=search) |
                Q(description__icontains=search) |
                Q(barcode__icontains=search)
            )
        
        # Category filtering
        category = self.data.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        
        # Product type filtering
        product_type = self.data.get('product_type')
        if product_type:
            queryset = queryset.filter(product_type=product_type)
        
        # Tracking method filtering
        tracking_method = self.data.get('tracking_method')
        if tracking_method:
            queryset = queryset.filter(tracking_method=tracking_method)
        
        # Unit of measure filtering
        unit_of_measure = self.data.get('unit_of_measure')
        if unit_of_measure:
            queryset = queryset.filter(unit_of_measure=unit_of_measure)
        
        # Boolean flags
        is_active = self.data.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active == 'true')
        
        is_saleable = self.data.get('is_saleable')
        if is_saleable:
            queryset = queryset.filter(is_saleable=True)
        
        is_purchasable = self.data.get('is_purchasable')
        if is_purchasable:
            queryset = queryset.filter(is_purchasable=True)
        
        is_manufacturable = self.data.get('is_manufacturable')
        if is_manufacturable:
            queryset = queryset.filter(is_manufacturable=True)
        
        is_stockable = self.data.get('is_stockable')
        if is_stockable:
            queryset = queryset.filter(is_stockable=True)
        
        is_variant = self.data.get('is_variant')
        if is_variant:
            queryset = queryset.filter(is_variant=True)
        
        # Price range filters
        min_selling_price = self.data.get('min_selling_price')
        if min_selling_price:
            try:
                queryset = queryset.filter(selling_price__gte=float(min_selling_price))
            except (ValueError, TypeError):
                pass
        
        max_selling_price = self.data.get('max_selling_price')
        if max_selling_price:
            try:
                queryset = queryset.filter(selling_price__lte=float(max_selling_price))
            except (ValueError, TypeError):
                pass
        
        min_cost_price = self.data.get('min_cost_price')
        if min_cost_price:
            try:
                queryset = queryset.filter(cost_price__gte=float(min_cost_price))
            except (ValueError, TypeError):
                pass
        
        max_cost_price = self.data.get('max_cost_price')
        if max_cost_price:
            try:
                queryset = queryset.filter(cost_price__lte=float(max_cost_price))
            except (ValueError, TypeError):
                pass
        
        # Stock level filters
        min_stock_level = self.data.get('min_stock_level')
        if min_stock_level:
            try:
                queryset = queryset.filter(minimum_stock__gte=float(min_stock_level))
            except (ValueError, TypeError):
                pass
        
        max_stock_level = self.data.get('max_stock_level')
        if max_stock_level:
            try:
                queryset = queryset.filter(maximum_stock__lte=float(max_stock_level))
            except (ValueError, TypeError):
                pass
        
        # Date filters
        created_after = self.data.get('created_after')
        if created_after:
            try:
                queryset = queryset.filter(created_at__date__gte=created_after)
            except (ValueError, TypeError):
                pass
        
        created_before = self.data.get('created_before')
        if created_before:
            try:
                queryset = queryset.filter(created_at__date__lte=created_before)
            except (ValueError, TypeError):
                pass
        
        # Special filters
        has_variants = self.data.get('has_variants')
        if has_variants == 'true':
            queryset = queryset.filter(variants__isnull=False).distinct()
        elif has_variants == 'false':
            queryset = queryset.filter(variants__isnull=True)
        
        has_tracking = self.data.get('has_tracking')
        if has_tracking == 'true':
            queryset = queryset.filter(tracking_units__isnull=False, tracking_units__is_active=True).distinct()
        elif has_tracking == 'false':
            queryset = queryset.filter(
                Q(tracking_units__isnull=True) | 
                Q(tracking_units__is_active=False)
            ).distinct()
        
        low_stock = self.data.get('low_stock')
        if low_stock == 'true':
            queryset = queryset.filter(
                is_stockable=True,
                minimum_stock__gt=0,
                is_active=True
            )
        
        return queryset
    
    def filter_category_tree(self, queryset, category_id):
        """Filter by category and all its subcategories"""
        if category_id:
            try:
                category = ProductCategory.objects.get(id=category_id)
                # Get category and all its descendants
                categories = [category]
                
                def get_descendants(cat):
                    children = cat.subcategories.all()
                    for child in children:
                        categories.append(child)
                        get_descendants(child)
                
                get_descendants(category)
                category_ids = [cat.id for cat in categories]
                return queryset.filter(category_id__in=category_ids)
            except ProductCategory.DoesNotExist:
                pass
        return queryset
