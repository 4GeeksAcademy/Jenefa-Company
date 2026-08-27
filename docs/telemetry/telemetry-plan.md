# Telemetry Plan: HealthCore Central Infrastructure
**Document Version:** 1.0.0  
**Target Architecture:** Cross-Border Outpatient Network (US & UK)  
**Author:** HealthCore Digital Unit  

---

## 1. Product Context & Strategic Alignment

### 1.1 Domain & Business Landscape
HealthCore operates a network of 12 outpatient clinics: 9 in the United States (Texas, Florida, Georgia) and 3 in the United Kingdom (London, Manchester). The clinical estate is highly fragmented, generating siloed workflows, disparate record keeping, and critical blind spots for executive leadership.

### 1.2 Identified System Vulnerabilities
*   **Siloed Systems:** US and UK clinics run on separate Electronic Health Record (EHR) platforms that cannot communicate. 
*   **Operational Leakage:** The network experiences a persistent 22% patient no-show rate, causing approximately $1.8 million in annual revenue losses.
*   **Revenue Denial:** Inconsistent coding and manual processes drive a 14% commercial claims denial rate in the US Market—more than double the industry average.
*   **Compliance Risks:** Independent data stores lack centralized audit logging, complicating strict statutory reporting required under US HIPAA and UK GDPR.

### 1.3 High-Frequency Client Traffic Controls
To prevent client telemetry loops from overwhelming ingestion servers, downstream collection pipelines enforce specific client-side ingestion thresholds:
*   **Debouncing (300ms window):** Applied to UI navigation steps, layout transitions, and interactive patient dashboard lookups to filter out interface click-thrashing.
*   **Throttling (1000ms ceiling):** Enforced on technical telemetry streams, automated endpoint health checks, and caught system errors to block cascading loop failures.

---

## 2. Standardized Event Envelope Contract

Every log, pixel trigger, or API trace emitted across the application layer must conform to the unified envelope contract below. Properties outside this baseline definition are blocked at the ingestion gateway.

| Field Name | Primitive Type | Nullability | Description / Validation Rule |
| :--- | :--- | :--- | :--- |
| `eventId` | String | Non-Null | Unique identifier generated as a canonical UUIDv4 string. |
| `timestamp` | String | Non-Null | Combined date-time formatted strictly to the ISO 8601 standard (`YYYY-MM-DDTHH:mm:ss.sssZ`). |
| `sessionId` | String | Non-Null | Unique session trace string tracking a single user interaction lifecycle. |
| `userId` | String | Nullable | Internal database primary key of the authenticated operator; null for anonymous actions. |
| `event_type` | String | Non-Null | Taxonomic label mapped strictly inside lowercase `entity_action` format. |
| `schemaVersion`| String | Non-Null | Semantic version tag specifying payload schema structure (e.g., `1.0.0`). |
| `requestId` | String | Non-Null | Unique HTTP request token linking client triggers to backend application logs. |
| `properties` | Object | Non-Null | Nested dictionary holding specific allowlisted payload metrics. |

---

## 3. Real-Time vs. Batch Delivery Matrix

Data distribution modes are determined entirely by the operational urgency of the business decision they fuel, rather than engineering preference.

────────────────┐│                        HEALTHCORE EVENT ROUTER                         │└───────────────────────────────────┬────────────────────────────────────┘│Is the data critical for compliance,immediate revenue loss, or core safety?│┌─────────────────┴─────────────────┐▼ YES                               ▼ NO┌──────────────────────┐            ┌──────────────────────┐│   STREAMING ROUTE    │            │     BATCH ROUTE      ││ (Real-Time Ingest)   │            │ (Periodic Windows)   │└──────────┬───────────┘            └──────────┬───────────┘│                                   │• Data Leak/Audit Safety            • Operational Reporting• Clinical Dropouts                 • Staff Admin Tracking• Direct Security Failure           • Routine UI Navigation

*   **Streaming Route (Real-Time Processing):** Reserved for real-time risk scoring, compliance logging, security breaches, and interactive scheduling interfaces.
*   **Batch Route (Periodic Processing):** Reserved for asynchronous updates, administrative tasks, and navigational flows destined for retrospective analysis on executive reporting dashboards.

