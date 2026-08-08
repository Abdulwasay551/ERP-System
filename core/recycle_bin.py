"""
Cross-model recycle bin: aggregates every soft-deleted row for the logged-in user's
company, and offers restore/purge/empty actions - all Owner/Manager only.

The model imports are deliberately deferred into functions (not module scope) because
`core` is imported by every other app's models.py (via SoftDeleteMixin) - importing
those apps' models back into core at module load time would create an import cycle.
"""
from django.utils import timezone

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from user_auth.permissions import IsOwnerOrManager
from .mixins import log_deletion
from .models import RecordDeletionLog


def _registry():
    from sales.models import Invoice, Payment
    from purchase.models import Bill, PurchasePayment, Supplier
    from crm.models import Customer
    from products.models import Product, ProductTracking
    from accounting.models import Expense
    from user_auth.models import User

    # (model, lookup used to scope a queryset to the requesting user's company)
    return [
        (Invoice, 'company'),
        (Payment, 'company'),
        (Bill, 'company'),
        (PurchasePayment, 'company'),
        (Supplier, 'company'),
        (Customer, 'company'),
        (Product, 'company'),
        (ProductTracking, 'product__company'),
        (Expense, 'company'),
        (User, 'company'),
    ]


def _label(model):
    return f'{model._meta.app_label}.{model._meta.model_name}'


def _find_model(label):
    for model, _lookup in _registry():
        if _label(model) == label:
            return model
    return None


@api_view(['GET'])
@permission_classes([IsOwnerOrManager])
def recycle_bin_list(request):
    company = request.user.company
    items = []
    for model, lookup in _registry():
        qs = model.all_objects.filter(is_deleted=True, **{lookup: company}).select_related('deleted_by')
        for obj in qs:
            items.append({
                'model': _label(model),
                'id': obj.pk,
                'repr': str(obj),
                'deleted_at': obj.deleted_at,
                'deleted_by': obj.deleted_by.email if obj.deleted_by else None,
            })
    items.sort(key=lambda i: i['deleted_at'] or timezone.now(), reverse=True)
    return Response({'results': items, 'count': len(items)})


def _get_instance(request):
    label = request.data.get('model')
    obj_id = request.data.get('id')
    model = _find_model(label) if label else None
    if not model or not obj_id:
        return None, Response({'error': 'model and id are required.'}, status=400)
    try:
        instance = model.all_objects.get(pk=obj_id)
    except model.DoesNotExist:
        return None, Response({'error': 'Not found.'}, status=404)
    # Company scoping - never let one company touch another's soft-deleted rows.
    company = request.user.company
    lookup = next(l for m, l in _registry() if m is model)
    scoped = model.all_objects.filter(pk=obj_id, **{lookup: company}).exists()
    if not scoped:
        return None, Response({'error': 'Not found.'}, status=404)
    return instance, None


@api_view(['POST'])
@permission_classes([IsOwnerOrManager])
def recycle_bin_restore(request):
    instance, error = _get_instance(request)
    if error:
        return error
    if not instance.is_deleted:
        return Response({'error': 'Not currently deleted.'}, status=400)
    instance.restore()
    log_deletion(instance, request.user, 'restored')
    _restore_cascaded_children(instance, request.user)
    return Response({'status': 'restored'})


def _restore_cascaded_children(instance, user):
    """Mirrors SoftDeleteViewSetMixin.cascade_to on the ViewSet side - restoring a
    parent brings its cascaded children back too, matching what deleting it took down
    with it. Only Invoice->Payment and Bill->PurchasePayment cascade (see plan)."""
    from sales.models import Invoice, Payment
    from purchase.models import Bill, PurchasePayment

    if isinstance(instance, Invoice):
        children = Payment.all_objects.filter(invoice=instance, is_deleted=True)
    elif isinstance(instance, Bill):
        children = PurchasePayment.all_objects.filter(bill=instance, is_deleted=True)
    else:
        children = []
    for child in children:
        child.restore()
        log_deletion(child, user, 'restored')


@api_view(['POST'])
@permission_classes([IsOwnerOrManager])
def recycle_bin_purge(request):
    instance, error = _get_instance(request)
    if error:
        return error
    if not instance.is_deleted:
        return Response({'error': 'Only soft-deleted items can be purged - delete it first.'}, status=400)
    log_deletion(instance, request.user, 'purged')
    instance.delete()
    return Response({'status': 'purged'})


@api_view(['POST'])
@permission_classes([IsOwnerOrManager])
def recycle_bin_empty(request):
    company = request.user.company
    purged_count = 0
    for model, lookup in _registry():
        for obj in list(model.all_objects.filter(is_deleted=True, **{lookup: company})):
            log_deletion(obj, request.user, 'purged')
            obj.delete()
            purged_count += 1
    return Response({'status': 'emptied', 'purged_count': purged_count})
