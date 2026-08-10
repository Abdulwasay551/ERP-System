from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from core.numbering import SEQUENCES, format_number, lease_range, resolve_model


@api_view(['GET'])
@permission_classes([AllowAny])
def health(request):
    """Trivial reachability check for mobile/web clients - no auth required."""
    return Response({'status': 'ok'})


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
