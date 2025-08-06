"""
Sample MRP Test Script
Creates sample data for testing the MRP functionality
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal

from user_auth.models import Company, User
from products.models import Product, ProductCategory
from crm.models import Partner
from inventory.models import Warehouse, StockItem
from sales.models import SalesOrder, SalesOrderItem
from manufacturing.models import (
    WorkCenter, BillOfMaterials, BillOfMaterialsItem, BOMOperation,
    DemandForecast, SupplierLeadTime, ReorderRule, MRPPlan
)
from manufacturing.mrp_engine import MRPEngine


class Command(BaseCommand):
    help = 'Create sample data for MRP testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company-id',
            type=int,
            help='Company ID to create data for',
        )

    def handle(self, *args, **options):
        if options['company_id']:
            try:
                company = Company.objects.get(id=options['company_id'])
            except Company.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Company with ID {options["company_id"]} does not exist'))
                return
        else:
            company = Company.objects.first()
            if not company:
                self.stdout.write(self.style.ERROR('No companies found'))
                return

        self.stdout.write(f'Creating sample MRP data for company: {company.name}')

        try:
            # Create sample categories
            raw_material_cat, _ = ProductCategory.objects.get_or_create(
                name='Raw Materials',
                company=company,
                defaults={'description': 'Raw materials for manufacturing'}
            )
            
            finished_goods_cat, _ = ProductCategory.objects.get_or_create(
                name='Finished Goods',
                company=company,
                defaults={'description': 'Finished products'}
            )

            # Create sample products
            products = {}
            
            # Raw materials
            steel_sheet = Product.objects.create(
                company=company,
                name='Steel Sheet',
                sku='RM-STEEL-001',
                category=raw_material_cat,
                product_type='material',
                sale_price=Decimal('50.00'),
                cost_price=Decimal('45.00'),
                description='Steel sheet for manufacturing'
            )
            products['steel'] = steel_sheet

            aluminum_rod = Product.objects.create(
                company=company,
                name='Aluminum Rod',
                sku='RM-ALU-001',
                category=raw_material_cat,
                product_type='material',
                sale_price=Decimal('30.00'),
                cost_price=Decimal('25.00'),
                description='Aluminum rod for manufacturing'
            )
            products['aluminum'] = aluminum_rod

            # Finished goods
            widget_a = Product.objects.create(
                company=company,
                name='Widget A',
                sku='FG-WIDGET-A',
                category=finished_goods_cat,
                product_type='product',
                sale_price=Decimal('200.00'),
                cost_price=Decimal('150.00'),
                description='Premium widget product'
            )
            products['widget_a'] = widget_a

            widget_b = Product.objects.create(
                company=company,
                name='Widget B',
                sku='FG-WIDGET-B',
                category=finished_goods_cat,
                product_type='product',
                sale_price=Decimal('300.00'),
                cost_price=Decimal('220.00'),
                description='Deluxe widget product'
            )
            products['widget_b'] = widget_b

            self.stdout.write('✓ Created sample products')

            # Create warehouses
            main_warehouse, _ = Warehouse.objects.get_or_create(
                company=company,
                name='Main Warehouse',
                defaults={
                    'code': 'MAIN-WH',
                    'warehouse_type': 'main',
                    'is_active': True
                }
            )

            # Create stock items with reorder rules
            for product in [steel_sheet, aluminum_rod]:
                stock_item, _ = StockItem.objects.get_or_create(
                    product=product,
                    warehouse=main_warehouse,
                    defaults={
                        'quantity': Decimal('1000'),
                        'available_quantity': Decimal('1000'),
                        'min_stock': Decimal('200'),
                        'max_stock': Decimal('2000'),
                        'reorder_point': Decimal('300'),
                        'safety_stock': Decimal('100'),
                        'lead_time_days': 7
                    }
                )

                # Create reorder rules
                ReorderRule.objects.get_or_create(
                    company=company,
                    product=product,
                    warehouse=main_warehouse,
                    defaults={
                        'reorder_method': 'reorder_point',
                        'minimum_stock': Decimal('200'),
                        'maximum_stock': Decimal('2000'),
                        'reorder_point': Decimal('300'),
                        'safety_stock': Decimal('100'),
                        'economic_order_quantity': Decimal('500'),
                        'lead_time_days': 7,
                        'average_daily_demand': Decimal('50'),
                        'auto_create_purchase_request': True,
                        'is_active': True
                    }
                )

            self.stdout.write('✓ Created stock items and reorder rules')

            # Create work centers
            work_center1, _ = WorkCenter.objects.get_or_create(
                company=company,
                name='Assembly Line 1',
                defaults={
                    'code': 'ASM-001',
                    'description': 'Main assembly line',
                    'capacity_per_hour': Decimal('10'),
                    'cost_per_hour': Decimal('50'),
                    'operating_hours_per_day': Decimal('8'),
                    'is_active': True
                }
            )

            work_center2, _ = WorkCenter.objects.get_or_create(
                company=company,
                name='Quality Control',
                defaults={
                    'code': 'QC-001',
                    'description': 'Quality control station',
                    'capacity_per_hour': Decimal('20'),
                    'cost_per_hour': Decimal('30'),
                    'operating_hours_per_day': Decimal('8'),
                    'is_active': True
                }
            )

            self.stdout.write('✓ Created work centers')

            # Create BOMs
            # BOM for Widget A
            bom_a, _ = BillOfMaterials.objects.get_or_create(
                company=company,
                product=widget_a,
                defaults={
                    'name': 'Widget A BOM',
                    'version': '1.0',
                    'manufacturing_type': 'make_to_order',
                    'lot_size': Decimal('1'),
                    'lead_time_days': 3,
                    'scrap_percentage': Decimal('2'),
                    'is_active': True,
                    'is_default': True
                }
            )

            # BOM items for Widget A
            BillOfMaterialsItem.objects.get_or_create(
                bom=bom_a,
                component=steel_sheet,
                defaults={
                    'quantity': Decimal('2'),
                    'unit_cost': Decimal('45'),
                    'sequence': 1
                }
            )

            BillOfMaterialsItem.objects.get_or_create(
                bom=bom_a,
                component=aluminum_rod,
                defaults={
                    'quantity': Decimal('1'),
                    'unit_cost': Decimal('25'),
                    'sequence': 2
                }
            )

            # BOM operations for Widget A
            BOMOperation.objects.get_or_create(
                bom=bom_a,
                work_center=work_center1,
                defaults={
                    'operation_name': 'Assembly',
                    'description': 'Assemble Widget A',
                    'sequence': 1,
                    'setup_time_minutes': Decimal('30'),
                    'run_time_per_unit_minutes': Decimal('45'),
                    'cleanup_time_minutes': Decimal('15'),
                    'operators_required': 1,
                    'cost_per_hour': Decimal('50')
                }
            )

            BOMOperation.objects.get_or_create(
                bom=bom_a,
                work_center=work_center2,
                defaults={
                    'operation_name': 'Quality Check',
                    'description': 'Quality inspection for Widget A',
                    'sequence': 2,
                    'setup_time_minutes': Decimal('10'),
                    'run_time_per_unit_minutes': Decimal('15'),
                    'cleanup_time_minutes': Decimal('5'),
                    'operators_required': 1,
                    'cost_per_hour': Decimal('30'),
                    'quality_check_required': True
                }
            )

            # BOM for Widget B (similar structure)
            bom_b, _ = BillOfMaterials.objects.get_or_create(
                company=company,
                product=widget_b,
                defaults={
                    'name': 'Widget B BOM',
                    'version': '1.0',
                    'manufacturing_type': 'make_to_order',
                    'lot_size': Decimal('1'),
                    'lead_time_days': 4,
                    'scrap_percentage': Decimal('3'),
                    'is_active': True,
                    'is_default': True
                }
            )

            BillOfMaterialsItem.objects.get_or_create(
                bom=bom_b,
                component=steel_sheet,
                defaults={
                    'quantity': Decimal('3'),
                    'unit_cost': Decimal('45'),
                    'sequence': 1
                }
            )

            BillOfMaterialsItem.objects.get_or_create(
                bom=bom_b,
                component=aluminum_rod,
                defaults={
                    'quantity': Decimal('2'),
                    'unit_cost': Decimal('25'),
                    'sequence': 2
                }
            )

            self.stdout.write('✓ Created BOMs with items and operations')

            # Create suppliers
            supplier1, _ = Partner.objects.get_or_create(
                company=company,
                name='Steel Supply Co.',
                defaults={
                    'partner_type': 'vendor',
                    'is_vendor': True,
                    'email': 'orders@steelsupply.com',
                    'phone': '+1-555-0101',
                    'is_active': True
                }
            )

            supplier2, _ = Partner.objects.get_or_create(
                company=company,
                name='Aluminum Works Ltd.',
                defaults={
                    'partner_type': 'vendor',
                    'is_vendor': True,
                    'email': 'sales@aluminumworks.com',
                    'phone': '+1-555-0102',
                    'is_active': True
                }
            )

            # Create supplier lead times
            SupplierLeadTime.objects.get_or_create(
                company=company,
                supplier=supplier1,
                product=steel_sheet,
                defaults={
                    'lead_time_days': 7,
                    'min_lead_time_days': 5,
                    'max_lead_time_days': 10,
                    'on_time_delivery_rate': Decimal('95'),
                    'quality_rating': Decimal('8.5'),
                    'price_per_unit': Decimal('45'),
                    'minimum_order_quantity': Decimal('100'),
                    'is_preferred': True,
                    'is_active': True
                }
            )

            SupplierLeadTime.objects.get_or_create(
                company=company,
                supplier=supplier2,
                product=aluminum_rod,
                defaults={
                    'lead_time_days': 5,
                    'min_lead_time_days': 3,
                    'max_lead_time_days': 7,
                    'on_time_delivery_rate': Decimal('92'),
                    'quality_rating': Decimal('9.0'),
                    'price_per_unit': Decimal('25'),
                    'minimum_order_quantity': Decimal('50'),
                    'is_preferred': True,
                    'is_active': True
                }
            )

            self.stdout.write('✓ Created suppliers and lead times')

            # Create demand forecasts
            today = timezone.now().date()
            for i in range(30):  # 30 days of forecasts
                forecast_date = today + timedelta(days=i)
                
                # Widget A forecast
                DemandForecast.objects.get_or_create(
                    company=company,
                    product=widget_a,
                    forecast_date=forecast_date,
                    defaults={
                        'forecast_quantity': Decimal('10') + (i % 5),  # Variable demand
                        'forecast_type': 'manual',
                        'confidence_level': Decimal('80'),
                        'planning_horizon_days': 30,
                        'is_active': True
                    }
                )

                # Widget B forecast
                DemandForecast.objects.get_or_create(
                    company=company,
                    product=widget_b,
                    forecast_date=forecast_date,
                    defaults={
                        'forecast_quantity': Decimal('5') + (i % 3),  # Variable demand
                        'forecast_type': 'manual',
                        'confidence_level': Decimal('75'),
                        'planning_horizon_days': 30,
                        'is_active': True
                    }
                )

            self.stdout.write('✓ Created demand forecasts')

            # Create sample sales orders for immediate demand
            customer, _ = Partner.objects.get_or_create(
                company=company,
                name='ABC Manufacturing',
                defaults={
                    'partner_type': 'customer',
                    'is_customer': True,
                    'email': 'orders@abcmfg.com',
                    'phone': '+1-555-0201',
                    'is_active': True
                }
            )

            # Create a sales order
            so = SalesOrder.objects.create(
                company=company,
                customer=customer,
                order_number='SO-2025-001',
                order_date=today,
                delivery_date=today + timedelta(days=14),
                status='confirmed',
                currency='USD',
                subtotal=Decimal('800'),
                total_amount=Decimal('800')
            )

            # Add items to sales order
            SalesOrderItem.objects.create(
                sales_order=so,
                product=widget_a,
                quantity=Decimal('20'),
                unit_price=Decimal('200'),
                total_price=Decimal('4000'),
                delivered_quantity=Decimal('0')
            )

            SalesOrderItem.objects.create(
                sales_order=so,
                product=widget_b,
                quantity=Decimal('10'),
                unit_price=Decimal('300'),
                total_price=Decimal('3000'),
                delivered_quantity=Decimal('0')
            )

            self.stdout.write('✓ Created sample sales orders')

            # Create and run a sample MRP plan
            mrp_plan = MRPPlan.objects.create(
                company=company,
                name=f'Sample MRP Plan - {today}',
                plan_date=today,
                planning_horizon_days=90,
                status='draft',
                include_safety_stock=True,
                include_reorder_points=True,
                consider_lead_times=True
            )

            self.stdout.write('✓ Created sample MRP plan')

            # Run the MRP calculation
            self.stdout.write('Running MRP calculation...')
            engine = MRPEngine(mrp_plan)
            success = engine.run_mrp_calculation()

            if success:
                mrp_plan.status = 'completed'
                mrp_plan.calculation_end = timezone.now()
                mrp_plan.save()
                
                requirements_count = mrp_plan.requirements.count()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ MRP calculation completed successfully!\n'
                        f'  Generated {requirements_count} requirements'
                    )
                )
            else:
                self.stdout.write(self.style.ERROR('✗ MRP calculation failed'))

            self.stdout.write('\n' + '='*60)
            self.stdout.write(
                self.style.SUCCESS(
                    f'Sample MRP data creation completed for {company.name}!\n\n'
                    f'Summary:\n'
                    f'  • Products: {len(products)} created\n'
                    f'  • BOMs: 2 created with components and operations\n'
                    f'  • Work Centers: 2 created\n'
                    f'  • Suppliers: 2 created with lead times\n'
                    f'  • Reorder Rules: 2 created\n'
                    f'  • Demand Forecasts: 60 created (30 days x 2 products)\n'
                    f'  • Sales Orders: 1 created\n'
                    f'  • MRP Plan: 1 created and calculated\n\n'
                    f'You can now test the MRP functionality!'
                )
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating sample data: {str(e)}'))
            raise
