"""
Phase C's outbox capture: after a successful write to one of a small whitelist of
push-back-eligible endpoints, records enough to replay the exact same request against
production later - see `core/desktop_sync_queue.py`'s module docstring for why a raw
request replay, not a row snapshot.

Only the highest-value, single-clean-entry-point creation endpoints are wired up in
this first pass (Customer, Payment, PurchasePayment, and the two "one call, multiple
rows" checkout-style endpoints, pos_checkout and vendor_invoice_create) - see the desktop
app plan's own scoping note. Everything else stays pull-only for now (Phase A already
tells the Desktop Sync screen to say so).

File-upload (multipart) requests are deliberately NOT captured here - `payment.attachment`
on pos_checkout/PaymentViewSet in particular. Replaying a file upload would mean storing
the file bytes in this table too, out of scope for this pass; a payment recorded offline
with a receipt photo attached will sync the payment itself but not the attachment.

A no-op everywhere except the desktop app (`settings.IS_DESKTOP`) - registered
unconditionally in MIDDLEWARE so production and desktop run the exact same settings
file, matching the rest of this project's "one codebase, gated by an env flag" pattern
(see core/desktop_sync.py's module docstring for the same reasoning).
"""
import json
import uuid

from django.conf import settings

# path -> a short label for the queue entry's `summary` column (Sync Conflicts screen).
PUSH_ELIGIBLE_PATHS = {
    '/api/sales/pos/checkout/': 'POS sale',
    '/api/sales/payments/': 'Customer payment',
    '/api/crm/customers/': 'New customer',
    '/api/purchase/vendor-invoice/': 'Vendor bill',
    '/api/purchase/purchase-payments/': 'Supplier payment',
}


class DesktopSyncQueueMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        eligible = (
            getattr(settings, 'IS_DESKTOP', False)
            and request.method in ('POST', 'PUT', 'PATCH')
            and request.path in PUSH_ELIGIBLE_PATHS
            and (request.content_type or '').startswith('application/json')
        )
        if eligible:
            # Force Django to read-and-cache request.body NOW, before the view (and
            # DRF's own stream-based JSON parsing) runs - otherwise DRF's parser may
            # consume the raw stream directly without ever populating the underlying
            # HttpRequest's cached _body, and reading request.body afterward raises
            # RawPostDataException. Accessing it here first makes Django replace the
            # stream with a re-readable BytesIO over the cached bytes, so the view's
            # own request.data parsing downstream still works unchanged.
            _ = request.body

        response = self.get_response(request)

        if eligible:
            self._maybe_queue(request, response)
        return response

    def _maybe_queue(self, request, response):
        if not (200 <= response.status_code < 300):
            return
        user = getattr(request, 'user', None)
        company = getattr(user, 'company', None)
        if company is None:
            return
        try:
            payload = json.loads(request.body or b'{}')
        except (ValueError, UnicodeDecodeError):
            return

        client_request_id = payload.get('client_request_id') or uuid.uuid4().hex
        payload['client_request_id'] = client_request_id

        try:
            response_data = json.loads((response.content or b'{}').decode('utf-8'))
        except (ValueError, UnicodeDecodeError):
            response_data = {}

        from core.desktop_sync_queue import DesktopSyncQueueEntry
        # get_or_create, not create: defensive against this ever running twice for the
        # same request (shouldn't happen for a single response) - never raise an
        # IntegrityError up through response handling over a queue-logging concern.
        DesktopSyncQueueEntry.objects.get_or_create(
            client_request_id=client_request_id,
            defaults=dict(
                company=company,
                method=request.method,
                path=request.path,
                payload_json=json.dumps(payload),
                response_json=json.dumps(response_data),
                summary=PUSH_ELIGIBLE_PATHS[request.path],
            ),
        )
