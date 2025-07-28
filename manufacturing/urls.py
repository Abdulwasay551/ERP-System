from django.urls import path
from .views import (
    manufacturing_dashboard, boms_ui, boms_add, boms_edit, boms_delete,
    workorders_ui, production_ui, quality_ui
)

app_name = 'manufacturing'

urlpatterns = [
    path('', manufacturing_dashboard, name='manufacturing_dashboard'),
    path('dashboard/', manufacturing_dashboard, name='manufacturing_dashboard'),
    path('dashboard-ui/', manufacturing_dashboard, name='manufacturing_dashboard_ui'),
    path('boms/', boms_ui, name='manufacturing_boms_ui'),
    path('boms-ui/', boms_ui, name='manufacturing_boms_ui'),
    path('boms/add/', boms_add, name='manufacturing_boms_add'),
    path('boms-add/', boms_add, name='manufacturing_boms_add'),
    path('boms/edit/<int:pk>/', boms_edit, name='manufacturing_boms_edit'),
    path('boms-edit/<int:pk>/', boms_edit, name='manufacturing_boms_edit'),
    path('boms/delete/<int:pk>/', boms_delete, name='manufacturing_boms_delete'),
    path('boms-delete/<int:pk>/', boms_delete, name='manufacturing_boms_delete'),
    path('workorders/', workorders_ui, name='manufacturing_workorders_ui'),
    path('workorders-ui/', workorders_ui, name='manufacturing_workorders_ui'),
    path('production/', production_ui, name='manufacturing_production_ui'),
    path('production-ui/', production_ui, name='manufacturing_production_ui'),
    path('quality/', quality_ui, name='manufacturing_quality_ui'),
    path('quality-ui/', quality_ui, name='manufacturing_quality_ui'),
]