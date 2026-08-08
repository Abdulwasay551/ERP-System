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

class PaymentViewSet(SoftDeleteViewSetMixin, viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['customer', 'invoice', 'method']
    ordering_fields = ['payment_date', 'amount', 'created_at']

    def get_queryset(self):
        return Payment.objects.filter(company=self.request.user.company)

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company, received_by=self.request.user)


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

            invoice = Invoice.objects.create(
                company=company, customer=customer, status='draft', created_by=request.user,
            )

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

                invoice_item = InvoiceItem.objects.create(
                    invoice=invoice, product=product, quantity=quantity, unit_price=unit_price,
                    tracking_unit_id=tracking_id, discounts=line.get('discounts') or [],
                )
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

            if paid_amount > 0:
                payment = Payment.objects.create(
                    company=company, customer=customer, invoice=invoice,
                    amount=paid_amount, method=payment_data.get('method', 'cash'),
                    reference=payment_data.get('reference', ''),
                    received_by=request.user, processed_by=request.user,
                    notes=payment_data.get('notes', ''),
                )
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

    return Response({
        'invoice_id': invoice.id,
        'invoice_number': invoice.invoice_number,
        'total': str(invoice.total),
        'paid_amount': str(invoice.paid_amount),
        'outstanding_amount': str(invoice.outstanding_amount),
        'pdf_url': invoice.pdf_file.url if invoice.pdf_file else None,
        'pdf_error': pdf_error,
    }, status=status.HTTP_201_CREATED)


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
def process_sales_return(request):
    """
    One-call customer return: validates each returned line against what's actually still
    outstanding on the invoice (tracked units must still be sold-and-tied-to-this-invoice;
    untracked quantities can't exceed what hasn't already been returned), then in one
    transaction creates the CreditNote + line items, restores stock (StockMovement with
    movement_type='sales_return' - same mechanism Invoice.reverse_inventory_movements()
    uses for a full-invoice cancellation, just per-line here), and credits the customer
    ledger for the refund.
    """
    company = request.user.company
    data = request.data
    invoice_id = data.get('invoice_id')
    items_data = data.get('items') or []
    if not invoice_id or not items_data:
        return Response({'error': 'invoice_id and items are required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        with transaction.atomic():
            try:
                invoice = Invoice.objects.select_related('customer').get(pk=invoice_id, company=company)
            except Invoice.DoesNotExist:
                raise ValueError(f'Invoice {invoice_id} not found.')

            credit_note = CreditNote.objects.create(
                company=company, customer=invoice.customer, invoice=invoice,
                created_by=request.user, reason=data.get('reason', 'return'),
                notes=data.get('notes', ''),
            )

            total_refund = Decimal('0')
            for line in items_data:
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

                CreditNoteItem.objects.create(
                    credit_note=credit_note, invoice_item=invoice_item, product=product,
                    tracking_unit=tracking_unit, quantity=quantity, unit_price=unit_price,
                )
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

    return Response(CreditNoteSerializer(credit_note).data, status=status.HTTP_201_CREATED)