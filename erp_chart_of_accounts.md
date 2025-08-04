# 🧾 ERP Chart of Accounts (COA) - Comprehensive & Modular

> **Purpose:** A complete, scalable Chart of Accounts structure for a large ERP system. Modular and tenant-friendly with support for all ERP apps including sales, purchase, manufacturing, HR, CRM, projects, inventory, and accounting.

---

## 🔹 1. ASSETS

### 1.1 Current Assets
- 1.1.1 Cash
  - 1.1.1.1 Petty Cash
  - 1.1.1.2 Cash on Hand
- 1.1.2 Bank Accounts
  - 1.1.2.1 Bank - HBL
  - 1.1.2.2 Bank - UBL
  - 1.1.2.3 Bank - Meezan
- 1.1.3 Accounts Receivable
  - 1.1.3.1 Customers - Local
  - 1.1.3.2 Customers - International
- 1.1.4 Inventory
  - 1.1.4.1 Raw Material Inventory
  - 1.1.4.2 WIP Inventory
  - 1.1.4.3 Finished Goods Inventory
  - 1.1.4.4 Scrap Inventory
  - 1.1.4.5 Transit Inventory
  - 1.1.4.6 Inventory Adjustment
- 1.1.5 Advances
  - 1.1.5.1 Advance to Employees
  - 1.1.5.2 Advance to Vendors
  
### 1.2 Non-Current Assets
- 1.2.1 Fixed Assets
  - 1.2.1.1 Machinery
  - 1.2.1.2 Vehicles
  - 1.2.1.3 Furniture & Fixtures
  - 1.2.1.4 Buildings
  - 1.2.1.5 Computers & Electronics
- 1.2.2 Accumulated Depreciation
  - 1.2.2.1 Depreciation - Machinery
  - 1.2.2.2 Depreciation - Vehicles
  - 1.2.2.3 Depreciation - Others

---

## 🔹 2. LIABILITIES

### 2.1 Current Liabilities
- 2.1.1 Accounts Payable
  - 2.1.1.1 Vendors - Local
  - 2.1.1.2 Vendors - International
- 2.1.2 Accrued Expenses
  - 2.1.2.1 Salaries Payable
  - 2.1.2.2 Rent Payable
  - 2.1.2.3 Utilities Payable
- 2.1.3 Tax Payable
  - 2.1.3.1 Sales Tax Payable
  - 2.1.3.2 Withholding Tax Payable
- 2.1.4 Short-Term Loans

### 2.2 Long-Term Liabilities
- 2.2.1 Long-Term Loans
- 2.2.2 Lease Obligations

---

## 🔹 3. EQUITY

- 3.1 Capital Accounts
  - 3.1.1 Owner’s Capital
  - 3.1.2 Partner’s Capital
- 3.2 Retained Earnings
- 3.3 Reserves
- 3.4 Drawings

---

## 🔹 4. INCOME (REVENUE)

- 4.1 Sales Revenue
  - 4.1.1 Product Sales - Local
  - 4.1.2 Product Sales - Export
  - 4.1.3 Service Revenue
  - 4.1.4 POS Sales
- 4.2 Other Income
  - 4.2.1 Rental Income
  - 4.2.2 Commission Income
  - 4.2.3 Discount Received
  - 4.2.4 Interest Income

---

## 🔹 5. COST OF GOODS SOLD (COGS)

- 5.1 Direct Material Costs
  - 5.1.1 Raw Material - Local
  - 5.1.2 Raw Material - Imported
  - 5.1.3 Freight & Insurance
- 5.2 Direct Labor
  - 5.2.1 Wages - Production
  - 5.2.2 Supervisor Salaries
- 5.3 Manufacturing Overhead
  - 5.3.1 Power & Fuel
  - 5.3.2 Factory Rent
  - 5.3.3 Depreciation - Factory Equipment
- 5.4 Adjustments
  - 5.4.1 Scrap Loss
  - 5.4.2 Wastage

---

## 🔹 6. OPERATING EXPENSES

### 6.1 Admin Expenses
- 6.1.1 Salaries - Admin
- 6.1.2 Rent - Office
- 6.1.3 Utilities - Office
- 6.1.4 Office Supplies
- 6.1.5 Insurance

### 6.2 Selling & Distribution
- 6.2.1 Marketing Expense
- 6.2.2 Sales Commission
- 6.2.3 Travel Expense
- 6.2.4 Transportation & Logistics

### 6.3 IT & Subscriptions
- 6.3.1 ERP Software
- 6.3.2 SaaS Tools
- 6.3.3 Internet & Hosting

### 6.4 Miscellaneous
- 6.4.1 Repairs & Maintenance
- 6.4.2 Legal & Professional Fees
- 6.4.3 Depreciation - Office Assets
- 6.4.4 Training & Development

---

## 🔹 7. OTHER EXPENSES

- 7.1 Bad Debts
- 7.2 Currency Exchange Loss
- 7.3 Penalties
- 7.4 Interest Expense
- 7.5 Donations & CSR

---

## 🧩 Add-Ons (Optional Account Groups)

### 8. Projects & Job Costing
- 8.1 Project Revenue
- 8.2 Project Direct Costs
- 8.3 Project Overheads

### 9. HR & Payroll
- 9.1 Salaries Payable
- 9.2 Bonus
- 9.3 Provident Fund
- 9.4 Gratuity
- 9.5 EOBI / SS

### 10. CRM / Customer Operations
- 10.1 Lead Incentives
- 10.2 Customer Loyalty Program
- 10.3 Refunds & Returns

### 11. Internal Transfers & Adjustments
- 11.1 Intercompany Transfers
- 11.2 Inventory Write-offs
- 11.3 Stock-in-Transit

---

## ✅ Design Notes:
- Each account has a unique code (e.g., 1.1.3.2) and belongs to a tenant (multi-company support).
- All accounts can be tagged with modules they impact (Sales, HR, Inventory, etc.)
- Optional accounts are nullable in transactions but available to be enabled per company.
- Subaccounts and groupings support deep nesting up to 5 levels.
- Designed to integrate with all core and optional ERP modules.

