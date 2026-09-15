# Functional and Technical Specifications: Pipeline to Production

## 1. Environment & Package Prerequisites
* **Orchestration Engine:** Prefect 3 must be strictly used.
* **Dependency Anchoring:** Lock versioning explicitly via the monorepo package layer:
  ```bash
  uv add "prefect>=3"
  ```

## 2. HealthCore Monorepo Structural Blueprint
The telemetry architecture must adhere to the following rigid folder boundaries:
* `data/pipelines/` — Orchestration layers, main flows, and independent subflows (Starting point: `data/pipelines/pipeline.py`).
* `data/process/` — Pure functional transformation logic and analytical tasks (Target: `data/process/kpis.py`).
* `data/raw/` — Source ingestion files and raw telemetry mock payloads.
* `data/eval/` — Downstream validation logs and analytical output artifacts (Target: `data/eval/latest_run_eval.json`).
* `tests/pipelines/` — Isolated pipeline validation testing code (Target: `tests/pipelines/test_pipeline.py`).
* `uis/backoffice/` — Next.js TypeScript App Router interface (Target: `uis/backoffice/src/app/reporting/page.tsx`).

---

## 3. Refactoring & Pipeline Topology (Phase 1)

### 3.1 Subflow Architecture
The single main flow located inside `data/pipelines/pipeline.py` must be completely refactored to delegate all primary execution phases to at least **three distinct subflows** decorated with `@flow`. 
* **Extraction Subflow:** Handles querying or parsing source data from `telemetry_events` and associated domain source models across our split EHR systems.
* **Transformation Subflow:** Coordinates individual processing tasks that compute required metrics.
* **Load Subflow:** Directs database writes or state persistence into the explicit target destination tables named within `CONTEXT-company.md`, outputting run summaries to `data/eval/latest_run_eval.json`.

### 3.2 Interface Isolation Constraints
* **State & Parameter Hygiene:** Global variables are strictly prohibited for transferring datasets or contexts between steps. Each subflow must declare explicit, strongly typed input arguments and deterministic return signatures.
* **Asynchronous / Optional Flows:** Any optional operations (such as cross-border notification alerts or secondary compliance file exports) must be isolated into their own dedicated subflows. The main orchestration flow must invoke these steps explicitly using Prefect's state capture framework:
  ```python
  subflow_name(..., return_state=True)
  ```

---

## 4. Test-Driven Data Integrity (Phase 2)

### 4.1 Test Location & Invocation
A dedicated test suite must be implemented exactly at `tests/pipelines/test_pipeline.py`. The suite must run seamlessly via standard testing frameworks and pass completely without errors using:
```bash
python -m pytest tests/pipelines/test_pipeline.py
```

### 4.2 Test Isolation & Fixtures
* **Hermetic Environment Constraints:** Tests must execute in complete isolation. They are strictly barred from establishing live network handshakes to external APIs or connecting to a physical database (complying with healthcare privacy isolation standards).
* **In-Memory Fixtures:** Mock datasets must be constructed directly within the test file. These in-memory fixtures must be structurally shaped precisely like the authentic event patterns documented in your `CONTEXT-company.md` schema (reflecting realistic US and UK telemetry inputs).

### 4.3 Mandatory Testing Scopes
The testing file must validate at least **three transformation tasks** computing distinct metrics, satisfying these specific criteria:
1. **Defensive Structural Failure Verification:** At least one unit test must explicitly assert that a transformation task exhibits robust, defensive behavior when processing malformed or invalid inputs (e.g., unexpected null variants, missing required fields, or mismatched data primitives).
2. **Deterministic Mathematical Verification:** At least one unit test must parse an accurately hand-calculated, known input fixture and assert that the task's final computed metric perfectly matches the structural definition in `CONTEXT-company.md`.

---

## 5. Command-Line Interface Compatibility (Phase 3)

Despite the extensive subflow topology modifications, backward compatibility is mandatory. The core entrypoint built during previous phases must remain fully operational. Operating teams must be able to seamlessly invoke the execution script directly from the terminal without errors or positional adjustments:
```bash
python data/pipelines/pipeline.py
```

---

## 6. Executive Business Dashboard (Phase 4)

### 6.1 Data Acquisition & Connectivity
The presentation layer is fully established at `uis/backoffice/src/app/reporting/page.tsx` as a Next.js server-side component. It dynamically queries live analytical aggregates using `fetchExecutiveKpis()` imported directly from the `uis/backoffice/src/services/reporting.ts` service layout.

### 6.2 Visualization & Data Contract Mapping
The table layout binds directly to the processed database columns to ensure data tracking consistency:
* **`Clinic`** — Renders target string values matching `clinic_location_id`.
* **`Region`** — Renders target market identifiers matching `market_region`.
* **`Network appointment volume`** — Reflects overall volume metrics via `network_appointment_volume`.
* **`Global no-show rate`** — Displays regional risk proportions via `global_no_show_rate`.
* **`Claims denial rate`** — Surfaces structural billing leaks via `claims_denial_rate`.
* **`Revenue net settled`** — Formats currency context natively using `revenue_currency` and `revenue_net_settled`.

---

## 7. Strict Constraints & Evaluation Matrix

To ensure a successful operational evaluation, the project must adhere to the following rigid validation boundaries:

| Evaluation Checkpoint | Structural Requirement | Constraint / Restriction |
| :--- | :--- | :--- |
| **Pipeline Core** | Main flow invokes at least **3 distinct subflows** (`@flow`). | No direct execution of core ETL tasks inside the main coordinator. |
| **Subflow Interfaces** | Explicit inputs and outputs defined per subflow. | **Zero reliance on global states** or shared variables. |
| **Naming Conventions** | Subflow, task, and test names must reflect `CONTEXT-company.md` metrics. | Generic names like `extract_data` or `run_transform` **will fail evaluation**. |
| **Testing Isolation** | Uses local, in-memory mock data fixtures. | **No live database or API calls** allowed in `test_pipeline.py`. |
| **Defensive Coverage** | Explicit tests for structural failures and malformed records. | Must catch null fields or incorrect type errors gracefully. |
| **System Integrity** | Core underlying source files must not be altered. | `telemetry_events` table and `services/telemetry/analysis.py` **must remain completely unmodified**. |
| **CLI Verification** | Script execution path must match original specifications. | `python data/pipelines/pipeline.py` must run end-to-end without errors. |

---

## 8. Additional Resiliency & Observability Enhancements
*(Note: If you identified operational improvements while reviewing your design questions in Part 1—such as an Idempotency-Key pattern for safe task retries, a pipeline heartbeat monitor, or concurrency locks to prevent overlapping executions—they should be noted below and documented inside `data/pipelines/PIPELINE_DESIGN.md` explaining which design question they satisfy).*

* **Enhancement 1:** [To be populated based on your specific design choices if applicable]
* **Enhancement 2:** [To be populated based on your specific design choices if applicable]
