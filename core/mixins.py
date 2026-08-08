from django.contrib.contenttypes.models import ContentType
from rest_framework import permissions
from rest_framework.response import Response

from user_auth.permissions import IsOwnerOrManager
from .models import RecordDeletionLog


def resolve_company(instance):
    """Most soft-deletable models have their own `company` FK; a couple (like
    ProductTracking) only reach it via a parent relation."""
    company = getattr(instance, 'company', None)
    if company is not None:
        return company
    product = getattr(instance, 'product', None)
    if product is not None:
        return product.company
    return None


def log_deletion(instance, user, action):
    RecordDeletionLog.objects.create(
        company=resolve_company(instance),
        content_type=ContentType.objects.get_for_model(instance.__class__),
        object_id=instance.pk,
        object_repr=str(instance),
        action=action,
        performed_by=user,
    )


class SoftDeleteViewSetMixin:
    """Mix into a ModelViewSet whose model uses SoftDeleteMixin (or the equivalent
    hand-rolled fields on User): `destroy()` soft-deletes instead of hard-deleting and
    is gated to Owner/Manager regardless of the ViewSet's other permission_classes.

    `cascade_to`: attribute names on the instance returning a related manager whose
    rows should be soft-deleted alongside the parent (e.g. an Invoice's `items` and
    `payments`) - kept deliberately narrow, see the plan's design-decisions section.
    """
    cascade_to = []

    def get_permissions(self):
        if self.action in ('destroy', 'edit'):
            return [permissions.IsAuthenticated(), IsOwnerOrManager()]
        return super().get_permissions()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.soft_delete(request.user)
        log_deletion(instance, request.user, 'deleted')
        for attr in self.cascade_to:
            related = getattr(instance, attr, None)
            if related is None:
                continue
            for child in related.all():
                if hasattr(child, 'soft_delete'):
                    child.soft_delete(request.user)
                    log_deletion(child, request.user, 'deleted')
        return Response(status=204)
