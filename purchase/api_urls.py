from rest_framework.routers import DefaultRouter
from django.urls import path
from .api_views import (
    SupplierViewSet, SupplierLedgerAdjustmentViewSet, TaxChargesTemplateViewSet, PurchaseRequisitionViewSet,
    PurchaseRequisitionItemViewSet, RequestForQuotationViewSet, RFQItemViewSet,
    SupplierQuotationViewSet, SupplierQuotationItemViewSet, PurchaseOrderViewSet,
    PurchaseOrderItemViewSet, PurchaseOrderTaxChargeViewSet, GoodsReceiptNoteViewSet,
    GRNItemViewSet, BillViewSet, BillItemViewSet, PurchasePaymentViewSet,
    PurchaseReturnViewSet, PurchaseReturnItemViewSet, PurchaseApprovalViewSet,
    DebitNoteViewSet,
    vendor_invoice_create, bill_receive_items, bill_confirm_received, process_vendor_return
)

router = DefaultRouter()

# Core Purchase Entities
router.register(r'suppliers', SupplierViewSet, basename='supplier')
router.register(r'supplier-ledger-adjustments', SupplierLedgerAdjustmentViewSet, basename='supplierledgeradjustment')
router.register(r'tax-charges-templates', TaxChargesTemplateViewSet, basename='taxchargestemplate')

# Purchase Requisition
router.register(r'purchase-requisitions', PurchaseRequisitionViewSet, basename='purchaserequisition')
router.register(r'purchase-requisition-items', PurchaseRequisitionItemViewSet, basename='purchaserequisitionitem')

# Request for Quotation
router.register(r'rfqs', RequestForQuotationViewSet, basename='requestforquotation')
router.register(r'rfq-items', RFQItemViewSet, basename='rfqitem')

# Supplier Quotations
router.register(r'supplier-quotations', SupplierQuotationViewSet, basename='supplierquotation')
router.register(r'supplier-quotation-items', SupplierQuotationItemViewSet, basename='supplierquotationitem')

# Purchase Orders
router.register(r'purchase-orders', PurchaseOrderViewSet, basename='purchaseorder')
router.register(r'purchase-order-items', PurchaseOrderItemViewSet, basename='purchaseorderitem')
router.register(r'purchase-order-tax-charges', PurchaseOrderTaxChargeViewSet, basename='purchaseordertaxcharge')

# Goods Receipt Note
router.register(r'grns', GoodsReceiptNoteViewSet, basename='goodsreceiptnote')
router.register(r'grn-items', GRNItemViewSet, basename='grnitem')

# Bills and Payments
router.register(r'bills', BillViewSet, basename='bill')
router.register(r'bill-items', BillItemViewSet, basename='billitem')
router.register(r'purchase-payments', PurchasePaymentViewSet, basename='purchasepayment')

# Purchase Returns
router.register(r'purchase-returns', PurchaseReturnViewSet, basename='purchasereturn')
router.register(r'purchase-return-items', PurchaseReturnItemViewSet, basename='purchasereturnitem')
router.register(r'debit-notes', DebitNoteViewSet, basename='debitnote')

# Approvals
router.register(r'purchase-approvals', PurchaseApprovalViewSet, basename='purchaseapproval')

urlpatterns = router.urls + [
    path('vendor-invoice/', vendor_invoice_create, name='vendor-invoice-create'),
    path('bills/<int:bill_id>/receive-items/', bill_receive_items, name='bill-receive-items'),
    path('bills/<int:bill_id>/confirm-received/', bill_confirm_received, name='bill-confirm-received'),
    path('returns/process/', process_vendor_return, name='process-vendor-return'),
]