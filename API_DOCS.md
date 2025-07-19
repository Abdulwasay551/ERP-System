# 📚 ERP System API Documentation

Welcome to the **ERP System API**! This document provides a complete overview of all available RESTful endpoints, grouped by module. All endpoints require authentication and are company-aware.

---

## 🔐 Authentication
- Obtain a token: `POST /api/token-auth/` with `{ "username": "<your-username>", "password": "<your-password>" }`
- Use `Authorization: Token <token>` in all API requests.

---

## 🚀 Quickstart Example
```bash
# Get your token
curl -X POST http://localhost:8000/api/token-auth/ -d "username=admin&password=yourpassword"

# List customers (CRM)
curl -H "Authorization: Token <token>" http://localhost:8000/api/crm/customers/
```

---

## 🗂️ API Endpoints by Module

### 🧑‍💼 CRM
Base: `/api/crm/`
| Resource         | Endpoint                | Methods           | Description                |
|------------------|------------------------|-------------------|----------------------------|
| Customers        | `/customers/`          | GET, POST         | List, create customers     |
|                  | `/customers/{id}/`     | GET, PUT, PATCH, DELETE | Retrieve/update/delete customer |
| Leads            | `/leads/`              | GET, POST         | List, create leads         |
| Opportunities    | `/opportunities/`      | GET, POST         | List, create opportunities |
| Communications   | `/communications/`     | GET, POST         | List, create comm logs     |

### 🛒 Sales
Base: `/api/sales/`
| Resource         | Endpoint                | Methods           | Description                |
|------------------|------------------------|-------------------|----------------------------|
| Products         | `/products/`           | GET, POST         | List, create products      |
| Taxes            | `/taxes/`              | GET, POST         | List, create taxes         |
| Quotations       | `/quotations/`         | GET, POST         | List, create quotations    |
| Sales Orders     | `/salesorders/`        | GET, POST         | List, create sales orders  |
| Sales Order Items| `/salesorderitems/`    | GET, POST         | List, create SO items      |
| Invoices         | `/invoices/`           | GET, POST         | List, create invoices      |
| Payments         | `/payments/`           | GET, POST         | List, create payments      |

### 🏬 Purchase
Base: `/api/purchase/`
| Resource         | Endpoint                | Methods           | Description                |
|------------------|------------------------|-------------------|----------------------------|
| Suppliers        | `/suppliers/`          | GET, POST         | List, create suppliers     |
| Purchase Orders  | `/purchaseorders/`     | GET, POST         | List, create PO            |
| Purchase Items   | `/purchaseorderitems/` | GET, POST         | List, create PO items      |
| Bills            | `/bills/`              | GET, POST         | List, create bills         |
| Payments         | `/purchasepayments/`   | GET, POST         | List, create payments      |

### 📦 Inventory
Base: `/api/inventory/`
| Resource         | Endpoint                | Methods           | Description                |
|------------------|------------------------|-------------------|----------------------------|
| Product Categories| `/productcategories/`  | GET, POST         | List, create categories    |
| Warehouses       | `/warehouses/`         | GET, POST         | List, create warehouses    |
| Stock Items      | `/stockitems/`         | GET, POST         | List, create stock items   |
| Stock Movements  | `/stockmovements/`     | GET, POST         | List, create movements     |
| Stock Alerts     | `/stockalerts/`        | GET, POST         | List, create alerts        |

### 💰 Accounting
Base: `/api/accounting/`
| Resource         | Endpoint                | Methods           | Description                |
|------------------|------------------------|-------------------|----------------------------|
| Accounts         | `/accounts/`           | GET, POST         | List, create accounts      |
| Journals         | `/journals/`           | GET, POST         | List, create journals      |
| Journal Entries  | `/journalentries/`     | GET, POST         | List, create entries       |
| Journal Items    | `/journalitems/`       | GET, POST         | List, create items         |
| Payables         | `/payables/`           | GET, POST         | List, create payables      |
| Receivables      | `/receivables/`        | GET, POST         | List, create receivables   |
| Bank Accounts    | `/bankaccounts/`       | GET, POST         | List, create bank accts    |
| Bank Reconciliations| `/bankreconciliations/`| GET, POST      | List, create reconciliations|
| Tax Configs      | `/taxconfigs/`         | GET, POST         | List, create tax configs   |
| Currencies       | `/currencies/`         | GET, POST         | List, create currencies    |
| Financial Statements| `/financialstatements/`| GET, POST      | List, create statements    |
| Audit Logs       | `/auditlogs/`          | GET, POST         | List, create audit logs    |
| Recurring Journals| `/recurringjournals/` | GET, POST         | List, create recurring journals |

### 👥 HR
Base: `/api/hr/`
| Resource         | Endpoint                | Methods           | Description                |
|------------------|------------------------|-------------------|----------------------------|
| Employees        | `/employees/`          | GET, POST         | List, create employees     |
| Attendance       | `/attendance/`         | GET, POST         | List, create attendance    |
| Leaves           | `/leaves/`             | GET, POST         | List, create leaves        |
| Payrolls         | `/payrolls/`           | GET, POST         | List, create payrolls      |
| Payslips         | `/payslips/`           | GET, POST         | List, create payslips      |
| HR Reports       | `/hreports/`           | GET, POST         | List, create HR reports    |

### 📁 Project Management
Base: `/api/project/`
| Resource         | Endpoint                | Methods           | Description                |
|------------------|------------------------|-------------------|----------------------------|
| Projects         | `/projects/`           | GET, POST         | List, create projects      |
| Tasks            | `/tasks/`              | GET, POST         | List, create tasks         |
| Time Entries     | `/timeentries/`        | GET, POST         | List, create time entries  |
| Project Reports  | `/projectreports/`     | GET, POST         | List, create reports       |

### 🏭 Manufacturing
Base: `/api/manufacturing/`
| Resource         | Endpoint                | Methods           | Description                |
|------------------|------------------------|-------------------|----------------------------|
| Bill of Materials| `/boms/`               | GET, POST         | List, create BOMs          |
| BOM Items        | `/bomitems/`           | GET, POST         | List, create BOM items     |
| Work Orders      | `/workorders/`         | GET, POST         | List, create work orders   |
| Production Plans | `/productionplans/`    | GET, POST         | List, create prod. plans   |

---

## 🛠️ Common RESTful Methods
- `GET /resource/` — List all
- `POST /resource/` — Create new
- `GET /resource/{id}/` — Retrieve one
- `PUT/PATCH /resource/{id}/` — Update
- `DELETE /resource/{id}/` — Delete

---

## 📝 Notes
- All endpoints require authentication.
- All data is filtered by the authenticated user's company.
- Use plural resource names (e.g., `/customers/`, `/products/`).
- For more details, see the code or contact the maintainers!

---

**Happy building with the ERP System API!** 🚀 