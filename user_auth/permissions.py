from rest_framework.permissions import BasePermission

class RoleIn(BasePermission):
    """
    Allow access only to users whose role name is in `allowed_roles`. Owner is
    always allowed regardless of `allowed_roles`, since Owner has full access.
    Django superusers (e.g. an account made via createsuperuser, which has no Role
    assigned) also always pass - otherwise a role-less superuser gets 403'd on every
    role-gated endpoint despite is_superuser=True, which reads as "broken permissions"
    rather than "missing role".
    Usage: set `allowed_roles = ['Manager', 'Cashier']` as a class attribute on the view.
    """
    allowed_roles = []

    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        if not getattr(user, 'role', None):
            return False
        allowed_roles = getattr(view, 'allowed_roles', self.allowed_roles)
        return user.role.name == 'Owner' or user.role.name in allowed_roles

class IsOwnerOrManager(RoleIn):
    """
    Shared "admin only" gate - Owner always passes (via RoleIn), Manager is the only
    other role allowed. Centralizes what used to be copy-pasted as a locally-defined
    `ManagerOrOwner(RoleIn): allowed_roles = ['Manager']` in accounting/api_views.py
    and user_auth/api_views.py. Used for destructive actions (delete/restore/purge)
    and staff management.
    """
    allowed_roles = ['Manager']

class DepartmentLevelPermission(BasePermission):
    """
    Allow access only to users in a specific department and with a minimum level.
    Usage: Add to permission_classes in your ViewSet and set required_department and min_level attributes.
    """
    required_department = None
    min_level = 1

    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        if not hasattr(user, 'role') or not user.role:
            return False
        if user.role.name == 'Owner':
            return True
        required_department = getattr(view, 'required_department', self.required_department)
        min_level = getattr(view, 'min_level', self.min_level)
        if required_department and user.role.department != required_department:
            return False
        if user.role.level > min_level:
            return False
        return True 