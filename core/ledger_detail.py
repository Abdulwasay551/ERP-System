"""Resolves the real document behind one CustomerLedger/SupplierLedger row.

Both ledgers are a flat, mixed feed (transaction_date/reference_type/reference_id/
debit/credit/balance) with no FK to the Invoice/Bill/Payment it came from -
`reference_id` is a bare BigIntegerField (see crm.models.CustomerLedger's own comment
on why: it's a generic pointer across several unrelated models, not one relation).
This module is the one place that knows how to turn `(reference_type, reference_id)`
back into the actual line-item/tracking/payment-method detail for the "extended
ledger" view and its PDF - both the ledger-entry-detail API action and
build_extended_ledger_pdf call this same function so the two stay in sync.

Only invoice/bill/payment are resolved (the three the extended-ledger feature was
actually asked for) - credit_note/debit_note/opening_balance/adjustment rows return
None and keep rendering as a plain description-only row, same as before.
"""
from crm.models import CustomerLedger


def resolve_ledger_entry_detail(entry):
    """`entry`: a CustomerLedger or SupplierLedger instance. Returns a plain dict for
    the extra detail block, or None if this reference_type has nothing further to show."""
    is_customer_side = isinstance(entry, CustomerLedger)
    ref_type = entry.reference_type
    ref_id = entry.reference_id

    if ref_type == 'invoice' and is_customer_side:
        return _invoice_detail(ref_id)
    if ref_type == 'bill' and not is_customer_side:
        return _bill_detail(ref_id)
    if ref_type == 'payment':
        return _payment_detail(ref_id, is_customer_side)
    return None


def _invoice_detail(invoice_id):
    from sales.models import Invoice
    from sales.serializers import InvoiceItemSerializer
    try:
        invoice = Invoice.all_objects.select_related('customer').get(pk=invoice_id)
    except Invoice.DoesNotExist:
        return None
    items = invoice.items.select_related('product', 'tracking_unit').all()
    return {
        'kind': 'invoice',
        'number': invoice.invoice_number,
        'status': invoice.status,
        'total': str(invoice.total),
        'paid_amount': str(invoice.paid_amount),
        'items': InvoiceItemSerializer(items, many=True).data,
    }


def _bill_detail(bill_id):
    from purchase.models import Bill
    from purchase.serializers import BillItemSerializer
    try:
        bill = Bill.all_objects.select_related('supplier').get(pk=bill_id)
    except Bill.DoesNotExist:
        return None
    items = bill.items.select_related('product').all()
    return {
        'kind': 'bill',
        'number': bill.bill_number,
        'status': bill.status,
        'total': str(bill.total_amount),
        'paid_amount': str(bill.paid_amount),
        'supplier_invoice_number': bill.supplier_invoice_number,
        'items': BillItemSerializer(items, many=True).data,
    }


def _payment_detail(payment_id, is_customer_side):
    if is_customer_side:
        from sales.models import Payment
        try:
            payment = Payment.all_objects.get(pk=payment_id)
        except Payment.DoesNotExist:
            return None
        return {
            'kind': 'payment',
            'number': payment.payment_number,
            'method': payment.method,
            'reference': payment.reference,
            'date': str(payment.payment_date),
            'amount': str(payment.amount),
            'invoice_id': payment.invoice_id,
        }
    from purchase.models import PurchasePayment
    try:
        payment = PurchasePayment.all_objects.get(pk=payment_id)
    except PurchasePayment.DoesNotExist:
        return None
    return {
        'kind': 'payment',
        'number': payment.payment_number,
        'method': payment.payment_method,
        'reference': payment.reference_number,
        'date': str(payment.payment_date),
        'amount': str(payment.amount),
        'bill_id': payment.bill_id,
    }
