from django.urls import path
from .views import purchaseorders_ui, purchaseorders_add, purchaseorders_edit, purchaseorders_delete

urlpatterns = [
    path('purchaseorders-ui/', purchaseorders_ui, name='purchase_purchaseorders_ui'),
    path('purchaseorders-add/', purchaseorders_add, name='purchase_purchaseorders_add'),
    path('purchaseorders-edit/<int:pk>/', purchaseorders_edit, name='purchase_purchaseorders_edit'),
    path('purchaseorders-delete/<int:pk>/', purchaseorders_delete, name='purchase_purchaseorders_delete'),
] 