# Product Context: Productionizing HealthCore Telemetry & Business KPIs

## 1. Executive Summary & Problem Context
HealthCore has expanded into a cross-border healthcare network operating **12 clinics** across the United States and the United Kingdom, generating **$28 million in annual revenue** and employing **200 staff members**. However, our underlying software infrastructure has fractured into isolated silos.

Currently, US clinics run on a legacy EHR platform and a phone-based scheduler, while UK clinics operate on an completely independent EHR framework with manual booking diaries. This technical debt leaves our Chief Executive Officer, **Dr. Sandra Okonkwo**, unable to answer basic operational questions—such as determining the network-wide appointment no-show rate or pinpointing billing denial peaks—without making manual phone calls to regional branch managers. 

To bridge this operational gap, **HealthCore Digital** is productionizing our telemetry and business data pipelines. We are transforming our prototype into an enterprise-grade orchestration system that aggregates cross-border events into structured, actionable business intelligence.

## 2. Business Realities & Operational Targets
This release directly targets three severe financial and administrative leaks identified across our clinical network:
* **The Patient Experience Leak:** HealthCore suffers from a **22% appointment no-show rate** across jurisdictions, resulting in **$1.8 million in lost annual revenue**. 
* **The Revenue Cycle Leak:** Inconsistent manual coding has driven our **US claims denial rate to 14%**, more than double the standard healthcare industry benchmark of 5-8%.
* **The Clinical Operations Leak:** Due to disconnected local platforms, healthcare providers waste an average of **35 minutes per day on manual documentation tasks** instead of delivering care.

## 3. Core Architectural & Product Principles

### Unified Domain Vocabulary
To eliminate contradictions across weekly departmental reporting streams, **generic engineering labels are strictly banned**. Every data field, Prefect orchestration subflow, and automated test suite must mirror HealthCore's true business taxonomy (e.g., `network_appointment_no_show_rate`, `us_commercial_claims_denial_rate`). System logic must natively partition metrics between `market_us` and `market_uk` compliance scopes.

### Safe Cross-Border Data Orchestration
Operating across distinct legal jurisdictions requires strict compliance boundaries. Because our software processes Protected Health Information (PHI), all automated pipelines must protect data integrity across **HIPAA** (United States) and **UK GDPR** (United Kingdom) privacy boundaries. By utilizing Prefect 3 to separate extraction from core mathematical transformations, we ensure our pipelines are structured, auditable, and resilient.

### Quality Assurance as a Production Gatekeeper
Silent data corruptions within medical billing schemas or scheduling tables can lead to catastrophic compliance breaks or millions in uncollected claims. Our product context demands that no pipeline deployment reaches production without passing a hermetic testing matrix inside `tests/pipelines/test_pipeline.py`. These tests validate mathematical assertions and verify defensive task behavior against malformed data inputs.

### Zero-Friction Leadership Visibility
The ultimate metric of success for this pipeline is executive utility. The data pipeline exposes its processed metrics via the secure `services/reporting/` API layer directly into a clean, human-readable backoffice interface located at `uis/backoffice/reporting/`. 

This interface is explicitly tailored for **Dr. Sandra Okonkwo** and her executive leadership team, delivering immediate, translation-free visibility into weekly clinic performance, financial collection metrics, and cross-border volume tracking.

## 4. Scope & Final Deliverables
* **Orchestration Engine:** A production-grade `data/pipelines/pipeline.py` script running on Prefect 3 that coordinates decoupled data fetching, metric transformation, and database loading.
* **CLI Integrity:** Complete preservation of the terminal invocation command for operations personnel.
* **Data Protection Test Suite:** Hermetic automated validation tests verifying mathematical tracking precision and error handling for malformed payloads.
* **Executive Backoffice Dashboard:** An intuitive reporting interface that visualizes regional KPI distributions over a weekly tracking cadence.
