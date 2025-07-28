from django.urls import path
from .views import (
    # Dashboard
    purchase_dashboard,
    
    # Suppliers
    suppliers_ui, supplier_add, supplier_edit,
    
    # Purchase Requisitions
    purchase_requisitions_ui, purchase_requisition_detail, 
    purchase_requisition_add, purchase_requisition_edit, purchase_requisition_approve,
    
    # Purchase Orders
    purchaseorders_ui, purchase_order_detail, purchaseorders_add, 
    purchase_order_approve, purchase_order_edit, purchase_order_cancel, 
    purchase_order_send_to_supplier, purchase_order_duplicate,
    
    # RFQ & Quotations
    rfq_ui, rfq_add, rfq_detail, rfq_edit,
    quotations_ui, quotation_add, quotation_detail, quotation_approve,
    quotation_compare, quotation_to_po,
    
    # GRN
    grn_ui, grn_detail, grn_add, get_po_items_ajax,
    
    # Returns
    returns_ui, return_add, return_detail, return_edit,
    
    # Quality Assurance
    quality_assurance, quality_inspection_conduct, quality_inspection_form,
    
    # Bills
    bills_ui, bill_detail, bill_add,
    
    # Payments
    payments_ui, payment_add,
)

app_name = 'purchase'

urlpatterns = [
    # Dashboard
    path('dashboard/', purchase_dashboard, name='dashboard'),
    
    # Suppliers
    path('suppliers-ui/', suppliers_ui, name='suppliers_ui'),
    path('suppliers-add/', supplier_add, name='supplier_add'),
    path('suppliers-edit/<int:pk>/', supplier_edit, name='supplier_edit'),
    
    # Purchase Requisitions
    path('requisitions-ui/', purchase_requisitions_ui, name='requisitions_ui'),
    path('requisitions/<int:pk>/', purchase_requisition_detail, name='requisition_detail'),
    path('requisitions-add/', purchase_requisition_add, name='requisition_add'),
    path('requisitions-edit/<int:pk>/', purchase_requisition_edit, name='requisition_edit'),
    path('requisitions/<int:pk>/approve/', purchase_requisition_approve, name='requisition_approve'),
    
    # Purchase Orders
    path('purchase-orders/', purchaseorders_ui, name='purchaseorders_ui'),
    path('purchase-orders/<int:pk>/', purchase_order_detail, name='purchase_order_detail'),
    path('purchase-orders/add/', purchaseorders_add, name='purchaseorders_add'),
    path('purchase-orders/<int:pk>/edit/', purchase_order_edit, name='purchase_order_edit'),
    path('purchase-orders/<int:pk>/approve/', purchase_order_approve, name='purchase_order_approve'),
    path('purchase-orders/<int:pk>/cancel/', purchase_order_cancel, name='purchase_order_cancel'),
    path('purchase-orders/<int:pk>/send-to-supplier/', purchase_order_send_to_supplier, name='purchase_order_send_to_supplier'),
    path('purchase-orders/<int:pk>/duplicate/', purchase_order_duplicate, name='purchase_order_duplicate'),
    
    # RFQ & Quotations
    path('rfq-ui/', rfq_ui, name='rfq_ui'),
    path('rfq-add/', rfq_add, name='rfq_add'),
    path('rfq/<int:pk>/', rfq_detail, name='rfq_detail'),
    path('rfq-edit/<int:pk>/', rfq_edit, name='rfq_edit'),
    path('quotations-ui/', quotations_ui, name='quotations_ui'),
    path('quotation-add/', quotation_add, name='quotation_add'),
    path('quotation/<int:pk>/', quotation_detail, name='quotation_detail'),
    path('quotation/<int:pk>/approve/', quotation_approve, name='quotation_approve'),
    path('quotation/compare/', quotation_compare, name='quotation_compare'),
    path('quotation/<int:pk>/to-po/', quotation_to_po, name='quotation_to_po'),
    
    # GRN
    path('grns-ui/', grn_ui, name='grns_ui'),
    path('grn/<int:pk>/', grn_detail, name='grn_detail'),
    path('grn-add/', grn_add, name='grn_add'),
    
    # AJAX Endpoints
    path('ajax/get-po-items/', get_po_items_ajax, name='get_po_items_ajax'),
    
    # Returns
    path('returns-ui/', returns_ui, name='returns_ui'),
    path('return/<int:pk>/', return_detail, name='return_detail'),
    path('return-add/', return_add, name='return_add'),
    path('return/<int:pk>/edit/', return_edit, name='return_edit'),
    
    # Quality Assurance
    path('quality-assurance/', quality_assurance, name='quality_assurance'),
    path('quality-inspection-conduct/', quality_inspection_conduct, name='quality_inspection_conduct'),
    path('quality-inspection-form/', quality_inspection_form, name='quality_inspection_form'),
    
    # Bills
    path('bills-ui/', bills_ui, name='bills_ui'),
    path('bills/<int:pk>/', bill_detail, name='bill_detail'),
    path('bills-add/', bill_add, name='bill_add'),
    
    # Payments
    path('payments-ui/', payments_ui, name='payments_ui'),
    path('payments-add/', payment_add, name='payment_add'),
]