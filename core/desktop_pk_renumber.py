"""
Local-side half of the reactive PK-conflict safety net (see core/pk_conflict.py for the
production-side half): once a push has succeeded and production reports a `pk_conflicts`
entry (its own row already landed correctly, at a DIFFERENT id than the desktop had
locally), this renumbers the desktop's LOCAL copy of that row to match - so the two
sides agree going forward, and any local write still referencing the old id doesn't
silently point at nothing.

Deliberately NOT a generic, whole-schema `_meta.get_fields()` walk: that would touch
every model with any relation to the renumbered one, including ones the desktop never
even queues, and would need re-auditing by hand anyway every time a new model/FK edge is
added - no safer than this explicit map, just less honest about needing maintenance.
CHILD_MAP/PAYLOAD_FK_KEYS/PATH_ID_PATTERNS below cover exactly the Phase-C model set
(see core/device_registry.py's validated_desktop_pk call sites) - extend all three
whenever that set grows.
"""
import json
import re

from django.apps import apps
from django.db import connection, transaction

# app_label.ModelName (the renumbered model) -> [(child app_label.ModelName, fk column)]
# for every LOCALLY-COMMITTED row that might reference it. Covers only models a desktop
# replay can create with an explicit PK.
CHILD_MAP = {
    'purchase.Supplier': [
        ('purchase.Bill', 'supplier_id'),
        ('purchase.PurchasePayment', 'supplier_id'),
        ('products.ProductTracking', 'supplier_id'),
    ],
    'purchase.Bill': [
        ('purchase.BillItem', 'bill_id'),
    ],
    'purchase.BillItem': [
        ('products.ProductTracking', 'bill_item_id'),
    ],
    'crm.Customer': [
        ('sales.Invoice', 'customer_id'),
        ('sales.Payment', 'customer_id'),
    ],
    'sales.Invoice': [
        ('sales.InvoiceItem', 'invoice_id'),
        ('sales.Payment', 'invoice_id'),
    ],
}

# app_label.ModelName (the renumbered model) -> [(queued path, payload JSON key)] for
# models referenced by their id INSIDE a request body - the inverse of
# core/desktop_sync.py::_build_replay_extras(). Patched into any still-`pending`
# DesktopSyncQueueEntry.payload_json before it's ever replayed.
PAYLOAD_FK_KEYS = {
    'purchase.Supplier': [
        ('/api/purchase/vendor-invoice/', 'supplier_id'),
        ('/api/purchase/purchase-payments/', 'supplier_id'),
    ],
    'crm.Customer': [
        ('/api/sales/payments/', 'customer_id'),
        ('/api/sales/pos/checkout/', 'customer_id'),
    ],
}

# app_label.ModelName -> [compiled regex] for models referenced by their id INSIDE the
# queued request's URL PATH rather than its body (e.g. bill_receive_items/
# confirm_received embed the bill id directly: /api/purchase/bills/<id>/receive-items/).
# Group 2 of each pattern must be the numeric id.
PATH_ID_PATTERNS = {
    'purchase.Bill': [
        re.compile(r'^(/api/purchase/bills/)(\d+)(/(?:receive-items|confirm-received)/)$'),
    ],
}


def renumber_local_pk(model_label, old_pk, new_pk):
    """Only ever runs against the desktop app's local SQLite database (mirrors
    core.device_registry.seed_device_ranges()'s own guard). Updates the renumbered row's
    own primary key, every locally-committed child row's FK to it (per CHILD_MAP), and
    any still-pending DesktopSyncQueueEntry referencing the old id - either in its
    payload (per PAYLOAD_FK_KEYS) or its URL path (per PATH_ID_PATTERNS) - all inside one
    transaction with FK checks deferred (SQLite enforces FKs immediately by default,
    which would reject an out-of-order parent/child update otherwise - the same
    mechanism core/snapshot.py's import already relies on for the same reason).

    A no-op if old_pk == new_pk (production happened to assign back the exact id that
    was requested - not actually a conflict, just reported defensively)."""
    if connection.vendor != 'sqlite':
        raise RuntimeError("renumber_local_pk must only run against the desktop app's local SQLite database.")
    if old_pk == new_pk:
        return

    model = apps.get_model(model_label)
    # SQLite's PRAGMA foreign_keys is a no-op once a transaction is already open (see
    # sqlite3/base.py's own disable_constraint_checking() comment: "Foreign key
    # constraints cannot be turned off while in a multi-statement transaction") - it
    # must be issued BEFORE transaction.atomic() starts one, not nested inside it.
    with connection.constraint_checks_disabled():
        with transaction.atomic():
            for child_label, fk_field in CHILD_MAP.get(model_label, []):
                child = apps.get_model(child_label)
                child._default_manager.filter(**{fk_field: old_pk}).update(**{fk_field: new_pk})
            model._default_manager.filter(pk=old_pk).update(id=new_pk)

    _patch_pending_queue_payloads(model_label, old_pk, new_pk)
    _patch_pending_queue_paths(model_label, old_pk, new_pk)


def _patch_pending_queue_payloads(model_label, old_pk, new_pk):
    from core.desktop_sync_queue import DesktopSyncQueueEntry

    keys = PAYLOAD_FK_KEYS.get(model_label, [])
    if not keys:
        return
    field_by_path = dict(keys)
    for entry in DesktopSyncQueueEntry.objects.filter(status='pending', path__in=field_by_path.keys()):
        payload = json.loads(entry.payload_json)
        field = field_by_path[entry.path]
        if payload.get(field) == old_pk:
            payload[field] = new_pk
            entry.payload_json = json.dumps(payload)
            entry.save(update_fields=['payload_json'])


def _patch_pending_queue_paths(model_label, old_pk, new_pk):
    from core.desktop_sync_queue import DesktopSyncQueueEntry

    patterns = PATH_ID_PATTERNS.get(model_label, [])
    if not patterns:
        return
    for entry in DesktopSyncQueueEntry.objects.filter(status='pending'):
        for pattern in patterns:
            m = pattern.match(entry.path)
            if m and int(m.group(2)) == old_pk:
                entry.path = f'{m.group(1)}{new_pk}{m.group(3)}'
                entry.save(update_fields=['path'])
                break
