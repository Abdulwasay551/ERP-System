"""
Phase A's automatic pull-sync: keeps the desktop app's local SQLite mirror fresh from
production whenever it can reach it. When it can't, this silently does nothing (not an
error) - the desktop app is already fully usable against whatever data it last had, per
its own local-first architecture (see desktop_server.py's module docstring).

Only meaningful under the desktop app's frozen `desktop_server.py` entry point
(USE_SQLITE=True) - importing this module server-side (production) is harmless (no
thread starts unless `start()` is called), but nothing here is ever wired into the
production deployment's own request/response cycle.

Credentials (a production refresh token) are stored outside the local SQLite DB
entirely, in `%APPDATA%\\MobileCornerERP\\sync_config.json`, DPAPI-encrypted via
`pywin32`'s `win32crypt` - deliberately NOT a DB row, so it never ends up inside a
Phase B backup export (a shop owner handing a `.json` backup file to someone shouldn't
also be handing over a production login token).
"""
import json
import os
import re
import threading
import time
from pathlib import Path

from django.utils import timezone

# Guards every drain() call (the periodic loop, a real-time per-write trigger, and a
# manual Sync Now button all eventually call drain()) so two cycles can never run
# concurrently and double-process the same 'pending' queue rows - see drain()'s own
# docstring. Process-wide, not per-loop-instance: get_loop() is already a module-level
# singleton, but a lock living on the class instance would still theoretically allow two
# instances to race if one were ever constructed by mistake.
_DRAIN_LOCK = threading.Lock()

SYNC_CONFIG_PATH = Path(os.environ.get('APPDATA', str(Path.home()))) / 'MobileCornerERP' / 'sync_config.json'
DEFAULT_SYNC_INTERVAL_SECONDS = int(os.environ.get('DESKTOP_SYNC_INTERVAL_SECONDS', '300'))
# A first sync attempt is delayed past server startup rather than run before
# waitress.serve() is reachable - the Tauri splash screen's own 90s timeout is already
# tight on a fresh-install full migration (see app-shell's README), don't add sync
# latency to that critical path.
STARTUP_DELAY_SECONDS = 15
REACHABILITY_TIMEOUT_SECONDS = 5
SYNC_REQUEST_TIMEOUT_SECONDS = 60


def _encrypt(data: bytes) -> bytes:
    import win32crypt
    return win32crypt.CryptProtectData(data, 'MobileCornerERP sync credentials', None, None, None, 0)


def _decrypt(data: bytes) -> bytes:
    import win32crypt
    return win32crypt.CryptUnprotectData(data, None, None, None, 0)[1]


def load_sync_config():
    """Returns the stored {production_url, refresh_token, company_id, last_synced_at,
    auth_required} dict, or None if never paired. `auth_required=True` means a past
    sync hit a 401 even after refresh-token exchange failed - the stored token is dead
    and the UI should prompt the Owner to pair again rather than the loop silently
    retrying forever against credentials that will never work."""
    if not SYNC_CONFIG_PATH.exists():
        return None
    try:
        return json.loads(_decrypt(SYNC_CONFIG_PATH.read_bytes()))
    except Exception:
        return None


def save_sync_config(config: dict):
    SYNC_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    SYNC_CONFIG_PATH.write_bytes(_encrypt(json.dumps(config).encode('utf-8')))


def clear_sync_config():
    if SYNC_CONFIG_PATH.exists():
        SYNC_CONFIG_PATH.unlink()


def _known_local_device_id():
    """This install's own previously-registered device_id, read from local SQLite (see
    DesktopDeviceIdentity's own docstring) - falls back to sync_config.json's copy for
    an install that paired before DesktopDeviceIdentity existed. None on a genuine
    first-ever pairing, or if migrations haven't created the table yet (defensive - this
    runs from a request handler, should never actually happen post-migrate)."""
    try:
        from core.device_registry import DesktopDeviceIdentity
        identity = DesktopDeviceIdentity.objects.filter(pk=1).first()
        if identity is not None and identity.device_id:
            return identity.device_id
    except Exception:
        pass
    config = load_sync_config()
    return config.get('device_id') if config else None


def _save_local_device_identity(device_id, range_start, range_end):
    from core.device_registry import DesktopDeviceIdentity
    DesktopDeviceIdentity.objects.update_or_create(
        pk=1, defaults={'device_id': device_id, 'range_start': range_start, 'range_end': range_end},
    )


