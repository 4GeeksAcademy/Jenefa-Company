# HealthCore Backoffice: Inventory Management Module Specifications

## 1. Product Brief & High-Level Scope

### Context & Objective
The HealthCore backend engineering team has completed development of the centralized `/inventory` API layer. This specification introduces the internal front-end inventory module within the unified HealthCore Backoffice platform. It eliminates dependency on external REST clients (e.g., Postman) for clinic operations staff managing clinical supply chains across the network's 12 locations.

### Target Persona & Core UX Philosophy
- **User Base:** HealthCore internal operations managers, clinic administrators, and nursing staff logging high-volume supply distributions across US and UK clinics.
- **Design Priority:** Speed and absolute data clarity take absolute priority over consumer-facing marketing polish. Operations personnel processing physical inventory deliveries or logging exits at 7:00 AM require robust, predictable form layouts that completely prevent cryptic system crashes or silent data failures.

### Technical Acceptance Criteria Matrix
- [ ] **Unified API Engine:** A dedicated integration file acts as the exclusive route coordinator; individual UI view components cannot make raw browser `fetch` calls independently.
- [ ] **Cross-Border Security Guards:** Active session authentication is required for all four inventory views. Unauthenticated access drops instantly and forces a redirect to the standard login screen.
- [ ] **Live Inventory Listing:** The data ledger coordinates directly with active API endpoints to render real-time balances alongside high-contrast low-stock visual alarms.
- [ ] **Inbound Delivery Intake:** An interactive form handles inbound clinic shipments, cleans field inputs completely on success, and parses API anomalies explicitly.
- [ ] **Guardrailed Dispersal Workflow:** The outbound dispersal module queries live inventory levels reactively before inputs are submitted, displaying early frontend warnings and targeted inline backend error tracking.
- [ ] **Immutable Operational Stream:** A read-only audit ledger tracks comprehensive historical clinic entries and exits, exposing unique operator IDs and localized timestamps.

---

## 2. API Integration Layer

### Centralized Architecture
- **Target Location:** `lib/inventory.ts`
- **Rule:** This library contains the sole authorized network request functions interacting with the remote `/inventory` API endpoints. UI views or local state hooks are strictly forbidden from executing raw, un-encapsulated global `fetch` operations.

### Cross-Border Identity Token Injection
- **Bearer Pattern:** Outbound requests hitting protected inventory endpoints must read the active operator's credential state and inject a standardized header:
  ```http
  Authorization: Bearer <token>
  ```
- **Token Source:** Pulled dynamically from the central application session storage layer (`localStorage`, React/Vue application state context, or encrypted browser cookies).

### HealthCore Compliance Error Handling
- **No Silent Failures:** Intercept network failures across the `4xx` client and `5xx` server ranges comprehensively.
- **Graceful Error Parsing:** To prevent staff frustration, never display unparsed JSON payloads, database trace logs, or structural stack warnings. Extract the core string messages provided by the API and render them clearly within predictable UI feedback blocks.

---

## 3. View 1: Products Inventory Ledger

### Routing Matrix
- **Internal Backoffice Path:** `/backoffice/inventory/products`

### Layout & Data Processing
- **Action:** Query `GET /inventory/products` immediately on component instantiation to compile the active clinical supplies sheet.
- **Field Rendering:** Align dataset tables directly with the strict corporate terminology matrices defined inside `CONTEXT.md`.
- **Interactive Hooks:** Each material row must display accessible link options or action triggers allowing clinic staff to navigate instantly to targeted intake or dispersal workflows for that specific item ID.

### High-Contrast Visual Stock Status
- **Objective:** Give morning clinical operations managers immediate clarity over stock shortages before patient appointment windows begin.
- **Rule:** Bind active balances to high-contrast visual indicators. Define precise numeric thresholds dividing optimal holdings from critical shortages, and document these mathematical limits explicitly within inline code comments.

---

## 4. View 2: Inbound Inventory Intake (Delivery Form)

### Routing Matrix
- **Internal Backoffice Path:** `/backoffice/inventory/orders/inbound`

### Input Validation & Form Fields
- **Item Choice Control:** Implement an interactive dropdown or searchable list component displaying human-readable item names. Staff must never be required to type raw, error-prone database string IDs manually.

### Submission Lifecycle States
- **Target Endpoint:** Packages inputs into a unified JSON object sent via `POST /inventory/orders/inbound`.
- **Success Sequence:** On successful completion, fully purge old user inputs from form controls and render a clear, green verification banner confirming the delivery was successfully logged into the database.
- **Failure Sequence:** If the endpoint rejects the submission, trap the resulting response, extract the message text, and mount it into a dedicated, highly visible alert box.

---

## 5. View 3: Outbound Inventory Dispersal (Consumption Form)

### Routing Matrix
- **Internal Backoffice Path:** `/backoffice/inventory/orders/outbound`

### Reactive Stock Guardrails
- **Pre-Flight Telemetry Fetching:** Selecting a medical item from the choice field must trigger an immediate backend query to find its precise available inventory level before the operator can type or execute a consumption quantity.
- **Reactive State Updates:** The displayed baseline availability count must recalculate reactively the exact millisecond a user selects a different product option.

### Validation & Defensive Error Treatment
- **Target Endpoint:** Submits outbound transactions via `POST /inventory/orders/outbound`.
- **UX Client Guard:** If staff enter a dispersal number that exceeds the current live availability balance, trigger an immediate high-contrast client-side warning badge. *(Note: This serves as an immediate front-end defensive safeguard against manual typos; the backend API remains the authoritative legal evaluator).*
- **Inline Outbound Error Parsing:** If an outbound call returns an `HTTP 400` status (e.g., due to a race condition causing insufficient stock), extract the error message string and bind it inline, immediately adjacent to the numerical dispersal input field.

---

## 6. View 4: Orders History Ledger

### Routing Matrix
- **Internal Backoffice Path:** `/backoffice/inventory/orders`

### Regulatory Audit Protection Policy
- **Strict Read-Only Enforcement:** In compliance with HealthCore data governance policies, this view serves as an unalterable operational record stream. Row deletion controls, dataset clear tools, and record modification windows must be entirely absent from the template layout.

### Data Layout & Audit Columns
- **Action:** Pull the full transaction log via `GET /inventory/orders`.
- **Mandatory Reporting Columns:** Each line item row must comprehensively display:
  - Product Name
  - Transaction Volume
  - Movement Class (Inbound vs Outbound distinction)
  - Logged Timestamp
  - Operator ID (`user_uuid` tracking the specific teammate account who created the ledger row).
- **Visual Segregation:** Differentiate inbound supply additions from outbound consumption paths instantly using contrasting text badge color classes or distinct directional vector markers (`↑` / `↓`).
