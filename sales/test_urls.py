# Sales Module URL Testing Script

from django.test import TestCase
from django.urls import reverse, resolve

class SalesURLTest(TestCase):
    
    def test_sales_dashboard_url(self):
        """Test sales dashboard URL resolves correctly"""
        url = reverse('sales:dashboard')
        self.assertEqual(url, '/sales/')
        
    def test_quotations_url(self):
        """Test quotations list URL resolves correctly"""
        url = reverse('sales:quotations')
        self.assertEqual(url, '/sales/quotations/')
        
    def test_sales_orders_url(self):
        """Test sales orders list URL resolves correctly"""
        url = reverse('sales:sales_orders')
        self.assertEqual(url, '/sales/sales-orders/')
        
    def test_invoices_url(self):
        """Test invoices list URL resolves correctly"""
        url = reverse('sales:invoices')
        self.assertEqual(url, '/sales/invoices/')
        
    def test_delivery_notes_url(self):
        """Test delivery notes list URL resolves correctly"""
        url = reverse('sales:delivery_notes')
        self.assertEqual(url, '/sales/delivery-notes/')
        
    def test_payments_url(self):
        """Test payments list URL resolves correctly"""
        url = reverse('sales:payments')
        self.assertEqual(url, '/sales/payments/')

    def test_currencies_url(self):
        """Test currencies list URL resolves correctly"""
        url = reverse('sales:currencies')
        self.assertEqual(url, '/sales/currencies/')

    def test_url_view_mapping(self):
        """Test that URLs resolve to correct view functions"""
        dashboard_resolver = resolve('/sales/')
        self.assertEqual(dashboard_resolver.view_name, 'sales:dashboard')
        
        quotations_resolver = resolve('/sales/quotations/')
        self.assertEqual(quotations_resolver.view_name, 'sales:quotations')
        
        sales_orders_resolver = resolve('/sales/sales-orders/')
        self.assertEqual(sales_orders_resolver.view_name, 'sales:sales_orders')