def pair_with_production(production_url, email, password):
    """First-run pairing: exchanges the Owner's production credentials for a refresh
    token, stores it encrypted, and returns the paired config. Called once from the
    Desktop Sync Settings screen - the sync loop itself never sees a raw password,
    only ever the stored refresh token from here on.

    Also registers this install as a Phase C device (POST /api/core/register-device/ on
    production) and stores its reserved PK/number range in the same config. If this
    exact install already knows its own device_id (see _known_local_device_id() - a
    re-pair, e.g. after a stale refresh token forced the user to log in again), that
    device_id is sent along so register_device() on production hands back the SAME
    already-reserved range instead of minting a new one - re-minting on every re-pair
    would silently orphan anything still queued locally under the old range (nothing
    still queued would validate against a range production no longer associates with
    this device - see core.device_registry.validated_desktop_pk()). Only a genuinely
    first-ever pairing (no known device_id) claims a brand-new range. The range only
    actually gets *seeded* into the local database once the first full snapshot import
    creates the local Company row - see DesktopSyncLoop.sync_now()'s call to
    seed_device_ranges() below.
    """
    import requests
    resp = requests.post(
        f'{production_url}/api/auth/token/',
        json={'email': email, 'password': password},
        timeout=SYNC_REQUEST_TIMEOUT_SECONDS,
    )
    resp.raise_for_status()
    tokens = resp.json()

    auth_header = {'Authorization': f"Bearer {tokens['access']}"}

    me_resp = requests.get(
        f'{production_url}/api/auth/me/', headers=auth_header, timeout=SYNC_REQUEST_TIMEOUT_SECONDS,
    )
    me_resp.raise_for_status()
    company_id = me_resp.json().get('company')

    known_device_id = _known_local_device_id()
    device_body = {'label': os.environ.get('COMPUTERNAME', '')}
    if known_device_id:
        device_body['device_id'] = known_device_id
    device_resp = requests.post(
        f'{production_url}/api/core/register-device/', headers=auth_header,
        json=device_body, timeout=SYNC_REQUEST_TIMEOUT_SECONDS,
    )
    device_resp.raise_for_status()
    device = device_resp.json()
    _save_local_device_identity(device['device_id'], device['range_start'], device['range_end'])

    config = {
        'production_url': production_url,
        'refresh_token': tokens['refresh'],
        'company_id': company_id,
        'device_id': device['device_id'],
        'range_start': device['range_start'],
        'range_end': device['range_end'],
        # A re-pair that got its OLD range back (device['device_id'] matches
        # known_device_id) already has that range seeded from before - re-seeding is
        # harmless (seed_device_ranges only ever moves counters forward) but unnecessary;
        # only force a fresh seed for a genuinely new range.
        'range_seeded': bool(known_device_id and device['device_id'] == known_device_id),
        'last_synced_at': None,
        'auth_required': False,
    }
    save_sync_config(config)
    return config


