# Product Context: HealthCore Engineering Operational Radar

## 1. Product Vision & Intent
This document defines the scope and purpose of the engineering telemetry reporting pipeline created by **HealthCore Digital**. HealthCore operates a cross-border network of **12 clinics** across the United States and the United Kingdom. The company's underlying tech estate is a highly fragmented patchwork of disparate legacy systems (including two distinct, non-communicating Electronic Health Record platforms, separate localized billing frameworks, and manual booking diaries) without a shared data layer. 

Historically, when a critical system failed, the technology team only found out after an affected clinic called to report the outage. This project acts as an immediate **technical operational radar** to provide real-time visibility into the system's infrastructure health, response velocity, and transactional failure rates across all 12 locations.

This is strictly a technical stability asset for the engineering team. It explicitly excludes executive business reporting metrics (e.g., patient appointment no-show rates, insurance claim denial percentages, or location-based revenue collection). Business intelligence pipelines are out of scope and belong to subsequent milestones. Every returned metric must incorporate a meaningful **grouping dimension** (e.g., separating trends by region, event type, or endpoint) to ensure operational actionability.

## 2. Core Personas
* **James Osei (CTO) & The Austin Core Team:** Reviewing cross-border service up-time, data sync latencies between US/UK databases, and localized API performance.
* **HealthCore Platform Engineers:** Monitoring exception distributions and isolating failure vectors before they disrupt clinic workflows.
* **Compliance & Data Officers (Claire Whitfield's Team):** Validating platform performance under strict, isolated regional constraints to guarantee audit trail continuity for HIPAA (US) and UK GDPR compliance frameworks.

## 3. Scope Boundaries & Constraints
* **Operational Over Business:** This tool strictly focuses on technical dimensions defined inside the event catalogue (`telemetry-plan.md`). Commercial funnel tracks are entirely out of scope.
* **Contextualized Dimensions:** Metrics must always answer questions about system behavior (volume trends, latent processing pathways, or failure rates) mapped against a clear grouping key (by date, endpoint, or error type).
* **Performance Boundary:** Ingestion tracking must not introduce internal infrastructure degradation. To prevent database exhaustion from duplicate telemetry calculations, high-frequency requests are completely isolated by a hard temporal cache.

## 4. Pre-requisites & Verification
Before executing or deploying this operational reporting system, engineers must complete the following infrastructure validation steps:
1. **Supabase Ingestion Check:** Connect to the Supabase instance and confirm that the `telemetry_events` table contains **at least 20 rows** exhibiting a distinct variety of `event_type` records.
2. **Backoffice Stimulation:** If the environment lacks sufficient records or fails to show systemic variety, engineers must trigger dummy activity in the project backoffice first—ensuring **at least one technical error event** is simulated to accurately test error pipeline capture.
3. **Event Catalogue Alignment:** Review the strict parameters within `telemetry-plan.md`. Today's pipeline targets the operational fields (`latency`, `is_error`, specific tag fields like `endpoint`) instead of user-focused metadata.