---

## 4. Golden Rule Telemetry Event Registry

Every event tracked must satisfy the strict validation sentence: 
*"We capture **[event_type]** because we need to know **[hypothesis]**, which allows us to make the decision **[concrete decision]**."*

### Category A: Patient Access & Clinical Operations

#### 1. appointment_booked
*   **Classification:** Mandatory Baseline
*   **Operational Validation:** We capture `appointment_booked` because we need to know regional volume shifts and booking channels, which allows us to make the decision to reallocate clinical staff across US and UK locations to match consumer demand.
*   **Delivery Mode:** Batch (Processed hourly for trend analysis)
*   **Property Allowlist:**
    ```json
    {
      "location_id": "String (Required) - Unique clinic index across the 12 locations",
      "region": "String (Required) - Enum value: ['US', 'UK']",
      "booking_channel": "String (Required) - Enum value: ['phone', 'front_desk', 'online_portal']",
      "specialty_requested": "String (Required) - Medical category matching clinic focus"
    }
    ```

#### 2. appointment_noshow_predicted
*   **Classification:** Identified Opportunity
*   **Operational Validation:** We capture `appointment_noshow_predicted` because we need to know which upcoming appointments exhibit a high drop-off probability, which allows us to make the decision to trigger automated SMS/email reminders or execute manual standby calls to keep slots full.
*   **Delivery Mode:** Stream (Real-time message broker ingest)
*   **Property Allowlist:**
    ```json
    {
      "location_id": "String (Required) - Clinic location marker",
      "calculated_risk_score": "Number (Required) - Floating value between 0.00 and 1.00",
      "lead_time_days": "Integer (Required) - Days remaining before the scheduled encounter",
      "risk_factors": "Array of Strings (Optional) - Anonymized flags indicating predictive variables"
    }
    ```

---

### Category B: Revenue Cycle Management & Billing

#### 3. billing_claim_compiled
*   **Classification:** Mandatory Baseline
*   **Operational Validation:** We capture `billing_claim_compiled` because we need to track insurance coding distributions and error flags before dispatch, which allows us to make the decision to flag and hold high-risk US claims before submission to lower the 14% denial rate.
*   **Delivery Mode:** Stream (Real-time screening before submission)
*   **Property Allowlist:**
    ```json
    {
      "claim_id": "String (Required) - Unique reference key",
      "region": "String (Required) - Enum value: ['US', 'UK']",
      "payer_type": "String (Required) - Enum value: ['commercial', 'medicare', 'medicaid', 'private_pay', 'nhs_contract']",
      "coding_standard": "String (Required) - Identifier tag (e.g., 'ICD-10-CM')",
      "pre_check_denial_risk": "Number (Required) - AI-calculated rejection risk value"
    }
    ```

#### 4. revenue_stream_reconciled
*   **Classification:** Identified Opportunity
*   **Operational Validation:** We capture `revenue_stream_reconciled` because we need to unify financial collection rates across scattered pipelines, which allows us to make the decision to adjust pricing structures or renegotiate underperforming insurance/NHS contracts directly.
*   **Delivery Mode:** Batch (Processed daily for financial ledger updates)
*   **Property Allowlist:**
    ```json
    {
      "reconciliation_id": "String (Required) - Unique balance log key",
      "currency": "String (Required) - Enum value: ['USD', 'GBP']",
      "gross_amount": "Number (Required) - Total value tracked before adjustments",
      "net_settled_amount": "Number (Required) - Verified revenue collected"
    }
    ```

---

### Category C: Compliance, Security & System Health

#### 5. patient_data_accessed
*   **Classification:** Mandatory Baseline
*   **Operational Validation:** We capture `patient_data_accessed` because we need a unified cross-border log of who views protected health info, which allows us to make the decision to terminate unauthorized permissions and present clean audit records to HIPAA and UK GDPR inspectors.
*   **Delivery Mode:** Stream (Immediate write to immutable compliance log)
*   **Property Allowlist:**
    ```json
    {
      "ehr_source": "String (Required) - Enum value: ['us_ehr_platform', 'uk_ehr_platform']",
      "accessing_role": "String (Required) - Role (e.g., 'Clinician', 'Billing Agent')",
      "jurisdiction": "String (Required) - Enum value: ['HIPAA', 'GDPR']",
      "anonymized_patient_token": "String (Required) - Masked cross-region patient hash"
    }
    ```

