from django.core.management.base import BaseCommand
from django.db import transaction
from products.models import Product


class Command(BaseCommand):
    help = 'Update product tracking configurations to ensure consistency'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            help='Print what would be done without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )
        
        # Get all products with tracking methods
        products = Product.objects.all()
        updated_count = 0
        
        with transaction.atomic():
            for product in products:
                changes_made = False
                original_values = {
                    'requires_individual_tracking': product.requires_individual_tracking,
                    'requires_expiry_tracking': product.requires_expiry_tracking,
                    'requires_batch_tracking': product.requires_batch_tracking,
                }
                
                # Auto-correct tracking flags based on tracking method
                if product.tracking_method == 'expiry':
                    if not product.requires_expiry_tracking:
                        product.requires_expiry_tracking = True
                        changes_made = True
                    if product.requires_individual_tracking:
                        product.requires_individual_tracking = False
                        changes_made = True
                    if product.requires_batch_tracking:
                        product.requires_batch_tracking = False
                        changes_made = True
                        
                elif product.tracking_method == 'batch':
                    if not product.requires_batch_tracking:
                        product.requires_batch_tracking = True
                        changes_made = True
                    if product.requires_individual_tracking:
                        product.requires_individual_tracking = False
                        changes_made = True
                        
                elif product.tracking_method in ['serial', 'imei', 'barcode']:
                    if not product.requires_individual_tracking:
                        product.requires_individual_tracking = True
                        changes_made = True
                    if product.requires_batch_tracking:
                        product.requires_batch_tracking = False
                        changes_made = True
                        
                elif product.tracking_method == 'none':
                    if product.requires_individual_tracking:
                        product.requires_individual_tracking = False
                        changes_made = True
                    if product.requires_expiry_tracking:
                        product.requires_expiry_tracking = False
                        changes_made = True
                    if product.requires_batch_tracking:
                        product.requires_batch_tracking = False
                        changes_made = True
                
                if changes_made:
                    updated_count += 1
                    
                    if dry_run:
                        self.stdout.write(
                            f"Would update {product.name} (SKU: {product.sku}):"
                        )
                        self.stdout.write(f"  Tracking method: {product.tracking_method}")
                        self.stdout.write(f"  Individual tracking: {original_values['requires_individual_tracking']} -> {product.requires_individual_tracking}")
                        self.stdout.write(f"  Expiry tracking: {original_values['requires_expiry_tracking']} -> {product.requires_expiry_tracking}")
                        self.stdout.write(f"  Batch tracking: {original_values['requires_batch_tracking']} -> {product.requires_batch_tracking}")
                        self.stdout.write("")
                    else:
                        product.save()
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Updated {product.name} (SKU: {product.sku}) tracking configuration"
                            )
                        )
            
            if dry_run:
                # Rollback the transaction in dry run mode
                transaction.set_rollback(True)
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"DRY RUN: {updated_count} products would be updated"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully updated {updated_count} products"
                )
            )
