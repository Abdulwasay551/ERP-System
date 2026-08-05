from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import Company, Role, User
from .serializers import CompanySerializer, RoleSerializer, UserSerializer
from .permissions import RoleIn


class ManagerOrOwner(RoleIn):
    allowed_roles = ['Manager']


class CompanyViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only: this shop's own company record (not multi-tenant management in Phase 1)."""
    serializer_class = CompanySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Company.objects.filter(pk=self.request.user.company_id)


class RoleViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only: roles are seeded (Owner/Manager/Cashier/Salesman/Warehouse), not
    managed via API in Phase 1."""
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Role.objects.filter(is_active=True)


class UserViewSet(viewsets.ModelViewSet):
    """Staff accounts for this company. Only Manager/Owner can list/create/edit users."""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, ManagerOrOwner]

    def get_queryset(self):
        return User.objects.filter(company=self.request.user.company)

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def me(request):
    """The logged-in user's own profile - almost always needed right after login."""
    return Response(UserSerializer(request.user).data)
