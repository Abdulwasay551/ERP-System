from rest_framework.permissions import BasePermission

class RoleIn(BasePermission):
    """
    Allow access only to users whose role name is in `allowed_roles`. Owner is
    always allowed regardless of `allowed_roles`, since Owner has full access.
    Usage: set `allowed_roles = ['Manager', 'Cashier']` as a class attribute on the view.
    """
    allowed_roles = []

    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated or not getattr(user, 'role', None):
            return False
        allowed_roles = getattr(view, 'allowed_roles', self.allowed_roles)
        return user.role.name == 'Owner' or user.role.name in allowed_roles

class DepartmentLevelPermission(BasePermission):
    """
    Allow access only to users in a specific department and with a minimum level.
    Usage: Add to permission_classes in your ViewSet and set required_department and min_level attributes.
    """
    required_department = None
    min_level = 1

    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated or not hasattr(user, 'role') or not user.role:
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