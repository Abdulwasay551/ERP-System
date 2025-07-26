from django.urls import path
from .views import (
    boms_ui, boms_add, boms_edit, boms_delete,
    workorders_ui, production_ui, quality_ui
)

urlpatterns = [
    path('boms-ui/', boms_ui, name='manufacturing_boms_ui'),
    path('boms-add/', boms_add, name='manufacturing_boms_add'),
    path('boms-edit/<int:pk>/', boms_edit, name='manufacturing_boms_edit'),
    path('boms-delete/<int:pk>/', boms_delete, name='manufacturing_boms_delete'),
    path('workorders-ui/', workorders_ui, name='manufacturing_workorders_ui'),
    path('production-ui/', production_ui, name='manufacturing_production_ui'),
    path('quality-ui/', quality_ui, name='manufacturing_quality_ui'),
]