# Specifications: Resilient HealthCore Business Performance Data Pipeline (Implementation Checkpoints)

## 1. Production Execution Environment & Dependencies
The active data orchestration engine utilizes **Prefect 3** to guarantee failure isolation, execution state management, and real-time operational visibility. 

### Dependency Enforcement
All environment containers and package manifests must explicitly require Prefect 3. Dependencies are declared and injected into the local monorepo workflow environment via:
```bash
uv add "prefect>=3"
```

## 2. Directory Layout & Decoupled Responsibilities
The pipeline logic adheres strictly to standard directional separation boundaries. Processing heavy-lifting is kept isolated within the data core to ensure it can run standalone outside of web serving containers.

📁 monorepo├── 📁 data/│   ├── 📁 raw/               # Landing zone for raw extractions and cached data payloads│   ├── 📁 process/           # Pure, reusable transformation functions and KPI calculators│   ├── 📁 pipelines/         # Active orchestration logic and pipeline execution scripts│   │   ├── 📄 PIPELINE_DESIGN.md # Approved design layout, execution command, and schedule spec│   │   └── 📄 pipeline.py     # [MAIN CLI ENTRYPOINT] Root flow defining 3+ tasks│   └── 📁 eval/              # Output directory for pipeline validation logs and sanity metrics└── 📁 services/├── 📁 telemetry/         # [UNTOUCHED] Legacy engineering collection & diagnostic modules└── 📁 reporting/         # [NEW APPLICATION MODULE] Thin API routing layer for HealthCore BI* **Strict Application Separation:** Files inside `services/reporting/` must import flows and controller tasks downward from `data/pipelines/pipeline.py`. 
* **Data Core Isolation:** Scripts within `data/pipelines/` or `data/process/` are strictly prohibited from importing application routes or frameworks from `services/`, keeping the pipeline code 100% independently verifiable.

## 3. Phase 1 & 2 — Flows, Tasks, and Resilience Controls

### Orchestration Signature (`data/pipelines/pipeline.py`)
* **Root Orchestrator Flow:** The file must define at least one central Prefect flow (`@flow`), specifically named `healthcore_business_performance_pipeline_flow`.
* **Task Isolation Layer:** The flow must orchestrate a minimum of three sequential, independent tasks (`@task`), ensuring explicit input signatures and deterministic output structures:
  1. `extract_telemetry_source_task`: Fetches operational delta boundaries from `telemetry_events`.
  2. `transform_business_kpis_task`: Compiles HealthCore executive metrics.
  3. `load_reporting_destination_task`: Manages high-integrity database commits.

### Transient Failure Mitigation (Smart Retries)
* **Configuration Rule:** Tasks that connect to external network interfaces, databases, or API nodes must configure active retries directly within the task decorator signature (e.g., `retries=3`, `retry_delay_seconds=15`).
* **Justification Constraint:** The code must include a structural comment immediately adjacent to the decorator providing an explicit engineering justification for the retry counts and backoff delay boundaries selected.

### Exception Interception & Non-Critical Isolation
* **Optional Task Boundary:** The pipeline must feature at least one non-critical/optional task step (such as an analytical quality evaluation run outputting to `data/eval/`).
* **State Control Interception:** This optional step must be called within the flow context utilizing `return_state=True`. 
* **Explicit Failure Handling:** The master flow must catch task failures programmatically using state checks (such as checking `.is_failed()`) instead of letting exceptions cascade. If the optional task drops an exception, the flow traps the error status, logs it, and continues executing the core extraction $\rightarrow$ transformation $\rightarrow$ load path without bringing down the system.

### Performance Caching Architecture
* **Target Step:** The primary transformation task must configure explicit result caching to avoid burning processing cycles during rapid re-runs.
* **Orchestration Fields:** The task signature must enforce a custom validation combination using `cache_key_fn` and a strict time-to-live configuration via `cache_expiration`.
* **Documentation Rule:** An inline source code comment must detail the precise parameters defining the cache validation key and specify exactly how long the data payload remains valid (e.g., 1 hour).

## 4. Phase 3 — Idempotency & Auditing Governance

### Explicit Multi-Run Idempotency Guarantee
* **The Core Requirement:** Executing the pipeline multiple times over identical dataset parameters or time window definitions must produce a completely identical state inside the reporting layer. It must generate zero row duplicates, prevent cumulative data inflation, and cause no value corruption.
* **The Strategy:** The loading phase executes an atomic **Upsert/Merge Pattern**. It keys calculations off the exact composite unique constraints configured within the HealthCore company database schema (`reporting_window_timestamp` + `clinic_location_id`). If an entry matching those constraints already exists, the incoming transaction updates the metric rows cleanly instead of appending duplicate entries.

### Mandatory Operational Audit Fields
Every single pipeline run must record an unalterable operational audit trail. This metadata layer must be saved directly to an internal log file or metadata database table, tracking a minimum of **5 mandatory audit parameters**:
1. `start_time` (`TIMESTAMP`): The exact execution launch clock.
2. `end_time` (`TIMESTAMP`): The exact execution completion clock.
3. `records_processed` (`INTEGER`): Volumetric count of raw elements captured.
4. `status` (`VARCHAR`): Final terminal execution state parameter (`COMPLETED`, `FAILED`).
5. `errors` (`TEXT / JSON`): Serialized exception traces, validation failures, or timeout logs.

## 5. Phase 4 — Standalone Script-Based Execution

### CLI Invocation Guarantee
* **Script Architecture:** The file `data/pipelines/pipeline.py` must feature an independent `if __name__ == "__main__":` execution block that directly invokes the main orchestrator flow.
* **CLI Validation Test:** The full end-to-end ETL flow must execute flawlessly without error via standard command-line script calls:
  ```bash
  python data/pipelines/pipeline.py
  ```
* **Scheduling Documentation Rule:** The intended operational cron schedule for HealthCore's weekly cadence, alongside the explicit terminal run command syntax, must be thoroughly documented within `data/pipelines/PIPELINE_DESIGN.md`.

## 6. Phase 5 — Application Layer Integration & API Contracts
The API endpoints are implemented inside a distinct service path at `services/reporting/`, completely isolated from legacy systems. These endpoints operate as thin delivery routers that delegate execution downwards without duplicating any ETL logic. They share identical security protocols and authentication conventions as the rest of the system API.

* **Endpoint 1: Run Metadata Status Check**
  * **Route:** `GET /services/reporting/status`
  * **Behavior:** Imports state checking capabilities to pull and return the 5 core metadata audit fields (`status`, `start_time`, `end_time`, `records_processed`, `errors`) from the last execution run.
* **Endpoint 2: Asynchronous Manual Trigger**
  * **Route:** `POST /services/reporting/trigger`
  * **Behavior:** Imports the main orchestrator flow from `data/pipelines/` to spin up an on-demand manual batch processing run for recovery or backfill operations.
* **Endpoint 3: Executive KPI Query Delivery**
  * **Route:** `GET /services/reporting/kpis`
  * **Behavior:** Directly reads from `reporting.executive_kpis`. The output response layout matches the strict JSON structure contract defined in the HealthCore specification file to feed the executive dashboard.

## 7. Rigid Evaluation Guardrails
* **Untouched Systems:** Under no circumstances should `telemetry_events` be written to by this pipeline, and the legacy file `services/telemetry/analysis.py` must remain completely untouched.
* **No Re-interpretations:** The final calculated values must match the definitions inside HealthCore's "KPIs to Measure" section exactly. Generic designs that ignore the company's precise data schema or structural vocabulary parameters will be rejected.