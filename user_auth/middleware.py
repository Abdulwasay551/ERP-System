from django.utils.deprecation import MiddlewareMixin
from .models import ActivityLog

class ActivityLogMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        # Exclude admin, static, and media paths
        if request.path.startswith('/admin') or request.path.startswith('/static') or request.path.startswith('/media'):
            return None
        if request.user.is_authenticated:
            ActivityLog.objects.create(
                user=request.user,
                action=f"{request.method} {request.path}",
                details=f"View: {view_func.__module__}.{view_func.__name__}",
                ip_address=self.get_client_ip(request)
            )
        return None

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip 