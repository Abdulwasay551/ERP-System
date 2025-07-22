from django.urls import path
from .views import purchaseorders_ui

urlpatterns = [
    path('purchaseorders-ui/', purchaseorders_ui, name='purchase_purchaseorders_ui'),
] 