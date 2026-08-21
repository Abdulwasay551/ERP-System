"""Shared line-item discount math, used identically by sales.InvoiceItem and
purchase.BillItem so both sides of the business (selling and buying) combine
discounts the same way.

A line can carry multiple discounts at once, e.g. a fixed rebate AND a
percentage off in one go. Each entry in `discounts` is
    {"type": "fixed" | "percent" | "per_unit", "value": "10.00"}
- fixed: a flat amount off the whole line.
- per_unit: a flat amount off each unit, multiplied by quantity.
- percent: a percentage off what's left after all fixed/per_unit discounts.

Combination order: sum every fixed/per_unit discount first (capped at the
line's base amount, so a line can never go negative), then apply every
percent discount sequentially to whatever remains.
"""
from decimal import Decimal


def compute_line_discount(base_amount, quantity, discounts):
    """Returns the total discount amount (Decimal) to subtract from base_amount."""
    base_amount = Decimal(str(base_amount or 0))
    quantity = Decimal(str(quantity or 0))
    if not discounts:
        return Decimal('0')

    flat_off = Decimal('0')
    percent_entries = []
    for entry in discounts:
        entry_type = entry.get('type')
        value = Decimal(str(entry.get('value') or 0))
        if entry_type == 'fixed':
            flat_off += value
        elif entry_type == 'per_unit':
            flat_off += value * quantity
        elif entry_type == 'percent':
            percent_entries.append(value)

    flat_off = min(flat_off, base_amount)
    remaining = base_amount - flat_off

    percent_off_total = Decimal('0')
    for percent in percent_entries:
        percent_off = remaining * (percent / Decimal('100'))
        percent_off_total += percent_off
        remaining -= percent_off

    total_discount = flat_off + percent_off_total
    return min(total_discount, base_amount)


def resolve_header_discount(base_amount, amount, discount_type):
    """
    Whole-invoice/whole-bill discount amount to subtract from base_amount (Decimal) -
    unlike line discounts, this is a single value with a single type, not a stack.
    'percent': amount is 0-100, applied to base_amount. 'fixed' (default/unknown):
    amount is a flat currency figure. Both capped at base_amount so a header discount
    can never drive the total negative.
    """
    base_amount = Decimal(str(base_amount or 0))
    amount = Decimal(str(amount or 0))
    if discount_type == 'percent':
        amount = base_amount * (amount / Decimal('100'))
    return min(amount, base_amount)
