from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Count, Sum, Avg, F
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
import json
import csv
from .models import Product, ProductCategory, ProductVariant, ProductTracking, Attribute, AttributeValue
from .forms import ProductForm, ProductCategoryForm, ProductTrackingForm, BulkTrackingImportForm


class ProductDashboardView(LoginRequiredMixin, ListView):
    """Product dashboard with statistics and quick actions"""
    template_name = 'products/dashboard.html'
    context_object_name = 'products'
    paginate_by = 10

    def get_queryset(self):
        return Product.objects.filter(
            company=self.request.user.company,
            is_active=True
        ).select_related('category').order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company
        
        # Dashboard statistics
        all_products = Product.objects.filter(company=company)
        active_products = all_products.filter(is_active=True)
        categories = ProductCategory.objects.filter(company=company, is_active=True)
        
        # Get inventory stats if inventory app is available
        try:
            from inventory.models import StockItem
            stockable_products = active_products.filter(is_stockable=True)
            stock_items = StockItem.objects.filter(
                company=company,
                product__in=stockable_products
            ).select_related('product')
            
            low_stock_count = stock_items.filter(
                quantity__lte=F('min_stock'),
                min_stock__gt=0
            ).count()
            
            out_of_stock_count = stock_items.filter(quantity=0).count()
            
            # Products ready for sale vs manufacturing
            ready_for_sale = stockable_products.filter(
                is_saleable=True,
                is_active=True
            ).count()
            
            manufacturing_items = stockable_products.filter(
                is_manufacturable=True,
                is_active=True
            ).count()
            
        except ImportError:
            # Inventory app not available
            low_stock_count = 0
            out_of_stock_count = 0
            ready_for_sale = active_products.filter(is_saleable=True).count()
            manufacturing_items = active_products.filter(is_manufacturable=True).count()
        
        context.update({
            'stats': {
                'total_products': all_products.count(),
                'active_products': active_products.count(),
                'total_categories': categories.count(),
                'low_stock_count': low_stock_count,
                'out_of_stock_count': out_of_stock_count,
                'ready_for_sale': ready_for_sale,
                'manufacturing_items': manufacturing_items,
                'stockable_products': active_products.filter(is_stockable=True).count(),
                'service_products': active_products.filter(product_type='service').count(),
            },
            'recent_products': active_products.order_by('-created_at')[:5],
            'top_categories': categories.annotate(
                product_count=Count('products', filter=Q(products__is_active=True))
            ).order_by('-product_count')[:5],
        })
        return context


class ProductListView(LoginRequiredMixin, ListView):
    """Product list view with filtering and search"""
    model = Product
    template_name = 'products/list.html'
    context_object_name = 'products'
    paginate_by = 20

    def get_queryset(self):
        queryset = Product.objects.filter(
            company=self.request.user.company
        ).select_related('category', 'created_by').prefetch_related('variants')
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(sku__icontains=search) |
                Q(description__icontains=search)
            )
        
        # Filter by category
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Filter by type
        product_type = self.request.GET.get('type')
        if product_type:
            queryset = queryset.filter(product_type=product_type)
        
        # Filter by status
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        # Filter by flags
        if self.request.GET.get('saleable'):
            queryset = queryset.filter(is_saleable=True)
        if self.request.GET.get('purchasable'):
            queryset = queryset.filter(is_purchasable=True)
        if self.request.GET.get('manufacturable'):
            queryset = queryset.filter(is_manufacturable=True)
        if self.request.GET.get('stockable'):
            queryset = queryset.filter(is_stockable=True)
        
        # Sorting
        sort_by = self.request.GET.get('sort', 'name')
        if sort_by in ['name', 'sku', 'created_at', 'selling_price', 'cost_price']:
            queryset = queryset.order_by(sort_by)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'categories': ProductCategory.objects.filter(
                company=self.request.user.company, 
                is_active=True
            ).order_by('name'),
            'product_types': Product.PRODUCT_TYPE_CHOICES,
            'search_query': self.request.GET.get('search', ''),
            'selected_category': self.request.GET.get('category', ''),
            'selected_type': self.request.GET.get('type', ''),
            'selected_status': self.request.GET.get('status', ''),
        })
        return context


