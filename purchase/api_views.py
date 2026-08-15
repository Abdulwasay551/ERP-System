from decimal import Decimal, InvalidOperation
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.db import transaction, IntegrityError
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.utils import timezone
from user_auth.permissions import RoleIn, IsOwnerOrManager
from core.pdf_utils import build_ledger_pdf, build_receiving_pdf
from core.mixins import SoftDeleteViewSetMixin, log_deletion
from core.idempotency import idempotent, IdempotentCreateMixin
from core.pk_conflict import PkConflictReportingMixin, save_with_pk_fallback


class ManagerOrWarehouse(RoleIn):
    allowed_roles = ['Manager', 'Warehouse']
from products.models import Product, ProductVariant, ProductTracking
from inventory.models import Warehouse, StockItem
from .models import (
    Supplier, TaxChargesTemplate, PurchaseRequisition, PurchaseRequisitionItem,
    RequestForQuotation, RFQItem, SupplierQuotation, SupplierQuotationItem,
    PurchaseOrder, PurchaseOrderItem, PurchaseOrderTaxCharge,
    GoodsReceiptNote, GRNItem, Bill, BillItem, PurchasePayment, SupplierLedgerAdjustment,
    PurchaseReturn, PurchaseReturnItem, PurchaseApproval
)
from .serializers import (
    SupplierSerializer, TaxChargesTemplateSerializer, PurchaseRequisitionSerializer,
    PurchaseRequisitionItemSerializer, RequestForQuotationSerializer, RFQItemSerializer,
    SupplierQuotationSerializer, SupplierQuotationItemSerializer, PurchaseOrderSerializer,
    PurchaseOrderItemSerializer, PurchaseOrderTaxChargeSerializer, GoodsReceiptNoteSerializer,
    GRNItemSerializer, BillSerializer, BillItemSerializer, PurchasePaymentSerializer,
    PurchaseReturnSerializer, PurchaseReturnItemSerializer, PurchaseApprovalSerializer,
    SupplierLedgerSerializer, SupplierLedgerAdjustmentSerializer
)

