from django.urls import path
from .api_views import health, global_search

urlpatterns = [
    path('health/', health, name='core-health'),
    path('search/', global_search, name='core-search'),
]
