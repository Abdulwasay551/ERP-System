# Purchase Module Document Upload Implementation

## Overview
Enhanced all purchase module models with document upload capabilities. All document fields are optional (null=True, blank=True) for frontend flexibility.

## Models Enhanced

### 1. Purchase Requisition
**Document Fields Added:**
- `requisition_document`: Main requisition document
- `technical_specifications`: Technical specs document  
- `budget_approval`: Budget approval document

**Upload Path:** `purchase/requisitions/`

### 2. Request for Quotation (RFQ)
**Document Fields Added:**
- `rfq_document`: RFQ document file
- `technical_specifications`: Technical specifications document
- `drawing_attachments`: Technical drawings or blueprints

**Upload Path:** `purchase/rfq/`

### 3. Supplier Quotation
**Document Fields Added:**
- `quotation_document`: Supplier quotation document
- `price_list`: Supplier price list
- `technical_brochure`: Product technical brochure
- `certificate_documents`: Quality certificates, compliance docs

**Upload Path:** `purchase/quotations/`

### 4. Purchase Order
**Document Fields Added:**
- `purchase_order_document`: Generated PO document
- `supplier_agreement`: Supplier agreement/contract
- `technical_drawings`: Technical drawings or specifications
- `amendment_documents`: PO amendments or revisions

**Upload Path:** `purchase/orders/`

### 5. Goods Receipt Note (GRN)
**Document Fields Added:**
- `delivery_challan`: Supplier delivery challan
- `packing_list`: Packing list document
- `quality_certificates`: Quality certificates from supplier
- `inspection_report`: Internal quality inspection report
- `photos_received_goods`: Photos of received goods

**Upload Path:** `purchase/grn/`

### 6. Bill/Purchase Invoice
**Document Fields Added:**
- `supplier_invoice`: Supplier invoice document
- `tax_invoice`: Tax invoice document
- `supporting_documents`: Supporting documents (receipts, etc.)
- `approval_documents`: Internal approval documents

**Upload Path:** `purchase/bills/`

### 7. Purchase Payment
**Document Fields Added:**
- `payment_receipt`: Payment receipt document
- `bank_statement`: Bank statement showing payment
- `check_copy`: Copy of check if payment by check
- `wire_transfer_advice`: Wire transfer advice document

**Upload Path:** `purchase/payments/`

### 8. Purchase Return
**Document Fields Added:**
- `return_authorization`: Return authorization document
- `quality_report`: Quality inspection report for return
- `photos_returned_items`: Photos of returned items
- `supplier_acknowledgment`: Supplier acknowledgment of return

**Upload Path:** `purchase/returns/`

### 9. Supplier
**Document Fields Added:**
- `registration_certificate`: Business registration certificate
- `tax_certificate`: Tax registration certificate
- `quality_certificates`: Quality certifications (ISO, etc.)
- `bank_documents`: Bank account verification documents
- `agreement_contract`: Master agreement or contract

**Upload Path:** `purchase/suppliers/`

## File Upload Organization

```
media/
└── purchase/
    ├── requisitions/
    │   ├── specs/
    │   └── budget/
    ├── rfq/
    │   ├── specs/
    │   └── drawings/
    ├── quotations/
    │   ├── pricelists/
    │   ├── brochures/
    │   └── certificates/
    ├── orders/
    │   ├── agreements/
    │   ├── drawings/
    │   └── amendments/
    ├── grn/
    │   ├── challan/
    │   ├── packing/
    │   ├── quality/
    │   ├── inspection/
    │   └── photos/
    ├── bills/
    │   ├── invoices/
    │   ├── tax/
    │   ├── supporting/
    │   └── approvals/
    ├── payments/
    │   ├── receipts/
    │   ├── statements/
    │   ├── checks/
    │   └── wire/
    ├── returns/
    │   ├── authorization/
    │   ├── quality/
    │   ├── photos/
    │   └── acknowledgment/
    └── suppliers/
        ├── registration/
        ├── tax/
        ├── quality/
        ├── bank/
        └── contracts/
```

## Frontend Implementation Notes

### File Upload Features:
1. **Multiple File Types Support**: PDF, DOC, DOCX, XLS, XLSX, JPG, PNG, DWG
2. **Drag & Drop Support**: Can be implemented in frontend
3. **File Size Validation**: Should be implemented in frontend/backend
4. **Preview Functionality**: For images and PDFs
5. **Download Links**: For uploaded documents

### Form Updates Required:
1. **Add `enctype="multipart/form-data"`** to all forms with file uploads
2. **File input fields** with appropriate accept attributes
3. **Progress indicators** for file uploads
4. **File preview sections** in detail views
5. **Error handling** for upload failures

### Security Considerations:
1. **File Type Validation**: Server-side validation of file types
2. **File Size Limits**: Implement maximum file size limits
3. **Virus Scanning**: Consider integrating virus scanning for uploads
4. **Access Control**: Ensure proper permissions for document access
5. **Storage Security**: Secure storage of sensitive documents

## Migration Requirements

After implementing these changes, run:
```bash
python manage.py makemigrations purchase
python manage.py migrate
```

## Next Steps

1. **Update all forms** to include file upload fields
2. **Create document management views** for viewing/downloading files
3. **Implement file validation** and security measures
4. **Add document preview functionality**
5. **Create audit trails** for document uploads/changes
6. **Implement document approval workflows** if needed
