"""
Phase C's collision-free ID scheme: each desktop install gets its own exclusive block
of primary-key space, reserved once at pairing time and never re-issued to anyone else.

Why a reserved range instead of remapping IDs on sync or switching to UUIDs - see the
plan's own Phase C writeup (`core/desktop_sync.py`'s module docstring links the same
story): a row created offline on the desktop already has a real, locally-assigned
integer PK the moment it's created (needed so it's immediately queryable/printable).
If that PK falls inside a block production's own auto-increment will also reach one
day, or a block another desktop device might independently pick, two real rows could
end up sharing one PK - or worse, production's own creation and a delayed desktop push
could each think they "won" the same number. Reserving a whole block per device up
front (production's own un-reserved counter, and every other device's block, all sit
outside it) means a desktop-assigned PK can always be pushed to production as-is, with
no remapping and no FK-cascade rewriting - see `core/desktop_sync.py::drain()`.

Ranges are allocated from ONE global counter (`DeviceIdRangeCounter`, a singleton row),
not per-company - a PK collision is possible across companies too, since every
Phase-C-eligible model's `id` column is one shared auto-increment sequence in
production's single Postgres database regardless of which company owns which row.

`RANGE_SIZE` (100,000,000 per device) starting at `RANGE_FLOOR` (10,000,000,000) gives
enormous headroom over any realistic shop's real row counts, and stays far above
production's own auto-increment for the lifetime of this project - production's counter
would need ten billion real rows in a single model before ever reaching this floor.
"""
import uuid

from django.db import models, transaction
from django.utils import timezone


def _new_device_id():
    return uuid.uuid4().hex

RANGE_FLOOR = 10_000_000_000
RANGE_SIZE = 100_000_000


class DeviceIdRangeCounter(models.Model):
    """Singleton row (always pk=1) - the one shared counter every device registration
    draws its next block from. Locked via select_for_update() the same way
    core.numbering.NumberSequence is, so two devices registering at the same moment can
    never be handed overlapping ranges."""
    id = models.PositiveIntegerField(primary_key=True, default=1)
    next_range_start = models.BigIntegerField(default=RANGE_FLOOR)

    def __str__(self):
        return f'next device range starts at {self.next_range_start}'


class DeviceRegistration(models.Model):
    """One row per paired desktop install. `device_id` is what the desktop app stores
    locally (in sync_config.json alongside its production credentials) and sends with
    every push-back request, so production can tell which device's reserved range a
    pushed row's PK is supposed to fall inside - see `core/desktop_sync.py::drain()`."""
    device_id = models.CharField(max_length=64, unique=True, default=_new_device_id)
    company = models.ForeignKey('user_auth.Company', on_delete=models.CASCADE, related_name='desktop_devices')
    label = models.CharField(max_length=255, blank=True)
    range_start = models.BigIntegerField()
    range_end = models.BigIntegerField()
    registered_at = models.DateTimeField(auto_now_add=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    revoked = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.label or self.device_id} ({self.range_start}-{self.range_end})'


def register_device(company, label='', device_id=None):
    """Atomically hands out the next unclaimed range and records the device that owns
    it - UNLESS `device_id` names a registration this exact device already holds, in
    which case that existing range is returned as-is. Called from the desktop app's
    pairing flow (POST /api/core/register-device/, right after pair_with_production()
    succeeds) on both a genuine first-ever pairing (device_id=None or unknown) and a
    re-pair of an already-seeded install (device_id known locally, see
    core/desktop_sync.py::pair_with_production()'s docstring) - re-minting a brand-new
    range on every re-pair would silently orphan anything still queued under the old
    one (validated_desktop_pk() can't validate a replay against a range production no
    longer associates with this device)."""
    if device_id:
        existing = DeviceRegistration.objects.filter(device_id=device_id, company=company, revoked=False).first()
        if existing is not None:
            update_fields = ['last_synced_at']
            existing.last_synced_at = timezone.now()
            if label and label != existing.label:
                existing.label = label
                update_fields.append('label')
            existing.save(update_fields=update_fields)
            return existing

    with transaction.atomic():
        counter, _ = DeviceIdRangeCounter.objects.select_for_update().get_or_create(
            pk=1, defaults={'next_range_start': RANGE_FLOOR},
        )
        range_start = counter.next_range_start
        range_end = range_start + RANGE_SIZE - 1
        counter.next_range_start = range_end + 1
        counter.save(update_fields=['next_range_start'])

        create_kwargs = dict(company=company, label=label, range_start=range_start, range_end=range_end)
        if device_id:
            # Reuse the caller's own remembered device_id rather than minting a random
            # one - so a FUTURE re-pair (device_id known locally, but somehow no longer
            # resolving above - e.g. this DeviceRegistration was revoked) still has a
            # stable identifier to look for, rather than a new random one every time.
            create_kwargs['device_id'] = device_id
        device = DeviceRegistration.objects.create(**create_kwargs)
    return device