class DesktopSyncLoop:
    """Runs as a daemon thread inside desktop_server.py. `sync_now()` is also called
    directly (not via the thread) by the /api/core/sync-now/ manual-trigger endpoint,
    so both paths share the exact same reachability-probe/import/cursor-update logic -
    no separate "manual sync" code path to drift out of sync with the periodic one."""

    def __init__(self, interval_seconds=DEFAULT_SYNC_INTERVAL_SECONDS):
        self.interval_seconds = interval_seconds
        self._thread = None
        self._stop_event = threading.Event()
        self.last_result = None  # last sync_now() outcome, for the manual-trigger endpoint to report back

    def start(self):
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._run, daemon=True, name='desktop-sync-loop')
        self._thread.start()

    def stop(self):
        self._stop_event.set()

    def _run(self):
        self._stop_event.wait(STARTUP_DELAY_SECONDS)
        while not self._stop_event.is_set():
            try:
                self.sync_now()
            except Exception as e:
                # A single bad cycle must never kill the loop - log and try again next
                # interval, matching the mobile app's own "server authoritative, real
                # failures surfaced but never fatal to the retry loop" philosophy.
                print(f'[desktop_sync] Unexpected error during sync cycle: {e}')
            self._stop_event.wait(self.interval_seconds)

    def is_reachable(self, production_url):
        import requests
        try:
            resp = requests.get(f'{production_url}/api/core/health/', timeout=REACHABILITY_TIMEOUT_SECONDS)
            return resp.status_code == 200
        except requests.RequestException:
            return False

    def sync_now(self):
        """Runs exactly one sync cycle: push (drain the local outbox against production's
        real API - Phase C) then pull (Phase A's delta import), sharing one refreshed
        access token between both. Returns a dict describing the outcome -
        {'status': 'synced'|'skipped'|'auth_required'|'error', 'push': {...}, ...} -
        never raises for an expected failure mode (offline, stale token); only truly
        unexpected exceptions propagate, and even those are caught by _run()'s loop
        above."""
        config = load_sync_config()
        if config is None:
            self.last_result = {'status': 'skipped', 'reason': 'not_paired'}
            return self.last_result
        if config.get('auth_required'):
            self.last_result = {'status': 'auth_required'}
            return self.last_result

        production_url = config['production_url']
        if not self.is_reachable(production_url):
            self.last_result = {'status': 'skipped', 'reason': 'offline'}
            return self.last_result

        import requests
        try:
            refresh_resp = requests.post(
                f'{production_url}/api/auth/token/refresh/',
                json={'refresh': config['refresh_token']},
                timeout=SYNC_REQUEST_TIMEOUT_SECONDS,
            )
            if refresh_resp.status_code == 401:
                config['auth_required'] = True
                save_sync_config(config)
                self.last_result = {'status': 'auth_required'}
                return self.last_result
            refresh_resp.raise_for_status()
            access_token = refresh_resp.json()['access']

            push_result = self.drain(production_url, access_token, config)
            if push_result.get('status') == 'auth_required':
                self.last_result = push_result
                return self.last_result

            since = config.get('last_synced_at')
            params = {'since': since} if since else {}
            export_resp = requests.get(
                f'{production_url}/api/core/export-snapshot/',
                params=params,
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=SYNC_REQUEST_TIMEOUT_SECONDS,
            )
            if export_resp.status_code == 401:
                config['auth_required'] = True
                save_sync_config(config)
                self.last_result = {'status': 'auth_required'}
                return self.last_result
            export_resp.raise_for_status()
            payload = export_resp.json()
        except requests.RequestException as e:
            # Reachability probe passed but the actual request still failed
            # (connection dropped mid-request, DNS hiccup, etc.) - treat exactly like
            # "offline", try again next interval, not a fatal error.
            self.last_result = {'status': 'skipped', 'reason': f'request_failed: {e}'}
            return self.last_result

        from core.snapshot import import_snapshot_data
        count = import_snapshot_data(payload['objects'], expected_company_id=config['company_id'])

        # Store the server's own exported_at as the next cursor, never local wall-clock
        # time - see export_company_snapshot's own docstring for why local time here
        # would risk silently skipping rows written between request and response.
        config['last_synced_at'] = payload['exported_at']

        # First time the local Company row genuinely exists (the very first sync_now()
        # after pairing always does a full import, never a delta - see pair_with_
        # production()) - seed this device's reserved PK/number range now, exactly
        # once, guarded by the flag rather than "since was None" so it's safe even if
        # this cycle is retried.
        if not config.get('range_seeded') and config.get('device_id'):
            from core.device_registry import seed_device_ranges
            from user_auth.models import Company
            company = Company.objects.filter(pk=config['company_id']).first()
            if company is not None:
                seed_device_ranges(company, config['range_start'])
                config['range_seeded'] = True

        save_sync_config(config)

        self.last_result = {'status': 'synced', 'objects_imported': count, 'since': since, 'push': push_result}
        return self.last_result

    def drain(self, production_url=None, access_token=None, config=None):
        """Push-back sync (Phase C): replays every pending local write in
        core.desktop_sync_queue.DesktopSyncQueueEntry against production's real API, in
        creation order, so idempotency/lease_range()-issued numbers and each model's own
        save()-embedded business logic (ledger postings, stock reduction) all apply on
        production exactly as if the action had happened there directly - see
        core/desktop_sync_queue.py's module docstring for why this replays the original
        endpoint rather than a raw row upsert. Each entry's desktop_pks/desktop_numbers
        are (re)built fresh from its own already-recorded response at replay time (see
        _build_replay_extras() below), not stored ahead of time.

        Stops (not fails) at the first entry it can't process due to connectivity - the
        remaining queue stays untouched for the next cycle, never partially replayed out
        of order. A genuine business-rejection (a real non-2xx response from production,
        not a network failure) marks that one entry 'failed' with production's own error
        message and moves on to the next - one bad row must never block every later,
        unrelated, perfectly valid write behind it in the queue. 'failed' entries are
        surfaced on the desktop app's Sync Conflicts screen for a human to review -
        never silently retried forever, never silently dropped.

        Callable standalone (sync_now() calls it internally, sharing one refreshed
        access token with the pull that follows) - omit all three args to have it do its
        own reachability probe and token refresh, e.g. from the real-time per-write
        trigger in core/desktop_sync_middleware.py.

        Guarded by the module-level _DRAIN_LOCK: if another drain cycle is already
        running (the periodic loop, a real-time trigger, or a manual Sync Now all
        eventually call this), returns immediately with status 'skipped' rather than
        running concurrently - two overlapping drains could both read and push the same
        'pending' rows at once. Not lossy: the skipped cycle's rows are still 'pending'
        and picked up fresh by whichever cycle runs next.
        """
        if not _DRAIN_LOCK.acquire(blocking=False):
            return {'status': 'skipped', 'reason': 'drain_in_progress'}
        try:
            return self._drain_locked(production_url, access_token, config)
        finally:
            _DRAIN_LOCK.release()

    def _drain_locked(self, production_url, access_token, config):
        if config is None:
            config = load_sync_config()
        if config is None or config.get('auth_required') or not config.get('device_id'):
            return {'status': 'skipped', 'reason': 'not_paired'}
        if production_url is None:
            production_url = config['production_url']

        import requests
        if access_token is None:
            if not self.is_reachable(production_url):
                return {'status': 'skipped', 'reason': 'offline'}
            try:
                refresh_resp = requests.post(
                    f'{production_url}/api/auth/token/refresh/',
                    json={'refresh': config['refresh_token']}, timeout=SYNC_REQUEST_TIMEOUT_SECONDS,
                )
                if refresh_resp.status_code == 401:
                    config['auth_required'] = True
                    save_sync_config(config)
                    return {'status': 'auth_required'}
                refresh_resp.raise_for_status()
                access_token = refresh_resp.json()['access']
            except requests.RequestException as e:
                return {'status': 'skipped', 'reason': f'request_failed: {e}'}

        import json
        from core.desktop_sync_queue import DesktopSyncQueueEntry

        headers = {'Authorization': f'Bearer {access_token}'}
        pushed = 0
        failed = 0
        for entry in DesktopSyncQueueEntry.objects.filter(status='pending').order_by('created_at'):
            try:
                payload = json.loads(entry.payload_json)
                response_data = json.loads(entry.response_json or '{}')
                pks, numbers = _build_replay_extras(entry.path, response_data)
            except (ValueError, KeyError) as e:
                # Malformed capture (shouldn't happen for a real entry, but a crash
                # here must never block every valid entry queued behind this one) -
                # mark this one entry failed and keep draining the rest.
                entry.status = 'failed'
                entry.error_message = f'Could not build replay payload: {e}'
                entry.save(update_fields=['status', 'error_message'])
                failed += 1
                continue

            payload['device_id'] = config['device_id']
            if pks:
                payload['desktop_pks'] = pks
            if numbers:
                payload['desktop_numbers'] = numbers

            try:
                resp = requests.request(
                    entry.method, f'{production_url}{entry.path}', json=payload,
                    headers=headers, timeout=SYNC_REQUEST_TIMEOUT_SECONDS,
                )
            except requests.RequestException:
                # Connectivity died mid-drain - stop here, this entry (and everything
                # after it, since order matters) stays pending for the next cycle.
                break

            if resp.status_code == 401:
                config['auth_required'] = True
                save_sync_config(config)
                return {'status': 'auth_required', 'pushed': pushed, 'failed': failed}

            if 200 <= resp.status_code < 300:
                entry.status = 'synced'
                entry.synced_at = timezone.now()
                entry.save(update_fields=['status', 'synced_at'])
                pushed += 1
                try:
                    resp_data = resp.json()
                except ValueError:
                    resp_data = {}
                _apply_pk_conflicts(resp_data.get('pk_conflicts') or [])
            else:
                entry.status = 'failed'
                try:
                    entry.error_message = json.dumps(resp.json())[:2000]
                except ValueError:
                    entry.error_message = resp.text[:2000]
                entry.save(update_fields=['status', 'error_message'])
                failed += 1

        return {'status': 'drained', 'pushed': pushed, 'failed': failed}


