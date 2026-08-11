from django.urls import path
from .api_views import health, global_search, lease_numbers, export_company_snapshot
from .recycle_bin import recycle_bin_list, recycle_bin_restore, recycle_bin_purge, recycle_bin_empty

urlpatterns = [
    path('health/', health, name='core-health'),
    path('search/', global_search, name='core-search'),
    path('lease-numbers/', lease_numbers, name='core-lease-numbers'),
    path('export-snapshot/', export_company_snapshot, name='core-export-snapshot'),
    path('recycle-bin/', recycle_bin_list, name='recycle-bin-list'),
    path('recycle-bin/restore/', recycle_bin_restore, name='recycle-bin-restore'),
    path('recycle-bin/purge/', recycle_bin_purge, name='recycle-bin-purge'),
    path('recycle-bin/empty/', recycle_bin_empty, name='recycle-bin-empty'),
]
