from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from user_auth.models import Company
from manufacturing.mrp_engine import run_automatic_mrp
from manufacturing.models import MRPRunLog
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run automated MRP calculation for all companies or a specific company'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company-id',
            type=int,
            help='Specify a company ID to run MRP for that company only',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force MRP run even if one was already completed today',
        )

    def handle(self, *args, **options):
        start_time = timezone.now()
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting automated MRP run at {start_time}')
        )

        if options['company_id']:
            # Run for specific company
            try:
                company = Company.objects.get(id=options['company_id'])
                companies = [company]
                self.stdout.write(f'Running MRP for company: {company.name}')
            except Company.DoesNotExist:
                raise CommandError(f'Company with ID {options["company_id"]} does not exist')
        else:
            # Run for all active companies
            companies = Company.objects.filter(is_active=True)
            self.stdout.write(f'Running MRP for {companies.count()} companies')

        total_success = 0
        total_errors = 0
        
        for company in companies:
            try:
                # Check if MRP already run today (unless forced)
                today = timezone.now().date()
                if not options['force']:
                    existing_run = MRPRunLog.objects.filter(
                        company=company,
                        run_timestamp__date=today,
                        status='success'
                    ).exists()
                    
                    if existing_run:
                        self.stdout.write(
                            self.style.WARNING(
                                f'MRP already completed today for {company.name}. Use --force to override.'
                            )
                        )
                        continue

                self.stdout.write(f'Processing company: {company.name}')
                
                # Run MRP
                mrp_plan, message = run_automatic_mrp(company)
                
                # Log the run
                execution_time = (timezone.now() - start_time).total_seconds()
                requirements_count = mrp_plan.requirements.count()
                
                MRPRunLog.objects.create(
                    company=company,
                    mrp_plan=mrp_plan,
                    trigger_source='scheduled',
                    execution_time_seconds=execution_time,
                    requirements_generated=requirements_count,
                    status='success',
                    configuration_snapshot={
                        'planning_horizon_days': mrp_plan.planning_horizon_days,
                        'include_safety_stock': mrp_plan.include_safety_stock,
                        'include_reorder_points': mrp_plan.include_reorder_points,
                        'consider_lead_times': mrp_plan.consider_lead_times,
                    }
                )
                
                total_success += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ {company.name}: {message} - {requirements_count} requirements generated'
                    )
                )
                
            except Exception as e:
                total_errors += 1
                error_msg = str(e)
                
                # Log the error
                MRPRunLog.objects.create(
                    company=company,
                    mrp_plan=None,
                    trigger_source='scheduled',
                    status='error',
                    error_message=error_msg
                )
                
                self.stdout.write(
                    self.style.ERROR(f'✗ {company.name}: Error - {error_msg}')
                )
                logger.error(f'MRP failed for company {company.name}: {error_msg}')

        end_time = timezone.now()
        total_time = (end_time - start_time).total_seconds()
        
        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(
            self.style.SUCCESS(
                f'MRP Run Summary:\n'
                f'  • Total companies processed: {len(companies)}\n'
                f'  • Successful runs: {total_success}\n'
                f'  • Failed runs: {total_errors}\n'
                f'  • Total execution time: {total_time:.2f} seconds\n'
                f'  • Completed at: {end_time}'
            )
        )
        
        if total_errors > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'\nWarning: {total_errors} companies had errors. Check logs for details.'
                )
            )
