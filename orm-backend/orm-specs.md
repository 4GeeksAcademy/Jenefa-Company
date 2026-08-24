# Functional & Technical Specifications - HealthCore Centralized Platform

## 1. System Architecture & Dual-Database Topology
The system extends the existing `HealthCore Digital` monorepo structure under the `services/` directory. It acts as a dual-persistence bridge connecting decoupled databases to balance user security with high-throughput transactional logging.

### 1.1 Multi-Persistence Responsibility Matrix
*   **Authentication & Session Cache (TinyDB)**: Maintains the existing fast, file-based document tracking baseline. It remains the definitive source of truth for the `User` metadata partition and the `get_current_user` execution lifecycle.
*   **Centralized Asset Persistence Layer (Supabase)**: A hosted, relational PostgreSQL backend managing core entity schemas and tracking orders.
*   **Deliberate Routing**: The FastAPI application maintains two concurrent, active database connections. Route handlers explicitly direct data operations to the correct target engine.
+------------------------------------+|   HealthCore Application Core      |+------------------------------------+/                            (Local Identity Checks)           (Relational Operations)/                                v                                  v+---------------------------+       +---------------------------+|   TinyDB (Auth Store)     |       |   Supabase (PostgreSQL)   ||  - Fast Document Lookups  |       |  - Clinical Asset Ledgers ||  - User IDs & Sessions    |       |  - Database FK Boundaries  |+---------------------------+       +---------------------------+
### 1.2 Resource Session Lifecycles
*   **Context Isolation**: To prevent session bleeding, connections are injected cleanly on a per-request workflow boundary via FastAPI `Depends()`. 
*   **Strict Anti-Global Policy**: No global session objects are permitted anywhere inside the codebase.
*   **Schema Synchronization**: Database-native relational structures are automatically verified or provisioned at runtime initialization via `SQLModel.metadata.create_all(engine)`.

## 2. Relational Object Mapping (ORM) & File Layers
Data persistence tasks use `SQLModel` to blend declarative ORM definitions with Pydantic type safety. Raw, unmapped SQLAlchemy syntax is prohibited.

### 2.1 Decoupled Source Layout Structure
*   `models.py`: Declares structures mapping direct subclasses of `SQLModel(table=True)`. Relational fields must enforce database-level Foreign Key attributes (`Field(foreign_key=...)`) to ensure referential constraints are managed natively inside the PostgreSQL cluster.
*   `schemas.py`: Contains presentation payloads mapping subclasses of Pydantic or `SQLModel(table=False)`.
*   **Response Isolation Protocol**: Endpoints are strictly blocked from returning raw database-level model entities. Data layers must explicitly translate or map records to client validation schemas inside `schemas.py` before serializing responses.

### 2.2 Mitigation of N+1 Performance Degradation
To preserve system bandwidth, array queries (such as clinical orders containing associated product configurations) must not load child elements lazily inside procedural loops. Backend query statements must use explicit relationships up front (`selectinload` or `joinedload`) to fetch records in single, unified operations.

## 3. Core Corporate & Operational Constraints

### 3.1 Immutable Clinical Inventory Stock Rules
*   **Non-Editable Balances**: Real-time asset levels are completely immutable on base tracking rows. No column storing direct stock numbers is allowed inside product definitions. 
*   **Ledger-Driven Balances**: Asset counts are derived entirely by calculating the mathematical sum of the transaction ledger history:
    $$\text{current\_stock} = \sum(\text{Inbound Quantities}) - \sum(\text{Outbound Quantities})$$
*   **Audit Tracking**: Inbound and outbound log rows must capture the operator's active string identifier (`user_uuid`) extracted directly from the TinyDB session block. No user database tables are mirrored inside Supabase.

### 3.2 Overdraft Guardrails & Data Validation
*   **Negative Balance Guardrails**: Outbound deployment entries are audited prior to execution. If a medical asset request exceeds available quantities inside the designated partition scope, the request is terminated.
*   **Rejection Response**: Transactions failing this test are rejected before any physical database write occurs. The path handler will abort and return an `HTTP 400 Bad Request` containing a clear description of the inventory failure.

## 4. Unified API Interface Routing

All operational processes are grouped under a dedicated FastAPI `APIRouter` prefixed at `/inventory` to enforce clean namespace boundaries.

| Method | Path | Auth Required | Execution Context |
| :--- | :--- | :--- | :--- |
| **GET** | `/inventory/products` | **Yes** | Surfaces all tracked medical supplies along with dynamically aggregated `current_stock` figures. |
| **POST** | `/inventory/products` | **Yes** | Registers a new supply line item with a starting balance of `0`. |
| **GET** | `/inventory/products/{id}` | **Yes** | Fetches details for a single supply asset with its scoped partition quantities attached. |
| **POST** | `/inventory/orders/inbound` | **Yes** | Logs arriving medical stock, writing the actor's `user_uuid` from TinyDB into the log row. |
| **POST** | `/inventory/orders/outbound` | **Yes** | Evaluates stock safety buffers and registers outgoing medical deployments if valid. |
| **GET** | `/inventory/orders` | **Yes** | Pulls the unified historical order log, pre-loading related product elements to prevent N+1 queries. |
