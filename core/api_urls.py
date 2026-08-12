from django.urls import path
from .api_views import (
    health, global_search, lease_numbers, export_company_snapshot,
    pair_desktop_with_production, sync_now, sync_status, register_device,
    sync_conflicts, discard_sync_conflict,
    export_all_companies_backup, export_all_companies_backup_excel,
)
from .recycle_bin import recycle_bin_list, recycle_bin_restore, recycle_bin_purge, recycle_bin_empty

urlpatterns = [
    path('health/', health, name='core-health'),
    path('search/', global_search, name='core-search'),
    path('lease-numbers/', lease_numbers, name='core-lease-numbers'),
    path('export-snapshot/', export_company_snapshot, name='core-export-snapshot'),
    path('pair-with-production/', pair_desktop_with_production, name='core-pair-with-production'),
    path('sync-now/', sync_now, name='core-sync-now'),
    path('sync-status/', sync_status, name='core-sync-status'),
    path('register-device/', register_device, name='core-register-device'),
    path('sync-conflicts/', sync_conflicts, name='core-sync-conflicts'),
    path('sync-conflicts/<int:entry_id>/discard/', discard_sync_conflict, name='core-discard-sync-conflict'),
    path('export-backup/', export_all_companies_backup, name='core-export-backup'),
    path('export-backup/excel/', export_all_companies_backup_excel, name='core-export-backup-excel'),
    path('recycle-bin/', recycle_bin_list, name='recycle-bin-list'),
    path('recycle-bin/restore/', recycle_bin_restore, name='recycle-bin-restore'),
    path('recycle-bin/purge/', recycle_bin_purge, name='recycle-bin-purge'),
    path('recycle-bin/empty/', recycle_bin_empty, name='recycle-bin-empty'),
]