def validated_desktop_pk(request_data, key, company):
    """The single check every push-back-accepting create view runs before honoring a
    client-supplied PK: `request_data` (the raw request body) must carry both a
    `desktop_pks` map with `key` in it and a `device_id`, and that device_id must name a
    real, non-revoked DeviceRegistration belonging to `company` whose reserved range
    actually contains the claimed value. Returns the validated integer PK to force, or
    None if any of that isn't true - which is also the ordinary case for every normal
    web/mobile/local-desktop create that was never a Phase C replay at all, so callers
    can pass the result straight through as `id=` without an if/else: `id=None` to
    Django's ORM is exactly the same as not passing `id` at all - the AutoField assigns
    normally.
    """
    desktop_pks = request_data.get('desktop_pks')
    device_id = request_data.get('device_id')
    if not desktop_pks or not device_id or key not in desktop_pks:
        return None
    try:
        pk = int(desktop_pks[key])
    except (TypeError, ValueError):
        print(f"[device_registry] Replay for '{key}' had a non-integer desktop_pks value "
              f"{desktop_pks.get(key)!r} - falling back to auto-assign.")
        return None
    device = DeviceRegistration.objects.filter(device_id=device_id, company=company).first()
    if device is None:
        # A replay WAS attempted (desktop_pks + device_id both present) but named a
        # device_id with no registration here - not the ordinary "never a replay at
        # all" case. Most likely an orphaned range from before a re-pair (see
        # register_device()'s docstring) - logged, not silent, even though the caller
        # still gets a safe auto-assigned fallback rather than a hard failure.
        print(f"[device_registry] Replay for '{key}' named device_id {device_id!r}, which has no "
              f"registration for this company - falling back to auto-assign (likely a stale range "
              f"from before a re-pair).")
        return None
    if not pk_in_device_range(device, pk):
        print(f"[device_registry] Replay for '{key}' claimed pk={pk}, outside device {device_id!r}'s "
              f"registered range [{device.range_start}, {device.range_end}] - falling back to "
              f"auto-assign (likely a stale range from before a re-pair, or the range was already "
              f"exhausted).")
        return None
    return pk


def validated_desktop_number(request_data, key, company):
    """Like validated_desktop_pk, but for an already-formatted document number
    (INV-000123 etc.) the desktop already generated locally via next_number() against a
    device-seeded NumberSequence counter (see seed_device_ranges()). Without this, a
    replayed create would let production's own next_number() call regenerate a brand
    new, different-looking number for the same row - the shop's already-printed receipt
    would say "INV-10000000700" while production's authoritative copy became
    "INV-000047", and the next pull-sync would silently overwrite the printed number
    with the second one. Returns the full formatted string to use verbatim, or None -
    the normal case for every non-replay create, in which case the caller should omit
    the field entirely so the model's own save() generates it as usual.

    Validates the number's own trailing numeric value against the same reserved range a
    raw PK would need to fall in, reusing pk_in_device_range() - both namespaces were
    seeded to the same range_start by seed_device_ranges(), so one range check covers
    both without a second reservation scheme.
    """
    desktop_numbers = request_data.get('desktop_numbers')
    device_id = request_data.get('device_id')
    if not desktop_numbers or not device_id or key not in desktop_numbers:
        return None
    value = desktop_numbers[key]
    try:
        numeric_part = int(str(value).split('-')[-1])
    except (ValueError, IndexError):
        return None
    device = DeviceRegistration.objects.filter(device_id=device_id, company=company).first()
    if device is None or not pk_in_device_range(device, numeric_part):
        return None
    return value


