from rest_framework import serializers
from .models import Product, Tax, Quotation, SalesOrder, SalesOrderItem, Invoice, Payment, CreditNote, CreditNoteItem

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
        # Invoices are only ever created via pos_checkout (a raw ORM call, not this
        # serializer), which fires stock movements + customer ledger entries in the same
        # transaction as setting these fields. A generic PATCH changing subtotal/total/
        # status/customer afterwards would desync stock and ledger from what the invoice
        # says - so only safe metadata stays editable here; line-item corrections go
        # through the returns/credit-note flow instead, which already updates both.
        read_only_fields = (
            'company', 'customer', 'created_by', 'invoice_number', 'invoice_date',
            'subtotal', 'tax_amount', 'discount_amount', 'shipping_amount', 'total',
            'paid_amount', 'status', 'pdf_file',
        )

class PaymentSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True, default=None)

    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ('company', 'payment_number', 'received_by', 'processed_by')


class CreditNoteItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    tracking_identifier = serializers.SerializerMethodField()

    class Meta:
        model = CreditNoteItem
        fields = '__all__'
        read_only_fields = ('credit_note', 'line_total')

    def get_tracking_identifier(self, obj):
        if not obj.tracking_unit:
            return None
        return obj.tracking_unit.imei_number or obj.tracking_unit.serial_number or obj.tracking_unit.barcode


class CreditNoteSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True, default=None)
    items = CreditNoteItemSerializer(many=True, read_only=True)

    class Meta:
        model = CreditNote
        fields = '__all__'
        read_only_fields = ('company', 'credit_number', 'created_by', 'total')