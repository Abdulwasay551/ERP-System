from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from core.numbering import SEQUENCES, format_number, lease_range, resolve_model
from core.snapshot import export_snapshot, export_snapshot_delta, export_all_companies_snapshot
from user_auth.permissions import IsOwnerOrManager, IsSuperuser


@api_view(['GET'])
@permission_classes([AllowAny])
def health(request):
    """Trivial reachability check for mobile/web clients - no auth required."""
    return Response({'status': 'ok'})


@api_view(['GET'])
@permission_classes([IsOwnerOrManager])
def export_company_snapshot(request):
    """
    Full company-data export for the desktop app's first-run pairing (Phase 3 of the
    desktop app plan) - everything the local SQLite copy needs to become a complete,
    PK-preserving mirror of this company's data. Owner/Manager only: this includes User
    rows (with hashed passwords) and every business record the company has, not
    something a Cashier/Salesman-level account should be able to pull down wholesale.

    Response: {"exported_at": <iso timestamp>, "company_id": ..., "objects": [...]} -
    `objects` is in django.core.serializers 'python'-format-then-JSON-safe shape, fed
    directly into core.snapshot.import_snapshot_data() (or the `import_snapshot`
    management command) on the receiving end.

    Optional `?since=<iso8601>` switches to a delta export (Phase A's ongoing pull-sync,
    as opposed to this endpoint's original one-time full-pairing use) - only models
    `core.sync_classification` marks delta-eligible, filtered to what's changed since
    that timestamp; see `core.snapshot.export_snapshot_delta()` for the exact
    semantics. The caller MUST store this response's own `exported_at` as its next
    `since` cursor, never its own local clock - using local time risks silently
    skipping rows written between this request and its response, if the two clocks
    disagree at all.
    """
    company = request.user.company
    since = request.query_params.get('since')
    objects = export_snapshot_delta(company, since) if since else export_snapshot(company)
    return Response({
        'exported_at': timezone.now().isoformat(),
        'company_id': company.id,
        'since': since,
        'objects': objects,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def lease_numbers(request):
    """
    Reserves a contiguous block of document numbers (invoice/bill/quotation/etc.) for
    this company, for the desktop app to spend offline without colliding with numbers
    the cloud (or another synced device) generates independently in the meantime - see
    core.numbering's module docstring for why this has to share the same atomic counter
    as normal single-document creation, not just peek at the last row.

    Body: {"sequence_key": "invoice", "count": 50}
    Response: {"sequence_key", "prefix", "digits", "range_start", "range_end", "year",
               "numbers": [...]} - `numbers` is the fully-formatted list (e.g.
    ["INV-000401", ..., "INV-000450"]) so the caller doesn't have to re-derive the
    zero-padding/year-prefixing format itself.
    """
    sequence_key = request.data.get('sequence_key')
    count = request.data.get('count')
    config = SEQUENCES.get(sequence_key)
    if not config:
        return Response({'error': f"Unknown sequence_key '{sequence_key}'."}, status=400)
    try:
        count = int(count)
    except (TypeError, ValueError):
        return Response({'error': 'count must be an integer.'}, status=400)
    if not (0 < count <= 1000):
        return Response({'error': 'count must be between 1 and 1000.'}, status=400)

    company = request.user.company
    model_cls = resolve_model(config['model_label'])
    range_start, range_end, year = lease_range(
        company, sequence_key, config['prefix'], config['digits'], count,
        model_cls, config['field_name'], config['manager_name'], config['year_scoped'],
        config.get('label_year', False),
    )
    numbers = [format_number(config['prefix'], config['digits'], v, year) for v in range(range_start, range_end + 1)]
    return Response({
        'sequence_key': sequence_key,
        'prefix': config['prefix'],
        'digits': config['digits'],
        'range_start': range_start,
        'range_end': range_end,
        'year': year,
        'numbers': numbers,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def global_search(request):
    """
    One box, every record type: looks up q against the human-readable numbers/names
    across invoices, vendor bills, credit notes, payments, products, customers and
    suppliers - the "search by ID from anywhere" entry point. Each result carries a
    `type` and `id` a client can turn into a deep link (frontend routes, mobile
    screens) rather than this endpoint prescribing a URL shape itself.
    """
    q = request.query_params.get('q', '').strip()
    if not q or len(q) < 2:
        return Response({'error': 'q must be at least 2 characters.'}, status=400)
    company = request.user.company
    results = []

    from sales.models import Invoice, CreditNote, Payment
    from purchase.models import Bill, PurchasePayment
    from products.models import Product
    from crm.models import Customer
    from purchase.models import Supplier

    for inv in Invoice.objects.filter(company=company, invoice_number__icontains=q).select_related('customer')[:10]:
        results.append({
            'type': 'invoice', 'id': inv.id, 'number': inv.invoice_number,
            'label': f'Invoice {inv.invoice_number}',
            'subtitle': inv.customer.name if inv.customer else 'Walk-in',
        })

    for bill in Bill.objects.filter(company=company, bill_number__icontains=q).select_related('supplier__partner')[:10]:
        results.append({
            'type': 'bill', 'id': bill.id, 'number': bill.bill_number,
            'label': f'Bill {bill.bill_number}',
            'subtitle': bill.supplier.partner.name if bill.supplier else '',
        })

    for cn in CreditNote.objects.filter(company=company, credit_number__icontains=q).select_related('customer')[:10]:
        results.append({
            'type': 'credit_note', 'id': cn.id, 'number': cn.credit_number,
            'label': f'Credit Note {cn.credit_number}',
            'subtitle': cn.customer.name if cn.customer else '',
        })

    for pay in Payment.objects.filter(company=company, payment_number__icontains=q).select_related('customer')[:10]:
        results.append({
            'type': 'payment', 'id': pay.id, 'number': pay.payment_number,
            'label': f'Payment {pay.payment_number}',
            'subtitle': pay.customer.name if pay.customer else '',
        })

    for pay in PurchasePayment.objects.filter(company=company, payment_number__icontains=q).select_related('supplier__partner')[:10]:
        results.append({
            'type': 'purchase_payment', 'id': pay.id, 'number': pay.payment_number,
            'label': f'Vendor Payment {pay.payment_number}',
            'subtitle': pay.supplier.partner.name if pay.supplier else '',
        })

    from django.db.models import Q
    for p in Product.objects.filter(
        Q(sku__icontains=q) | Q(name__icontains=q) | Q(barcode__icontains=q), company=company
    )[:10]:
        results.append({
            'type': 'product', 'id': p.id, 'number': p.sku,
            'label': p.name, 'subtitle': p.sku,
        })

    for c in Customer.objects.filter(Q(name__icontains=q) | Q(customer_code__icontains=q) | Q(phone__icontains=q), company=company)[:10]:
        results.append({
            'type': 'customer', 'id': c.id, 'number': c.customer_code,
            'label': c.name, 'subtitle': c.customer_code,
        })

    for s in Supplier.objects.filter(
        Q(partner__name__icontains=q) | Q(supplier_code__icontains=q), company=company
    ).select_related('partner')[:10]:
        results.append({
            'type': 'supplier', 'id': s.id, 'number': s.supplier_code,
            'label': s.partner.name, 'subtitle': s.supplier_code,
        })

    return Response({'results': results})


# --- Desktop app pull-sync control endpoints (Phase A) ---
#
# These three are local-only in practice: only ever called by the desktop app's own
# bundled frontend against its own local backend at 127.0.0.1:8010, never meant to be
# hit on the production deployment. They're not otherwise gated by environment because
# this is the same Django codebase both places - `core.desktop_sync`'s credential
# storage lazily imports `pywin32`'s `win32crypt` (Windows-only), so calling these on
# production (Linux/Vercel) would fail loudly with a clear ImportError rather than
# silently doing something wrong, which is an acceptable failure mode for routes no
# real caller would ever reach there.

@api_view(['POST'])
@permission_classes([IsOwnerOrManager])
def pair_desktop_with_production(request):
    """First-run pairing: the desktop app exchanges the Owner's production login for a
    refresh token, stored encrypted for the background sync loop to use from then on -
    see core.desktop_sync.pair_with_production()'s own docstring.

    Body: {"production_url", "email", "password"}
    """
    from core.desktop_sync import pair_with_production
    import requests

    production_url = request.data.get('production_url', '').rstrip('/')
    email = request.data.get('email')
    password = request.data.get('password')
    if not (production_url and email and password):
        return Response({'error': 'production_url, email, and password are required.'}, status=400)
    try:
        config = pair_with_production(production_url, email, password)
    except requests.HTTPError as e:
        return Response({'error': f'Production rejected those credentials: {e}'}, status=400)
    except requests.RequestException as e:
        return Response({'error': f'Could not reach production: {e}'}, status=400)
    except ImportError:
        return Response({'error': 'Desktop sync is only available in the Windows desktop app build.'}, status=400)

    return Response({
        'paired': True,
        'production_url': config['production_url'],
        'company_id': config['company_id'],
    })


@api_view(['POST'])
@permission_classes([IsOwnerOrManager])
def sync_now(request):
    """Manual "Sync Now" trigger - runs exactly one cycle of the same logic the
    background loop runs periodically, so there's no separate code path to drift out
    of sync with it."""
    from core.desktop_sync import get_loop
    try:
        result = get_loop().sync_now()
    except ImportError:
        return Response({'error': 'Desktop sync is only available in the Windows desktop app build.'}, status=400)
    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sync_status(request):
    """Current pairing/sync state for the Desktop Sync Settings screen - deliberately
    never returns the stored refresh_token itself."""
    from core.desktop_sync import get_loop, load_sync_config
    config = load_sync_config()
    if config is None:
        return Response({'paired': False})
    return Response({
        'paired': True,
        'production_url': config['production_url'],
        'last_synced_at': config.get('last_synced_at'),
        'auth_required': config.get('auth_required', False),
        'last_result': get_loop().last_result,
    })


# --- Disaster-recovery backup export (Phase B) ---
#
# Superuser-only, not IsOwnerOrManager: this spans every company on the system, not
# just the caller's own shop (see IsSuperuser's own docstring in user_auth/permissions.py
# for why IsOwnerOrManager - which doesn't check user.company - would be the wrong gate
# here on a genuinely multi-tenant deployment). Restoring a backup back in is
# deliberately NOT an API endpoint at all - see
# core.snapshot.import_all_companies_snapshot()'s docstring and
# core/management/commands/restore_all_companies.py.

@api_view(['GET'])
@permission_classes([IsSuperuser])
def export_all_companies_backup(request):
    """Full disaster-recovery backup - every company's complete data. Restore via
    `python manage.py restore_all_companies --file <this response saved to disk>`.

    Response: {"exported_at", "company_ids": [...], "objects": [...]}
    """
    from user_auth.models import Company
    objects = export_all_companies_snapshot()
    return Response({
        'exported_at': timezone.now().isoformat(),
        'company_ids': list(Company.objects.values_list('id', flat=True)),
        'objects': objects,
    })


@api_view(['GET'])
@permission_classes([IsSuperuser])
def export_all_companies_backup_excel(request):
    """Same data as export_all_companies_backup, rendered as a multi-sheet workbook
    for human review only - see core.excel_export's module docstring for why this is
    never a restore path."""
    from django.http import HttpResponse
    from core.excel_export import build_backup_workbook
    import io

    objects = export_all_companies_snapshot()
    try:
        wb = build_backup_workbook(objects)
    except ImportError:
        return Response({'error': 'Excel export requires the openpyxl library, which is not installed.'}, status=500)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = 'attachment; filename="mobile-corner-backup.xlsx"'
    return response