def pk_in_device_range(device, value):
    """True if `value` falls inside `device`'s reserved block and the device hasn't been
    revoked - the check every push-back-accepting create endpoint runs before honoring a
    client-supplied PK, so a compromised or misbehaving device can never claim a PK
    outside its own reserved space (which would risk exactly the collision this whole
    scheme exists to prevent)."""
    return (
        not device.revoked
        and device.range_start <= value <= device.range_end
    )


class DesktopDeviceIdentity(models.Model):
    """Local-only singleton (lives in the desktop app's own SQLite, never production)
    recording which device_id/range THIS install last registered - read by
    core.desktop_sync.pair_with_production() before a re-pair so it can send the same
    device_id back to register_device() instead of always minting a brand-new one (see
    that function's docstring for why that matters). Deliberately durable local
    business data, not a credential - unlike sync_config.json's DPAPI-encrypted refresh
    token, this is safe to survive in a Phase B backup and to persist even if
    sync_config.json itself is cleared/corrupted."""
    id = models.PositiveIntegerField(primary_key=True, default=1)
    device_id = models.CharField(max_length=64)
    range_start = models.BigIntegerField()
    range_end = models.BigIntegerField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.device_id} ({self.range_start}-{self.range_end})'


def seed_device_ranges(company, range_start):
    """One-time, called right after a device's range is registered (and again after any
    full snapshot (re)import, which leaves SQLite's own auto-increment sitting near
    production's real low numbers): pushes every relevant table's SQLite AUTOINCREMENT
    counter, and every document-numbering counter (core.numbering.SEQUENCES), forward to
    `range_start`. From this point on, every row created locally - a raw integer PK or a
    formatted document number like INV-000123 - falls inside a block no other device and
    no un-reserved production counter will ever independently reach.

    Only ever runs against the desktop app's local SQLite database - refuses outright
    against Postgres, since production's own counters must never be moved. Takes the
    raw `range_start` integer rather than a DeviceRegistration instance - the desktop
    app never has a local row for its own device (that row only exists on production),
    just the range boundaries it stored from register_device()'s response.
    """
    from django.db import connection
    if connection.vendor != 'sqlite':
        raise RuntimeError("seed_device_ranges must only run against the desktop app's local SQLite database.")

    from core.snapshot import MANIFEST
    from django.apps import apps
    floor = range_start - 1  # sqlite_sequence.seq is "last used", not "next"
    # Django's SQLite cursor wrapper expects %s-style placeholders (it rewrites them to
    # ? internally before handing off to sqlite3) - raw "?" here breaks last_executed_
    # query()'s own %-substitution for query logging whenever DEBUG=True.
    with connection.cursor() as cur:
        for app_label, model_name, _scope in MANIFEST:
            table = apps.get_model(app_label, model_name)._meta.db_table
            cur.execute(
                'UPDATE sqlite_sequence SET seq = %s WHERE name = %s AND seq < %s',
                [floor, table, floor],
            )
            if cur.rowcount == 0:
                cur.execute(
                    'INSERT OR IGNORE INTO sqlite_sequence (name, seq) VALUES (%s, %s)',
                    [table, floor],
                )

    from django.utils import timezone
    from core.numbering import SEQUENCES, NumberSequence
    year = timezone.now().year
    for sequence_key, config in SEQUENCES.items():
        key = f"{sequence_key}-{year}" if config.get('year_scoped') else sequence_key
        seq, _ = NumberSequence.objects.get_or_create(company=company, sequence_key=key, defaults={'next_value': range_start})
        if seq.next_value < range_start:
            seq.next_value = range_start
            seq.save(update_fields=['next_value'])
