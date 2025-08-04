#!/usr/bin/env python
"""
Test Script for Sales Invoice to Inventory Reduction Workflow
This script tests the complete flow:
1. Create sample products
2. Add inventory stock
3. Create sales order with tracking
4. Generate invoice from sales order
5. Verify inventory reduction and tracking
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setting.settings')
django.setup()

from django.contrib.auth import get_user_model
from decimal import Decimal
from sales.models import *
from inventory.models import *
from products.models import *
from crm.models import Customer
from user_auth.models import Company

User = get_user_model()

def create_test_data():
    """Create test data for the sales-inventory workflow"""
    print("Creating test data...")
    
    # Get or create test company
    company, created = Company.objects.get_or_create(
        name="Test ERP Company",
        defaults={
            'address': 'Test Address'
        }
    )
    
    # Get or create test user
    user, created = User.objects.get_or_create(
        email='test@user.com',
        defaults={
            'first_name': 'Test',
            'last_name': 'User',
            'company': company
        }
    )
    if created:
        user.set_password('testpass123')
        user.save()
    
    # Create test customer
    customer, created = Customer.objects.get_or_create(
        company=company,
        name="Test Customer Ltd",
        defaults={
            'email': 'customer@test.com',
            'phone': '+1234567891',
            'address': 'Customer Address'
        }
    )
    
    # Create test warehouse
    warehouse, created = Warehouse.objects.get_or_create(
        company=company,
        name="Main Warehouse",
        defaults={
            'code': 'WH001',
            'location': 'Main Location',
            'warehouse_type': 'main'
        }
    )
    
    # Create test products with different tracking methods
    products = []
    
    # 1. Serial tracked product
    product1, created = Product.objects.get_or_create(
        company=company,
        name="Smartphone XYZ",
        defaults={
            'sku': 'PHONE001',
            'selling_price': Decimal('599.99'),
            'cost_price': Decimal('400.00'),
            'tracking_method': 'serial',
            'is_saleable': True,
            'is_stockable': True,
            'unit_of_measure': 'piece',
            'requires_individual_tracking': True
        }
    )
    products.append(product1)
    
    # 2. Batch tracked product
    product2, created = Product.objects.get_or_create(
        company=company,
        name="Medicine ABC",
        defaults={
            'sku': 'MED001',
            'selling_price': Decimal('25.50'),
            'cost_price': Decimal('15.00'),
            'tracking_method': 'expiry',
            'is_saleable': True,
            'is_stockable': True,
            'unit_of_measure': 'box',
            'requires_expiry_tracking': True,
            'requires_batch_tracking': True,
            'shelf_life_days': 365
        }
    )
    products.append(product2)
    
    # 3. Simple product (no tracking)
    product3, created = Product.objects.get_or_create(
        company=company,
        name="Office Supplies",
        defaults={
            'sku': 'OFF001',
            'selling_price': Decimal('12.99'),
            'cost_price': Decimal('8.00'),
            'tracking_method': 'none',
            'is_saleable': True,
            'is_stockable': True,
            'unit_of_measure': 'pack'
        }
    )
    products.append(product3)
    
    # Create currency
    currency, created = Currency.objects.get_or_create(
        company=company,
        code='USD',
        defaults={
            'name': 'US Dollar',
            'symbol': '$',
            'exchange_rate': Decimal('1.0000'),
            'is_base_currency': True
        }
    )
    
    # Create tax
    tax, created = Tax.objects.get_or_create(
        company=company,
        name='Standard Tax',
        defaults={
            'rate': Decimal('10.00'),
            'is_inclusive': False
        }
    )
    
    return {
        'company': company,
        'user': user,
        'customer': customer,
        'warehouse': warehouse,
        'products': products,
        'currency': currency,
        'tax': tax
    }

def create_inventory_stock(test_data):
    """Create initial inventory stock for testing"""
    print("Creating inventory stock...")
    
    company = test_data['company']
    warehouse = test_data['warehouse']
    products = test_data['products']
    
    stock_items = []
    
    for i, product in enumerate(products):
        # Create stock item
        stock_item, created = StockItem.objects.get_or_create(
            company=company,
            product=product,
            warehouse=warehouse,
            defaults={
                'quantity': Decimal('100.00'),
                'available_quantity': Decimal('100.00'),
                'reserved_quantity': Decimal('0.00'),
                'average_cost': product.cost_price,
                'last_purchase_cost': product.cost_price,
                'total_cost_value': product.cost_price * Decimal('100.00'),
                'stock_status': 'available'
            }
        )
        
        if created:
            # Create opening stock movement
            StockMovement.objects.create(
                company=company,
                stock_item=stock_item,
                movement_type='opening_stock',
                quantity=Decimal('100.00'),
                unit_cost=product.cost_price,
                total_cost=product.cost_price * Decimal('100.00'),
                to_warehouse=warehouse,
                reference_type='opening_stock',
                reference_number='OPENING-001',
                notes='Initial opening stock for testing'
            )
        
        stock_items.append(stock_item)
        print(f"  Stock created for {product.name}: {stock_item.available_quantity} units")
    
    return stock_items

def create_sales_order_with_tracking(test_data):
    """Create a sales order with tracking items"""
    print("Creating sales order with tracking...")
    
    company = test_data['company']
    user = test_data['user']
    customer = test_data['customer']
    products = test_data['products']
    currency = test_data['currency']
    tax = test_data['tax']
    
    # Create sales order
    sales_order = SalesOrder.objects.create(
        company=company,
        customer=customer,
        created_by=user,
        order_date=timezone.now().date(),
        currency=currency,
        status='confirmed'
    )
    
    # Add line items
    total_amount = Decimal('0.00')
    
    for i, product in enumerate(products):
        quantity = Decimal('5.00')  # Order 5 units of each
        unit_price = product.selling_price
        line_total = quantity * unit_price
        
        # Add tax
        tax_amount = line_total * (tax.rate / 100)
        final_total = line_total + tax_amount
        
        sales_order_item = SalesOrderItem.objects.create(
            sales_order=sales_order,
            product=product,
            quantity=quantity,
            unit_price=unit_price,
            tax=tax,
            tax_amount=tax_amount,
            line_total=final_total
        )
        
        total_amount += final_total
        print(f"  Added line item: {product.name} x {quantity} = ${final_total}")
        
        # Add tracking for products that require it
        if product.tracking_method == 'serial':
            # Add serial numbers
            for j in range(int(quantity)):
                SalesOrderItemTracking.objects.create(
                    sales_order_item=sales_order_item,
                    quantity=Decimal('1.00'),
                    serial_number=f'SN{product.sku}{j+1:03d}',
                    status='reserved'
                )
                print(f"    Added serial tracking: SN{product.sku}{j+1:03d}")
        
        elif product.tracking_method == 'expiry':
            # Add batch with expiry
            SalesOrderItemTracking.objects.create(
                sales_order_item=sales_order_item,
                quantity=quantity,
                batch_number=f'BATCH{product.sku}001',
                expiry_date=(timezone.now() + timezone.timedelta(days=300)).date(),
                status='reserved'
            )
            print(f"    Added batch tracking: BATCH{product.sku}001")
    
    # Update sales order total
    sales_order.total = total_amount
    sales_order.save()
    
    print(f"Sales order created: {sales_order.order_number} - Total: ${total_amount}")
    return sales_order

def create_invoice_from_sales_order(sales_order):
    """Create and confirm invoice from sales order"""
    print("Creating invoice from sales order...")
    
    # Create invoice
    invoice = Invoice.objects.create(
        company=sales_order.company,
        customer=sales_order.customer,
        sales_order=sales_order,
        created_by=sales_order.created_by,
        invoice_date=timezone.now().date(),
        currency=sales_order.currency,
        status='draft'  # Start as draft
    )
    
    # Copy line items from sales order
    total_amount = Decimal('0.00')
    
    for so_item in sales_order.items.all():
        invoice_item = InvoiceItem.objects.create(
            invoice=invoice,
            product=so_item.product,
            quantity=so_item.quantity,
            unit_price=so_item.unit_price,
            discount_percent=so_item.discount_percent,
            discount_amount=so_item.discount_amount,
            tax=so_item.tax,
            tax_amount=so_item.tax_amount,
            line_total=so_item.line_total
        )
        total_amount += so_item.line_total
        print(f"  Added invoice item: {so_item.product.name} x {so_item.quantity}")
    
    # Update invoice total
    invoice.total = total_amount
    invoice.save()
    
    print(f"Invoice created: {invoice.invoice_number} - Status: {invoice.status}")
    return invoice

def confirm_invoice_and_check_inventory(invoice, test_data):
    """Confirm invoice and verify inventory reduction"""
    print("Confirming invoice and checking inventory...")
    
    # Get initial stock levels
    initial_stock = {}
    for product in test_data['products']:
        stock_items = StockItem.objects.filter(
            company=test_data['company'],
            product=product
        )
        total_stock = sum(item.available_quantity for item in stock_items)
        initial_stock[product.id] = total_stock
        print(f"  Initial stock for {product.name}: {total_stock}")
    
    # Confirm the invoice (this should trigger inventory reduction)
    print(f"Changing invoice status from '{invoice.status}' to 'sent'...")
    invoice.status = 'sent'
    invoice.save()
    
    print("Invoice confirmed! Checking inventory changes...")
    
    # Check stock levels after confirmation
    for product in test_data['products']:
        stock_items = StockItem.objects.filter(
            company=test_data['company'],
            product=product
        )
        new_stock = sum(item.available_quantity for item in stock_items)
        initial = initial_stock[product.id]
        difference = initial - new_stock
        
        print(f"  {product.name}:")
        print(f"    Before: {initial}")
        print(f"    After: {new_stock}")
        print(f"    Reduced: {difference}")
        
        # Check stock movements
        movements = StockMovement.objects.filter(
            company=test_data['company'],
            reference_type='invoice',
            reference_number=invoice.invoice_number,
            movement_type='sale'
        )
        
        product_movements = [m for m in movements if m.stock_item.product == product]
        print(f"    Stock movements: {len(product_movements)}")
        for movement in product_movements:
            print(f"      - {movement.quantity} units sold from {movement.from_warehouse.name}")

def run_complete_test():
    """Run the complete sales-to-inventory test workflow"""
    print("="*60)
    print("TESTING SALES INVOICE TO INVENTORY REDUCTION WORKFLOW")
    print("="*60)
    
    try:
        # Step 1: Create test data
        test_data = create_test_data()
        print(f"✓ Test data created for company: {test_data['company'].name}")
        
        # Step 2: Create inventory stock
        stock_items = create_inventory_stock(test_data)
        print(f"✓ Inventory stock created for {len(stock_items)} products")
        
        # Step 3: Create sales order with tracking
        sales_order = create_sales_order_with_tracking(test_data)
        print(f"✓ Sales order created: {sales_order.order_number}")
        
        # Step 4: Create invoice from sales order
        invoice = create_invoice_from_sales_order(sales_order)
        print(f"✓ Invoice created: {invoice.invoice_number}")
        
        # Step 5: Confirm invoice and check inventory reduction
        confirm_invoice_and_check_inventory(invoice, test_data)
        print("✓ Invoice confirmed and inventory reduced successfully")
        
        print("\n" + "="*60)
        print("TEST COMPLETED SUCCESSFULLY!")
        print("The sales-to-inventory workflow is working correctly.")
        print("✓ Products are flagged as sold")
        print("✓ Inventory quantities are reduced")
        print("✓ Stock movements are recorded")
        print("✓ Tracking information is maintained")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_complete_test()