def _build_replay_extras(path, response_data):
    """Given the ORIGINAL local response for one of the five push-eligible paths (see
    core/desktop_sync_middleware.py's PUSH_ELIGIBLE_PATHS), builds the desktop_pks/
    desktop_numbers dicts a replay against production needs to inject so production's
    copy lands on the exact same PKs and document numbers already committed to locally.
    Each branch is specific to that one endpoint's own response shape - there's no way
    to make this generic without the endpoint itself describing its own PK/number
    fields, which felt like more machinery than five short, readable branches. Returns
    ({}, {}) for any path not in this list (defensive - PUSH_ELIGIBLE_PATHS should
    already guarantee this never happens for a real captured entry)."""
    if path == '/api/crm/customers/':
        return {'customer': response_data['id']}, {'customer_code': response_data['customer_code']}
    if path == '/api/sales/payments/':
        return {'payment': response_data['id']}, {'payment_number': response_data['payment_number']}
    if path == '/api/purchase/purchase-payments/':
        return {'purchase_payment': response_data['id']}, {'payment_number': response_data['payment_number']}
    if path == '/api/sales/pos/checkout/':
        pks = {'invoice': response_data['invoice_id'], 'items': response_data['item_ids']}
        numbers = {'invoice_number': response_data['invoice_number']}
        if response_data.get('payment_id'):
            pks['payment'] = response_data['payment_id']
        if response_data.get('payment_number'):
            numbers['payment_number'] = response_data['payment_number']
        return pks, numbers
    if path == '/api/purchase/vendor-invoice/':
        pks = {
            'bill': response_data['bill_id'],
            'items': [item['bill_item_id'] for item in response_data.get('items', [])],
        }
        return pks, {'bill_number': response_data['bill_number']}
    if path == '/api/purchase/suppliers/':
        return {'supplier': response_data['id']}, {'supplier_code': response_data['supplier_code']}
    if path == '/api/products/products/':
        return {'product': response_data['id']}, {}
    if path == '/api/accounting/expenses/':
        return {'expense': response_data['id']}, {}
    if path == '/api/sales/returns/process/':
        pks = {'credit_note': response_data['id'], 'items': response_data.get('item_ids', [])}
        return pks, {'credit_number': response_data['credit_number']}
    if path == '/api/purchase/returns/process/':
        pks = {'debit_note': response_data['id'], 'items': response_data.get('item_ids', [])}
        return pks, {'debit_number': response_data['debit_number']}
    if re.match(r'^/api/purchase/bills/\d+/receive-items/$', path):
        return {'tracking_units': response_data.get('tracking_unit_ids', [])}, {}
    # Customer PATCH (/api/crm/customers/<id>/) and bill_confirm_received need no
    # extras at all - an update carries no new PK to preserve, and the target row's id
    # is already baked into the request path itself.
    return {}, {}


def _apply_pk_conflicts(pk_conflicts):
    """A successful push's response can carry a `pk_conflicts` list (see
    core/pk_conflict.py::create_with_pk_fallback()) when production had to assign a
    DIFFERENT id than the one this row was created with locally - a genuine PK
    collision that production already resolved on its own side. Renumbers this
    device's local copy to match, so both sides agree going forward - see
    core/desktop_pk_renumber.py. Given the device-range-stability fix in
    core.device_registry.register_device(), this should rarely have anything to do in
    practice; a renumber failure here is logged, not fatal to the rest of the drain
    cycle (the entry itself already synced successfully - only the local bookkeeping
    would stay stale)."""
    if not pk_conflicts:
        return
    from core.desktop_pk_renumber import renumber_local_pk
    for conflict in pk_conflicts:
        try:
            renumber_local_pk(conflict['model'], conflict['requested_id'], conflict['assigned_id'])
        except Exception as e:
            print(f"[desktop_sync] Failed to renumber local {conflict.get('model')} "
                  f"{conflict.get('requested_id')} -> {conflict.get('assigned_id')}: {e}")


_loop_instance = None


def get_loop():
    global _loop_instance
    if _loop_instance is None:
        _loop_instance = DesktopSyncLoop()
    return _loop_instance