class ProductDetailView(LoginRequiredMixin, DetailView):
    """Product detail view"""
    model = Product
    template_name = 'products/detail.html'
    context_object_name = 'product'

    def get_queryset(self):
        return Product.objects.filter(
            company=self.request.user.company
        ).select_related('category', 'created_by', 'updated_by')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object
        
        # Get inventory information if available
        try:
            from inventory.models import StockItem, StockMovement
            
            # Get stock items for this product across all warehouses
            stock_items = StockItem.objects.filter(
                company=self.request.user.company,
                product=product
            ).select_related('warehouse')
            
            total_stock = sum(item.quantity for item in stock_items)
            total_available = sum(item.available_quantity for item in stock_items)
            total_locked = sum(item.locked_quantity for item in stock_items)
            total_reserved = sum(item.reserved_quantity for item in stock_items)
            
            # Recent stock movements
            recent_movements = StockMovement.objects.filter(
                stock_item__product=product,
                company=self.request.user.company
            ).select_related('stock_item__warehouse').order_by('-timestamp')[:10]
            
            # Purchase information if available
            try:
                from purchase.models import GRNItem, BillItem, PurchaseOrderItem
                
                recent_purchases = GRNItem.objects.filter(
                    product=product,
                    grn__company=self.request.user.company
                ).select_related('grn__supplier').order_by('-created_at')[:5]
                
                recent_bills = BillItem.objects.filter(
                    product=product,
                    bill__company=self.request.user.company
                ).select_related('bill__supplier').order_by('-created_at')[:5]
                
            except ImportError:
                recent_purchases = []
                recent_bills = []
            
            inventory_context = {
                'stock_items': stock_items,
                'total_stock': total_stock,
                'total_available': total_available,
                'total_locked': total_locked,
                'total_reserved': total_reserved,
                'recent_movements': recent_movements,
                'recent_purchases': recent_purchases,
                'recent_bills': recent_bills,
                'stock_status': 'Available' if total_available > 0 else ('Locked' if total_locked > 0 else 'Out of Stock'),
            }
            
        except ImportError:
            inventory_context = {
                'inventory_available': False,
            }
        
        context.update({
            'variants': product.variants.filter(is_active=True),
            'tracking_units': product.tracking_units.filter(is_active=True).order_by('-created_at'),
            'product_attributes': product.product_attributes.select_related('attribute'),
            **inventory_context,
        })
        return context


# AJAX and utility views
@login_required
@require_POST
def toggle_product_active(request, pk):
    """Toggle product active status via AJAX"""
    product = get_object_or_404(Product, pk=pk, company=request.user.company)
    product.is_active = not product.is_active
    product.updated_by = request.user
    product.save()
    
    return JsonResponse({
        'success': True,
        'is_active': product.is_active,
        'message': f'Product {"activated" if product.is_active else "deactivated"} successfully'
    })


@login_required
@require_POST
def duplicate_product(request, pk):
    """Duplicate a product"""
    original_product = get_object_or_404(Product, pk=pk, company=request.user.company)
    
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
    
    messages.success(request, f'Product duplicated successfully! New product: {new_product.name}')
    return redirect('products:detail', pk=new_product.pk)


@login_required
@require_POST
def bulk_toggle_active(request):
    """Bulk toggle active status for multiple products"""
    product_ids = request.POST.getlist('product_ids')
    if not product_ids:
        return JsonResponse({'success': False, 'message': 'No products selected'})
    
    products = Product.objects.filter(
        id__in=product_ids,
        company=request.user.company
    )
    
    updated_count = 0
    for product in products:
        product.is_active = not product.is_active
        product.updated_by = request.user
        product.save()
        updated_count += 1
    
    return JsonResponse({
        'success': True,
        'message': f'{updated_count} products updated successfully'
    })