class SupplierViewSet(IdempotentCreateMixin, PkConflictReportingMixin, SoftDeleteViewSetMixin, viewsets.ModelViewSet):
    serializer_class = SupplierSerializer
    # Vendor management is a purchasing/warehouse concern, not shop-floor sales.
    permission_classes = [permissions.IsAuthenticated, ManagerOrWarehouse]
    filterset_fields = ['status', 'supplier_type', 'is_active']
    ordering_fields = ['partner__name', 'created_at', 'overall_rating']

    def get_queryset(self):
        qs = Supplier.objects.filter(company=self.request.user.company).select_related('partner')
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(partner__name__icontains=search) |
                Q(partner__phone__icontains=search) |
                Q(partner__email__icontains=search) |
                Q(partner__city__icontains=search)
            )
        return qs.order_by('partner__name')

    def perform_create(self, serializer):
        from core.device_registry import validated_desktop_pk, validated_desktop_number
        company = self.request.user.company
        # Supplier.id is the value other push-eligible rows (Bill.supplier_id,
        # PurchasePayment.supplier_id) actually need preserved - Partner (the linked
        # contact-info row Supplier.partner points at, created inside
        # SupplierSerializer.create()) is never referenced by its own PK anywhere else,
        # so it doesn't need its own desktop_pks entry.
        explicit_id = validated_desktop_pk(self.request.data, 'supplier', company)
        extra = {}
        explicit_code = validated_desktop_number(self.request.data, 'supplier_code', company)
        if explicit_code:
            extra['supplier_code'] = explicit_code
        conflict = save_with_pk_fallback(serializer, explicit_id, company=company, created_by=self.request.user, **extra)
        if conflict:
            self._pk_conflicts = [{'model': 'purchase.Supplier', **conflict}]

    @action(detail=False, methods=['get'])
    def active_suppliers(self, request):
        suppliers = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(suppliers, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def ledger(self, request, pk=None):
        supplier = self.get_object()
        entries = supplier.ledger_entries.all().order_by('-transaction_date', '-created_at')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        if date_from:
            entries = entries.filter(transaction_date__gte=date_from)
        if date_to:
            entries = entries.filter(transaction_date__lte=date_to)

        try:
            page = max(int(request.query_params.get('page', 1)), 1)
            page_size = min(max(int(request.query_params.get('page_size', 25)), 1), 200)
        except ValueError:
            page = 1
            page_size = 25

        count = entries.count()
        start = (page - 1) * page_size
        page_entries = entries[start:start + page_size]
        return Response({
            'count': count,
            'page': page,
            'page_size': page_size,
            'total_pages': (count + page_size - 1) // page_size if count else 1,
            'results': SupplierLedgerSerializer(page_entries, many=True).data,
        })

    @action(detail=True, methods=['get'], url_path='ledger/pdf')
    def ledger_pdf(self, request, pk=None):
        supplier = self.get_object()
        entries = supplier.ledger_entries.all().order_by('transaction_date', 'created_at')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        if date_from:
            entries = entries.filter(transaction_date__gte=date_from)
        if date_to:
            entries = entries.filter(transaction_date__lte=date_to)
        entries = list(entries)
        closing_balance = entries[-1].balance if entries else supplier.get_outstanding_balance()
        name = supplier.partner.name
        buf = build_ledger_pdf(name, 'Supplier', entries, date_from, date_to, closing_balance)
        response = HttpResponse(buf.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{name}-ledger.pdf"'
        return response

    @action(detail=True, methods=['get'], url_path='outstanding-balance')
    def outstanding_balance(self, request, pk=None):
        supplier = self.get_object()
        return Response({'supplier_id': supplier.id, 'outstanding_balance': str(supplier.get_outstanding_balance())})


class SupplierLedgerAdjustmentViewSet(IdempotentCreateMixin, SoftDeleteViewSetMixin, viewsets.ModelViewSet):
    """Manual debit/credit against a supplier's ledger - not tied to a bill/payment.
    Mirrors crm.CustomerLedgerAdjustmentViewSet exactly, including the Owner/Manager-only
    gate (direct balance manipulation with no bill paper trail behind it)."""
    serializer_class = SupplierLedgerAdjustmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]
    filterset_fields = ['supplier', 'entry_type']
    ordering_fields = ['transaction_date', 'amount', 'created_at']

    def get_queryset(self):
        return SupplierLedgerAdjustment.objects.filter(company=self.request.user.company)

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company, created_by=self.request.user)


class TaxChargesTemplateViewSet(viewsets.ModelViewSet):
    serializer_class = TaxChargesTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return TaxChargesTemplate.objects.filter(company=self.request.user.company)

class PurchaseRequisitionViewSet(viewsets.ModelViewSet):
    serializer_class = PurchaseRequisitionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return PurchaseRequisition.objects.filter(company=self.request.user.company)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        requisition = self.get_object()
        requisition.status = 'approved'
        requisition.approved_by = request.user
        requisition.save()
        return Response({'status': 'approved'})
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        requisition = self.get_object()
        requisition.status = 'rejected'
        requisition.rejected_reason = request.data.get('reason', '')
        requisition.save()
        return Response({'status': 'rejected'})

class PurchaseRequisitionItemViewSet(viewsets.ModelViewSet):
    serializer_class = PurchaseRequisitionItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return PurchaseRequisitionItem.objects.filter(purchase_requisition__company=self.request.user.company)

class RequestForQuotationViewSet(viewsets.ModelViewSet):
    serializer_class = RequestForQuotationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return RequestForQuotation.objects.filter(company=self.request.user.company)

class RFQItemViewSet(viewsets.ModelViewSet):
    serializer_class = RFQItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return RFQItem.objects.filter(rfq__company=self.request.user.company)

class SupplierQuotationViewSet(viewsets.ModelViewSet):
    serializer_class = SupplierQuotationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return SupplierQuotation.objects.filter(company=self.request.user.company)
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        quotation = self.get_object()
        quotation.status = 'accepted'
        quotation.save()
        return Response({'status': 'accepted'})

class SupplierQuotationItemViewSet(viewsets.ModelViewSet):
    serializer_class = SupplierQuotationItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return SupplierQuotationItem.objects.filter(quotation__company=self.request.user.company)

