# Technical Specification: HealthCore Telemetry Ingestion Pipeline (Phases 1, 2 & 3)

## 1. Database Schema (`telemetry_events`)
The telemetry persistence layer is implemented in Supabase (PostgreSQL) as a dedicated datastore for the **HealthCore Digital** engineering unit. The data model is optimized for high-throughput, write-heavy workloads, fast cross-border monitoring, and real-time dashboard analytics.

### Table Definition
*   **Table Name**: `telemetry_events`
*   **Total Columns**: Exactly 8 columns.
*   **Immutability Rule**: Strict write-only storage. No `UPDATE` or `DELETE` logic, triggers, or API permissions are permitted. Telemetry facts are immutable once recorded. This provides an absolute, unalterable trail vital for healthcare auditing.

### Columns & Mappings
The table structural composition maps directly from the unchanged `TelemetryEvent` design across 8 database columns:

| Column Name | PostgreSQL Data Type | Source / Healthcare Context |
| :--- | :--- | :--- |
| `id` | `UUID` / `BIGINT` | Primary Key (Generated automatically) |
| `event_type` | `TEXT` | Core Analytical Dimension (e.g., `inbound_order`, `outbound_order`, `failed_login`) |
| `timestamp` | `TIMESTAMPTZ` | Temporal Anchor (Critical for time-series operational tracking) |
| `service` | `TEXT` | Source Service Identifier (e.g., `inventory_module`, `backoffice`) |
| `tags` | `JSONB` | Dynamic key-value context store (Preserves allowlist properties and domain context) |
| `user_id` | `TEXT` | HealthCore Clinical Staff / System Actor ID (Nullable) |
| `session_id`| `TEXT` | Active application session identifier (Nullable) |
| `environment`| `TEXT` | Runtime environment metadata (e.g., `us_clinic_prod`, `uk_clinic_prod`, `sandbox`) |

### Scale Optimization (Indexes)
To ensure the table remains highly queryable as millions of events stream in from all 12 multi-national clinics, three specific indexes must be built:
1.  **B-Tree Index** on `timestamp` (For temporal slicing, windowing, and population of real-time executive KPIs).
2.  **B-Tree Index** on `event_type` (For fast filtering on unique telemetry and system health anomalies).
3.  **GIN Index** on `tags` (Using `jsonb_path_ops` or standard GIN to allow lightning-fast nested searches inside specific clinic dimensions).

```sql
-- DDL Verification: 8-Column Target Table
CREATE TABLE telemetry_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    service TEXT NOT NULL,
    tags JSONB NOT NULL DEFAULT '{}'::jsonb,
    user_id TEXT,
    session_id TEXT,
    environment TEXT
);

-- Indexing for Scale & Cross-Border Slicing
CREATE INDEX idx_telemetry_events_timestamp ON telemetry_events (timestamp DESC);
CREATE INDEX idx_telemetry_events_type ON telemetry_events (event_type);
CREATE INDEX idx_telemetry_events_tags ON telemetry_events USING gin (tags);
```

---

## 2. API Contract & Handler Pipeline
*   **Endpoint**: `POST /telemetry/events` (Identical to the original Phase 1 stub).
*   **Frontend Constraints**: Zero modifications allowed. Payload structure remains unchanged.

### Data Ingestion Signature (Loose Envelope)
To prevent total batch rejection, the FastAPI router signature must explicitly bypass static array type hints for the data array:

```json
{
  "events": [
    { "event_type": "inbound_order", "timestamp": "2026-09-08T10:00:00Z", "service": "inventory_module", "tags": {"warehouse": "austin_hub"} },
    { "invalid_event_structure": true }
  ]
}
```

### Handler Processing Flow (Per-Event Partial Validation)
The controller must accept the envelope loosely and validate items iteratively:

