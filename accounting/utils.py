from .models import Account
from django.core.exceptions import ValidationError

def validate_account_for_posting(account: Account):
    if not account.is_active:
        raise ValidationError('Account is not active.')
    if account.is_group:
        raise ValidationError('Cannot post to a group account.')
    return True

def auto_post_journal(company, account, debit=0, credit=0, description='', reference='', user=None, journal_type='general', date=None):
    from .models import Journal, JournalEntry, JournalItem
    validate_account_for_posting(account)
    journal, _ = Journal.objects.get_or_create(company=company, type=journal_type, defaults={'name': journal_type.title()})
    entry = JournalEntry.objects.create(journal=journal, company=company, date=date, reference=reference, created_by=user)
    JournalItem.objects.create(entry=entry, account=account, debit=debit, credit=credit, description=description)
    return entry

def auto_post_journal_multi(company, lines, description='', reference='', user=None, journal_type='general', date=None):
    """
    Batch post multiple debit/credit lines to a journal entry.
    lines: list of dicts, each with keys: account, debit, credit, (optional) description
    Example:
        lines = [
            {'account': acc1, 'debit': 100},
            {'account': acc2, 'credit': 100, 'description': 'To revenue'}
        ]
    """
    from .models import Journal, JournalEntry, JournalItem
    journal, _ = Journal.objects.get_or_create(company=company, type=journal_type, defaults={'name': journal_type.title()})
    entry = JournalEntry.objects.create(journal=journal, company=company, date=date, reference=reference, created_by=user)
    for line in lines:
        account = line['account']
        validate_account_for_posting(account)
        JournalItem.objects.create(
            entry=entry,
            account=account,
            debit=line.get('debit', 0),
            credit=line.get('credit', 0),
            description=line.get('description', description)
        )
    return entry

def auto_post_context(company, context_type, context_obj, user=None, date=None):
    """
    Context-aware posting for business events (sales, purchase, payroll, etc.).
    context_type: 'sales', 'purchase', 'payroll', etc.
    context_obj: the model instance (e.g., Invoice, Bill, Payroll)
    Posts appropriate journal entries based on context.
    """
    # Example for sales invoice
    if context_type == 'sales':
        account_receivable = context_obj.account  # e.g., Invoice.account
        revenue_account = getattr(context_obj, 'revenue_account', None)
        amount = context_obj.total
        lines = [
            {'account': account_receivable, 'debit': amount, 'description': 'Invoice receivable'},
        ]
        if revenue_account:
            lines.append({'account': revenue_account, 'credit': amount, 'description': 'Sales revenue'})
        return auto_post_journal_multi(company, lines, reference=str(context_obj.pk), user=user, journal_type='sales', date=date)
    # Add more context types as needed
    raise NotImplementedError(f'Context type {context_type} not implemented.') 