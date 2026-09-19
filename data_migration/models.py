from django.db import models

from user_auth.models import Company


class LegacyIDMap(models.Model):
    """Maps a BizNet legacy source row to the ERP row created for it.

    Written immediately after every row this import creates, so each phase of the
    migration is idempotent/resumable (a re-run skips source rows already mapped here)
    and later phases can resolve a legacy FK (e.g. SalesBody.ProductID) to the new PK
    without re-deriving it.
    """

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='legacy_id_maps')
    source_table = models.CharField(max_length=64, help_text="BizNet table name, lowercase, e.g. 'products'")
    source_pk = models.CharField(max_length=64, help_text="BizNet primary key as text, e.g. ProductID/PartyID/SaleID")
    target_app_label = models.CharField(max_length=64)
    target_model = models.CharField(max_length=64)
    target_id = models.BigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'source_table', 'source_pk'],
                name='uniq_legacy_source_row',
            ),
        ]
        indexes = [
            models.Index(fields=['company', 'source_table', 'target_id']),
        ]

    def __str__(self):
        return f"{self.source_table}:{self.source_pk} -> {self.target_app_label}.{self.target_model}:{self.target_id}"
