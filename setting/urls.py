"""
URL configuration for setting project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from user_auth.views import login_view, logout_view, dashboard
from rest_framework.authtoken.views import obtain_auth_token
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('', dashboard, name='dashboard'),
    path('crm/', include('crm.urls')),
    path('sales/', include('sales.urls')),
    path('purchase/', include('purchase.urls')),
    path('inventory/', include('inventory.urls')),
    path('accounting/', include('accounting.urls')),
    path('hr/', include('hr.urls')),
    path('project_mgmt/', include('project_mgmt.urls')),
    path('manufacturing/', include('manufacturing.urls')),
    path('api/crm/', include('crm.api_urls')),
    path('api/sales/', include('sales.api_urls')),
    path('api/purchase/', include('purchase.api_urls')),
    path('api/inventory/', include('inventory.api_urls')),
    path('api/accounting/', include('accounting.api_urls')),
    path('api/hr/', include('hr.api_urls')),
    path('api/project/', include('project_mgmt.api_urls')),
    path('api/manufacturing/', include('manufacturing.api_urls')),
    path('api/token-auth/', obtain_auth_token, name='api_token_auth'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
