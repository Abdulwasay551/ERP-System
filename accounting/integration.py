"""
Module Integration Services and Signals
These handle automatic journal entry creation when transactions occur in other modules.
"""

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal
from .models import Account, Journal, JournalEntry, JournalItem, ModuleAccountMapping, AutoJournalEntry
from user_auth.models import Company


class AccountingIntegrationService:
    """
    Service class for creating automatic journal entries from module transactions
    """
    
    @staticmethod
    def create_journal_entry(company, transaction_type, amount, description, 
                           source_module, source_model, source_object_id, 
                           date=None, reference=None):
        """
        Create a journal entry automatically based on transaction type mapping
        
        Args:
            company: Company instance
            transaction_type: Type of transaction (from ModuleAccountMapping.TRANSACTION_TYPES)
            amount: Transaction amount
            description: Journal entry description
            source_module: Source module name (e.g., 'sales', 'purchase')
            source_model: Source model name (e.g., 'Invoice', 'Bill')
            source_object_id: ID of the source object
            date: Transaction date (defaults to today)
            reference: Transaction reference
            
        Returns:
            JournalEntry instance or None if mapping doesn't exist
        """
        from django.utils import timezone
        
        try:
            # Get account mapping for this transaction type
            mapping = ModuleAccountMapping.objects.get(
                company=company,
                transaction_type=transaction_type,
                is_active=True
            )
            
            # Create journal entry
            journal_entry = JournalEntry.objects.create(
                company=company,
                date=date or timezone.now().date(),
                reference=reference or f"{source_module.upper()}-{source_object_id}",
                description=description,
                posted=True  # Auto-post integration entries
            )
            
            # Create debit item
            JournalItem.objects.create(
                journal_entry=journal_entry,
                account=mapping.debit_account,
                description=description,
                debit=amount,
                credit=Decimal('0.00')
            )
            
            # Create credit item
            JournalItem.objects.create(
                journal_entry=journal_entry,
                account=mapping.credit_account,
                description=description,
                debit=Decimal('0.00'),
                credit=amount
            )
            
            # Create audit trail
            AutoJournalEntry.objects.create(
                company=company,
                journal_entry=journal_entry,
                source_module=source_module,
                source_model=source_model,
                source_object_id=source_object_id,
                transaction_type=transaction_type
            )
            
            return journal_entry
            
        except ModuleAccountMapping.DoesNotExist:
            # No mapping configured - skip automatic entry
            return None
        except Exception as e:
            # Log error but don't raise to avoid breaking module operations
            print(f"Error creating automatic journal entry: {e}")
            return None
    
    @staticmethod
    def reverse_journal_entry(auto_journal_entry):
        """
        Reverse an automatically created journal entry
        
        Args:
            auto_journal_entry: AutoJournalEntry instance to reverse
            
        Returns:
            JournalEntry instance of the reversal
        """
        from django.utils import timezone
        
        original_entry = auto_journal_entry.journal_entry
        
        # Create reversal entry
        reversal_entry = JournalEntry.objects.create(
            company=original_entry.company,
            date=timezone.now().date(),
            reference=f"REV-{original_entry.reference}",
            description=f"Reversal of {original_entry.description}",
            posted=True
        )
        
        # Reverse each journal item
        for item in original_entry.items.all():
            JournalItem.objects.create(
                journal_entry=reversal_entry,
                account=item.account,
                description=f"Reversal of {item.description}",
                debit=item.credit,  # Swap debit/credit
                credit=item.debit
            )
        
        return reversal_entry


# Signal handlers for automatic journal entry creation
# These will be triggered when records are created in other modules

