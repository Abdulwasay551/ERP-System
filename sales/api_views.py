from decimal import Decimal, InvalidOperation
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Q, Sum
from django.core.files.base import ContentFile
from user_auth.permissions import RoleIn
from products.models import ProductTracking
from inventory.models import StockItem
from crm.models import Customer
from core.pdf_utils import render_pdf
from .models import Product, Tax, Quotation, SalesOrder, SalesOrderItem, Invoice, InvoiceItem, Payment
from .serializers import ProductSerializer, TaxSerializer, QuotationSerializer, SalesOrderSerializer, SalesOrderItemSerializer, InvoiceSerializer, PaymentSerializer

class ProductViewSet(viewsets.ModelViewSet):
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

class InvoiceViewSet(viewsets.ModelViewSet):
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Invoice.objects.filter(company=self.request.user.company)

class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(company=self.request.user.company)

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company, received_by=self.request.user)


class POSStaff(RoleIn):
    allowed_roles = ['Manager', 'Cashier', 'Salesman']


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

                InvoiceItem.objects.create(
                    invoice=invoice, product=product, quantity=quantity, unit_price=unit_price,
                    tracking_unit_id=tracking_id
                )
                subtotal += quantity * unit_price

            try:
                discount_amount = Decimal(str(data.get('discount_amount', '0')))
            except InvalidOperation:
                raise ValueError('Invalid discount_amount.')

            invoice.subtotal = subtotal
            invoice.discount_amount = discount_amount
            invoice.total = subtotal - discount_amount

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
                pdf_path = render_pdf('sales/invoice_pdf.html', {
                    'invoice': invoice, 'items': invoice.items.all(), 'company': company,
                })
                with open(pdf_path, 'rb') as f:
                    invoice.pdf_file.save(f'{invoice.invoice_number}.pdf', ContentFile(f.read()), save=True)
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