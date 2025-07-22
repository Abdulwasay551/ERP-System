from django.urls import path
from .views import boms_ui

urlpatterns = [
    path('boms-ui/', boms_ui, name='manufacturing_boms_ui'),
] 