class PurchaseOrderViewSet(viewsets.ModelViewSet):
    serializer_class = PurchaseOrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return PurchaseOrder.objects.filter(company=self.request.user.company)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        order = self.get_object()
        order.status = 'approved'
        order.approved_by = request.user
        order.save()
        return Response({'status': 'approved'})
    
    @action(detail=True, methods=['post'])
    def send_to_supplier(self, request, pk=None):
        order = self.get_object()
        order.status = 'sent_to_supplier'
        order.save()
        return Response({'status': 'sent_to_supplier'})

class PurchaseOrderItemViewSet(viewsets.ModelViewSet):
    serializer_class = PurchaseOrderItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return PurchaseOrderItem.objects.filter(purchase_order__company=self.request.user.company)

class PurchaseOrderTaxChargeViewSet(viewsets.ModelViewSet):
    serializer_class = PurchaseOrderTaxChargeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return PurchaseOrderTaxCharge.objects.filter(purchase_order__company=self.request.user.company)

class GoodsReceiptNoteViewSet(viewsets.ModelViewSet):
    serializer_class = GoodsReceiptNoteSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return GoodsReceiptNote.objects.filter(company=self.request.user.company)
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """
        Marks the GRN's status only - this legacy RFQ->PO->GRN pipeline predates and
        isn't wired to inventory. The shop's actual receiving flow is
        vendor_invoice_create -> bill_receive_items -> bill_confirm_received (see
        BillViewSet.pending_receipt below), which writes real StockItem/ProductTracking
        rows. Writing stock here too would create a second, divergent path for stock to
        enter the system alongside the canonical one.
        """
        grn = self.get_object()
        grn.status = 'accepted'
        grn.save()
        return Response({'status': 'accepted'})

class GRNItemViewSet(viewsets.ModelViewSet):
    serializer_class = GRNItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return GRNItem.objects.filter(grn__company=self.request.user.company)

