from django.urls import path
from .views import boms_ui, boms_add, boms_edit, boms_delete

urlpatterns = [
    path('boms-ui/', boms_ui, name='manufacturing_boms_ui'),
    path('boms-add/', boms_add, name='manufacturing_boms_add'),
    path('boms-edit/<int:pk>/', boms_edit, name='manufacturing_boms_edit'),
    path('boms-delete/<int:pk>/', boms_delete, name='manufacturing_boms_delete'),
] 