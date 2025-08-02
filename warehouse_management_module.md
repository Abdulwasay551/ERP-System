# 🏢 ERP Warehouse Management Submodule (WMS) - Flexible & Extensible

> **Purpose:** A modular warehouse management system (WMS) design for ERP platforms, supporting multi-company, multi-location, and bin-level inventory with full traceability and optional advanced features.

---

## 🔹 1. Core Warehouse Structure

### 1.1 Warehouse Types
| Type                | Description                                | Optional |
|---------------------|--------------------------------------------|----------|
| Raw Material        | Stores raw materials for manufacturing     | ❌       |
| Work-In-Progress    | Holds items under production               | ✅       |
| Finished Goods      | Contains ready-for-sale products           | ❌       |
| Scrap               | Keeps unusable or rejected goods           | ✅       |
| Transit             | Temporarily holds goods in transfer        | ✅       |
| Quarantine          | Isolates items for inspection/QC           | ✅       |
| Returns             | Vendor or customer return items            | ✅       |
| Virtual             | For dropshipping or outsourced fulfillment | ✅       |

### 1.2 Warehouse Hierarchy
- Company → Warehouse → Zone → Aisle → Shelf → Bin
- Example:
  - Company: ACME Pvt Ltd
    - Warehouse: Karachi Plant
      - Zone: Zone A
        - Aisle: A1
          - Shelf: S1
            - Bin: B1

### 1.3 Warehouse Fields
| Field Name           | Description                          |
|----------------------|--------------------------------------|
| Name                 | Unique name per company              |
| Code                 | Short code (e.g., KHI-RAW-01)        |
| Location Type        | Physical / Virtual                   |
| Company              | ForeignKey to owning company         |
| Parent Warehouse     | Optional (for nested warehouses)     |
| Is Active            | Boolean flag                         |
| Address / Coordinates| Useful for logistics                 |
| Default For          | Raw / FG / WIP / Scrap, etc.         |

---

## 🔹 2. Bin & Location Tracking

### 2.1 Bin Management (Optional)
- Enable fine-grained stock placement
- Each bin tracks:
  - Max capacity (by UOM)
  - Assigned item types
  - FIFO / FEFO compliance
  - Barcode/QR

### 2.2 Zone & Aisle Planning
- Helps optimize picking paths
- Can be tagged by temperature zones or access restrictions

### 2.3 Storage Constraints (Optional)
- Fragile, Flammable, Cold Storage
- Weight or volume restrictions per bin

---

## 🔹 3. Permissions & Roles

| Role              | Permissions                                                   |
|-------------------|---------------------------------------------------------------|
| Warehouse Manager | Full CRUD on warehouses, transfers, and inventory             |
| Storekeeper       | Can receive, pick, transfer, and count stock                  |
| QC Inspector      | Can approve/reject stock during GRN or after quarantine       |
| Auditor           | Read-only access with inventory adjustment flag               |

- Access control can be assigned per warehouse, zone, or bin
- Users can be restricted to certain companies or locations

---

## 🔹 4. Integration with ERP Modules

| Module       | Integration Role                                  |
|--------------|----------------------------------------------------|
| Inventory    | Tracks stock level and movements                  |
| Sales        | Assigns warehouse for delivery                    |
| Purchase     | Routes incoming stock to correct warehouse        |
| Manufacturing| Moves stock between raw → WIP → FG                |
| Accounting   | Warehouse value = inventory asset                 |
| CRM/Projects | Allocates stock per warehouse per client/project  |

---

## 🔹 5. Configurations

- **Enable Multi-Warehouse per Company**
- **Allow Negative Stock (optional)**
- **Default Warehouse per Transaction Type**
  - E.g., Sales = FG Warehouse, Purchase = Raw Material Warehouse
- **Track Expiry per Location**
- **FIFO/FEFO per Bin**
- **Restrict Items to Specific Warehouses** (e.g., Chemicals only in Chemical Store)
- **Inter-Warehouse Transfer Rules**

---

## 🔹 6. Optional Features (Advanced)

| Feature                    | Description                                       |
|----------------------------|---------------------------------------------------|
| Barcode Scanning           | Scan bins/items for faster operations             |
| RFID Tagging               | Automatic bin movement & traceability             |
| IoT Integration            | Real-time temperature, humidity monitoring        |
| Mobile Warehouse App       | For scanning, picking, stock taking               |
| Auto Put-Away Rules        | Suggest optimal bin placement                     |
| Auto Replenishment Alerts  | Suggest restock based on thresholds               |
| Pick List Optimization     | Smart pick path generation                        |
| Cross-Docking              | Direct transfer from GRN to delivery              |

---

## 🔹 7. Key Transactions

| Transaction         | Description                                       | Affects Stock | Affects Accounting |
|---------------------|---------------------------------------------------|---------------|---------------------|
| Stock Transfer       | Move stock between warehouses/bins              | ✅            | ❌                  |
| Stock Receipt (GRN)  | Goods arrive to warehouse from supplier         | ✅            | ✅                  |
| Delivery Outbound    | Stock shipped from warehouse to customer         | ✅            | ✅                  |
| Inter-Warehouse Move | Internal stock shift (e.g., RM → FG)             | ✅            | Optional            |
| Stock Adjustment     | Manual correction or audit result                | ✅            | ✅                  |

---

## 🔹 8. Reports

| Report Name             | Description                                    |
|-------------------------|------------------------------------------------|
| Warehouse Stock Report  | Total stock per warehouse                     |
| Bin-Wise Stock Report   | Quantity per bin                              |
| Warehouse Utilization   | Space usage and capacity                      |
| Inbound / Outbound Log  | Goods moved in and out                        |
| Transfer History        | Internal stock movement                       |
| FIFO/FEFO Compliance    | Batches picked correctly                      |
| Stock Ageing Report     | Oldest stock in each location                 |

---

## ✅ Design Principles
- 100% modular: All features optional
- Bin/Zone/Hierarchy support without enforcing them
- Multi-tenant and multi-company ready
- Inventory and accounting integration ready
- Designed for scale, automation, and traceability