@login_required
def export_products(request):
    """Export products to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="products.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'SKU', 'Name', 'Category', 'Type', 'UOM', 'Cost Price', 'Selling Price',
        'Saleable', 'Purchasable', 'Manufacturable', 'Stockable', 'Active'
    ])
    
    products = Product.objects.filter(company=request.user.company).select_related('category')
    for product in products:
        writer.writerow([
            product.sku,
            product.name,
            product.category.name if product.category else '',
            product.get_product_type_display(),
            product.get_unit_of_measure_display(),
            product.cost_price,
            product.selling_price,
            'Yes' if product.is_saleable else 'No',
            'Yes' if product.is_purchasable else 'No',
            'Yes' if product.is_manufacturable else 'No',
            'Yes' if product.is_stockable else 'No',
            'Yes' if product.is_active else 'No',
        ])
    
    return response


# Placeholder views for forms (will be implemented when forms are created)
class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    template_name = 'products/form.html'
    fields = ['name', 'sku', 'description', 'category', 'product_type', 'unit_of_measure', 
              'cost_price', 'selling_price', 'is_saleable', 'is_purchasable', 
              'is_manufacturable', 'is_stockable', 'tracking_method']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = ProductCategory.objects.filter(
            company=self.request.user.company,
            is_active=True
        ).order_by('name')
        return context

    def form_valid(self, form):
        form.instance.company = self.request.user.company
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Product created successfully!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('products:detail', kwargs={'pk': self.object.pk})

class ProductUpdateView(LoginRequiredMixin, UpdateView):
    model = Product
    template_name = 'products/form.html'
    fields = ['name', 'sku', 'description', 'category', 'product_type', 'unit_of_measure', 
              'cost_price', 'selling_price', 'is_saleable', 'is_purchasable', 
              'is_manufacturable', 'is_stockable', 'tracking_method']

    def get_queryset(self):
        return Product.objects.filter(company=self.request.user.company)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = ProductCategory.objects.filter(
            company=self.request.user.company,
            is_active=True
        ).order_by('name')
        return context

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, 'Product updated successfully!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('products:detail', kwargs={'pk': self.object.pk})

# Category views
class CategoryListView(LoginRequiredMixin, ListView):
    model = ProductCategory
    template_name = 'products/category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return ProductCategory.objects.filter(company=self.request.user.company)

class CategoryDetailView(LoginRequiredMixin, DetailView):
    model = ProductCategory
    template_name = 'products/category_detail.html'
    context_object_name = 'category'

    def get_queryset(self):
        return ProductCategory.objects.filter(company=self.request.user.company)

class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = ProductCategory
    template_name = 'products/category_form.html'
    fields = ['name', 'code', 'description', 'parent']

    def form_valid(self, form):
        form.instance.company = self.request.user.company
        return super().form_valid(form)

class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = ProductCategory
    template_name = 'products/category_form.html'
    fields = ['name', 'code', 'description', 'parent']

    def get_queryset(self):
        return ProductCategory.objects.filter(company=self.request.user.company)

# Variant views
class VariantDetailView(LoginRequiredMixin, DetailView):
    model = ProductVariant
    template_name = 'products/variant_detail.html'
    context_object_name = 'variant'

    def get_queryset(self):
        return ProductVariant.objects.filter(product__company=self.request.user.company)

class VariantCreateView(LoginRequiredMixin, CreateView):
    model = ProductVariant
    template_name = 'products/variant_form.html'
    fields = ['name', 'sku', 'color', 'size', 'material', 'cost_price', 'selling_price']

    def form_valid(self, form):
        product_id = self.kwargs['product_id']
        product = get_object_or_404(Product, id=product_id, company=self.request.user.company)
        form.instance.product = product
        return super().form_valid(form)

class VariantUpdateView(LoginRequiredMixin, UpdateView):
    model = ProductVariant
    template_name = 'products/variant_form.html'
    fields = ['name', 'sku', 'color', 'size', 'material', 'cost_price', 'selling_price']

    def get_queryset(self):
        return ProductVariant.objects.filter(product__company=self.request.user.company)

# Tracking views
class TrackingListView(LoginRequiredMixin, ListView):
    model = ProductTracking
    template_name = 'products/tracking_list.html'
    context_object_name = 'tracking_units'

    def get_queryset(self):
        product_id = self.kwargs['product_id']
        return ProductTracking.objects.filter(
            product_id=product_id,
            product__company=self.request.user.company
        )

class TrackingDetailView(LoginRequiredMixin, DetailView):
    model = ProductTracking
    template_name = 'products/tracking_detail.html'
    context_object_name = 'tracking_unit'

    def get_queryset(self):
        return ProductTracking.objects.filter(product__company=self.request.user.company)

class TrackingCreateView(LoginRequiredMixin, CreateView):
    model = ProductTracking
    template_name = 'products/tracking_form.html'
    fields = ['serial_number', 'imei_number', 'barcode', 'variant', 'purchase_date', 'warranty_expiry', 'notes']

    def form_valid(self, form):
        product_id = self.kwargs['product_id']
        product = get_object_or_404(Product, id=product_id, company=self.request.user.company)
        form.instance.product = product
        form.instance.created_by = self.request.user
        return super().form_valid(form)

class TrackingUpdateView(LoginRequiredMixin, UpdateView):
    model = ProductTracking
    template_name = 'products/tracking_form.html'
    fields = ['serial_number', 'imei_number', 'barcode', 'variant', 'purchase_date', 'warranty_expiry', 'notes']

    def get_queryset(self):
        return ProductTracking.objects.filter(product__company=self.request.user.company)

# Attribute views
class AttributeListView(LoginRequiredMixin, ListView):
    model = Attribute
    template_name = 'products/attribute_list.html'
    context_object_name = 'attributes'

    def get_queryset(self):
        return Attribute.objects.filter(company=self.request.user.company)

class AttributeDetailView(LoginRequiredMixin, DetailView):
    model = Attribute
    template_name = 'products/attribute_detail.html'
    context_object_name = 'attribute'

    def get_queryset(self):
        return Attribute.objects.filter(company=self.request.user.company)

class AttributeCreateView(LoginRequiredMixin, CreateView):
    model = Attribute
    template_name = 'products/attribute_form.html'
    fields = ['name', 'data_type', 'is_required']

    def form_valid(self, form):
        form.instance.company = self.request.user.company
        return super().form_valid(form)

class AttributeUpdateView(LoginRequiredMixin, UpdateView):
    model = Attribute
    template_name = 'products/attribute_form.html'
    fields = ['name', 'data_type', 'is_required']

    def get_queryset(self):
        return Attribute.objects.filter(company=self.request.user.company)


@login_required
def import_products(request):
    """Import products from CSV (placeholder for now)"""
    if request.method == 'POST':
        messages.info(request, 'Import functionality coming soon!')
        return redirect('products:list')
    
    return render(request, 'products/import.html')


# Additional views for all sidebar menu items

class VariantListView(LoginRequiredMixin, ListView):
    """Product variants list view"""
    model = ProductVariant
    template_name = 'products/variant_list.html'
    context_object_name = 'object_list'
    paginate_by = 20

    def get_queryset(self):
        product_id = self.kwargs.get('product_id')
        if product_id:
            return ProductVariant.objects.filter(
                product_id=product_id,
                product__company=self.request.user.company
            ).select_related('product')
        return ProductVariant.objects.filter(
            product__company=self.request.user.company
        ).select_related('product')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company
        product_id = self.kwargs.get('product_id')
        
        if product_id:
            context['product'] = get_object_or_404(Product, id=product_id, company=company)
        
        # Add summary statistics
        variants = ProductVariant.objects.filter(product__company=company)
        context.update({
            'total_variants': variants.count(),
            'products_with_variants': Product.objects.filter(company=company, variants__isnull=False).distinct().count(),
            'active_variants': variants.filter(is_active=True).count(),
            'avg_price': variants.aggregate(avg_price=Avg('selling_price'))['avg_price'] or 0,
            'parent_products': Product.objects.filter(company=company, variants__isnull=False).distinct(),
        })
        
        return context


class VariantDetailView(LoginRequiredMixin, DetailView):
    """Product variant detail view"""
    model = ProductVariant
    template_name = 'products/variant_detail.html'
    context_object_name = 'variant'

    def get_queryset(self):
        return ProductVariant.objects.filter(
            product__company=self.request.user.company
        ).select_related('product')


class VariantCreateView(LoginRequiredMixin, CreateView):
    """Create new product variant"""
    model = ProductVariant
    template_name = 'products/variant_form.html'
    fields = ['product', 'name', 'sku', 'color', 'size', 'material', 'cost_price', 'selling_price', 'minimum_stock', 'is_active']

    def get_queryset(self):
        return ProductVariant.objects.filter(product__company=self.request.user.company)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product_id = self.kwargs.get('product_id')
        if product_id:
            context['product'] = get_object_or_404(Product, id=product_id, company=self.request.user.company)
        context['products'] = Product.objects.filter(company=self.request.user.company, is_active=True)
        return context

    def form_valid(self, form):
        product_id = self.kwargs.get('product_id')
        if product_id:
            form.instance.product = get_object_or_404(Product, id=product_id, company=self.request.user.company)
        messages.success(self.request, 'Product variant created successfully!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('products:variant_detail', kwargs={'pk': self.object.pk})


class VariantUpdateView(LoginRequiredMixin, UpdateView):
    """Update product variant"""
    model = ProductVariant
    template_name = 'products/variant_form.html'
    fields = ['name', 'sku', 'color', 'size', 'material', 'cost_price', 'selling_price', 'minimum_stock', 'is_active']

    def get_queryset(self):
        return ProductVariant.objects.filter(product__company=self.request.user.company)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products'] = Product.objects.filter(company=self.request.user.company, is_active=True)
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Product variant updated successfully!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('products:variant_detail', kwargs={'pk': self.object.pk})


class TrackingListView(LoginRequiredMixin, ListView):
    """Product tracking list view"""
    model = ProductTracking
    template_name = 'products/tracking_list.html'
    context_object_name = 'tracking_items'
    paginate_by = 20

    def get_queryset(self):
        product_id = self.kwargs.get('product_id')
        queryset = ProductTracking.objects.filter(
            product__company=self.request.user.company
        ).select_related('product', 'variant', 'created_by')
        
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        
        # Filter by tracking method
        tracking_method = self.request.GET.get('tracking_method')
        if tracking_method:
            if tracking_method == 'serial':
                queryset = queryset.filter(serial_number__isnull=False)
            elif tracking_method == 'imei':
                queryset = queryset.filter(imei_number__isnull=False)
            elif tracking_method == 'barcode':
                queryset = queryset.filter(barcode__isnull=False)
        
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product_id = self.kwargs.get('product_id')
        if product_id:
            context['product'] = get_object_or_404(Product, id=product_id, company=self.request.user.company)
        context['tracking_methods'] = [
            ('serial', 'Serial Number'),
            ('imei', 'IMEI Number'),
            ('barcode', 'Barcode'),
        ]
        return context


class TrackingDetailView(LoginRequiredMixin, DetailView):
    """Product tracking detail view"""
    model = ProductTracking
    template_name = 'products/tracking_detail.html'
    context_object_name = 'tracking_item'

    def get_queryset(self):
        return ProductTracking.objects.filter(
            product__company=self.request.user.company
        ).select_related('product', 'variant', 'created_by')


class TrackingCreateView(LoginRequiredMixin, CreateView):
    """Create new product tracking"""
    model = ProductTracking
    template_name = 'products/tracking_form.html'
    fields = ['product', 'variant', 'serial_number', 'imei_number', 'barcode', 'purchase_date', 'warranty_expiry', 'notes', 'is_available', 'is_active']

    def get_queryset(self):
        return ProductTracking.objects.filter(product__company=self.request.user.company)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product_id = self.kwargs.get('product_id')
        if product_id:
            context['product'] = get_object_or_404(Product, id=product_id, company=self.request.user.company)
        context['products'] = Product.objects.filter(company=self.request.user.company, is_active=True)
        return context

    def form_valid(self, form):
        product_id = self.kwargs.get('product_id')
        if product_id:
            form.instance.product = get_object_or_404(Product, id=product_id, company=self.request.user.company)
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Product tracking created successfully!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('products:tracking_detail', kwargs={'pk': self.object.pk})


class TrackingUpdateView(LoginRequiredMixin, UpdateView):
    """Update product tracking"""
    model = ProductTracking
    template_name = 'products/tracking_form.html'
    fields = ['variant', 'serial_number', 'imei_number', 'barcode', 'purchase_date', 'warranty_expiry', 'notes', 'is_available', 'is_active']

    def get_queryset(self):
        return ProductTracking.objects.filter(product__company=self.request.user.company)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products'] = Product.objects.filter(company=self.request.user.company, is_active=True)
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Product tracking updated successfully!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('products:tracking_detail', kwargs={'pk': self.object.pk})


class AttributeListView(LoginRequiredMixin, ListView):
    """Product attributes list view"""
    model = Attribute
    template_name = 'products/attributes.html'
    context_object_name = 'attributes'
    paginate_by = 20

    def get_queryset(self):
        return Attribute.objects.filter(
            company=self.request.user.company
        ).order_by('name')


class AttributeDetailView(LoginRequiredMixin, DetailView):
    """Product attribute detail view"""
    model = Attribute
    template_name = 'products/attribute_detail.html'
    context_object_name = 'attribute'

    def get_queryset(self):
        return Attribute.objects.filter(company=self.request.user.company)


class AttributeCreateView(LoginRequiredMixin, CreateView):
    """Create new product attribute"""
    model = Attribute
    template_name = 'products/attribute_form.html'
    fields = ['name', 'data_type', 'is_required', 'is_active']

    def form_valid(self, form):
        form.instance.company = self.request.user.company
        messages.success(self.request, 'Product attribute created successfully!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('products:attribute_detail', kwargs={'pk': self.object.pk})


class AttributeUpdateView(LoginRequiredMixin, UpdateView):
    """Update product attribute"""
    model = Attribute
    template_name = 'products/attribute_form.html'
    fields = ['name', 'data_type', 'is_required', 'is_active']

    def get_queryset(self):
        return Attribute.objects.filter(company=self.request.user.company)

    def form_valid(self, form):
        messages.success(self.request, 'Product attribute updated successfully!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('products:attribute_detail', kwargs={'pk': self.object.pk})


@login_required
def product_performance_view(request):
    """Product performance analytics"""
    company = request.user.company
    
    # Get product statistics
    products = Product.objects.filter(company=company)
    context = {
        'stats': {
            'total_products': products.count(),
            'active_products': products.filter(is_active=True).count(),
            'top_categories': products.values('category__name').annotate(
                count=Count('id')
            ).order_by('-count')[:10],
            'product_types': products.values('product_type').annotate(
                count=Count('id')
            ).order_by('-count'),
        },
        'tracking_stats': {
            'total_tracked': ProductTracking.objects.filter(product__company=company).count(),
            'available_items': ProductTracking.objects.filter(product__company=company, is_available=True).count(),
            'serial_tracked': ProductTracking.objects.filter(product__company=company, serial_number__isnull=False).count(),
            'imei_tracked': ProductTracking.objects.filter(product__company=company, imei_number__isnull=False).count(),
            'barcode_tracked': ProductTracking.objects.filter(product__company=company, barcode__isnull=False).count(),
        }
    }
    
    return render(request, 'products/performance.html', context)


@login_required
def inventory_reports_view(request):
    """Inventory reports view"""
    company = request.user.company
    
    # Get inventory data
    products = Product.objects.filter(company=company, is_stockable=True)
    tracking_summary = ProductTracking.objects.filter(product__company=company).aggregate(
        total_items=Count('id'),
        available_items=Count('id', filter=Q(is_available=True)),
    )
    tracking_summary['unavailable_items'] = tracking_summary['total_items'] - tracking_summary['available_items']
    
    context = {
        'stockable_products': products.count(),
        'products_with_variants': products.filter(is_variant=True).count(),
        'tracking_summary': tracking_summary,
        'category_breakdown': products.values('category__name').annotate(
            count=Count('id')
        ).order_by('-count'),
    }
    
    return render(request, 'products/inventory_reports.html', context)


@login_required 
def low_stock_alerts_view(request):
    """Low stock alerts view"""
    company = request.user.company
    
    # Find products below minimum stock (simplified logic for now)
    low_stock_products = Product.objects.filter(
        company=company,
        is_stockable=True,
        is_active=True,
        minimum_stock__gt=0
    ).order_by('minimum_stock')
    
    context = {
        'low_stock_products': low_stock_products[:50],  # Limit results
        'total_alerts': low_stock_products.count(),
    }
    
    return render(request, 'products/low_stock_alerts.html', context)


# =====================================
# PRODUCT TRACKING VIEWS
# =====================================

@login_required
def product_tracking_dashboard(request):
    """Dashboard for product tracking overview"""
    company = request.user.company
    
    # Get tracking statistics
    total_tracked_units = ProductTracking.objects.filter(
        product__company=company
    ).count()
    
    expired_units = ProductTracking.objects.filter(
        product__company=company,
        expiry_date__lt=timezone.now().date()
    ).count()
    
    expiring_soon = ProductTracking.objects.filter(
        product__company=company,
        expiry_date__gte=timezone.now().date(),
        expiry_date__lte=timezone.now().date() + timedelta(days=30)
    ).count()
    
    trackable_products = Product.objects.filter(
        company=company,
        tracking_method__in=['serial', 'imei', 'barcode', 'batch'],
        is_active=True
    ).count()
    
    # Recent tracking activities
    recent_tracking = ProductTracking.objects.filter(
        product__company=company
    ).select_related('product', 'current_warehouse').order_by('-created_at')[:10]
    
    context = {
        'stats': {
            'total_tracked_units': total_tracked_units,
            'expired_units': expired_units,
            'expiring_soon': expiring_soon,
            'trackable_products': trackable_products,
        },
        'recent_tracking': recent_tracking,
        'title': 'Product Tracking Dashboard'
    }
    
    return render(request, 'products/tracking-dashboard.html', context)


@login_required
def product_tracking_list(request):
    """List all product tracking units with filtering"""
    company = request.user.company
    
    tracking_units = ProductTracking.objects.filter(
        product__company=company
    ).select_related('product', 'current_warehouse', 'supplier', 'variant')
    
    # Calculate statistics
    from django.db.models import Count, Case, When, IntegerField
    from datetime import datetime, timedelta
    
    today = timezone.now().date()
    month_from_now = today + timedelta(days=30)
    
    stats = tracking_units.aggregate(
        available_count=Count(Case(When(status='available', then=1), output_field=IntegerField())),
        sold_count=Count(Case(When(status='sold', then=1), output_field=IntegerField())),
        expiring_count=Count(Case(
            When(expiry_date__lte=month_from_now, expiry_date__gte=today, then=1), 
            output_field=IntegerField()
        )),
        issues_count=Count(Case(
            When(status__in=['damaged', 'expired', 'quarantined'], then=1), 
            output_field=IntegerField()
        ))
    )
    
    # Filtering
    product_filter = request.GET.get('product')
    status_filter = request.GET.get('status')
    warehouse_filter = request.GET.get('warehouse')
    tracking_type_filter = request.GET.get('tracking_type')
    expiry_filter = request.GET.get('expiry')
    
    if product_filter:
        tracking_units = tracking_units.filter(product__id=product_filter)
    
    if status_filter:
        tracking_units = tracking_units.filter(status=status_filter)
    
    if warehouse_filter:
        tracking_units = tracking_units.filter(current_warehouse__id=warehouse_filter)
    
    if tracking_type_filter:
        tracking_units = tracking_units.filter(product__tracking_method=tracking_type_filter)
    
    if expiry_filter == 'expired':
        tracking_units = tracking_units.filter(expiry_date__lt=timezone.now().date())
    elif expiry_filter == 'expiring_soon':
        tracking_units = tracking_units.filter(
            expiry_date__gte=timezone.now().date(),
            expiry_date__lte=timezone.now().date() + timedelta(days=30)
        )
    
    # Search
    search_query = request.GET.get('search')
    if search_query:
        tracking_units = tracking_units.filter(
            Q(serial_number__icontains=search_query) |
            Q(imei_number__icontains=search_query) |
            Q(barcode__icontains=search_query) |
            Q(batch_number__icontains=search_query) |
            Q(product__name__icontains=search_query) |
            Q(product__sku__icontains=search_query)
        )
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(tracking_units.order_by('-created_at'), 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Filter options
    products = Product.objects.filter(
        company=company,
        tracking_method__in=['serial', 'imei', 'barcode', 'batch'],
        is_active=True
    ).order_by('name')
    
    from inventory.models import Warehouse
    warehouses = Warehouse.objects.filter(company=company, is_active=True).order_by('name')
    
    context = {
        'page_obj': page_obj,
        'products': products,
        'warehouses': warehouses,
        'tracking_types': Product.PRODUCT_TRACKING_CHOICES,
        'status_choices': ProductTracking._meta.get_field('status').choices,
        'title': 'Product Tracking Units',
        'today': today,
        'month_from_now': month_from_now,
        **stats
    }
    
    return render(request, 'products/tracking-list-enhanced.html', context)


@login_required
def product_tracking_detail(request, pk):
    """Detail view for a specific tracking unit"""
    tracking_unit = get_object_or_404(ProductTracking, pk=pk, product__company=request.user.company)
    
    context = {
        'tracking_unit': tracking_unit,
        'title': f'Tracking Unit Details - {tracking_unit.product.name}'
    }
    
    return render(request, 'products/tracking-detail.html', context)


@login_required
def product_tracking_label(request, pk):
    """Generate a printable label for a tracking unit"""
    tracking_unit = get_object_or_404(ProductTracking, pk=pk, product__company=request.user.company)
    
    context = {
        'tracking_unit': tracking_unit,
        'title': 'Tracking Label'
    }
    
    return render(request, 'products/tracking-label.html', context)
    tracking_unit = get_object_or_404(
        ProductTracking,
        pk=pk,
        product__company=request.user.company
    )
    
    # Get movement history from inventory
    from inventory.models import StockMovement
    movements = StockMovement.objects.filter(
        tracking_number=tracking_unit.get_tracking_value()
    ).order_by('-timestamp')
    
    context = {
        'tracking_unit': tracking_unit,
        'movements': movements,
        'title': f'Tracking Unit - {tracking_unit.get_tracking_value()}'
    }
    
    return render(request, 'products/tracking-detail.html', context)


@login_required
def product_tracking_add(request):
    """Add new tracking unit"""
    if request.method == 'POST':
        form = ProductTrackingForm(request.POST)
        if form.is_valid():
            tracking_unit = form.save(commit=False)
            tracking_unit.created_by = request.user
            tracking_unit.save()
            
            messages.success(request, f'Tracking unit created successfully: {tracking_unit.get_tracking_value()}')
            return redirect('product_tracking_detail', pk=tracking_unit.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProductTrackingForm()
    
    context = {
        'form': form,
        'title': 'Add Product Tracking Unit'
    }
    
    return render(request, 'products/tracking-form.html', context)


@login_required
def product_tracking_edit(request, pk):
    """Edit tracking unit"""
    tracking_unit = get_object_or_404(
        ProductTracking,
        pk=pk,
        product__company=request.user.company
    )
    
    if request.method == 'POST':
        form = ProductTrackingForm(request.POST, instance=tracking_unit)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tracking unit updated successfully.')
            return redirect('product_tracking_detail', pk=tracking_unit.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProductTrackingForm(instance=tracking_unit)
    
    context = {
        'form': form,
        'tracking_unit': tracking_unit,
        'title': f'Edit Tracking Unit - {tracking_unit.get_tracking_value()}'
    }
    
    return render(request, 'products/tracking-form.html', context)


@login_required
def bulk_tracking_import(request):
    """Bulk import tracking data"""
    if request.method == 'POST':
        form = BulkTrackingImportForm(request.user, request.POST)
        if form.is_valid():
            try:
                product = form.cleaned_data['product']
                tracking_data = form.cleaned_data['tracking_data']
                warehouse = form.cleaned_data.get('warehouse')
                
                created_count = 0
                errors = []
                
                for tracking_number in tracking_data:
                    try:
                        # Check if tracking number already exists
                        existing = ProductTracking.objects.filter(
                            product__company=request.user.company
                        )
                        
                        # Filter by the appropriate tracking field
                        if product.tracking_method == 'serial':
                            existing = existing.filter(serial_number=tracking_number)
                        elif product.tracking_method == 'imei':
                            existing = existing.filter(imei_number=tracking_number)
                        elif product.tracking_method == 'barcode':
                            existing = existing.filter(barcode=tracking_number)
                        elif product.tracking_method == 'batch':
                            existing = existing.filter(batch_number=tracking_number)
                        
                        if existing.exists():
                            errors.append(f'Tracking number {tracking_number} already exists')
                            continue
                        
                        # Create new tracking unit
                        tracking_unit = ProductTracking(
                            product=product,
                            created_by=request.user,
                            current_warehouse=warehouse
                        )
                        tracking_unit.set_tracking_value(tracking_number)
                        tracking_unit.save()
                        
                        created_count += 1
                        
                    except Exception as e:
                        errors.append(f'Error with {tracking_number}: {str(e)}')
                
                if created_count > 0:
                    messages.success(request, f'Successfully imported {created_count} tracking units.')
                
                if errors:
                    for error in errors[:10]:  # Show first 10 errors
                        messages.warning(request, error)
                    if len(errors) > 10:
                        messages.warning(request, f'... and {len(errors) - 10} more errors.')
                
                if created_count > 0:
                    return redirect('product_tracking_list')
                
            except Exception as e:
                messages.error(request, f'Error during import: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BulkTrackingImportForm(request.user)
    
    context = {
        'form': form,
        'title': 'Bulk Import Tracking Data'
    }
    
    return render(request, 'products/bulk-tracking-import.html', context)


@login_required
def expiry_alerts(request):
    """View for tracking expiry alerts"""
    company = request.user.company
    
    # Expired items
    expired_items = ProductTracking.objects.filter(
        product__company=company,
        expiry_date__lt=timezone.now().date()
    ).select_related('product', 'current_warehouse').order_by('expiry_date')
    
    # Expiring soon (next 30 days)
    expiring_soon = ProductTracking.objects.filter(
        product__company=company,
        expiry_date__gte=timezone.now().date(),
        expiry_date__lte=timezone.now().date() + timedelta(days=30)
    ).select_related('product', 'current_warehouse').order_by('expiry_date')
    
    # Expiring in 7 days (critical)
    expiring_critical = ProductTracking.objects.filter(
        product__company=company,
        expiry_date__gte=timezone.now().date(),
        expiry_date__lte=timezone.now().date() + timedelta(days=7)
    ).select_related('product', 'current_warehouse').order_by('expiry_date')
    
    context = {
        'expired_items': expired_items,
        'expiring_soon': expiring_soon,
        'expiring_critical': expiring_critical,
        'title': 'Product Expiry Alerts'
    }
    
    return render(request, 'products/expiry-alerts.html', context)


# =====================================
# AJAX VIEWS FOR DYNAMIC FORMS
# =====================================

@login_required
def get_product_tracking_info(request):
    """Get tracking information for a product (AJAX)"""
    product_id = request.GET.get('product_id')
    
    if not product_id:
        return JsonResponse({'success': False, 'error': 'No product ID provided'})
    
    try:
        product = Product.objects.get(id=product_id, company=request.user.company)
        
        data = {
            'success': True,
            'tracking_method': product.tracking_method,
            'tracking_method_display': product.get_tracking_method_display(),
            'requires_individual_tracking': product.requires_individual_tracking,
            'requires_expiry_tracking': product.requires_expiry_tracking,
            'requires_batch_tracking': product.requires_batch_tracking,
            'shelf_life_days': product.shelf_life_days,
            'is_trackable': product.is_trackable(),
            'tracking_field_name': product.get_tracking_field_name(),
        }
        
        return JsonResponse(data)
        
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Product not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def search_tracking_units(request):
    """Search tracking units (AJAX)"""
    query = request.GET.get('q', '')
    product_id = request.GET.get('product_id')
    
    tracking_units = ProductTracking.objects.filter(
        product__company=request.user.company,
        status='available'
    )
    
    if product_id:
        tracking_units = tracking_units.filter(product__id=product_id)
    
    if query:
        tracking_units = tracking_units.filter(
            Q(serial_number__icontains=query) |
            Q(imei_number__icontains=query) |
            Q(barcode__icontains=query) |
            Q(batch_number__icontains=query)
        )
    
    tracking_units = tracking_units.select_related('product')[:10]
    
    data = []
    for unit in tracking_units:
        data.append({
            'id': unit.id,
            'tracking_value': unit.get_tracking_value(),
            'product_name': unit.product.name,
            'tracking_type': unit.product.get_tracking_method_display(),
            'warehouse': unit.current_warehouse.name if unit.current_warehouse else '',
            'expiry_date': unit.expiry_date.isoformat() if unit.expiry_date else None,
        })
    
    return JsonResponse({'tracking_units': data})


# Add missing imports
from django.utils import timezone
from datetime import timedelta
