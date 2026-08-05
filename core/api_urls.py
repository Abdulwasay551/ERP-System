from django.urls import path
from .api_views import health

urlpatterns = [
    path('health/', health, name='core-health'),
]
