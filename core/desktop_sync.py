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
import threading
import time
from pathlib import Path

from django.utils import timezone

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


def pair_with_production(production_url, email, password):
    """First-run pairing: exchanges the Owner's production credentials for a refresh
    token, stores it encrypted, and returns the paired config. Called once from the
    Desktop Sync Settings screen - the sync loop itself never sees a raw password,
    only ever the stored refresh token from here on.

    Also registers this install as a new Phase C device (POST /api/core/register-device/
    on production) and stores its reserved PK/number range in the same config - a fresh
    pairing always claims a brand-new range rather than trying to recall a previous
    device_id, since a cleared/reinstalled sync_config.json means this machine has no
    memory of ever having one (see core.device_registry.register_device()'s own
    docstring on why an abandoned old range is an acceptable, harmless cost - the range
    space has enormous headroom). The range only actually gets *seeded* into the local
    database once the first full snapshot import creates the local Company row - see
    DesktopSyncLoop.sync_now()'s call to seed_device_ranges() below.
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

    device_resp = requests.post(
        f'{production_url}/api/core/register-device/', headers=auth_header,
        json={'label': os.environ.get('COMPUTERNAME', '')}, timeout=SYNC_REQUEST_TIMEOUT_SECONDS,
    )
    device_resp.raise_for_status()
    device = device_resp.json()

    config = {
        'production_url': production_url,
        'refresh_token': tokens['refresh'],
        'company_id': company_id,
        'device_id': device['device_id'],
        'range_start': device['range_start'],
        'range_end': device['range_end'],
        'range_seeded': False,
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
        """Runs exactly one sync cycle. Returns a dict describing the outcome -
        {'status': 'synced'|'skipped'|'auth_required'|'error', ...} - never raises for
        an expected failure mode (offline, stale token); only truly unexpected
        exceptions propagate, and even those are caught by _run()'s loop above."""
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

        self.last_result = {'status': 'synced', 'objects_imported': count, 'since': since}
        return self.last_result


_loop_instance = None


def get_loop():
    global _loop_instance
    if _loop_instance is None:
        _loop_instance = DesktopSyncLoop()
    return _loop_instance
