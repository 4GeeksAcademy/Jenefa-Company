# Technical Specifications: HealthCore Telemetry & Business KPI Pipelines (Part 3)

## 1. Directory Structure & File Artifacts
All modules, scripts, and validation profiles must map strictly to the primary HealthCore monorepo layout. 
* **Main Data Pipeline Entrypoint:** `data/pipelines/pipeline.py`
* **HealthCore Metric Transformation Logic:** `data/process/`
* **Ingestion Layer Data Source:** `data/raw/` (Contains raw `telemetry_events` and historical clinic logs)
* **Quality Assurance Outputs & Audits:** `data/eval/`
* **Isolated Testing Framework:** `tests/pipelines/test_pipeline.py`
* **Executive Backoffice Dashboard UI:** `uis/backoffice/reporting/`

## 2. Protected Systems & Core Dependencies
* **Orchestration Framework:** Prefect 3 engine layer pinned explicitly via `uv add "prefect>=3"`.
* **Immutable Layers:** The base `telemetry_events` event schema and the analytical engine inside `services/telemetry/analysis.py` must remain completely unmodified throughout this architecture split.

## 3. Workflow Orchestration & HealthCore Subflow Topology
The central flow inside `data/pipelines/pipeline.py` must coordinate at least **three distinct subflows** (decorated with `@flow`) executing sequentially. To maintain system boundaries, subflows must explicitly pass parameters and return payload states without relying on global script variables.

┌────────────────────────────────────────────────────────┐│             HealthCore Main Orchestrator Flow          ││       (data/pipelines/pipeline.py Entrypoint)          │└──────────────────────────┬─────────────────────────────┘│┌─────────────────┼─────────────────┐▼                 ▼                 ▼┌─────────────────┐ ┌───────────────┐ ┌──────────────┐│ Fetch Network   │ │ Compute Executive│ │ Load Central ││ Telemetry Flow  │ │ KPI Matrix Flow│ │ Reporting DB ││   (@flow)       │ │   (@flow)     │ │   (@flow)    │└─────────────────┘ └───────────────┘ └──────────────┘
### Subflow Component Breakdown
1. **Extraction Subflow (`fetch_network_telemetry_flow`):** Connects to `telemetry_events` to stream clinical actions, scheduling records, and billing actions across all 12 clinics (US and UK markets).
2. **Transformation Subflow (`compute_executive_kpi_matrix_flow`):** Coordinates individual `@task` processes to calculate the specific performance metrics demanded by Dr. Sandra Okonkwo.
3. **Load Subflow (`load_central_reporting_db_flow`):** Commits the computed metrics safely into the production destination tables to back the reporting microservice.
4. **Secondary Branch Execution:** Optional operations (such as automated compliance escalation alerts to Claire Whitfield or real-time pipeline telemetry alerts to James Osei) must run as detached subflows using `return_state=True`.

## 4. Strict Domain Nomenclature & Taxonomy
Generic placeholder functions are strictly prohibited. Every subflow, task, data column, and test assertion must utilize the explicit domain terminology defined in **"KPIs to Measure"** from `CONTEXT-company.md` and the `pdf_qq-2xk.pdf` file:

* **Patient Experience Domain:** `network_appointment_no_show_rate` (Targeting the 22% network failure rate).
* **Revenue Cycle Domain:** `us_commercial_claims_denial_rate` (Targeting the 14% billing leakage profile).
* **Clinical Operations Domain:** `provider_clinical_documentation_time_delta` (Tracking the 35-minute daily administrative friction).
* **Regional Context Filters:** Columns and schemas must cleanly distinguish between `market_us` (Texas, Florida, Georgia) and `market_uk` (London, Manchester) clinic metrics.

## 5. Execution Interface & Backwards Compatibility
* **CLI Execution Script:** `python data/pipelines/pipeline.py`
* **Behavior Requirement:** The `__main__` entrypoint must execute seamlessly from end to end on raw file streams, preserving the operational scripts established during prior technical milestones without a manual code rewrite.

## 6. Hermetic Quality Assurance Suite
* **Target Isolation File:** `tests/pipelines/test_pipeline.py`
* **Test Isolation Constraints:** Zero dependencies on external networks, active EHR instances, or running databases. All processing states must use in-memory mock data arrays structured precisely like HealthCore telemetry.
* **Execution Validation Command:** Must execute perfectly via:
  ```bash
  python -m pytest tests/pipelines/test_pipeline.py
  ```
* **Mandatory Testing Coverage Profiles:**
  * *Defensive Ingestion Test:* At least one test must validate task resiliency against invalid telemetry payloads, including null parameters in regional EHR fields or invalid data types in billing codes.
  * *Mathematical KPI Contract Validation:* At least one test must assert that a hand-calculated mock telemetry payload yields the mathematically exact `network_appointment_no_show_rate` (22%) and `us_commercial_claims_denial_rate` (14%) defined in the documentation.

## 7. Executive Reporting Dashboard
* **Target File Path:** `uis/backoffice/reporting/`
* **Data Sourcing Contract:** Direct extraction from the filesystem or database backends is explicitly forbidden. The frontend must query metrics through the secure `services/reporting/` API layer built in Part 2.
* **Stakeholder Focus Layer:** Designed specifically for **Dr. Sandra Okonkwo** to eliminate contradictory manual reports.
* **Interface Annotation Requirements:** 
  * Displays explicit tracking rows or charts for `network_appointment_no_show_rate`, `us_commercial_claims_denial_rate`, and `provider_clinical_documentation_time_delta`.
  * Every view card must clearly surface the reporting window period (Weekly cadence tracking) and allow comparative filtering by location across the 12 clinics.