from django import template
from decimal import Decimal, InvalidOperation

register = template.Library()

@register.filter
def div(value, arg):
    """
    Divides the value by the argument.
    Usage: {{ value|div:arg }}
    """
    try:
        # Handle different number types
        if value is None or arg is None:
            return 0
        
        # Convert to Decimal for precise calculation
        dividend = Decimal(str(value))
        divisor = Decimal(str(arg))
        
        if divisor == 0:
            return 0
        
        result = dividend / divisor
        return float(result)
    except (ValueError, InvalidOperation, TypeError):
        return 0

@register.filter
def mul(value, arg):
    """
    Multiplies the value by the argument.
    Usage: {{ value|mul:arg }}
    """
    try:
        if value is None or arg is None:
            return 0
        
        multiplicand = Decimal(str(value))
        multiplier = Decimal(str(arg))
        
        result = multiplicand * multiplier
        return float(result)
    except (ValueError, InvalidOperation, TypeError):
        return 0

@register.filter
def sub(value, arg):
    """
    Subtracts the argument from the value.
    Usage: {{ value|sub:arg }}
    """
    try:
        if value is None or arg is None:
            return 0
        
        minuend = Decimal(str(value))
        subtrahend = Decimal(str(arg))
        
        result = minuend - subtrahend
        return float(result)
    except (ValueError, InvalidOperation, TypeError):
        return 0

@register.filter
def percentage(value, total):
    """
    Calculates percentage of value relative to total.
    Usage: {{ value|percentage:total }}
    """
    try:
        if value is None or total is None or total == 0:
            return 0
        
        val = Decimal(str(value))
        tot = Decimal(str(total))
        
        if tot == 0:
            return 0
        
        result = (val / tot) * 100
        return float(result)
    except (ValueError, InvalidOperation, TypeError):
        return 0

@register.filter
def currency(value):
    """
    Formats a number as currency.
    Usage: {{ value|currency }}
    """
    try:
        if value is None:
            return "$0.00"
        
        num = float(value)
        return f"${num:,.2f}"
    except (ValueError, TypeError):
        return "$0.00"

@register.filter
def abs_value(value):
    """
    Returns the absolute value.
    Usage: {{ value|abs_value }}
    """
    try:
        if value is None:
            return 0
        return abs(float(value))
    except (ValueError, TypeError):
        return 0
