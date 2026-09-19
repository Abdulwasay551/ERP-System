"""Shared helpers for the BizNet -> ERP historical migration management commands.

Source data is read directly from the `biznet` Postgres database (a local, read-only
copy of the converted legacy SQL Server DB - see E:\\BizNetPG) via the `biznet` Django
DB alias. We never use the ORM against that alias (no models are registered there) -
just raw SQL through django.db.connections['biznet'].
"""
from django.db import connections

from .models import LegacyIDMap


def biznet_fetch_all(sql, params=None):
    """Run a read-only query against the biznet DB alias and return a list of dicts."""
    with connections['biznet'].cursor() as cur:
        cur.execute(sql, params or [])
        columns = [col[0] for col in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()]


def record_map(company, source_table, source_pk, obj):
    """Record that `source_table`/`source_pk` (BizNet) produced `obj` (ERP row).
    Idempotent: safe to call again for the same source row (e.g. on a re-run)."""
    LegacyIDMap.objects.update_or_create(
        company=company,
        source_table=source_table,
        source_pk=str(source_pk).strip(),
        defaults={
            'target_app_label': obj._meta.app_label,
            'target_model': obj._meta.model_name,
            'target_id': obj.pk,
        },
    )


def load_map(company, source_table):
    """Return {source_pk: target_id} for every row already migrated from source_table."""
    return {
        m.source_pk: m.target_id
        for m in LegacyIDMap.objects.filter(company=company, source_table=source_table)
    }


def already_migrated_pks(company, source_table):
    return set(
        LegacyIDMap.objects.filter(company=company, source_table=source_table)
        .values_list('source_pk', flat=True)
    )


def bulk_record_map(company, source_table, source_pk_to_obj):
    """Bulk version of record_map() for when hundreds/thousands of rows were just
    bulk_created (each `obj` must already have `.pk` populated - true for bulk_create()
    against Postgres, which returns generated PKs). ignore_conflicts=True makes this
    safe to call again on a re-run without duplicating map rows for source_pks already
    recorded (relies on LegacyIDMap's unique_together constraint)."""
    rows = [
        LegacyIDMap(
            company=company, source_table=source_table, source_pk=str(pk).strip(),
            target_app_label=obj._meta.app_label, target_model=obj._meta.model_name,
            target_id=obj.pk,
        )
        for pk, obj in source_pk_to_obj
    ]
    LegacyIDMap.objects.bulk_create(rows, batch_size=2000, ignore_conflicts=True)


def bulk_create_chunked(model_cls, instances, batch_size=2000, **kwargs):
    """bulk_create in chunks, returning the same instances list (with .pk populated by
    Postgres's RETURNING support) so callers can zip them back against source rows."""
    for i in range(0, len(instances), batch_size):
        model_cls.objects.bulk_create(instances[i:i + batch_size], **kwargs)
    return instances
