#!/usr/bin/env python
"""
Script to clear all data from the database to resolve migration issues.
This will delete all data but keep the database structure.
"""

import os
import sys
import django

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setting.settings')
django.setup()

from django.db import connection
from django.core.management.color import no_style

def clear_all_data():
    """Clear all data from all tables in the database."""
    style = no_style()
    
    with connection.cursor() as cursor:
        # Get all table names
        cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public';")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"Found {len(tables)} tables to clear...")
        
        # Disable foreign key checks temporarily
        cursor.execute("SET session_replication_role = replica;")
        
        # Clear all tables
        for table in tables:
            if not table.startswith('django_'):  # Skip Django system tables
                print(f"Clearing table: {table}")
                try:
                    cursor.execute(f"TRUNCATE TABLE {table} CASCADE;")
                except Exception as e:
                    print(f"Warning: Could not clear table {table}: {e}")
        
        # Re-enable foreign key checks
        cursor.execute("SET session_replication_role = DEFAULT;")
        
        print("Database data cleared successfully!")
        print("\nNext steps:")
        print("1. Delete existing migrations (except __init__.py)")
        print("2. Run: python manage.py makemigrations")
        print("3. Run: python manage.py migrate")

if __name__ == "__main__":
    print("⚠️  WARNING: This will delete ALL data from the database!")
    print("Are you sure you want to continue? (yes/no): ", end="")
    
    confirm = input().lower().strip()
    if confirm in ['yes', 'y']:
        try:
            clear_all_data()
        except Exception as e:
            print(f"Error: {e}")
            print("Make sure the database is accessible and try again.")
    else:
        print("Operation cancelled.")
