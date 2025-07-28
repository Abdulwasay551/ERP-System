# Purchase Module Implementation Plan

## Overview
Complete Purchase-to-Pay (P2P) workflow implementation with UOM conversion, quality control, and automatic accounting integration.

## Workflow Sequence
```
Requisition → RFQ → Quotation → Purchase Order → GRN → Purchase Invoice → Payment
```

## 1. Purchase Requisition (PR)
**Purpose**: Internal request for materials/services
**Status Flow**: Draft → Pending Approval → Approved → Rejected → Partially Ordered → Fully Ordered → Cancelled

### Features:
- Department-wise requisitions
- Multi-item support with specifications
- Approval workflow
- Preferred supplier suggestions
- Cost estimation

### Models Enhancement:
```python
class PurchaseRequisition:
    - pr_number (auto-generated)
    - department
    - requested_by
    - request_date
    - required_date
    - purpose
    - status
    - approved_by
    - approved_date
    - total_estimated_cost
    - warehouse (FK to Warehouse)
```

## 2. Request for Quotation (RFQ)
**Purpose**: Formal request to suppliers for pricing
**Trigger**: Created from approved requisitions
**Status Flow**: Draft → Sent → Responses Received → Completed → Cancelled

### Features:
- Multi-supplier invitation
- Response deadline tracking
- UOM specifications
- Comparison matrix
- Automated follow-ups

### Models Enhancement:
```python
class RFQ:
    - rfq_number (auto-generated)
    - requisition (FK)
    - suppliers (M2M)
    - response_deadline
    - status
    - created_by
    - warehouse (FK)

class RFQItem:
    - rfq (FK)
    - product (FK)
    - quantity
    - required_uom
    - specifications
    - preferred_supplier
```

## 3. Supplier Quotations
**Purpose**: Supplier responses to RFQ
**Features**: UOM conversion, pricing comparison, terms & conditions

### UOM Conversion System:
- Base unit tracking (smallest unit)
- Package/bulk conversions
- Supplier-specific UOM handling
- Price per unit calculations

### Models Enhancement:
```python
class SupplierQuotation:
    - quotation_number
    - rfq (FK)
    - supplier (FK)
    - quotation_date
    - valid_until
    - delivery_time_days
    - payment_terms
    - discount_percentage
    - discount_amount
    - discount_per_item
    - total_amount
    - status (pending/approved/rejected)

class SupplierQuotationItem:
    - quotation (FK)
    - rfq_item (FK)
    - quoted_uom (FK to UnitOfMeasure)
    - package_qty
    - unit_price
    - total_price
    - delivery_time
    - specifications
```

## 4. Purchase Order (PO)
**Purpose**: Legal commitment to purchase
**Features**: Documentation only (no inventory/accounting impact)

### Features:
- Supplier selection from quotations
- Terms & conditions
- Delivery schedules
- Three discount types:
  - Percentage discount
  - Fixed amount discount
  - Per-item discount
- Purchase limits validation
- Delivery terms

### Models Enhancement:
```python
class PurchaseOrder:
    - po_number (auto-generated)
    - quotation (FK)
    - supplier (FK)
    - po_date
    - delivery_date
    - warehouse (FK) # replaces address
    - purchase_limit
    - delivery_terms
    - discount_type (percentage/amount/per_item)
    - discount_value
    - subtotal
    - discount_amount
    - total_amount
    - status (draft/sent/acknowledged/delivered/cancelled)
    - terms_conditions

class PurchaseOrderItem:
    - purchase_order (FK)
    - product (FK)
    - quantity
    - uom (FK)
    - unit_price
    - item_discount
    - total_price
    - delivery_date
```

## 5. Goods Receipt Note (GRN)
**Purpose**: Physical receipt verification with quality control
**Features**: Quality inspection, UOM handling, inventory impact

### Quality Control Features:
- Received quantity vs ordered
- Quality inspection
- Accept/Reject decisions
- Tracking numbers
- Vehicle & gate entry details

### Models Enhancement:
```python
class GoodsReceiptNote:
    - grn_number (auto-generated)
    - purchase_order (FK)
    - received_date
    - received_by (FK to User)
    - inspected_by (FK to User)
    - vehicle_number
    - gate_entry_number
    - status (draft/received/inspected/completed)
    - total_received_value

class GRNItem:
    - grn (FK)
    - po_item (FK)
    - uom (FK)
    - ordered_qty
    - received_qty
    - accepted_qty
    - rejected_qty
    - tracking_number
    - remarks
    - unit_price
    - total_value
    - quality_status (pending/passed/failed/partial)

# Inventory Impact (use_status = 'locked' until invoice)
class InventoryTransaction:
    - grn_item (FK)
    - product (FK)
    - warehouse (FK)
    - quantity
    - uom (FK)
    - unit_cost (null until invoice)
    - use_status ('locked'/'available')
```

## 6. Purchase Invoice/Bill
**Purpose**: Vendor billing with accounting integration
**Features**: Invoice matching, automatic accounting entries

### Accounting Integration:
```
Dr. COGS/Inventory | Cr. Accounts Payable (Vendor)
Dr. Expense/Asset Account | Cr. Accounts Payable (Supplier)
```

### Models Enhancement:
```python
class PurchaseInvoice:
    - invoice_number
    - vendor_invoice_number
    - grn (FK)
    - invoice_date
    - due_date
    - payment_terms
    - discount_percentage
    - discount_amount
    - tax_amount
    - total_amount
    - status (draft/posted/paid/cancelled)

# Auto-unlock inventory after invoice posting
```

## 7. Payment Management
**Purpose**: Payment tracking and alerts
**Features**: Due date alerts, payment scheduling

### Payment Alerts:
- Dashboard notifications
- Email reminders
- Payment due reports
- Overdue tracking

## 8. Sidebar Navigation Structure
```
Purchase Module:
├── Dashboard
├── Requisitions ⬆️ (moved up)
├── RFQ
├── Quotations
├── Purchase Orders
├── Goods Receipt Notes
├── Purchase Invoices/Bills
├── Payments
└── Reports
```

## 9. UOM Implementation Details

### Base Unit System:
- Every product has a base unit (smallest measurable unit)
- All conversions calculated from base unit
- Supplier-specific packaging handled

### Example: Balloon Product
```
Base Unit: 1 Balloon
Supplier A: Packet (10 balloons) @ $5/packet = $0.50/balloon
Supplier B: Box (50 balloons) @ $20/box = $0.40/balloon
```

## 10. Implementation Priority

### Phase 1: Core Models & Basic Flow
1. Update models with new fields
2. Create migrations
3. Basic CRUD operations

### Phase 2: UOM & Quality Control
1. UOM conversion system
2. GRN quality control
3. Inventory locking mechanism

### Phase 3: Accounting Integration
1. Automatic journal entries
2. Inventory valuation
3. Payment tracking

### Phase 4: Advanced Features
1. Approval workflows
2. Payment alerts
3. Reporting dashboard

## 11. Mock Data Removal
- Remove all hardcoded sample data
- Implement dynamic data from models
- Add proper error handling for empty states

## 12. Discount System Implementation

### Three Discount Types:
1. **Percentage Discount**: Applied to total amount
2. **Fixed Amount Discount**: Flat reduction
3. **Per-Item Discount**: Individual item discounts

### Calculation Flow:
```
Subtotal = Sum of (Quantity × Unit Price) for all items
- Apply per-item discounts first
- Then apply percentage or fixed amount discount
Total = Subtotal - Total Discounts + Taxes
```

This plan ensures complete P2P workflow with proper UOM handling, quality control, and automatic accounting integration.
