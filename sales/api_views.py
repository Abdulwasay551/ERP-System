from decimal import Decimal, InvalidOperation
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Q, Sum, Avg
from django.core.files.base import ContentFile
from django.http import HttpResponse
from django.utils import timezone
from user_auth.permissions import RoleIn
from products.models import ProductTracking
from inventory.models import StockItem, StockMovement
from crm.models import Customer, CustomerLedger
from core.pdf_utils import build_invoice_pdf, build_invoice_pdf_a4
from core.mixins import SoftDeleteViewSetMixin, log_deletion
from core.idempotency import idempotent, IdempotentCreateMixin
from core.pk_conflict import PkConflictReportingMixin, save_with_pk_fallback
from .models import Product, Tax, Quotation, SalesOrder, SalesOrderItem, Invoice, InvoiceItem, Payment, CreditNote, CreditNoteItem
from .serializers import (
    ProductSerializer, TaxSerializer, QuotationSerializer, SalesOrderSerializer, SalesOrderItemSerializer,
    InvoiceSerializer, PaymentSerializer, CreditNoteSerializer,
)

class ProductViewSet(SoftDeleteViewSetMixin, viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Product.objects.filter(company=self.request.user.company)

class TaxViewSet(viewsets.ModelViewSet):
    serializer_class = TaxSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Tax.objects.filter(company=self.request.user.company)

class QuotationViewSet(viewsets.ModelViewSet):
    serializer_class = QuotationSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Quotation.objects.filter(company=self.request.user.company)

class SalesOrderViewSet(viewsets.ModelViewSet):
    serializer_class = SalesOrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return SalesOrder.objects.filter(company=self.request.user.company)

class SalesOrderItemViewSet(viewsets.ModelViewSet):
    serializer_class = SalesOrderItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return SalesOrderItem.objects.filter(sales_order__company=self.request.user.company)

class InvoiceViewSet(SoftDeleteViewSetMixin, viewsets.ModelViewSet):
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    # InvoiceItem has no independent list view (always accessed nested via invoice.items),
    # so it doesn't need its own SoftDeleteMixin/visibility - only Payment does, since it's
    # independently queryable (Invoice.paid_amount aggregates over invoice.payments).
    cascade_to = ['payments']
    filterset_fields = ['status', 'customer', 'invoice_date']
    ordering_fields = ['invoice_date', 'total', 'created_at', 'invoice_number']
    def get_queryset(self):
        return Invoice.objects.filter(company=self.request.user.company)

    @action(detail=True, methods=['get'], url_path='returnable-items')
    def returnable_items(self, request, pk=None):
        """
        Per-line breakdown of what's still eligible for a return on this invoice - for
        tracked items, one row per unit still marked sold against this invoice; for
        untracked items, remaining quantity after subtracting anything already returned.
        """
        invoice = self.get_object()
        rows = []
        for item in invoice.items.select_related('product', 'tracking_unit').all():
            if item.product.tracking_method in ('serial', 'imei'):
                if item.tracking_unit_id and item.tracking_unit.status == 'sold' and item.tracking_unit.sold_invoice_id == invoice.id:
                    identifier = item.tracking_unit.imei_number or item.tracking_unit.serial_number
                    rows.append({
                        'invoice_item_id': item.id,
                        'product_id': item.product_id,
                        'product_name': item.product.name,
                        'tracking_id': item.tracking_unit_id,
                        'tracking_identifier': identifier,
                        'unit_price': str(item.unit_price),
                        'returnable_quantity': '1',
                    })
            else:
                already_returned = item.return_items.aggregate(total=Sum('quantity'))['total'] or 0
                remaining = item.quantity - already_returned
                if remaining > 0:
                    rows.append({
                        'invoice_item_id': item.id,
                        'product_id': item.product_id,
                        'product_name': item.product.name,
                        'tracking_id': None,
                        'tracking_identifier': None,
                        'unit_price': str(item.unit_price),
                        'returnable_quantity': str(remaining),
                    })
        return Response(rows)

    @action(detail=True, methods=['get'])
    def pdf(self, request, pk=None):
        """Regenerates the invoice PDF on demand rather than relying on the stored
        pdf_file - Vercel's serverless filesystem is ephemeral, so a file saved at
        checkout time may not still be there by the time someone downloads it.
        ?size=a4 for a full-page printer invoice; defaults to the mini billing-machine
        receipt (?size=mini, or omitted)."""
        invoice = self.get_object()
        items = invoice.items.select_related('product').all()
        if request.query_params.get('size') == 'a4':
            buf = build_invoice_pdf_a4(invoice, items)
        else:
            buf = build_invoice_pdf(invoice, items)
        response = HttpResponse(buf.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{invoice.invoice_number}.pdf"'
        return response

    @action(detail=True, methods=['post'])
    def edit(self, request, pk=None):
        """
        Owner/Manager-only correction of an already-posted invoice: header fields plus a
        full replacement item list (product_id/unit_price/quantity/discounts/tracking_id
        per line, same shape pos_checkout accepts). Reverse -> replace -> reapply: undo
        this invoice's current stock/tracking effects (releases any tracked units back to
        available), swap in the new item set, recompute totals, then reapply stock
        reduction and ledger/paid-amount - reuses the exact same methods pos_checkout and
        Invoice.save() already rely on for creation, rather than hand-rolling new delta
        logic. get_permissions() (core.mixins.SoftDeleteViewSetMixin) gates this to
        Owner/Manager only.
        """
        invoice = self.get_object()
        data = request.data
        items_data = data.get('items') or []
        if not items_data:
            return Response({'error': 'items are required.'}, status=status.HTTP_400_BAD_REQUEST)

        company = request.user.company
        try:
            with transaction.atomic():
                for field in ('due_date', 'payment_terms', 'notes', 'invoice_date'):
                    if field in data:
                        setattr(invoice, field, data[field])
                if data.get('customer_id'):
                    try:
                        invoice.customer = Customer.objects.get(pk=data['customer_id'], company=company)
                    except Customer.DoesNotExist:
                        raise ValueError(f"Customer {data['customer_id']} not found.")

                was_confirmed = invoice.status != 'draft'
                if was_confirmed:
                    invoice.reverse_inventory_movements()

                invoice.items.all().delete()

                subtotal = Decimal('0')
                line_discounts_total = Decimal('0')
                for line in items_data:
                    product_id = line.get('product_id')
                    if not product_id:
                        raise ValueError('Each item requires a product_id.')
                    try:
                        product = Product.objects.get(pk=product_id, company=company)
                    except Product.DoesNotExist:
                        raise ValueError(f'Product {product_id} not found.')

                    tracking_id = line.get('tracking_id')
                    if tracking_id:
                        if not ProductTracking.objects.filter(pk=tracking_id, product=product, status='available').exists():
                            raise ValueError(f'Tracking unit {tracking_id} is not available for sale.')
                        quantity = Decimal('1')
                    else:
                        try:
                            quantity = Decimal(str(line.get('quantity', '1')))
                        except InvalidOperation:
                            raise ValueError(f'Invalid quantity for product {product_id}.')
                        if quantity <= 0:
                            raise ValueError(f'quantity must be > 0 for product {product.name}.')

                    try:
                        unit_price = Decimal(str(line['unit_price'])) if line.get('unit_price') else product.selling_price
                    except InvalidOperation:
                        raise ValueError(f'Invalid unit_price for product {product_id}.')

                    invoice_item = InvoiceItem.objects.create(
                        invoice=invoice, product=product, quantity=quantity, unit_price=unit_price,
                        tracking_unit_id=tracking_id, discounts=line.get('discounts') or [],
                    )
                    subtotal += quantity * unit_price
                    line_discounts_total += invoice_item.discount_amount

                try:
                    discount_amount = Decimal(str(data.get('discount_amount', invoice.discount_amount)))
                except InvalidOperation:
                    raise ValueError('Invalid discount_amount.')

                invoice.subtotal = subtotal
                invoice.discount_amount = discount_amount
                invoice.total = subtotal - line_discounts_total - discount_amount
                invoice.save()

                if was_confirmed:
                    invoice.process_inventory_reduction()
                    invoice.update_customer_ledger_debit()

                total_paid = invoice.payments.aggregate(total=Sum('amount'))['total'] or 0
                invoice.paid_amount = total_paid
                invoice.status = 'paid' if total_paid >= invoice.total else 'partially_paid'
                invoice.save(update_fields=['paid_amount', 'status'])

                log_deletion(invoice, request.user, 'edited')
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(InvoiceSerializer(invoice).data)

class PaymentViewSet(IdempotentCreateMixin, PkConflictReportingMixin, SoftDeleteViewSetMixin, viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['customer', 'invoice', 'method']
    ordering_fields = ['payment_date', 'amount', 'created_at']

    def get_queryset(self):
        return Payment.objects.filter(company=self.request.user.company)

    def perform_create(self, serializer):
        from core.device_registry import validated_desktop_pk, validated_desktop_number
        company = self.request.user.company
        explicit_id = validated_desktop_pk(self.request.data, 'payment', company)
        extra = {}
        explicit_number = validated_desktop_number(self.request.data, 'payment_number', company)
        if explicit_number:
            extra['payment_number'] = explicit_number
        conflict = save_with_pk_fallback(serializer, explicit_id, company=company, received_by=self.request.user, **extra)
        if conflict:
            self._pk_conflicts = [{'model': 'sales.Payment', **conflict}]


class POSStaff(RoleIn):
    allowed_roles = ['Manager', 'Cashier', 'Salesman']


def _avg_purchase_price(product):
    """Historical cost signal for the POS below-cost warning: average purchase_price
    across all of this product's tracked units (any status - it's a cost reference,
    not a stock check), falling back to the product's set cost_price when it has no
    tracked purchase history yet (e.g. an untracked/bulk product)."""
    avg = ProductTracking.all_objects.filter(
        product=product, purchase_price__isnull=False
    ).aggregate(avg=Avg('purchase_price'))['avg']
    return avg if avg is not None else (product.cost_price or Decimal('0'))


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, POSStaff])
def pos_search(request):
    """
    Single scanner-agnostic lookup for the POS screen: `q` can be an exact scanned code
    (IMEI/serial/barcode, from a camera scan or a physical USB/Bluetooth scanner acting as
    a keyboard) or a partial name/brand/SKU typed to browse. Tracked items (phones) return
    one row per available unit, since each has its own price/condition; untracked items
    (accessories) return one row with the pooled available quantity.
    """
    q = request.query_params.get('q', '').strip()
    if not q:
        return Response({'error': 'q query parameter is required.'}, status=status.HTTP_400_BAD_REQUEST)
    company = request.user.company
    results = []

    tracked_units = ProductTracking.objects.filter(
        Q(imei_number=q) | Q(serial_number=q) | Q(barcode=q) |
        Q(product__name__icontains=q) | Q(product__brand__icontains=q) | Q(product__sku__icontains=q),
        product__company=company, status='available'
    ).select_related('product', 'variant')[:20]

    for unit in tracked_units:
        unit_price = unit.selling_price if unit.selling_price is not None else unit.product.selling_price
        variant_label = None
        if unit.variant:
            variant_label = ' '.join(filter(None, [unit.variant.color, unit.variant.size])) or unit.variant.name
        results.append({
            'product_id': unit.product.id,
            'tracking_id': unit.id,
            'name': unit.product.name,
            'brand': unit.product.brand,
            'variant': variant_label,
            'identifier': unit.get_tracking_value(),
            'tracking_method': unit.product.tracking_method,
            'unit_price': str(unit_price),
            'avg_purchase_price': str(_avg_purchase_price(unit.product)),
            'available_qty': 1,
        })

    untracked_products = Product.objects.filter(
        Q(barcode=q) | Q(sku__icontains=q) | Q(name__icontains=q),
        company=company, tracking_method='none', is_saleable=True, is_active=True
    )[:20]

    for product in untracked_products:
        available = StockItem.objects.filter(company=company, product=product).aggregate(
            total=Sum('available_quantity'))['total'] or 0
        if available > 0:
            results.append({
                'product_id': product.id,
                'tracking_id': None,
                'name': product.name,
                'brand': product.brand,
                'variant': None,
                'identifier': product.barcode or product.sku,
                'tracking_method': 'none',
                'unit_price': str(product.selling_price),
                'avg_purchase_price': str(_avg_purchase_price(product)),
                'available_qty': str(available),
            })

    return Response(results[:20])


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, POSStaff])
@idempotent
def pos_checkout(request):
    """
    One-call POS checkout: cart of items -> Invoice + InvoiceItems -> stock reduction
    (via Invoice.save()'s existing status-transition hook) -> Payment (credits the
    customer ledger) -> invoice PDF. Bypasses the enterprise Quotation->SalesOrder
    pipeline entirely, same as vendor_invoice_create bypasses RFQ->PO->GRN.
    """
    company = request.user.company
    data = request.data
    items_data = data.get('items') or []
    if not items_data:
        return Response({'error': 'items are required.'}, status=status.HTTP_400_BAD_REQUEST)

    # Phase C push-back replay: desktop_pks (validated against the calling device's own
    # reserved range - see core.device_registry.validated_desktop_pk's docstring) lets
    # this exact same endpoint, called again later against production, force the new
    # Invoice/InvoiceItem/Payment rows onto the identical PKs already committed to
    # locally, instead of production silently assigning its own - see
    # core/desktop_sync_queue.py's module docstring for why this has to be a real
    # replay of the endpoint (re-running Invoice.save()'s stock reduction and
    # Payment.save()'s ledger posting) rather than a raw row upsert.
    from core.device_registry import validated_desktop_pk, validated_desktop_number
    from core.pk_conflict import create_with_pk_fallback
    desktop_item_pks = (data.get('desktop_pks') or {}).get('items') or []
    pk_conflicts = []

    try:
        with transaction.atomic():
            customer_id = data.get('customer_id')
            if customer_id:
                try:
                    customer = Customer.objects.get(pk=customer_id, company=company)
                except Customer.DoesNotExist:
                    raise ValueError(f'Customer {customer_id} not found.')
            else:
                customer, _ = Customer.objects.get_or_create(
                    company=company, customer_code='WALKIN',
                    defaults={'name': 'Walk-in Customer'}
                )

            explicit_invoice_id = validated_desktop_pk(data, 'invoice', company)
            invoice_kwargs = dict(
                company=company, customer=customer, status='draft', created_by=request.user,
            )
            explicit_invoice_number = validated_desktop_number(data, 'invoice_number', company)
            if explicit_invoice_number:
                invoice_kwargs['invoice_number'] = explicit_invoice_number
            invoice, invoice_conflict = create_with_pk_fallback(Invoice.objects, explicit_invoice_id, **invoice_kwargs)
            if invoice_conflict:
                pk_conflicts.append({'model': 'sales.Invoice', **invoice_conflict})

            subtotal = Decimal('0')
            line_discounts_total = Decimal('0')
            for index, line in enumerate(items_data):
                product_id = line.get('product_id')
                if not product_id:
                    raise ValueError('Each item requires a product_id.')
                try:
                    product = Product.objects.get(pk=product_id, company=company)
                except Product.DoesNotExist:
                    raise ValueError(f'Product {product_id} not found.')

                tracking_id = line.get('tracking_id')
                if tracking_id:
                    if not ProductTracking.objects.filter(pk=tracking_id, product=product, status='available').exists():
                        raise ValueError(f'Tracking unit {tracking_id} is no longer available for sale.')
                    quantity = Decimal('1')
                else:
                    try:
                        quantity = Decimal(str(line.get('quantity', '1')))
                    except InvalidOperation:
                        raise ValueError(f'Invalid quantity for product {product_id}.')
                    if quantity <= 0:
                        raise ValueError(f'quantity must be > 0 for product {product.name}.')

                try:
                    unit_price = Decimal(str(line['unit_price'])) if line.get('unit_price') else product.selling_price
                except InvalidOperation:
                    raise ValueError(f'Invalid unit_price for product {product_id}.')

                item_id = None
                if index < len(desktop_item_pks):
                    item_id = validated_desktop_pk({'desktop_pks': {'item': desktop_item_pks[index]}, 'device_id': data.get('device_id')}, 'item', company)
                invoice_item, item_conflict = create_with_pk_fallback(
                    InvoiceItem.objects, item_id,
                    invoice=invoice, product=product, quantity=quantity, unit_price=unit_price,
                    tracking_unit_id=tracking_id, discounts=line.get('discounts') or [],
                )
                if item_conflict:
                    pk_conflicts.append({'model': 'sales.InvoiceItem', **item_conflict})
                subtotal += quantity * unit_price
                line_discounts_total += invoice_item.discount_amount

            try:
                discount_amount = Decimal(str(data.get('discount_amount', '0')))
            except InvalidOperation:
                raise ValueError('Invalid discount_amount.')

            invoice.subtotal = subtotal
            invoice.discount_amount = discount_amount
            invoice.total = subtotal - line_discounts_total - discount_amount

            payment_data = data.get('payment') or {}
            try:
                paid_amount = Decimal(str(payment_data.get('amount'))) if payment_data.get('amount') is not None else invoice.total
            except InvalidOperation:
                raise ValueError('Invalid payment amount.')

            invoice.paid_amount = paid_amount
            invoice.status = 'paid' if paid_amount >= invoice.total else 'partially_paid'
            invoice.save()  # triggers stock reduction + tracking sale + customer ledger debit

            payment = None
            if paid_amount > 0:
                explicit_payment_id = validated_desktop_pk(data, 'payment', company)
                payment_kwargs = dict(
                    company=company, customer=customer, invoice=invoice,
                    amount=paid_amount, method=payment_data.get('method', 'cash'),
                    reference=payment_data.get('reference', ''),
                    received_by=request.user, processed_by=request.user,
                    notes=payment_data.get('notes', ''),
                )
                explicit_payment_number = validated_desktop_number(data, 'payment_number', company)
                if explicit_payment_number:
                    payment_kwargs['payment_number'] = explicit_payment_number
                payment, payment_conflict = create_with_pk_fallback(Payment.objects, explicit_payment_id, **payment_kwargs)
                if payment_conflict:
                    pk_conflicts.append({'model': 'sales.Payment', **payment_conflict})
                if 'attachment' in request.FILES:
                    payment.attachment = request.FILES['attachment']
                    payment.save()

            pdf_error = None
            try:
                buf = build_invoice_pdf(invoice, invoice.items.select_related('product').all())
                invoice.pdf_file.save(f'{invoice.invoice_number}.pdf', ContentFile(buf.read()), save=True)
            except Exception as e:
                pdf_error = str(e)

    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    response_body = {
        'invoice_id': invoice.id,
        'invoice_number': invoice.invoice_number,
        'total': str(invoice.total),
        'paid_amount': str(invoice.paid_amount),
        'outstanding_amount': str(invoice.outstanding_amount),
        'pdf_url': invoice.pdf_file.url if invoice.pdf_file else None,
        'pdf_error': pdf_error,
        # Every row this call actually created, keyed the same way desktop_pks accepts
        # them back in on replay (Phase C) - core.desktop_sync_middleware records this
        # response verbatim so DesktopSyncLoop.drain() can build the replay payload
        # without needing its own endpoint-specific knowledge of pos_checkout's shape.
        'item_ids': [item.id for item in invoice.items.order_by('id')],
        'payment_id': payment.id if payment else None,
        'payment_number': payment.payment_number if payment else None,
    }
    # Only present when a replay's client-supplied PK genuinely collided with a row
    # production's own auto-increment already created - see core/pk_conflict.py. Read by
    # DesktopSyncLoop.drain() to renumber this device's local copy to match.
    if pk_conflicts:
        response_body['pk_conflicts'] = pk_conflicts
    return Response(response_body, status=status.HTTP_201_CREATED)


class CreditNoteViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only - credit notes are only ever created via process_sales_return, which
    also has to restore stock and credit the customer ledger in the same transaction."""
    serializer_class = CreditNoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = CreditNote.objects.filter(company=self.request.user.company).select_related('customer', 'invoice')
        invoice_id = self.request.query_params.get('invoice')
        if invoice_id:
            qs = qs.filter(invoice_id=invoice_id)
        return qs.order_by('-credit_date', '-id')


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, POSStaff])
@idempotent
def process_sales_return(request):
    """
    One-call customer return: validates each returned line against what's actually still
    outstanding on the invoice (tracked units must still be sold-and-tied-to-this-invoice;
    untracked quantities can't exceed what hasn't already been returned), then in one
    transaction creates the CreditNote + line items, restores stock (StockMovement with
    movement_type='sales_return' - same mechanism Invoice.reverse_inventory_movements()
    uses for a full-invoice cancellation, just per-line here), and credits the customer
    ledger for the refund.

    Phase C push-back replay, same pattern as pos_checkout/vendor_invoice_create:
    desktop_pks.credit_note / desktop_pks.items (indexed like vendor_invoice_create's
    own item list) let a replay force the CreditNote/CreditNoteItem rows onto the exact
    PKs already committed locally.
    """
    from core.device_registry import validated_desktop_pk, validated_desktop_number
    from core.pk_conflict import create_with_pk_fallback

    company = request.user.company
    data = request.data
    invoice_id = data.get('invoice_id')
    items_data = data.get('items') or []
    if not invoice_id or not items_data:
        return Response({'error': 'invoice_id and items are required.'}, status=status.HTTP_400_BAD_REQUEST)
    desktop_item_pks = (data.get('desktop_pks') or {}).get('items') or []
    pk_conflicts = []

    try:
        with transaction.atomic():
            try:
                invoice = Invoice.objects.select_related('customer').get(pk=invoice_id, company=company)
            except Invoice.DoesNotExist:
                raise ValueError(f'Invoice {invoice_id} not found.')

            explicit_credit_note_id = validated_desktop_pk(data, 'credit_note', company)
            credit_note_kwargs = dict(
                company=company, customer=invoice.customer, invoice=invoice,
                created_by=request.user, reason=data.get('reason', 'return'),
                notes=data.get('notes', ''),
            )
            explicit_credit_number = validated_desktop_number(data, 'credit_number', company)
            if explicit_credit_number:
                credit_note_kwargs['credit_number'] = explicit_credit_number
            credit_note, credit_note_conflict = create_with_pk_fallback(CreditNote.objects, explicit_credit_note_id, **credit_note_kwargs)
            if credit_note_conflict:
                pk_conflicts.append({'model': 'sales.CreditNote', **credit_note_conflict})

            total_refund = Decimal('0')
            for index, line in enumerate(items_data):
                invoice_item_id = line.get('invoice_item_id')
                if not invoice_item_id:
                    raise ValueError('Each item requires an invoice_item_id.')
                try:
                    invoice_item = InvoiceItem.objects.select_related('product', 'tracking_unit').get(
                        pk=invoice_item_id, invoice=invoice
                    )
                except InvoiceItem.DoesNotExist:
                    raise ValueError(f'Invoice item {invoice_item_id} not found on this invoice.')

                product = invoice_item.product
                tracking_id = line.get('tracking_id')
                # Refund at the post-discount per-unit price, not the raw list unit_price,
                # so a discounted sale doesn't refund more than the customer actually paid.
                net_unit_price = (
                    (invoice_item.unit_price * invoice_item.quantity - invoice_item.discount_amount) / invoice_item.quantity
                    if invoice_item.quantity else invoice_item.unit_price
                )

                if product.tracking_method in ('serial', 'imei'):
                    if not tracking_id:
                        raise ValueError(f'{product.name} is tracked - a tracking_id is required to return it.')
                    try:
                        tracking_unit = ProductTracking.objects.get(pk=tracking_id, product=product)
                    except ProductTracking.DoesNotExist:
                        raise ValueError(f'Tracking unit {tracking_id} not found.')
                    if tracking_unit.status != 'sold' or tracking_unit.sold_invoice_id != invoice.id:
                        raise ValueError(f'{product.name} ({tracking_id}) is not currently sold on this invoice - it may already have been returned.')
                    quantity = Decimal('1')
                    unit_price = net_unit_price
                else:
                    tracking_unit = None
                    try:
                        quantity = Decimal(str(line.get('quantity', '1')))
                    except InvalidOperation:
                        raise ValueError(f'Invalid quantity for {product.name}.')
                    if quantity <= 0:
                        raise ValueError(f'quantity must be > 0 for {product.name}.')
                    already_returned = invoice_item.return_items.aggregate(total=Sum('quantity'))['total'] or 0
                    if already_returned + quantity > invoice_item.quantity:
                        raise ValueError(
                            f'Cannot return {quantity} of {product.name} - only '
                            f'{invoice_item.quantity - already_returned} left returnable on this invoice.'
                        )
                    unit_price = net_unit_price

                item_id = None
                if index < len(desktop_item_pks):
                    item_id = validated_desktop_pk({'desktop_pks': {'item': desktop_item_pks[index]}, 'device_id': data.get('device_id')}, 'item', company)
                credit_note_item, item_conflict = create_with_pk_fallback(
                    CreditNoteItem.objects, item_id,
                    credit_note=credit_note, invoice_item=invoice_item, product=product,
                    tracking_unit=tracking_unit, quantity=quantity, unit_price=unit_price,
                )
                if item_conflict:
                    pk_conflicts.append({'model': 'sales.CreditNoteItem', **item_conflict})
                total_refund += quantity * unit_price

                stock_item = StockItem.objects.filter(company=company, product=product).order_by('-created_at').first()
                if stock_item is None:
                    raise ValueError(f'No stock record found for {product.name} - cannot restore stock for this return.')

                StockMovement.objects.create(
                    company=company, stock_item=stock_item, movement_type='sales_return',
                    quantity=quantity, unit_cost=stock_item.average_cost, total_cost=quantity * stock_item.average_cost,
                    to_warehouse=stock_item.warehouse, reference_number=f'{credit_note.credit_number}',
                    reference_type='invoice', reference_id=invoice.id,
                    notes=f'Customer return - {credit_note.credit_number} against {invoice.invoice_number}',
                    performed_by=request.user,
                )

                if tracking_unit:
                    tracking_unit.status = 'available'
                    tracking_unit.sold_to_customer = None
                    tracking_unit.sold_date = None
                    tracking_unit.sold_invoice = None
                    tracking_unit.save()

            credit_note.subtotal = total_refund
            credit_note.total = total_refund
            credit_note.save()

            CustomerLedger.objects.create(
                company=company, customer=invoice.customer, transaction_date=timezone.now().date(),
                reference_type='credit_note', reference_id=credit_note.id,
                description=f'Return {credit_note.credit_number} against {invoice.invoice_number}',
                debit_amount=0, credit_amount=total_refund, created_by=request.user,
            )

    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    response_body = CreditNoteSerializer(credit_note).data
    # Creation-order item ids a replay's desktop_pks.items must match - read by
    # core.desktop_sync._build_replay_extras(), same convention as vendor_invoice_create.
    response_body['item_ids'] = list(credit_note.items.order_by('id').values_list('id', flat=True))
    if pk_conflicts:
        response_body['pk_conflicts'] = pk_conflicts
    return Response(response_body, status=status.HTTP_201_CREATED)