1.  **Loose Type Acceptance**: Declare the input body with a generic dictionary or schema structure matching `{"events": list[dict]}`. Do **not** declare `events: list[TelemetryEvent]`. A static list structure would cause FastAPI to automatically reject the whole request body with a `422 Unprocessable Entity` error, dropping the entire telemetry window if a single payload row contains corrupt data.
2.  **Iterative Processing Loop**:
    *   Iterate through each raw dictionary item in the list inside a `try/except ValidationError` block.
    *   Execute `TelemetryEvent.model_validate(raw_item)` using the unchanged model contract from the previous project phase, **reusing it completely as-is without any structural updates**.
    *   **Success**: Add the validated item's flat properties and serialized keys to a target database-insertion list.
    *   **Failure**: Catch the validation exception, isolate the error, and increment a `rejected` count metrics counter without breaking or cancelling the batch loop.
3.  **Atomic Persistence**: Execute a **single bulk insert operation** per batch to database storage for all accumulated valid entities. Do not fire sequential row-by-row queries.
4.  **Response Object**: Return a status code `200 OK` with the exact telemetry footprint:
    ```json
    {
      "received": N,
      "stored": M,
      "rejected": R
    }
    ```
    *Where `N` is total received, `M` is successfully persisted, and `R` is rejected.*

### Client Compatibility Rule
*   The system response payload is backward-compatible with the frontend. The client-side `TelemetryService` **only evaluates the HTTP status code** (expecting a `2xx` series status to confirm pipeline flush) and does not read or parse the response body dictionary.

---

## 3. Phase 3 — End-to-End Verification Protocol

To verify the integration, the following three-step verification script must be executed manually:

### Step 3.1: Live Traffic Generation via Backoffice
Execute workflows in the frontend backoffice interface to trigger actual telemetry streams reflecting real HealthCore clinic activity:
*   **Business Flow 1 (Inbound)**: Register at least one inbound order in the system's inventory module (simulating clinic resource receiving).
*   **Business Flow 2 (Outbound)**: Register at least one outbound order in the system's inventory module (simulating medical supply deployment).
*   **Technical Flow**: Generate at least one technical event manually (e.g., triggering a failed user login attempt, routing to a broken resource path, or spawning a visible system error to verify automated health monitoring).

### Step 3.2: Direct Database Invariant Audit
Query the Supabase database directly using the SQL Editor or an API client to confirm record schema structural adherence:
```sql
SELECT event_type, timestamp, tags, service FROM telemetry_events ORDER BY timestamp DESC LIMIT 10;
```
*   **Verification Rule**: Ensure records are fully present and that values correctly sit inside individual columns, specifically inspecting that `event_type`, `timestamp`, and the nested keys within the `tags` JSONB object map perfectly to the telemetry layout configuration.
*   **Tag Integrity**: Stored JSON context objects must preserve structural allowlists and explicitly retain the **CONTEXT-specific dimensions** (such as `warehouse`, `office`, or clinic location parameters) mapped out in your project `telemetry-plan.md`.

### Step 3.3: Partial Validation Fault Injection Testing
Simulate an unstable payload batch using `curl` or an HTTP desktop client (e.g., Postman/Insomnia) to test partial error boundaries:

```bash
curl -X POST https://your-backend-url/telemetry/events \
  -H "Content-Type: application/json" \
  -d '{
    "events": [
      {
        "event_type": "inbound_order",
        "timestamp": "2026-09-08T14:15:00Z",
        "service": "inventory_module",
        "tags": {"warehouse": "london_clinic_1"}
      },
      {
        "event_type": "corrupted_telemetry_datum",
        "timestamp": "malformed-date-string-format",
        "service": "inventory_module",
        "tags": {}
      }
    ]
  }'
```
*   **Expected Behavior**: The API must return an HTTP status code `200 OK`. The body response dictionary must return exactly `{"received": 2, "stored": 1, "rejected": 1}`. Inspection of Supabase should confirm that only the `inbound_order` event row was written to storage.