class BillViewSet(SoftDeleteViewSetMixin, viewsets.ModelViewSet):
    serializer_class = BillSerializer
    permission_classes = [permissions.IsAuthenticated]
    cascade_to = ['payments']
    filterset_fields = ['status', 'supplier', 'goods_received']
    ordering_fields = ['bill_date', 'total_amount', 'created_at']

    def get_queryset(self):
        return Bill.objects.filter(company=self.request.user.company)
    
    @action(detail=True, methods=['post'])
    def three_way_match(self, request, pk=None):
        bill = self.get_object()
        matched = bill.validate_three_way_match()
        bill.save()
        return Response({
            'status': 'matched' if matched else 'mismatched',
            'three_way_match_status': bill.three_way_match_status,
            'po_match_status': bill.po_match_status,
            'grn_match_status': bill.grn_match_status,
            'has_additional_items': bill.has_additional_items,
            'has_quantity_variances': bill.has_quantity_variances,
        })

    @action(detail=False, methods=['get'], url_path='pending-receipt')
    def pending_receipt(self, request):
        """Vendor invoices recorded but not yet physically received - for the dashboard."""
        bills = self.get_queryset().filter(goods_received=False).order_by('-bill_date')
        serializer = self.get_serializer(bills, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def pdf(self, request, pk=None):
        """Goods-received note for this bill, generated fresh on each request."""
        bill = self.get_object()
        buf = build_receiving_pdf(bill, bill.items.select_related('product').all())
        response = HttpResponse(buf.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{bill.bill_number}-receiving.pdf"'
        return response

    @action(detail=True, methods=['post'])
    def edit(self, request, pk=None):
        """
        Owner/Manager-only correction of a posted bill. Header fields are always
        editable. Per line: once received_quantity > 0 (bill_receive_items() has
        scanned/counted any of it), product and quantity lock - unlike invoices, bill
        receiving has no StockMovement-style audit trail, so there's no safe way to undo
        units that already landed on a shelf or were sold onward. Price/discount stay
        editable on every line regardless, cascading into that line's already-created
        ProductTracking.purchase_price so the average-purchase-price cost warning (see
        pos_search's avg_purchase_price) stays accurate. StockItem.average_cost is a
        rolling weighted average with no clean after-the-fact correction formula -
        deliberately left alone here rather than risking a wrong recompute of it.
        get_permissions() (core.mixins.SoftDeleteViewSetMixin) gates this to Owner/
        Manager only.
        """
        bill = self.get_object()
        data = request.data
        items_data = data.get('items') or []
        if not items_data:
            return Response({'error': 'items are required.'}, status=status.HTTP_400_BAD_REQUEST)

        company = request.user.company
        try:
            with transaction.atomic():
                if data.get('supplier_id'):
                    try:
                        bill.supplier = Supplier.objects.get(pk=data['supplier_id'], company=company)
                    except Supplier.DoesNotExist:
                        raise ValueError(f"Supplier {data['supplier_id']} not found.")
                for field in ('bill_date', 'due_date', 'supplier_invoice_number', 'notes'):
                    if field in data:
                        setattr(bill, field, data[field])

                existing_items = {item.id: item for item in bill.items.all()}
                kept_ids = set()

                for line in items_data:
                    line_id = line.get('id')
                    try:
                        unit_price = Decimal(str(line['unit_price'])) if line.get('unit_price') is not None else None
                    except InvalidOperation:
                        raise ValueError('Invalid unit_price.')
                    discounts = line.get('discounts')

                    if line_id:
                        bill_item = existing_items.get(int(line_id))
                        if not bill_item:
                            raise ValueError(f'Bill item {line_id} not found on this bill.')
                        kept_ids.add(bill_item.id)

                        if bill_item.received_quantity > 0:
                            new_product_id = line.get('product_id')
                            new_quantity = line.get('quantity')
                            if new_product_id and int(new_product_id) != bill_item.product_id:
                                raise ValueError(
                                    f"{bill_item.product.name}: product can't be changed - "
                                    f"{bill_item.received_quantity} unit(s) already received on this line."
                                )
                            if new_quantity is not None and Decimal(str(new_quantity)) != bill_item.quantity:
                                raise ValueError(
                                    f"{bill_item.product.name}: quantity can't be changed - "
                                    f"{bill_item.received_quantity} unit(s) already received on this line."
                                )
                        else:
                            if line.get('product_id'):
                                try:
                                    bill_item.product = Product.objects.get(pk=line['product_id'], company=company)
                                except Product.DoesNotExist:
                                    raise ValueError(f"Product {line['product_id']} not found.")
                            if line.get('quantity') is not None:
                                try:
                                    new_qty = Decimal(str(line['quantity']))
                                except InvalidOperation:
                                    raise ValueError(f'Invalid quantity for bill item {line_id}.')
                                if new_qty <= 0:
                                    raise ValueError('quantity must be > 0.')
                                bill_item.quantity = new_qty

                        if unit_price is not None:
                            bill_item.unit_price = unit_price
                        if discounts is not None:
                            bill_item.discounts = discounts
                        bill_item.save()

                        if unit_price is not None and bill_item.received_quantity > 0:
                            bill_item.product_tracking_units.update(purchase_price=unit_price)
                    else:
                        product_id = line.get('product_id')
                        if not product_id:
                            raise ValueError('Each new item requires a product_id.')
                        try:
                            product = Product.objects.get(pk=product_id, company=company)
                        except Product.DoesNotExist:
                            raise ValueError(f'Product {product_id} not found.')
                        try:
                            quantity = Decimal(str(line.get('quantity', '0')))
                        except InvalidOperation:
                            raise ValueError(f'Invalid quantity for product {product_id}.')
                        if quantity <= 0:
                            raise ValueError(f'quantity must be > 0 for product {product.name}.')
                        new_item = BillItem.objects.create(
                            bill=bill, product=product, quantity=quantity,
                            unit_price=unit_price or Decimal('0'), item_source='manual',
                            discounts=discounts or [],
                        )
                        kept_ids.add(new_item.id)

                for item_id, bill_item in existing_items.items():
                    if item_id not in kept_ids:
                        if bill_item.received_quantity > 0:
                            raise ValueError(
                                f"{bill_item.product.name}: can't remove this line - "
                                f"{bill_item.received_quantity} unit(s) already received against it."
                            )
                        bill_item.delete()

                try:
                    bill.discount_amount = Decimal(str(data.get('discount_amount', bill.discount_amount)))
                except InvalidOperation:
                    raise ValueError('Invalid discount_amount.')
                bill.subtotal = sum(item.line_total for item in bill.items.all())
                bill.total_amount = bill.subtotal + bill.tax_amount - bill.discount_amount
                bill.save()

                if bill.paid_amount >= bill.total_amount and bill.total_amount > 0:
                    bill.status = 'paid'
                elif bill.paid_amount > 0:
                    bill.status = 'partially_paid'
                bill.save(update_fields=['status'])

                log_deletion(bill, request.user, 'edited')
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(BillSerializer(bill).data)

class BillItemViewSet(viewsets.ModelViewSet):
    serializer_class = BillItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return BillItem.objects.filter(bill__company=self.request.user.company)

class PurchasePaymentViewSet(IdempotentCreateMixin, PkConflictReportingMixin, SoftDeleteViewSetMixin, viewsets.ModelViewSet):
    serializer_class = PurchasePaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['supplier', 'bill', 'payment_method', 'status']
    ordering_fields = ['payment_date', 'amount', 'created_at']

    def get_queryset(self):
        return PurchasePayment.objects.filter(company=self.request.user.company)

    def perform_create(self, serializer):
        from core.device_registry import validated_desktop_pk, validated_desktop_number
        company = self.request.user.company
        explicit_id = validated_desktop_pk(self.request.data, 'purchase_payment', company)
        extra = {}
        explicit_number = validated_desktop_number(self.request.data, 'payment_number', company)
        if explicit_number:
            extra['payment_number'] = explicit_number
        conflict = save_with_pk_fallback(serializer, explicit_id, company=company, created_by=self.request.user, **extra)
        if conflict:
            self._pk_conflicts = [{'model': 'purchase.PurchasePayment', **conflict}]

class PurchaseReturnViewSet(viewsets.ModelViewSet):
    serializer_class = PurchaseReturnSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return PurchaseReturn.objects.filter(company=self.request.user.company)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        return_order = self.get_object()
        return_order.status = 'approved'
        return_order.approved_by = request.user
        return_order.save()
        return Response({'status': 'approved'})

class PurchaseReturnItemViewSet(viewsets.ModelViewSet):
    serializer_class = PurchaseReturnItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return PurchaseReturnItem.objects.filter(purchase_return__company=self.request.user.company)

class PurchaseApprovalViewSet(viewsets.ModelViewSet):
    serializer_class = PurchaseApprovalSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return PurchaseApproval.objects.filter(company=self.request.user.company)
    
    @action(detail=False, methods=['get'])
    def pending_approvals(self, request):
        approvals = self.get_queryset().filter(
            Q(approver=request.user) & Q(status='pending')
        )
        serializer = self.get_serializer(approvals, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        approval = self.get_object()
        approval.status = 'approved'
        approval.approved_at = timezone.now()
        approval.comments = request.data.get('comments', '')
        approval.save()
        return Response({'status': 'approved'})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, ManagerOrWarehouse])
@idempotent
def vendor_invoice_create(request):
    """
    Record a vendor invoice (manual bill, bypassing RFQ->PO->GRN - same philosophy as the
    POS quick-sale endpoint bypassing Quotation->SalesOrder). This only records what was
    invoiced/expected; it does NOT create stock or tracking units, because the vendor's
    invoice commonly arrives before the physical phones do. The liability is recorded on
    the supplier ledger immediately (via Bill.save()); physical stock is only created when
    bill_receive_items() is called against this bill, once the shipment actually arrives.
    """
    company = request.user.company
    data = request.data

    supplier_id = data.get('supplier_id')
    items_data = data.get('items') or []

    if not supplier_id or not items_data:
        return Response({'error': 'supplier_id and items are required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        supplier = Supplier.objects.get(pk=supplier_id, company=company)
    except Supplier.DoesNotExist:
        return Response({'error': f'Supplier {supplier_id} not found.'}, status=status.HTTP_404_NOT_FOUND)

    warehouse = None
    if data.get('warehouse_id'):
        try:
            warehouse = Warehouse.objects.get(pk=data['warehouse_id'], company=company)
        except Warehouse.DoesNotExist:
            return Response({'error': f"Warehouse {data['warehouse_id']} not found."}, status=status.HTTP_404_NOT_FOUND)

    # Phase C push-back replay - see sales.api_views.pos_checkout's matching comment for
    # the full reasoning (same mechanism, same reason it has to be a real replay of this
    # endpoint rather than a raw row upsert: Bill.save() posts to the supplier ledger).
    from core.device_registry import validated_desktop_pk, validated_desktop_number
    from core.pk_conflict import create_with_pk_fallback
    desktop_item_pks = (data.get('desktop_pks') or {}).get('items') or []
    pk_conflicts = []

    try:
        with transaction.atomic():
            explicit_bill_id = validated_desktop_pk(data, 'bill', company)
            bill_kwargs = dict(
                company=company,
                supplier=supplier,
                warehouse=warehouse,
                supplier_invoice_number=data.get('supplier_invoice_number', ''),
                bill_date=data.get('bill_date') or timezone.now().date(),
                matching_type='manual',
                status='approved',
                goods_received=False,
                created_by=request.user,
            )
            explicit_bill_number = validated_desktop_number(data, 'bill_number', company)
            if explicit_bill_number:
                bill_kwargs['bill_number'] = explicit_bill_number
            bill, bill_conflict = create_with_pk_fallback(Bill.objects, explicit_bill_id, **bill_kwargs)
            if bill_conflict:
                pk_conflicts.append({'model': 'purchase.Bill', **bill_conflict})

            item_summaries = []
            for index, line in enumerate(items_data):
                product_id = line.get('product_id')
                if not product_id:
                    raise ValueError('Each item requires a product_id.')
                try:
                    product = Product.objects.get(pk=product_id, company=company)
                except Product.DoesNotExist:
                    raise ValueError(f'Product {product_id} not found.')

                variant = None
                if line.get('variant_id'):
                    try:
                        variant = ProductVariant.objects.get(pk=line['variant_id'], product=product)
                    except ProductVariant.DoesNotExist:
                        raise ValueError(f"Variant {line['variant_id']} not found for product {product_id}.")

                try:
                    unit_price = Decimal(str(line.get('unit_price', '0')))
                    quantity = Decimal(str(line.get('expected_quantity', '0')))
                except InvalidOperation:
                    raise ValueError(f'Invalid unit_price/expected_quantity for product {product_id}.')
                if quantity <= 0:
                    raise ValueError(f'expected_quantity must be > 0 for product {product.name}.')

                item_id = None
                if index < len(desktop_item_pks):
                    item_id = validated_desktop_pk({'desktop_pks': {'item': desktop_item_pks[index]}, 'device_id': data.get('device_id')}, 'item', company)
                bill_item, item_conflict = create_with_pk_fallback(
                    BillItem.objects, item_id,
                    bill=bill, product=product, variant=variant,
                    quantity=quantity, unit_price=unit_price, item_source='manual',
                    discounts=line.get('discounts') or [],
                )
                if item_conflict:
                    pk_conflicts.append({'model': 'purchase.BillItem', **item_conflict})
                item_summaries.append({
                    'bill_item_id': bill_item.id, 'product_id': product.id,
                    'product_name': product.name, 'expected_quantity': str(quantity),
                    'tracking_method': product.tracking_method,
                })

            try:
                bill.discount_amount = Decimal(str(data.get('discount_amount', '0')))
            except InvalidOperation:
                raise ValueError('Invalid discount_amount.')
            bill.subtotal = sum(item.line_total for item in bill.items.all())
            bill.total_amount = bill.subtotal + bill.tax_amount - bill.discount_amount
            bill.save()

    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    response_body = {
        'bill_id': bill.id,
        'bill_number': bill.bill_number,
        'supplier': supplier.name,
        'total_amount': str(bill.total_amount),
        'goods_received': bill.goods_received,
        'items': item_summaries,
    }
    if pk_conflicts:
        response_body['pk_conflicts'] = pk_conflicts
    return Response(response_body, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, ManagerOrWarehouse])
@idempotent
def bill_receive_items(request, bill_id):
    """
    Scan the physical shipment against a previously-recorded vendor invoice: for each
    line, either a list of scanned IMEI/serial/barcode `codes` (individually tracked
    products) or a `quantity` (accessories). Callable multiple times as the user works
    through the shipment product-by-product ("select mobile model, add bulk, scan, done,
    add another product"); call bill_confirm_received() once everything has arrived.

    Phase C push-back replay: `desktop_pks.tracking_units` is a flat list of PKs, one
    per individually-tracked unit created by this call, in the same order those units
    get created below (line-by-line, code-by-code within a line) - a replay against
    production sends the same list back so each ProductTracking row lands on the exact
    PK already committed locally, matching the indexed-list pattern
    vendor_invoice_create already uses for its own items. Accessory (non-individually-
    tracked) lines only ever get/create a StockItem by natural key (company, product,
    warehouse), never a fresh row with its own id to preserve - see StockItem's
    get_or_create() calls below, unchanged.
    """
    from core.device_registry import validated_desktop_pk
    from core.pk_conflict import create_with_pk_fallback

    company = request.user.company
    data = request.data
    items_data = data.get('items') or []
    warehouse_id = data.get('warehouse_id')
    desktop_tracking_pks = (data.get('desktop_pks') or {}).get('tracking_units') or []
    tracking_index = 0
    pk_conflicts = []

    try:
        bill = Bill.objects.get(pk=bill_id, company=company)
    except Bill.DoesNotExist:
        return Response({'error': f'Bill {bill_id} not found.'}, status=status.HTTP_404_NOT_FOUND)

    warehouse = bill.warehouse
    if warehouse_id:
        try:
            warehouse = Warehouse.objects.get(pk=warehouse_id, company=company)
        except Warehouse.DoesNotExist:
            return Response({'error': f'Warehouse {warehouse_id} not found.'}, status=status.HTTP_404_NOT_FOUND)
    if not warehouse:
        return Response({'error': 'warehouse_id is required (bill has no default warehouse set).'}, status=status.HTTP_400_BAD_REQUEST)

    if not items_data:
        return Response({'error': 'items are required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        with transaction.atomic():
            tracking_units_created = 0
            tracking_unit_ids = []
            line_summaries = []

            for line in items_data:
                bill_item_id = line.get('bill_item_id')
                if not bill_item_id:
                    raise ValueError('Each item requires a bill_item_id.')
                try:
                    bill_item = BillItem.objects.get(pk=bill_item_id, bill=bill)
                except BillItem.DoesNotExist:
                    raise ValueError(f'Bill item {bill_item_id} not found on bill {bill_id}.')

                product = bill_item.product
                variant = bill_item.variant

                if product.tracking_method in ('imei', 'serial', 'barcode'):
                    codes = line.get('codes') or []
                    if not codes:
                        raise ValueError(
                            f'Product {product.name} requires individual codes '
                            f'({product.get_tracking_method_display()}) - none provided.'
                        )
                    if bill_item.received_quantity + len(codes) > bill_item.quantity:
                        raise ValueError(
                            f'{product.name}: receiving {len(codes)} more would total '
                            f'{bill_item.received_quantity + len(codes)}, more than the '
                            f'{bill_item.quantity} ordered on this line.'
                        )
                    tracking_field = product.get_tracking_field_name()

                    for code in codes:
                        code = str(code).strip()
                        if not code:
                            raise ValueError(f'Empty tracking code for product {product.name}.')
                        if product.tracking_method == 'imei' and not (len(code) == 15 and code.isdigit()):
                            raise ValueError(
                                f'"{code}" is not a valid IMEI for {product.name} - an IMEI must be '
                                f'exactly 15 digits.'
                            )
                        if ProductTracking.objects.filter(**{tracking_field: code}).exists():
                            raise ValueError(f'{product.get_tracking_method_display()} "{code}" already exists in the system.')
                        explicit_tracking_id = None
                        if tracking_index < len(desktop_tracking_pks):
                            explicit_tracking_id = validated_desktop_pk(
                                {'desktop_pks': {'unit': desktop_tracking_pks[tracking_index]}, 'device_id': data.get('device_id')},
                                'unit', company,
                            )
                        tracking_index += 1
                        tracking_unit, tracking_conflict = create_with_pk_fallback(
                            ProductTracking.objects, explicit_tracking_id,
                            product=product,
                            variant=variant,
                            current_warehouse=warehouse,
                            supplier=bill.supplier,
                            bill_item=bill_item,
                            purchase_price=bill_item.unit_price,
                            purchase_date=bill.bill_date,
                            status='available',
                            created_by=request.user,
                            **{tracking_field: code}
                        )
                        if tracking_conflict:
                            pk_conflicts.append({'model': 'products.ProductTracking', **tracking_conflict})
                        tracking_unit_ids.append(tracking_unit.id)
                        tracking_units_created += 1

                    # Dual-write a StockItem alongside ProductTracking (mirrors the
                    # existing GRN receiving pattern) - process_inventory_reduction() is
                    # StockItem-driven, so without this a tracked product sold via POS
                    # would silently never get its ProductTracking unit marked sold.
                    stock_item, _ = StockItem.objects.get_or_create(
                        company=company, product=product, warehouse=warehouse,
                        defaults={'stock_status': 'available', 'purchase_status': 'ready_for_use'}
                    )
                    stock_item.update_average_cost(Decimal(len(codes)), bill_item.unit_price)
                    stock_item.quantity += len(codes)
                    stock_item.save()

                    bill_item.received_quantity += len(codes)
                    bill_item.save(update_fields=['received_quantity'])

                    line_summaries.append({'bill_item_id': bill_item.id, 'product_name': product.name, 'units_received': len(codes)})
                else:
                    quantity = Decimal(str(line.get('quantity', '0')))
                    if quantity <= 0:
                        raise ValueError(f'quantity must be > 0 for product {product.name}.')
                    if bill_item.received_quantity + quantity > bill_item.quantity:
                        raise ValueError(
                            f'{product.name}: receiving {quantity} more would total '
                            f'{bill_item.received_quantity + quantity}, more than the '
                            f'{bill_item.quantity} ordered on this line.'
                        )
                    stock_item, _ = StockItem.objects.get_or_create(
                        company=company, product=product, warehouse=warehouse,
                        defaults={'stock_status': 'available', 'purchase_status': 'ready_for_use'}
                    )
                    # update_average_cost() computes the new weighted average from the
                    # CURRENT (pre-addition) quantity + the incoming quantity, then saves -
                    # so quantity must only be incremented after that call, not before.
                    stock_item.update_average_cost(quantity, bill_item.unit_price)
                    stock_item.quantity += quantity
                    stock_item.save()

                    bill_item.received_quantity += quantity
                    bill_item.save(update_fields=['received_quantity'])

                    line_summaries.append({'bill_item_id': bill_item.id, 'product_name': product.name, 'quantity_received': str(quantity)})

    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except IntegrityError as e:
        return Response({'error': f'Database integrity error: {e}'}, status=status.HTTP_400_BAD_REQUEST)

    response_body = {
        'bill_id': bill.id,
        'tracking_units_created': tracking_units_created,
        # Flat, creation-order list a replay's desktop_pks.tracking_units must match -
        # read by core.desktop_sync._build_replay_extras().
        'tracking_unit_ids': tracking_unit_ids,
        'items': line_summaries,
    }
    if pk_conflicts:
        response_body['pk_conflicts'] = pk_conflicts
    return Response(response_body, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, ManagerOrWarehouse])
@idempotent
def bill_confirm_received(request, bill_id):
    """Mark a vendor invoice's goods as fully received, with an optional review note.
    No new PK'd rows created (just flips flags on the existing Bill), so no desktop_pks
    handling needed - only whitelisted for push-back (core/desktop_sync_middleware.py)
    and idempotency-guarded like every other push-eligible write."""
    company = request.user.company
    try:
        bill = Bill.objects.get(pk=bill_id, company=company)
    except Bill.DoesNotExist:
        return Response({'error': f'Bill {bill_id} not found.'}, status=status.HTTP_404_NOT_FOUND)

    bill.goods_received = True
    bill.received_at = timezone.now()
    bill.received_by = request.user
    bill.receipt_notes = request.data.get('receipt_notes', '')
    bill.save()

    return Response({
        'bill_id': bill.id,
        'bill_number': bill.bill_number,
        'goods_received': bill.goods_received,
        'received_at': bill.received_at,
        'receipt_notes': bill.receipt_notes,
    }, status=status.HTTP_200_OK) 