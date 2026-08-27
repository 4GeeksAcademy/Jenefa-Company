# Product Context: HealthCore Central Telemetry Framework

## 1. Domain & Business Landscape
HealthCore is an outpatient healthcare services provider operating a cross-border network of 12 clinics: 9 in the United States (Texas, Florida, Georgia) and 3 in the United Kingdom (London, Manchester). The operational estate is highly fragmented, presenting major data-visibility blocks across distinct revenue streams, scheduling workflows, and Electronic Health Record (EHR) platforms. 

### System Constraints & Core Challenges
*   **Split Record Architecture:** Two different, non-communicating EHR systems isolate US and UK clinical workflows.
*   **Operational Inefficiencies:** High appointment no-show rates (22% network-wide) cause $1.8 million in annual losses.
*   **Revenue Leakage:** A 14% commercial claims denial rate in the US (double the industry average) due to manual entries and inconsistent coding practices.
*   **Compliance Fragmentation:** Strict regulatory requirements under US HIPAA and UK GDPR necessitate definitive access logging and cross-border audit segregation.

## 2. Standardized Event Envelope Contract
Every telemetry payload emitted across the HealthCore application layers must wrap its business-specific attributes inside this standard execution wrapper. No untracked metadata keys are permitted.

| Field Name | Primitive Type | Nullability | Description / Validation Rule |
| :--- | :--- | :--- | :--- |
| `eventId` | String | Non-Null | Unique identifier generated as a canonical UUIDv4 string. |
| `timestamp` | String | Non-Null | Combined date-time formatted strictly to the ISO 8601 standard (`YYYY-MM-DDTHH:mm:ss.sssZ`). |
| `sessionId` | String | Non-Null | Unique identifier tracing a single user interaction session context. |
| `userId` | String | Nullable | Identity code of the authenticated operator or patient; null if unauthenticated. |
| `event_type` | String | Non-Null | Taxonomic label mapped strictly inside lowercase `entity_action` format. |
| `schemaVersion`| String | Non-Null | Semantic version tag specifying payload schema structure (e.g., `1.0.0`). |
| `requestId` | String | Non-Null | Unique trace token matching API logs across distributed services. |
| `properties` | Object | Non-Null | Nested dictionary holding specific allowlisted payload metrics. |

## 3. Real-Time vs. Batch Delivery Matrix
To protect data layer efficiency, event distribution streams are segregated by operational decision urgency, rather than simple technical convenience.

┌────────────────────────────────────────────────────────────────────────┐│                        HEALTHCORE EVENT ROUTER                         │└───────────────────────────────────┬────────────────────────────────────┘│Is the data critical for compliance,immediate revenue loss, or core safety?│┌─────────────────┴─────────────────┐▼ YES                               ▼ NO┌──────────────────────┐            ┌──────────────────────┐│   STREAMING ROUTE    │            │     BATCH ROUTE      ││ (Real-Time Ingest)   │            │ (Periodic Windows)   │└──────────┬───────────┘            └──────────┬───────────┘│                                   │• Data Leak/Audit Safety            • Operational Reporting• Clinical Dropouts                 • Staff Admin Tracking• Direct Security Failure           • Routine UI Navigation
*   **Streaming Route (Real-Time Processing):** Reserved for events feeding instant risk mitigations, automated compliance alerts, security exceptions, or interactive scheduling interfaces.
*   **Batch Route (Periodic Processing):** Reserved for operational reporting metrics, background tasks, and general screen navigation tracking that inform retrospective executive dashboards.

## 4. High-Frequency Client Traffic Controls
*   **Debouncing (300ms window):** Applied to UI navigation steps, layout transitions, and interactive patient dashboard lookups to eliminate network thrashing.
*   **Throttling (1000ms ceiling):** Applied to error-capture systems, retry attempts, and automated health checks to prevent execution loops from degrading database performance.