from django.urls import path, include
from . import views

app_name = 'products'

urlpatterns = [
    # API URLs
    path('api/', include('products.api_urls')),
    
    # Dashboard and main views
    path('', views.ProductDashboardView.as_view(), name='dashboard'),
    path('list/', views.ProductListView.as_view(), name='list'),
    path('create/', views.ProductCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ProductDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.ProductUpdateView.as_view(), name='update'),
    path('<int:pk>/toggle-active/', views.toggle_product_active, name='toggle_active'),
    path('<int:pk>/duplicate/', views.duplicate_product, name='duplicate'),
    
    # Category management
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_update'),
    
    # Variant management
    path('variants/', views.VariantListView.as_view(), name='variant_list'),
    path('variants/create/', views.VariantCreateView.as_view(), name='variant_create_generic'),
    path('<int:product_id>/variants/', views.VariantListView.as_view(), name='variant_list_by_product'),
    path('<int:product_id>/variants/create/', views.VariantCreateView.as_view(), name='variant_create'),
    path('variants/<int:pk>/', views.VariantDetailView.as_view(), name='variant_detail'),
    path('variants/<int:pk>/edit/', views.VariantUpdateView.as_view(), name='variant_update'),
    
    # Tracking management
    path('tracking/', views.product_tracking_list, name='tracking_list'),
    path('tracking/dashboard/', views.product_tracking_dashboard, name='tracking_dashboard'),
    path('tracking/add/', views.product_tracking_add, name='tracking_add'),
    path('tracking/<int:pk>/', views.product_tracking_detail, name='tracking_detail'),
    path('tracking/<int:pk>/edit/', views.product_tracking_edit, name='tracking_edit'),
    path('tracking/bulk-import/', views.bulk_tracking_import, name='bulk_tracking_import'),
    path('tracking/expiry-alerts/', views.expiry_alerts, name='expiry_alerts'),
    
    # Legacy tracking URLs (for backward compatibility)
    path('<int:product_id>/tracking/', views.TrackingListView.as_view(), name='tracking_list_by_product'),
    path('<int:product_id>/tracking/create/', views.TrackingCreateView.as_view(), name='tracking_create'),
    path('tracking-legacy/<int:pk>/', views.TrackingDetailView.as_view(), name='tracking_detail_legacy'),
    path('tracking-legacy/<int:pk>/edit/', views.TrackingUpdateView.as_view(), name='tracking_update_legacy'),
    
    # Attribute management
    path('attributes/', views.AttributeListView.as_view(), name='attribute_list'),
    path('attributes/create/', views.AttributeCreateView.as_view(), name='attribute_create'),
    path('attributes/<int:pk>/', views.AttributeDetailView.as_view(), name='attribute_detail'),
    path('attributes/<int:pk>/edit/', views.AttributeUpdateView.as_view(), name='attribute_update'),
    
    # Reports and Analytics
    path('performance/', views.product_performance_view, name='performance'),
    path('inventory-reports/', views.inventory_reports_view, name='inventory_reports'),
    path('low-stock-alerts/', views.low_stock_alerts_view, name='low_stock_alerts'),
    
    # Bulk operations
    path('bulk-toggle-active/', views.bulk_toggle_active, name='bulk_toggle_active'),
    path('export/', views.export_products, name='export'),
    path('import/', views.import_products, name='import'),
    
    # AJAX endpoints
    path('ajax/product-tracking-info/', views.get_product_tracking_info, name='ajax_product_tracking_info'),
    path('ajax/search-tracking-units/', views.search_tracking_units, name='ajax_search_tracking_units'),
]
