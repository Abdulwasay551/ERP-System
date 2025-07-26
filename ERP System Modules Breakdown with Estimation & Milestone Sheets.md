# **ERP System MVP Overview (Connected via Chart of Accounts)**

Each module is multi-tenant and linked to the centralized **Chart of Accounts (COA)**, which handles all financial tracking, validation, and journal entry logic.

---

## **✅ 1\. `user_auth` – User & Company Authentication**

### **Features:**

* Multi-tenant user authentication (Users belong to Companies)

* Role-based access control (Admin, Manager, Accountant, etc.)

* Session & token-based login (DRF \+ Django)

* Password reset, invitation system

### **Key Models:**

* `User`

* `Company`

* `UserCompanyRole`

### **Dependencies:**

* Base system for access to all modules

* Used for tracking who performed financial transactions

---

## **📘 2\. `chart_of_accounting` – Central COA System (Already Implemented)**

### **Features:**

* Hierarchical multi-level COA: Category \> Group \> Account

* Default system accounts (sales revenue, inventory, COGS, etc.)

* Sub-ledgers for Vendors, Customers

* Context-based auto-posting (`auto_post_context`)

* Validation: active accounts, not a group account, correct side

### **Used By:**

* ALL other apps: sales, purchases, inventory, etc.

---

## **🛒 3\. `sales` – Sales Orders & Invoicing**

### **Features:**

* Sales Quotes → Sales Orders → Invoices

* Customer management & sub-ledger accounts

* Product sales with tax & pricing rules

* Auto-posting to Accounts Receivable, Sales Revenue, Tax Payable

### **COA Integration:**

* Debit: **Accounts Receivable (Customer)**

* Credit: **Sales Revenue**, **Tax Payable**

---

## **📥 4\. `purchase` – Purchase Orders & Vendor Bills**

### **Features:**

* Supplier management with sub-ledger accounts

* Purchase Requests → Purchase Orders → Bills

* Payment scheduling & status tracking

* Integration with Inventory for goods receiving

* Auto-posting to Payables & COGS

### **COA Integration:**

* Debit: **COGS / Inventory**

* Credit: **Accounts Payable (Vendor)**

---

## **🏭 5\. `manufacturing` – BOM & Production Orders**

### **Features:**

* Bill of Materials (BoM)

* Work Orders, Routing Steps

* Raw Material Consumption & Finished Goods creation

* Cost computation from materials, labor, overhead

* Auto inventory move & journal entries

### **COA Integration:**

* Debit: **WIP / Finished Goods**

* Credit: **Raw Materials**, **Labor Expense**

---

## **📦 6\. `inventory` – Stock Management**

### **Features:**

* Multi-location warehouses

* Product & lot tracking

* Goods receiving, internal moves, delivery orders

* Real-time stock valuation (FIFO/Avg)

* Auto-journal entries for stock moves (if perpetual inventory)

### **COA Integration:**

* Debit: **Inventory Asset**

* Credit: **Inventory Adjustment / COGS**

---

## **🤝 7\. `crm` – Customer Relationship Management**

### **Features:**

* Lead, Opportunity, Customer tracking

* Sales team pipeline & status stages

* Schedule meetings, calls, tasks

* Convert leads to sales quotations

* Optional integration with marketing tools

### **COA Integration:**

* No direct accounting, but generates potential future transactions

---

## **🧑‍💼 8\. `hr` – Human Resources**

### **Features:**

* Employee database (join date, position, department)

* Attendance, leaves, contracts

* Payroll base (can expand later)

* Employee expenses & reimbursements

### **COA Integration:**

* Debit: **Salary/Wages Expense**

* Credit: **Cash / Bank / Employee Payable**

---

## **📁 9\. `project_management` – Tasks, Projects, Timesheets**

### **Features:**

* Project & Task hierarchy

* User assignment, status tracking

* Timesheet logging

* Cost tracking from hours & materials

### **COA Integration:**

* Project-based cost accounting (optional)

* Debit: **Project Cost / Labor**

* Credit: **Employee Expense / WIP**

---

# **🔁 Cross-Cutting Integrations**

| Feature | Affected Apps | Notes |
| ----- | ----- | ----- |
| **Chart of Accounts (COA)** | All apps | Single source of truth for financial accounts |
| **Auto-posting Utility** | sales, purchase, hr, inventory, mfg | `auto_post_context(company, type, obj, ...)` |
| **Multi-Tenant Support** | All apps | Company-based data isolation |
| **Role-based Permissions** | All apps | Guards on data creation and access |
| **Journals & Audit Trail** | All apps | Each transaction posts to journal entry with user & timestamp |
| **Sub-Ledger Accounts** | Sales (Customer), Purchase (Vendor), HR (Employee) | Managed via `Account.parent` relationships |

---

# **🧱 MVP Deployment Stack**

| Layer | Stack |
| ----- | ----- |
| Backend | Django, Django REST Framework |
| Frontend | Django Templates \+ AJAX (jQuery/HTMX) |
| DB | Supabase PostgreSQL (multi-tenant) |
| Auth | Django \+ DRF Token/Auth JWT |
| Hosting | Render/VPS/EC2 or Dockerized |
| Others | Celery (optional), Redis (for jobs), Stripe (if payments) |

