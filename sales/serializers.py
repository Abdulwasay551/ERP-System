from rest_framework import serializers
from .models import Product, Tax, Quotation, SalesOrder, SalesOrderItem, Invoice, Payment

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

class TaxSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tax
        fields = '__all__'

class QuotationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quotation
        fields = '__all__'

class SalesOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesOrder
        fields = '__all__'

class SalesOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesOrderItem
        fields = '__all__'

class InvoiceSerializer(serializers.ModelSerializer):
    # customer_name/outstanding_amount aren't picked up by fields = '__all__' -
    # customer_name needs the dotted source, outstanding_amount is a @property.
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    outstanding_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Invoice
        fields = '__all__'

class PaymentSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True, default=None)

    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ('company', 'payment_number', 'received_by', 'processed_by')