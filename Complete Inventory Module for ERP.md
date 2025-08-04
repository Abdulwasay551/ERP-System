**Complete Inventory Module for ERP**

---

**Overview:**  
 This document provides a  explanation of the **Inventory Module** in an ERP system, covering its full structure, functionalities, workflows, integrations, and accounting implications. It is designed from an accountant’s perspective, focused on accuracy, traceability, and integration with production and sales.

---

**1\. Warehouse Structure Configuration:**  
 Create logical and physical warehouse locations:

| Warehouse Type | Description |
| ----- | ----- |
| Raw Material Warehouse | Stores purchased raw materials |
| Work-in-Progress (WIP) Warehouse | Temporarily holds items under production |
| Finished Goods Warehouse | Stores completed products ready for sale |
| Scrap Warehouse | Keeps defective or unusable materials |
| Transit Warehouse | Temporarily holds in-transit goods (optional) |

---

**3\. Item Master Settings:**  
 Each inventory item must have a complete master record:

| Field | Description |
| ----- | ----- |
| Item Code / Name | Unique identifier |
| Item Group | Categorization (e.g., Raw, FG) |
| UOM (Unit of Measure) | Kg, piece, box, etc. |
| Reorder Level | Minimum stock threshold |
| Lead Time | Time to replenish |
| Default Warehouse | Primary storage location |
| Valuation Method | FIFO / Weighted Average |
| Item Type | Stock / Non-stock / Service |
| Serial/Lot Tracking | Yes/No |
| Expiry Tracking | Yes/No (for perishable items) |

---

 

 

**4\. Inventory Transactions & Flow:**

| Transaction | Description | Affects Stock? | Affects Accounts? |
| ----- | ----- | ----- | ----- |
| Purchase Receipt (GRN) | Receive from vendor | Yes (IN) | Yes |
| Stock Transfer | Move between warehouses | Yes | No |
| Material Issue | Raw material to WIP | Yes (OUT) | Yes |
| Material Receipt | WIP to Finished Goods | Yes (IN) | Yes |
| Delivery Note | Goods sent to customer | Yes (OUT) | Yes |
| Stock Adjustment | Manual stock correction | Yes | Yes (if value updated) |
| Opening Entry | Initial stock setup | Yes | Yes |
| Stock Reconciliation | Audit correction | Yes | Yes |

---

**5\. Inventory Valuation Methods:**

* **FIFO (First-In, First-Out)** – Oldest stock cost used first  
* **Weighted Average** – Average of all purchases  
* **Standard Costing** *(less common)* – Predefined item cost

**6\. Integrations with Other Modules:**

| Integrated Module | Inventory Impact |
| ----- | ----- |
| **Purchase** | Increases stock (via GRN) |
| **Production** | Issues raw material, adds finished goods |
| **Sales** | Decreases stock (delivery) |
| **Accounts** | Updates stock value, COGS, inventory asset |
| **MRP** | Triggers replenishment based on planning |
| **POS** | Immediate delivery/sale of inventory |

---

**7\. Inventory Reports:**

* **Stock Ledger** – All movements per item  
* **Stock Balance Report** – Qty and value on hand per warehouse  
* **Valuation Report** – Total inventory value  
* **Reorder Report** – What to reorder and when  
* **Batch/Serial Tracking** – Trace inventory history  
* **Stock Ageing** – Stock held beyond X days  
* **Shortage Report** – Items not available for production or sale

---

**8\. Key Configurations:**

* Set **minimum stock levels**, **safety stock**, and **reorder quantities**  
* Enable **automatic reordering** (optional)  
* Define **stock UOM conversion** (e.g., 1 box \= 10 pcs)  
* Configure **valuation accounts**:

| Stock Account Type | Default Account |
| ----- | ----- |
| Inventory Asset | Inventory on Hand |
| Stock Adjustment | Inventory Adjustment Account |
| COGS | Cost of Goods Sold |

---

**9\. Common Accounting Entries:**

| Action | Debit | Credit |
| ----- | ----- | ----- |
| GRN (with invoice) | Inventory Asset | Accounts Payable |
| Material Issue | WIP Inventory / COGS | Raw Material Inventory |
| FG Receipt | FG Inventory | WIP Inventory |
| Delivery Note | COGS | FG Inventory |
| Stock Adjustment (loss) | Inventory Loss | Inventory Asset |

---

**Next Steps:**

* Finalize item master data  
* Create warehouse locations  
* Define all mappings with accounts and valuation  
* Set up BoMs and link production

