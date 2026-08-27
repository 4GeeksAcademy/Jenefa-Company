# Telemetry Specifications: HealthCore Technical Matrix

## 1. Golden Rule Framework
No event may exist in this telemetry specification unless it strictly satisfies the business validation sentence:
*"We capture **[event_type]** because we need to know **[hypothesis]**, which allows us to make the decision **[concrete decision]**."*

## 2. Complete Telemetry Event Registry

### Category A: Business & Patient Operations (Scheduling & EHR Integration)

#### 1. appointment_booked
*   **Classification:** Mandatory Baseline
*   **Operational Validation:** We capture `appointment_booked` because we need to know regional volume shifts and booking methods, which allows us to make the decision to reallocate clinical staff across US and UK locations to match consumer demand.
*   **Delivery Channel:** Batch (Processed hourly for historical patterns)
*   **Property Allowlist:**
    *   `location_id` (String, Required): Unique clinic index across the 12 locations.
    *   `region` (String, Required): Set explicitly to `US` or `UK`.
    *   `booking_channel` (String, Required): Enum values: `["phone", "front_desk", "online_portal"]`.
    *   `specialty_requested` (String, Required): Medical category matching clinician focus.

#### 2. appointment_noshow_predicted
*   **Classification:** Identified Opportunity
*   **Operational Validation:** We capture `appointment_noshow_predicted` because we need to know which appointments exhibit a high drop-off probability, which allows us to make the decision to trigger automated SMS/email reminders or execute manual standby calls to keep slots full.
*   **Delivery Channel:** Stream (Requires real-time alert trigger pipeline)
*   **Property Allowlist:**
    *   `location_id` (String, Required): Clinic location marker.
    *   `calculated_risk_score` (Number, Required): Floating value between `0.00` and `1.00`.
    *   `lead_time_days` (Integer, Required): Days remaining before the scheduled encounter slot.
    *   `risk_factors` (Array of Strings, Optional): Anonymized flags indicating predictive variables.

---

### Category B: Revenue Cycle Management & Billing

#### 3. billing_claim_compiled
*   **Classification:** Mandatory Baseline
*   **Operational Validation:** We capture `billing_claim_compiled` because we need to track insurance coding distributions and error flags before dispatch, which allows us to make the decision to flag and hold high-risk US claims before submission to lower the 14% denial rate.
*   **Delivery Channel:** Stream (Enables preventative real-time pre-screening)
*   **Property Allowlist:**
    *   `claim_id` (String, Required): Unique reference key.
    *   `region` (String, Required): Fixed to `US` or `UK`.
    *   `payer_type` (String, Required): Enum values: `["commercial", "medicare", "medicaid", "private_pay", "nhs_contract"]`.
    *   `coding_standard` (String, Required): Identifier flag (e.g., `ICD-10-CM`).
    *   `pre_check_denial_risk` (Number, Required): AI-calculated rejection risk value.

#### 4. revenue_stream_reconciled
*   **Classification:** Identified Opportunity
*   **Operational Validation:** We capture `revenue_stream_reconciled` because we need to unify financial collection rates across scattered pipelines, which allows us to make the decision to adjust pricing structures or renegotiate underperforming insurance/NHS contracts directly.
*   **Delivery Channel:** Batch (Processed daily for financial ledger updates)
*   **Property Allowlist:**
    *   `reconciliation_id` (String, Required): Unique balance log key.
    *   `currency` (String, Required): Set to `USD` or `GBP`.
    *   `gross_amount` (Number, Required): Total value tracked before adjustments.
    *   `net_settled_amount` (Number, Required): Verified revenue collected.

---

### Category C: Compliance, Data Governance & System Health

#### 5. patient_data_accessed
*   **Classification:** Mandatory Baseline
*   **Operational Validation:** We capture `patient_data_accessed` because we need a unified cross-border log of who views protected health info, which allows us to make the decision to terminate unauthorized permissions and present clean audit records to HIPAA and UK GDPR inspectors.
*   **Delivery Channel:** Stream (Critical compliance security requirement)
*   **Property Allowlist:**
    *   `ehr_source` (String, Required): Enum values: `["us_ehr_platform", "uk_ehr_platform"]`.
    *   `accessing_role` (String, Required): Clinician, Admin, Billing Agent, or System Service.
    *   `jurisdiction` (String, Required): Set explicitly to `HIPAA` or `GDPR`.
    *   `anonymized_patient_token` (String, Required): Masked cross-region patient hash.

#### 6. system_health_checked
*   **Classification:** Identified Opportunity
*   **Operational Validation:** We capture `system_health_checked` because we need to actively map the operational status of legacy endpoints and spreadsheets, which allows us to make the decision to deploy technical hotfixes before clinics report outages.
*   **Delivery Channel:** Stream (Ensures real-time uptime monitoring)
*   **Property Allowlist:**
    *   `target_subsystem` (String, Required): Target service (e.g., `us_billing_api`, `uk_booking_sheet`).
    *   `status_state` (String, Required): Enum values: `["healthy", "degraded", "unreachable"]`.
    *   `latency_ms` (Integer, Required): Connection response latency in milliseconds.

---

### Category D: UI Usability & Navigation Flows

#### 7. clinical_documentation_abandoned
*   **Classification:** Identified Opportunity
*   **Operational Validation:** We capture `clinical_documentation_abandoned` because we need to pinpoint friction points within clinical entry software, which allows us to make the decision to deploy AI transcription assistance to reclaim the 35 minutes lost daily to admin tasks.
*   **Delivery Channel:** Batch (Processed daily to analyze application usability)
*   **Property Allowlist:**
    *   `screen_view_id` (String, Required): Structural identifier of the interface segment.
    *   `time_spent_seconds` (Integer, Required): Cumulative duration prior to exit events.
    *   `character_count` (Integer, Required): Volume of field text provided before exit.

#### 8. client_navigation_tracked
*   **Classification:** Identified Opportunity
*   **Operational Validation:** We capture `client_navigation_tracked` because we need to observe layout drop-offs within onboarding and scheduling workflows, which allows us to make the decision to simplify multi-page systems into single-screen interactions.
*   **Delivery Channel:** Batch (Collected periodically for trend analysis)
*   **Property Allowlist:**
    *   `origin_route` (String, Required): Current active route path string.
    *   `destination_route` (String, Required): Intended forward-facing route path string.
    *   `user_type` (String, Required): Enum values: `["patient", "clinical_staff", "operations_staff"]`.

## 3. PII, Privacy & Data Sanitization Strategy
Handling Protected Health Information (PHI) under HIPAA and personal data under UK GDPR requires non-negotiable security boundaries.

*   **Identifiable Medical Entities:** Explicit diagnostic tags, physical clinic notes, raw names, and insurance claim strings are barred from the properties block.
*   **Cryptographic Masking:** Global IDs (like Patient Keys) are scrubbed and replaced with one-way salted SHA-256 hashes generated at the application border before event emission.
*   **String Scrubbing:** System log dumps pass through strict regex filters to strip medical record parameters or unhashed credential fields before storage.

## 4. Discarded Events & Technical Trade-offs
*   **`audio_dictation_stream_sampled` (Discarded):** Considered for AI clinical documentation capture. Discarded due to extreme cloud storage costs and the high legal risks of inadvertently persisting unencrypted patient audio strings.
*   **`mouse_movement_sampled` (Discarded):** Considered for fine-grained interface interaction tracking. Discarded because it creates massive payload volumes that waste client bandwidth and network throughput without providing actionable business value.
