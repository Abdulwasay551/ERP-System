from django.urls import path
from .views import stockitems_ui, stockitems_add, stockitems_edit, stockitems_delete

urlpatterns = [
    path('stockitems-ui/', stockitems_ui, name='inventory_stockitems_ui'),
    path('stockitems-add/', stockitems_add, name='inventory_stockitems_add'),
    path('stockitems-edit/<int:pk>/', stockitems_edit, name='inventory_stockitems_edit'),
    path('stockitems-delete/<int:pk>/', stockitems_delete, name='inventory_stockitems_delete'),
] 