# Product Context Configuration (CONTEXT.md Reference)

> **CRITICAL COMPLIANCE DIRECTIVE:** To satisfy HealthCore's data governance standards and cross-border operational requirements, all front-end interfaces, column headers, input descriptors, error callouts, and system sheets must utilize the corporate domain vocabulary defined in this document. Generic development placeholders are strictly prohibited.

## 1. Corporate Domain Vocabulary Mapping

### Products Inventory Catalog Data (`GET /inventory/products`)

| Core Backend Code Property | UI Production Label | Visual Formatting & Layout Logic |
| :--- | :--- | :--- |
| `id` | *(Hidden Metadata)* | Passed silently to options objects; completely masked from clinic staff views to prevent typographical data errors. |
| `name` | **Clinical Item Name** | Rendered in bold, high-contrast typography across product logs and item selection pickers. |
| `sku` | **Stock Keeping Unit (SKU)** | Formatted as a secondary, muted identifier code below primary titles. |
| `current_stock` | **Available Inventory** | The central structural counter. Must render reactively in form screens before consumption metrics can be typed. |
| `price` | **Unit Cost** | Parsed directly into a currency string format ($XX.XX for US clinics / £XX.XX for UK locations). |

### Orders History Ledger Data (`GET /inventory/orders`)

| Core Backend Code Property | UI Production Label | Visual Formatting & Layout Logic |
| :--- | :--- | :--- |
| `product_name` | **Clinical Item Name** | Readable name tracking the specific clinical asset that was moved. |
| `quantity` | **Transaction Volume** | Clear base integer indicating total units moved. |
| `order_type` | **Movement Class** | System enum mapping (`inbound`/`outbound`). Controls layout styling rules. |
| `created_at` | **Logged Timestamp** | Localized to track the date and time across respective US/UK operating timezones. |
| `user_uuid` | **Operator ID** | The explicit employee identifier used to fulfill internal data audits and clinical accountability trackers. |

---

## 2. Interface State & Validation Definitions

### Dynamic Stock Status Thresholds (Products Catalog View)
To preserve clinical readiness across alternating medical shifts, visual badges dynamically update based on active balance volumes:
* **Status: Stock Level Stable**
  - *Logical Constraint:* `Available Inventory >= 20 units`
  - *UI Presentation:* Solid high-visibility green text banner or check badge.
* **Status: Low Stock Warning**
  - *Logical Constraint:* `Available Inventory < 20 units`
  - *UI Presentation:* High-contrast orange or deep amber badge alert to signal immediate re-order priority.

### Movement Class Visual Styling (Orders History Ledger)
* **Inbound Movement Context:** Represented consistently as **"Restock/Replenish"** using bright green UI accents or clear upward indicators (`↑`) to show stock additions.
* **Outbound Movement Context:** Represented consistently as **"Fulfillment/Removal"** using slate blue UI accents or clear downward indicators (`↓`) to show stock exits.

### Interactive Form Section Components
* **Inbound Delivery Intake View:** Header titled **"Inbound Inventory Intake"**. The master submission input is labeled **"Select Target Item"**.
* **Outbound Dispersal Entry View:** Header titled **"Outbound Inventory Dispersal"**. The primary numeric quantity interaction module is explicitly labeled **"Dispersal Amount"**.
