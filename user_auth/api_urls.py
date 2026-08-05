from rest_framework.routers import DefaultRouter
from django.urls import path
from .api_views import CompanyViewSet, RoleViewSet, UserViewSet, me

router = DefaultRouter()
router.register(r'companies', CompanyViewSet, basename='company')
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'users', UserViewSet, basename='user')

urlpatterns = router.urls + [
    path('me/', me, name='auth-me'),
]