@receiver(post_save, sender='sales.Invoice')
def create_sales_invoice_journal_entry(sender, instance, created, **kwargs):
    """Create journal entry when sales invoice is created"""
    if created and hasattr(instance, 'company'):
        try:
            AccountingIntegrationService.create_journal_entry(
                company=instance.company,
                transaction_type='sales_invoice',
                amount=instance.total_amount if hasattr(instance, 'total_amount') else Decimal('0.00'),
                description=f"Sales Invoice #{instance.id}",
                source_module='sales',
                source_model='Invoice',
                source_object_id=str(instance.id),
                date=instance.date if hasattr(instance, 'date') else None,
                reference=f"INV-{instance.id}"
            )
        except (ValueError, AttributeError):
            # Skip if mapping doesn't exist or required fields are missing
            pass


@receiver(post_save, sender='purchase.Bill')
def create_purchase_invoice_journal_entry(sender, instance, created, **kwargs):
    """Create journal entry when purchase bill is created"""
    if created and hasattr(instance, 'company'):
        try:
            AccountingIntegrationService.create_journal_entry(
                company=instance.company,
                transaction_type='purchase_invoice',
                amount=instance.total_amount if hasattr(instance, 'total_amount') else Decimal('0.00'),
                description=f"Purchase Bill #{instance.id}",
                source_module='purchase',
                source_model='Bill',
                source_object_id=str(instance.id),
                date=instance.date if hasattr(instance, 'date') else None,
                reference=f"PINV-{instance.id}"
            )
        except (ValueError, AttributeError):
            pass


@receiver(post_save, sender='inventory.StockMovement')
def create_inventory_journal_entry(sender, instance, created, **kwargs):
    """Create journal entry for inventory movements"""
    if created and hasattr(instance, 'company'):
        try:
            # Determine transaction type based on movement type
            transaction_type = 'inventory_adjustment'
            if hasattr(instance, 'movement_type'):
                if instance.movement_type == 'in':
                    transaction_type = 'inventory_receipt'
                elif instance.movement_type == 'out':
                    transaction_type = 'inventory_issue'
            
            AccountingIntegrationService.create_journal_entry(
                company=instance.company,
                transaction_type=transaction_type,
                amount=instance.value if hasattr(instance, 'value') else Decimal('0.00'),
                description=f"Stock Movement - {instance.product.name if hasattr(instance, 'product') else 'Unknown'}",
                source_module='inventory',
                source_model='StockMovement',
                source_object_id=str(instance.id),
                date=instance.date if hasattr(instance, 'date') else None,
                reference=f"STK-{instance.id}"
            )
        except (ValueError, AttributeError):
            pass


@receiver(post_save, sender='hr.Payroll')
def create_payroll_journal_entry(sender, instance, created, **kwargs):
    """Create journal entry for payroll processing"""
    if created and hasattr(instance, 'company'):
        try:
            AccountingIntegrationService.create_journal_entry(
                company=instance.company,
                transaction_type='payroll_salary',
                amount=instance.total_salary if hasattr(instance, 'total_salary') else Decimal('0.00'),
                description=f"Payroll for {instance.period if hasattr(instance, 'period') else 'Unknown Period'}",
                source_module='hr',
                source_model='Payroll',
                source_object_id=str(instance.id),
                date=instance.date if hasattr(instance, 'date') else None,
                reference=f"PAY-{instance.id}"
            )
        except (ValueError, AttributeError):
            pass


@receiver(post_save, sender='manufacturing.WorkOrder')
def create_manufacturing_journal_entry(sender, instance, created, **kwargs):
    """Create journal entry for manufacturing work orders"""
    if not created and hasattr(instance, 'company') and hasattr(instance, 'status'):
        # Only create entry when work order is completed
        if instance.status == 'completed':
            try:
                AccountingIntegrationService.create_journal_entry(
                    company=instance.company,
                    transaction_type='production_completion',
                    amount=instance.total_cost if hasattr(instance, 'total_cost') else Decimal('0.00'),
                    description=f"Production Completion - WO #{instance.id}",
                    source_module='manufacturing',
                    source_model='WorkOrder',
                    source_object_id=str(instance.id),
                    date=instance.completion_date if hasattr(instance, 'completion_date') else None,
                    reference=f"WO-{instance.id}"
                )
            except (ValueError, AttributeError):
                pass
