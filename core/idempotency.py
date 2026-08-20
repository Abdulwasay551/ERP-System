"""
Idempotency support for offline-capable writes (mobile POS checkout, vendor invoice
creation, payments, expenses, customer/supplier creation): if a queued write is retried
after its response never reached the device (dropped connection, app killed mid-request),
the retry must not create a second Invoice/Bill/Payment/etc. A client that includes a
`client_request_id` in the POST body gets that guarantee; a client that doesn't is
completely unaffected (this is purely additive - no existing caller breaks).

Two entry points sharing one underlying model:
- `@idempotent` decorator, for `@api_view` function-based views (pos_checkout,
  vendor_invoice_create).
- `IdempotentCreateMixin`, for ModelViewSets whose `create()` should get the same
  guarantee (Payment, PurchasePayment, Expense, Customer, Supplier).
"""
import json
from functools import wraps

from django.db import models
from rest_framework.response import Response
from rest_framework.utils.encoders import JSONEncoder


class IdempotencyKey(models.Model):
    """One row per successfully-completed request that supplied a client_request_id.
    A repeat of the same (company, client_request_id) returns the stored response
    instead of re-running the (side-effecting) view."""
    # String reference ('app_label.ModelName'), not an eager `from user_auth.models
    # import Company` - this module now gets imported from core/models.py (so
    # apps.get_model('core', 'IdempotencyKey') always finds it, see that file's
    # comment), and user_auth/models.py itself imports from core.models before
    # `Company` is defined there - an eager import here would deadlock that cycle.
    # Django resolves string FK references lazily, after all apps have loaded.
    company = models.ForeignKey('user_auth.Company', on_delete=models.CASCADE, related_name='idempotency_keys')
    client_request_id = models.CharField(max_length=100)
    response_status = models.PositiveSmallIntegerField()
    response_body = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('company', 'client_request_id')

    def __str__(self):
        return f'{self.company_id}:{self.client_request_id}'


def _find_existing(company, client_request_id):
    if not (company and client_request_id):
        return None
    return IdempotencyKey.objects.filter(company=company, client_request_id=client_request_id).first()


def _store(company, client_request_id, response):
    if not (company and client_request_id) or not (200 <= response.status_code < 300):
        return
    # response.data can hold raw Python objects a view built by hand (a datetime,
    # Decimal, etc.) rather than already-stringified Serializer output - DRF's own
    # renderer handles those fine at response time, but Django's plain JSONField here
    # uses the stdlib json encoder underneath, which doesn't know what a datetime is.
    # Round-tripping through DRF's JSONEncoder first (the same one the real HTTP
    # response gets rendered with) normalizes everything into JSON-safe primitives
    # before it ever reaches the database - a real bug this exact way already hit
    # bill_confirm_received's raw `received_at` datetime once push-back sync started
    # actually replaying it with a client_request_id attached.
    safe_body = json.loads(json.dumps(response.data, cls=JSONEncoder))
    # get_or_create, not create: a genuine race (two near-simultaneous retries) should
    # silently keep whichever row won, not raise an IntegrityError up into the response.
    IdempotencyKey.objects.get_or_create(
        company=company, client_request_id=client_request_id,
        defaults={'response_status': response.status_code, 'response_body': safe_body},
    )


def idempotent(view_func):
    """Wraps an `@api_view` function. Must be the innermost decorator (closest to the
    function) so request.user/request.data are already populated by the time it runs:
        @api_view(['POST'])
        @permission_classes([...])
        @idempotent
        def my_view(request): ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        client_request_id = request.data.get('client_request_id')
        company = getattr(request.user, 'company', None)
        existing = _find_existing(company, client_request_id)
        if existing:
            return Response(existing.response_body, status=existing.response_status)
        response = view_func(request, *args, **kwargs)
        _store(company, client_request_id, response)
        return response
    return wrapper


class IdempotentCreateMixin:
    """Mix into a ModelViewSet (before viewsets.ModelViewSet in the MRO) to give its
    `create()` action the same replay-safe guarantee as `@idempotent`."""

    def create(self, request, *args, **kwargs):
        client_request_id = request.data.get('client_request_id')
        company = getattr(request.user, 'company', None)
        existing = _find_existing(company, client_request_id)
        if existing:
            return Response(existing.response_body, status=existing.response_status)
        response = super().create(request, *args, **kwargs)
        _store(company, client_request_id, response)
        return response