#### 6. system_health_checked
*   **Classification:** Identified Opportunity
*   **Operational Validation:** We capture `system_health_checked` because we need to actively map the operational status of legacy endpoints and spreadsheets, which allows us to make the decision to deploy technical hotfixes before clinics report outages.
*   **Delivery Mode:** Stream (Ensures real-time uptime monitoring)
*   **Property Allowlist:**
    ```json
    {
      "target_subsystem": "String (Required) - Target service (e.g., 'us_billing_api', 'uk_booking_sheet')",
      "status_state": "String (Required) - Enum value: ['healthy', 'degraded', 'unreachable']",
      "latency_ms": "Integer (Required) - Connection response latency in milliseconds"
    }
    ```

---

### Category D: Usability & Application Navigation

#### 7. clinical_documentation_abandoned
*   **Classification:** Identified Opportunity
*   **Operational Validation:** We capture `clinical_documentation_abandoned` because we need to pinpoint friction points within clinical entry software, which allows us to make the decision to deploy AI transcription assistance to reclaim the 35 minutes lost daily to admin tasks.
*   **Delivery Mode:** Batch (Processed daily for interface optimization analysis)
*   **Property Allowlist:**
    ```json
    {
      "screen_view_id": "String (Required) - Structural identifier of the interface segment",
      "time_spent_seconds": "Integer (Required) - Cumulative duration prior to exit events",
      "character_count": "Integer (Required) - Volume of field text provided before exit"
    }
    ```

#### 8. client_navigation_tracked
*   **Classification:** Identified Opportunity
*   **Operational Validation:** We capture `client_navigation_tracked` because we need to observe layout drop-offs within onboarding and scheduling workflows, which allows us to make the decision to simplify multi-page systems into single-screen interactions.
*   **Delivery Mode:** Batch (Collected periodically for trend analysis)
*   **Property Allowlist:**
    ```json
    {
      "origin_route": "String (Required) - Current active route path string",
      "destination_route": "String (Required) - Intended forward-facing route path string",
      "user_type": "String (Required) - Enum value: ['patient', 'clinical_staff', 'operations_staff']"
    }
    ```

---

## 5. Privacy, PII Sanitization & Data Protection

Because HealthCore handles highly sensitive Protected Health Information (PHI) and Personal Data across statutory boundaries, strict compliance processing is applied at the application boundary prior to emission.

*   **Zero PHI Injection:** Free-text clinical notes, exact diagnostic strings, names, and explicit prescription records are fundamentally barred from entering the tracking payload.
*   **Cryptographic Obfuscation:** Direct personal keys (such as Patient IDs or National Insurance numbers) are completely stripped and replaced with one-way salted SHA-256 tokens generated at the application border.
*   **Log Interception Filters:** Error payloads and stack traces pass through strict automated regex filtering blocks to clean out accidental inputs like password characters, billing variables, or session cookies before payload compilation.

---

## 6. Discarded Candidate Events & Risk Analysis

To safeguard computational resources and network limits, several candidate indicators were systematically reviewed and excluded:

*   **`audio_dictation_stream_sampled` (Discarded):** Proposed to monitor clinical note dictation helper tools. Discarded due to high transmission overhead and severe legal liabilities linked to transmitting or caching raw voice patterns across geographic borders.
*   **`mouse_movement_sampled` (Discarded):** Proposed to map clinic operator user fatigue. Discarded because it generates massive, low-value datasets that degrade browser network buffers without answering clear business hypotheses.
*   **`patient_billing_card_entered` (Discarded):** Proposed to analyze payment submission speed. Discarded to completely isolate the telemetry infrastructure from PCI-DSS audit surfaces and credit handling frameworks.
