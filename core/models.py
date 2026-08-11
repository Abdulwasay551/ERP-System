from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class SoftDeleteQuerySetMixin:
    """Mix into any manager (plain or a model-specific one like User's UserManager) so
    `.get_queryset()` hides soft-deleted rows regardless of what base manager a model
    already uses. Must come first in the MRO, e.g. `class UserManager(
    SoftDeleteQuerySetMixin, BaseUserManager)`, so its filter runs and still chains to
    the base manager's own get_queryset()."""

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class SoftDeleteManager(SoftDeleteQuerySetMixin, models.Manager):
    """Drop-in default manager for models with no pre-existing custom manager."""
    pass


class SoftDeleteMixin(models.Model):
    """Adds recoverable delete to a model: `.delete()` on the DRF ViewSet layer should
    call `soft_delete(user)` instead of Django's real delete. The default `objects`
    manager hides soft-deleted rows from every normal query; `all_objects` includes
    them, used by the recycle bin.
    """
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+',
    )

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def soft_delete(self, user):
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])


class RecordDeletionLog(models.Model):
    """Cross-model audit trail for soft-delete/restore/purge - the only durable record
    once a row is actually purged (its own deleted_by/deleted_at disappear with it)."""
    ACTION_CHOICES = [
        ('deleted', 'Deleted'),
        ('restored', 'Restored'),
        ('purged', 'Purged'),
        ('edited', 'Edited'),
    ]

    company = models.ForeignKey('user_auth.Company', on_delete=models.CASCADE, related_name='deletion_logs')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    object_repr = models.CharField(max_length=255)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='+',
    )
    performed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-performed_at']

    def __str__(self):
        return f'{self.action} {self.content_type.model} #{self.object_id} by {self.performed_by}'


# IdempotencyKey and NumberSequence are defined in core/idempotency.py and
# core/numbering.py respectively (kept alongside the logic that uses them, rather than
# dumped into this general models.py) - but Django's app registry only registers a model
# the moment its defining module is actually imported. Importing them here guarantees
# that happens as soon as the `core` app loads, not only incidentally whenever something
# else happens to import sales/purchase's api_views (which pull in core.idempotency)
# first - apps.get_model('core', 'IdempotencyKey') (used by core/snapshot.py) must work
# reliably regardless of import order. Placed at the *bottom* of this file, not the top:
# both modules import `from user_auth.models import Company`, and user_auth/models.py
# itself imports `SoftDeleteQuerySetMixin` from this file - importing them before that
# class is defined would deadlock the circular import.
from core.idempotency import IdempotencyKey  # noqa: E402,F401
from core.numbering import NumberSequence  # noqa: E402,F401
