from rest_framework.permissions import BasePermission

class DepartmentLevelPermission(BasePermission):
    """
    Allow access only to users in a specific department and with a minimum level.
    Usage: Add to permission_classes in your ViewSet and set required_department and min_level attributes.
    """
    required_department = None
    min_level = 1

    def has_permission(self, request, view):
        user = request.user
        required_department = getattr(view, 'required_department', self.required_department)
        min_level = getattr(view, 'min_level', self.min_level)
        if not user.is_authenticated or not hasattr(user, 'role') or not user.role:
            return False
        if required_department and user.role.department != required_department:
            return False
        if user.role.level > min_level:
            return False
        return True 