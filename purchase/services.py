"""
Shared bill-receiving logic - one line's worth of "physically scan/count this in" work,
used identically whether it happens later via bill_receive_items() (the normal flow) or
immediately at bill-creation time via vendor_invoice_create()'s optional per-line
`received: true` (the shop already has the phones in hand when recording the invoice).
Extracted so both call sites share one set of IMEI-format/uniqueness checks and one
StockItem/average-cost bump, instead of two copies drifting apart over time.
"""
from decimal import Decimal

from products.models import ProductTracking
from inventory.models import StockItem


def receive_bill_line(bill_item, warehouse, company, user, codes=None, quantity=None, tracking_pk_provider=None):
    """
    Receives one bill line - either a list of tracking `codes` (imei/serial/barcode
    products) or a plain `quantity` (untracked products); which one is used is decided
    by the line's product.tracking_method, not by which argument the caller happened to
    pass. Raises ValueError on any validation failure (bad IMEI format, duplicate code,
    over-receipt past what was ordered) - never partially applies a line's own effects.

    `tracking_pk_provider`, if given, is called with no arguments once per tracking code
    created, in order, and should return an explicit PK to try (or None for a normal
    auto-assigned PK) - this is how each call site plugs in its own desktop-replay
    PK-indexing contract (bill_receive_items' `desktop_pks.tracking_units` vs.
    vendor_invoice_create's own) without this shared function needing to know about it.

    Returns (summary: dict, tracking_unit_ids: list[int], pk_conflicts: list[dict]).
    """
    from core.pk_conflict import create_with_pk_fallback

    product = bill_item.product
    variant = bill_item.variant
    tracking_unit_ids = []
    pk_conflicts = []

    if product.tracking_method in ('imei', 'serial', 'barcode'):
        codes = codes or []
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
            explicit_tracking_id = tracking_pk_provider() if tracking_pk_provider else None
            tracking_unit, tracking_conflict = create_with_pk_fallback(
                ProductTracking.objects, explicit_tracking_id,
                product=product,
                variant=variant,
                current_warehouse=warehouse,
                supplier=bill_item.bill.supplier,
                bill_item=bill_item,
                purchase_price=bill_item.unit_price,
                purchase_date=bill_item.bill.bill_date,
                status='available',
                created_by=user,
                **{tracking_field: code}
            )
            if tracking_conflict:
                pk_conflicts.append({'model': 'products.ProductTracking', **tracking_conflict})
            tracking_unit_ids.append(tracking_unit.id)

        # Dual-write a StockItem alongside ProductTracking (mirrors the existing GRN
        # receiving pattern) - process_inventory_reduction() is StockItem-driven, so
        # without this a tracked product sold via POS would silently never get its
        # ProductTracking unit marked sold.
        stock_item, _ = StockItem.objects.get_or_create(
            company=company, product=product, warehouse=warehouse,
            defaults={'stock_status': 'available', 'purchase_status': 'ready_for_use'}
        )
        stock_item.update_average_cost(Decimal(len(codes)), bill_item.unit_price)
        stock_item.quantity += len(codes)
        stock_item.save()

        bill_item.received_quantity += len(codes)
        bill_item.save(update_fields=['received_quantity'])

        summary = {'bill_item_id': bill_item.id, 'product_name': product.name, 'units_received': len(codes)}
    else:
        quantity = Decimal(str(quantity or '0'))
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
        # update_average_cost() computes the new weighted average from the CURRENT
        # (pre-addition) quantity + the incoming quantity, then saves - so quantity must
        # only be incremented after that call, not before.
        stock_item.update_average_cost(quantity, bill_item.unit_price)
        stock_item.quantity += quantity
        stock_item.save()

        bill_item.received_quantity += quantity
        bill_item.save(update_fields=['received_quantity'])

        summary = {'bill_item_id': bill_item.id, 'product_name': product.name, 'quantity_received': str(quantity)}

    return summary, tracking_unit_ids, pk_conflicts
