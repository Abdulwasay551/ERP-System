"""
Phase C's outbox capture: after a successful write to one of a whitelist of
push-back-eligible endpoints, records enough to replay the exact same request against
production later - see `core/desktop_sync_queue.py`'s module docstring for why a raw
request replay, not a row snapshot.

Only single-clean-entry-point creation/update endpoints high-value enough for a shop to
plausibly use while offline are wired up here (see PUSH_ELIGIBLE_PATTERNS below) -
everything else stays pull-only for now (Phase A already tells the Desktop Sync screen
to say so).

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
import re
import threading
import uuid

from django.conf import settings

# (compiled path pattern, short label for the queue entry's `summary` column) - checked
# in order, first match wins. A regex (not an exact-match dict) so a path with an id in
# the middle (e.g. a Customer PATCH, or the bill-receiving actions) can be whitelisted
# too, not just a fixed collection-create URL.
PUSH_ELIGIBLE_PATTERNS = [
    (re.compile(r'^/api/sales/pos/checkout/$'), 'POS sale'),
    (re.compile(r'^/api/sales/payments/$'), 'Customer payment'),
    (re.compile(r'^/api/sales/returns/process/$'), 'Sales return'),
    (re.compile(r'^/api/crm/customers/$'), 'New customer'),
    (re.compile(r'^/api/crm/customers/\d+/$'), 'Customer update'),
    (re.compile(r'^/api/purchase/vendor-invoice/$'), 'Vendor bill'),
    (re.compile(r'^/api/purchase/purchase-payments/$'), 'Supplier payment'),
    (re.compile(r'^/api/purchase/suppliers/$'), 'New supplier'),
    (re.compile(r'^/api/purchase/bills/\d+/receive-items/$'), 'Receive items'),
    (re.compile(r'^/api/purchase/bills/\d+/confirm-received/$'), 'Confirm received'),
    (re.compile(r'^/api/purchase/returns/process/$'), 'Vendor return'),
    (re.compile(r'^/api/products/products/$'), 'New product'),
    (re.compile(r'^/api/accounting/expenses/$'), 'New expense'),
]


def _match_eligible_path(path):
    """Returns the summary label for the first pattern `path` matches, or None."""
    for pattern, summary in PUSH_ELIGIBLE_PATTERNS:
        if pattern.match(path):
            return summary
    return None


class DesktopSyncQueueMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        summary = (
            _match_eligible_path(request.path)
            if (
                getattr(settings, 'IS_DESKTOP', False)
                and request.method in ('POST', 'PUT', 'PATCH')
                and (request.content_type or '').startswith('application/json')
            )
            else None
        )
        if summary:
            # Force Django to read-and-cache request.body NOW, before the view (and
            # DRF's own stream-based JSON parsing) runs - otherwise DRF's parser may
            # consume the raw stream directly without ever populating the underlying
            # HttpRequest's cached _body, and reading request.body afterward raises
            # RawPostDataException. Accessing it here first makes Django replace the
            # stream with a re-readable BytesIO over the cached bytes, so the view's
            # own request.data parsing downstream still works unchanged.
            _ = request.body

        response = self.get_response(request)

        if summary:
            self._maybe_queue(request, response, summary)
        return response

    def _maybe_queue(self, request, response, summary):
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
                summary=summary,
            ),
        )

        # Real-time sync-on-write: don't make the shop wait up to
        # DEFAULT_SYNC_INTERVAL_SECONDS (or a manual Sync Now click) for a write made
        # while genuinely online to actually reach production. Fire-and-forget - must
        # never block this response. Silently skipped (not queued twice, not lost) if a
        # drain is already running elsewhere - see core.desktop_sync's _DRAIN_LOCK.
        threading.Thread(target=self._trigger_drain, daemon=True, name='desktop-sync-realtime').start()

    def _trigger_drain(self):
        try:
            from core.desktop_sync import get_loop
            get_loop().drain()
        except Exception as e:
            # Never let a background sync attempt surface as an error anywhere a real
            # user would see it - same "log and move on" philosophy as the periodic
            # loop's own _run() catch-all.
            print(f'[desktop_sync_middleware] Real-time drain trigger failed: {e}')
