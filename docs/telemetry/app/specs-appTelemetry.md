# Technical Specification: Telemetry Tracking Pipeline (HealthCore)

## 1. Backend Ingestion: Phase 1 Stub Endpoint (FastAPI)

### 1.1 Routing & Architectural Standards
- **Endpoint:** `POST /telemetry/events`
- **Location:** Managed within an isolated router module nested inside `services/`.
- **Environment Management:** The backend must explicitly read from and declare `TELEMETRY_ENDPOINT` in its environment setup to anchor the route pattern from day one.

### 1.2 Data Transfer Objects (Pydantic Schema)
The `TelemetryEvent` model implements standard tracking envelopes matching the validated structural design from Phase 1.

```python
from pydantic import BaseModel, Field
from typing import Dict, Any, List
from datetime import datetime

class TelemetryEvent(BaseModel):
    eventId: str = Field(..., description="Unique event identifier UUID")
    timestamp: datetime = Field(..., description="ISO-8601 formatted event occurrence timestamp")
    sessionId: str = Field(..., description="Client session identifier token")
    userId: str = Field(..., description="Authenticated clinic staff/user unique account key")
    event_type: str = Field(..., description="Taxonomic domain category string matching HealthCore workflows")
    schemaVersion: str = Field(..., description="Semantic version tracker tracking tracking schema shifts")
    requestId: str = Field(..., description="Server tracking parameter for tracing request lifecycles")
    properties: Dict[str, Any] = Field(..., description="Metadata container for context payload maps")

class TelemetryBatchRequest(BaseModel):
    events: List[TelemetryEvent] = Field(..., description="Array batch containing individual telemetry signals")
```

### 1.3 Behavioral Lifecycle
1. Accept incoming HTTP POST payloads matching the structured `TelemetryBatchRequest` schema shape.
2. Extract the payload array, logging total batch sizes and checking individual `event_type` strings.
3. Return an immediate HTTP `200 OK` with format: `{"received": N}` where N is the total parsed count. No storage or database writes are performed.


## 2. Frontend Client: Phase 2 TelemetryService (TypeScript)

### 2.1 File Location & Configuration
- **Path Target:** Built inside `uis/backoffice/src/services/telemetry.ts`.
- **Environment Resolution:** The destination target must be dynamically evaluated from `NEXT_PUBLIC_TELEMETRY_ENDPOINT`. Hardcoding is prohibited.
- **Local Configurations:** Root `.env.local` files must configure `NEXT_PUBLIC_TELEMETRY_ENDPOINT=http://localhost:8000/telemetry/events` to ensure offline developer parity.

### 2.2 Core Infrastructure Mechanisms
- **Local In-Memory Queue:** Employs an internal memory array to hold tracking records. Events are never sent one-by-one.
- **Batch & Debounce Lifecycle:** Dispatches queue payloads to the endpoint address when either of these thresholds is crossed:
  - Every **10 seconds**, OR
  - As soon as the queue hits **20 events**.
- **Exact Capture Timestamps:** The `timestamp` property must record the client-side execution time when the action occurs, not the post-debounce delivery time.
- **Reliable Tab-Close Flushing:** Hooks into browser `visibilitychange` events to pass pending array elements via `navigator.sendBeacon` when a clinic terminal is hidden or shut down.
- **Network Resilience:** Implements up to **3 transmission attempts** driven by an exponential backoff loop before dropping the batch. Telemetry processing must never block backoffice workflows.

### 2.3 Automatic Metadata Enrichment
The core service must auto-populate envelope metadata keys at runtime. Consumer modules or UI tracking hooks must never provide these parameters manually:
- `eventId` (UUID generated at exact capture time)
- `sessionId` (retrieved from system session storage memory)
- `userId` (derived from active identity authentication profile tokens)
- `timestamp` (ISO-8601 string calculated precisely at event snapshot time)
- `schemaVersion` (derived from a static application code constant)
- `requestId` (correlation tracking hash value)

### 2.4 Exposed Public Interface API
```typescript
export function track(
  eventType: string, 
  properties: Record<string, unknown>
): void;
```
*Architecture Rule:* All interface event tracking must pass through this singular `track()` signature. Direct usage of `fetch` or `axios` to target telemetry routes is strictly forbidden.


## 3. Global Instrumentation & Activity: Phase 3

### 3.1 Strict Schema Compliance Guardrails
- **Ground Truth Mapping:** Every single `event_type` name and `properties` map key must match the vocabulary rules of `docs/telemetry/event-schemas.json` and cross-referenced with HealthCore's operational domain parameters in `CONTEXT-company.md`.
- **Dictionary Allowlist Enforcement:** Property maps must strictly align with schemas. Speculative padding or adding columns "just in case" is forbidden.
- **Instrumentation Priority Strategy:** Technical leads require balanced tracking coverage across multiple operational domains over raw feature depth. Broad tracking must span across both infrastructure stability metrics and backoffice business events.
- **Implementation Sequence:** Strict enforcement of the phase order workflow: Stub Endpoint -> Centralized TelemetryService -> Component Instrumentation. No tracking markers may be added to UI files until the underlying service layer is fully complete.

### 3.2 Cross-Cutting Technical Instrumentation Baseline
A global technical health monitoring pattern must apply across the entire application workspace, independent of specific medical business modules:
- **Uncaught Errors:** Bind monitoring hooks to `window.onerror`, unhandled promise failures (`unhandledrejection`), and root interface Error Boundaries to ensure the Austin dev team knows about failures instantly.
- **Performance Diagnostics:** Capture underlying platform latency by logging page load durations or network call execution delays on core EHR synchronization API wrappers.
- **User Navigation Flow:** Instrument automatic page view event indicators covering the main navigation layouts of the clinic backoffice workspace.

### 3.3 Performance and Web Vitals Instrumentation
- **Metric Collection:** Implement core performance telemetry via Next.js `reportWebVitals` (or framework-agnostic equivalents).
- **Payload Schema:** Emit Web Vitals metrics as standard events, adding the current frontend **route or page string context** directly into the event's `properties` payload block.

### 3.4 Centralized Security & Authentication Instrumentation
Capture authentication events (failed login attempts, session expiries) globally inside localized authentication hooks or dedicated route middleware. Do not write tracking logic inside individual page files.
- **Failed Login Payload Guardrails:** Record login failures inside the `properties` block using these exact tokens to assist security monitoring:
  - `invalid_credentials`
  - `session_expired`
  - `network_error`
- **Data Privacy Blacklist (PII/PHI Guard):** Grounded in HIPAA and UK GDPR requirements, **no telemetry event may capture PII or PHI**. Payload properties must never store user/patient names, cleartext email addresses, passwords, or descriptive medical notes.

### 3.5 Evaluation & Grading Checkpoints
1. Verify the active backend `POST /telemetry/events` route handles payload arrays matching the `TelemetryEvent` configuration structure.
2. Confirm the processing pipeline yields exactly `{ "received": N }` showing correct integer processing totals.
3. Validate via browser Developer Tools (Network layer tab) that outbound JSON batch requests are packed correctly, avoid redundant endpoints, and secure an HTTP `200 OK` from the server stub.