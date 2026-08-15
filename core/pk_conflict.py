"""
Reactive safety net for the rare case (given the device-range-stability fix in
core/device_registry.py::register_device()) where a desktop replay's client-supplied PK
still genuinely collides with a row production's own auto-increment sequence already
created at that same integer. Rather than let that IntegrityError bubble up and fail the
whole create - the "conflict, can't create object" symptom this exists to prevent - each
PK-forcing create call can go through create_with_pk_fallback() instead of calling
`manager.create(id=explicit_id, ...)` directly: on a genuine PK-constraint violation, it
rolls back just that one insert (a real SAVEPOINT, not the caller's whole transaction)
and retries with no explicit id, letting production auto-assign a value guaranteed not
to collide - then reports what happened so the caller can surface it to the desktop app
for a local renumber (see core/desktop_pk_renumber.py).
"""
from django.db import IntegrityError, transaction

# Best-effort text match for "this IntegrityError was specifically a PK/id collision",
# not some other uniqueness violation (a duplicate SKU/customer_code should still fail
# loudly, not silently retry into a second, differently-numbered duplicate of what the
# caller actually intended to reject). Postgres constraint names for a primary key
# always end in `_pkey`; SQLite reports 'UNIQUE constraint failed' against the table's
# rowid alias column, not a named constraint - covered for completeness even though this
# helper is only ever exercised against Postgres in production requests.
_PK_CONFLICT_HINTS = ('_pkey', 'unique constraint failed')


def _is_pk_conflict(error: IntegrityError) -> bool:
    message = str(error).lower()
    return any(hint in message for hint in _PK_CONFLICT_HINTS)


class PkConflictReportingMixin:
    """Mix into a ModelViewSet, alongside IdempotentCreateMixin and BEFORE it in the
    MRO (`class FooViewSet(IdempotentCreateMixin, PkConflictReportingMixin, ...)`), so
    perform_create() can attach `self._pk_conflicts` (set only when
    save_with_pk_fallback() actually had to fall back) and have it merged into the
    create response body as `pk_conflicts` - core.desktop_sync.drain() reads this key to
    know a local renumber is needed. IdempotentCreateMixin must run OUTSIDE this (see
    the MRO note) so its cached replay response already includes `pk_conflicts` rather
    than caching an incomplete body. A ViewSet whose perform_create() never sets
    `_pk_conflicts` behaves identically to before (key omitted entirely)."""

    def create(self, request, *args, **kwargs):
        self._pk_conflicts = None
        response = super().create(request, *args, **kwargs)
        if self._pk_conflicts:
            response.data['pk_conflicts'] = self._pk_conflicts
        return response


def save_with_pk_fallback(serializer, explicit_id, **extra_kwargs):
    """Like create_with_pk_fallback, but wraps a DRF serializer's own `.save()` -
    whatever custom create() logic it has (e.g. SupplierSerializer also creating a
    linked Partner row) - instead of a bare manager.create() call, for ModelViewSet
    perform_create() methods. `extra_kwargs` are the usual serializer.save() kwargs
    (company=..., created_by=..., etc, NOT including id). Returns
    conflict_info_or_None; the serializer's own `.instance` ends up holding whichever
    row actually got created either way."""
    if explicit_id is None:
        serializer.save(**extra_kwargs)
        return None
    try:
        with transaction.atomic():
            serializer.save(id=explicit_id, **extra_kwargs)
        return None
    except IntegrityError as e:
        if not _is_pk_conflict(e):
            raise
        serializer.save(**extra_kwargs)
        return {'requested_id': explicit_id, 'assigned_id': serializer.instance.id}


def create_with_pk_fallback(manager, explicit_id, **kwargs):
    """Try creating with `id=explicit_id`. When `explicit_id` is None (the overwhelming
    common case - every ordinary web/mobile/unpaired-desktop create, not a Phase C
    replay), this is exactly `manager.create(**kwargs)` with no extra transaction
    overhead, since a None id can never conflict.

    When `explicit_id` is set (a genuine replay) and it collides, rolls back to a
    SAVEPOINT taken right before the attempt and retries with no explicit id. Any other
    IntegrityError (a real business-rule violation - e.g. a duplicate document number)
    is re-raised unchanged; only a genuine PK collision gets this fallback.

    Returns (instance, conflict_info_or_None) - conflict_info is
    `{'requested_id': explicit_id, 'assigned_id': instance.id}` when a fallback actually
    happened, None otherwise. Callers building a response should attach a `model` label
    to conflict_info before including it in `pk_conflicts` (this helper doesn't know its
    caller's model label) - see the call sites in purchase/crm/sales api_views.py.
    """
    if explicit_id is None:
        return manager.create(**kwargs), None
    try:
        with transaction.atomic():
            instance = manager.create(id=explicit_id, **kwargs)
        return instance, None
    except IntegrityError as e:
        if not _is_pk_conflict(e):
            raise
        instance = manager.create(**kwargs)
        return instance, {'requested_id': explicit_id, 'assigned_id': instance.id}
