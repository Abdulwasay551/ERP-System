from django import template

register = template.Library()

@register.filter(name='get_status_class')
def get_status_class(status):
    """
    Returns appropriate Bootstrap class based on status
    """
    status_map = {
        'draft': 'secondary',
        'sent': 'info',
        'viewed': 'primary',
        'paid': 'success',
        'overdue': 'danger',
        'cancelled': 'dark',
        'refunded': 'warning',
        'partially_paid': 'warning',
    }
    return status_map.get(status.lower(), 'secondary')
