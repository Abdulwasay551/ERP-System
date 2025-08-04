#!/usr/bin/env python
"""
Script to add sales tracking fields to inventory models
This will add fields to track when items are sold via sales invoices
"""

from django.db import migrations, models
import django.db.models.deletion

def add_sales_tracking_fields():
    """
    Add sales tracking fields to StockSerial and StockLot models
    """
    
    # For StockSerial model - add sales tracking
    serial_fields_to_add = [
        ("is_available", models.BooleanField(default=True, help_text="Available for sale")),
        ("sold_to_customer", models.ForeignKey('crm.Customer', on_delete=models.SET_NULL, null=True, blank=True, related_name='purchased_serials')),
        ("sales_invoice", models.ForeignKey('sales.Invoice', on_delete=models.SET_NULL, null=True, blank=True, related_name='sold_serials')),
        ("sale_date", models.DateTimeField(null=True, blank=True)),
        ("sale_price", models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)),
    ]
    
    # For StockLot model - add sales tracking
    lot_fields_to_add = [
        ("sold_quantity", models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Quantity sold from this lot")),
        ("last_sale_date", models.DateTimeField(null=True, blank=True)),
        ("average_sale_price", models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)),
    ]
    
    print("Sales tracking fields defined for inventory models:")
    print("\nStockSerial fields:")
    for field_name, field_def in serial_fields_to_add:
        print(f"  - {field_name}: {field_def}")
    
    print("\nStockLot fields:")
    for field_name, field_def in lot_fields_to_add:
        print(f"  - {field_name}: {field_def}")
    
    print("\nTo add these fields, you need to:")
    print("1. Add the fields manually to the StockSerial and StockLot models in inventory/models.py")
    print("2. Run: python manage.py makemigrations inventory")
    print("3. Run: python manage.py migrate")

if __name__ == "__main__":
    add_sales_tracking_fields()
