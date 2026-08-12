"""
Phase C's push-back outbox: one row per locally-created business write on the desktop
app, waiting to be replayed against production once reachable - see
`core/desktop_sync_middleware.py` (which fills this table) and
`core/desktop_sync.py::DesktopSyncLoop.drain()` (which empties it).

Deliberately captures the raw (method, path, payload_json) rather than a snapshot of
the resulting model rows - see core/desktop_sync.py's module docstring for why: several
of these writes (Payment.save() posting to the customer ledger, Invoice.save()
triggering stock reduction) run real business logic that lives inside the model's own
save() override, not just field assignment. Replaying the same request against
production's real endpoint re-runs that logic there too, exactly as if the action had
been performed live on production - a raw row-upsert (like Phase A/B's snapshot import,
which deliberately bypasses save() so it never re-triggers that logic on already-
materialized data) would silently skip it.

Mirrors the shape of the mobile app's own `sync_queue` SQLite table
(`mobile/lib/services/offline_db.dart`) as closely as possible - same field names,
same pending/synced/failed status vocabulary - since this solves the same problem
(queued writes surviving a period offline) even though the underlying mechanics differ
(mobile queues *before* any local write happens at all; the desktop already has a real
local ORM write to draw the request from).
"""
from django.db import models


class DesktopSyncQueueEntry(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('synced', 'Synced'),
        ('failed', 'Failed'),
        ('discarded', 'Discarded'),  # a human reviewed a failed entry and dismissed it
    ]

    company = models.ForeignKey('user_auth.Company', on_delete=models.CASCADE, related_name='desktop_sync_queue_entries')
    client_request_id = models.CharField(max_length=64, unique=True)
    method = models.CharField(max_length=10)
    path = models.CharField(max_length=255)
    payload_json = models.TextField()
    response_json = models.TextField(blank=True)
    summary = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    synced_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    retry_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.status}: {self.method} {self.path} ({self.client_request_id})'
