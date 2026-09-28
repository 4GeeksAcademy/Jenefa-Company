# Engineering Technical Specifications: Nightly Telemetry Script

## 1. Database Data Model & Schema Definition

A new table named `job_runs` must be established within the unified schema layer to track execution lifecycles, manage concurrency controls, and maintain processing history.

### 1.1 Field Properties & Vocabulary Matrix

| Field Name | Storage Data Type | Constraints / Attributes | Description / Purpose |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` or `UUID` | Primary Key, Auto-increment | Unique execution entry identifier. |
| `job_name` | `VARCHAR(255)` | Not Null | Token matching the specific task (e.g., `'nightly_export'`). |
| `target_date` | `DATE` | Not Null | Date targeted for operation (required for per-day idempotency check). |
| `status` | `VARCHAR(50)` | Not Null | Restricted state token: `pending`, `processing`, `completed`, `failed`. |
| `started_at` | `TIMESTAMP WITH TZ` | Nullable | Exact clock time when the task execution loop begins. |
| `finished_at` | `TIMESTAMP WITH TZ` | Nullable | Exact clock time when the task execution loop terminates. |
| `error_message` | `TEXT` | Nullable | Stores full string exception traces on task execution failure. |
| `created_at` | `TIMESTAMP WITH TZ` | Not Null, Default Now | Record audit footprint generation timestamp. |

### 1.2 Performance & Uniqueness Indexes
To guarantee high-efficiency lookups and prevent data collisions across HealthCore's high-volume global data layers, a composite index must be configured across the tracking table:
```sql
CREATE INDEX idx_job_runs_name_date ON job_runs(job_name, target_date);
```

### 1.3 Architectural Coexistence Boundary
* **`job_runs` (Nightly Orchestration):** Tracks script state, locks concurrent executions, preserves archival CSV export markers, and enforces script idempotency.
* **`pipeline_runs` / `pipeline_run_audit` (Internal ETL Core):** Monitors internal extraction sub-steps, watermarks, processing metrics, and structural transformation performance.
* These layers are functionally separate and must never be merged.

---

## 2. Status Control Layer (`services/job_runner.py`)

All task orchestration, transaction boundary management, and schema tracking logic must be encapsulated inside a dedicated `job_runner` module within the application `services/` layer.

### 2.1 Core Interface Functions
The module must expose the following interface mechanics:
* `create_job_run(job_name: str, target_date: date) -> JobRunRecord`: Allocates a new record initialized to `pending` status.
* `has_processing_lock(job_name: str) -> bool`: Scans the table for entries matching the target `job_name` where `status == 'processing'`. Returns `True` if an active execution lock is held.
* `has_completed_for_date(job_name: str, target_date: date) -> bool`: Evaluates if an execution entry matching the parameters has already finished successfully (`status == 'completed'`).
* `update_job_status(job_id: int, status: str, error_message: str | None = None)`: Shifts state transitions, auto-populating timestamps matching task completion or failure.

### 2.2 Canonical State Machine Workflow
The background runner process must strictly follow this sequential state progression:

[pending] ──► [processing] ──► [completed]│└──► [failed] (Captures & logs Exception message)
1. **`pending`**: The record is generated before any work begins, signaling that the task is queued.
2. **`processing`**: Set at the absolute beginning of script execution. This state acts as the atomic lock.
3. **`completed`**: Updated only after all steps (CSV backup and pipeline subprocess execution) finish successfully.
4. **`failed`**: Triggered if any unhandled error or exception is caught. **Crucial:** A `try/except/finally` block must guarantee this transition so a process never leaves behind a stalling `processing` zombie lock.

---

## 3. Main Script Specification (`scripts/nightly_export.py`)

The standalone background orchestration engine resides in the `scripts/` folder and must be directly executable from the system command-line interface:
```bash
python scripts/nightly_export.py
```

### 3.1 Script Execution Sequence & Logic Flow

[Start] ──► Resolve target_date (Env / UTC Yesterday)│├──► Check has_processing_lock() ──► [True] ──► Abort Silently│├──► Check has_completed_for_date() ──► [True] ──► Log Skip & Exit│└──► Set status = 'processing' (Lock Acquired)│├──► Export telemetry_events for target_date to CSV│├──► Trigger Data Pipeline Subprocess│└──► [Success] ──► Set status = 'completed' (Release Lock)
### 3.2 Detailed Step-by-Step Flow

#### Step 1: Target Date Resolution
The script checks for a `TARGET_DATE` environment variable override string (`YYYY-MM-DD`). If this variable is absent, it defaults to **yesterday's date in UTC**:
$$\text{Target Date} = \text{datetime.now(timezone.utc).date()} - \text{timedelta(days=1)}$$

#### Step 2: Concurrency Lock Check
The script queries `has_processing_lock('nightly_export')`. If an active row is returned, the script **aborts silently and logs the cancellation** to prevent parallel executions.

#### Step 3: Idempotency Check
The script queries `has_completed_for_date('nightly_export', target_date)`. If a matching completed record exists, the script logs that the execution was skipped as a duplicate and exits safely without recreating files or re-triggering the pipeline.

#### Step 4: Lock Acquisition
The script updates the `job_runs` status to `processing`.

#### Step 5: Archival Data Extraction
The script queries the `telemetry_events` table for records matching the resolved `target_date`. It exports these rows to a flat CSV file inside `data/raw/` using the naming pattern `telemetry_YYYY-MM-DD.csv`. The file is generated **only if it does not already exist**.

#### Step 6: Core Subprocess Invocation
Once the CSV export completes, the script calls the internal data processing pipeline as an isolated system subprocess using the mandated entry point command:
```bash
python -m data.pipelines.telemetry_kpi_daily.run --no-prefect
```

#### Step 7: Finalize Status Update
* **Success Path:** The script transitions the tracking row status to `completed` and records execution metrics.
* **Failure Path:** A broad `except` block catches any issues, saves the exception string to `error_message`, sets the status to `failed`, and propagates the error to the logs.

---

## 4. Trigger Mechanism & Deployment Justification

### 4.1 Production Environment Strategy
The execution of `scripts/nightly_export.py` must be handled externally via the **Host OS System Crontab** daemon or an isolated, dedicated scheduler container. 

┌──────────────────────────────────────┐│        OS Cron Daemon / Container    │└──────────────────┬───────────────────┘│ Fires Nightly (0 1 * * *)▼┌──────────────────────────────────────┐     Isolated Process│    python scripts/nightly_export.py  ├────────────────────────┐└──────────────────────────────────────┘                        │▼┌──────────────────────────────────┐│  FastAPI Application Thread Pool ││     (Completely Untouched)       │└──────────────────────────────────┘
### 4.2 Architectural Justification
* **Thread Decoupling:** Running background routines directly inside FastAPI (via loops or threads) risks worker starvation, web socket degradation, and memory leaks that can impact public-facing request threads across HealthCore's 12 clinics.
* **Lifecycle Independence:** OS-level scheduling ensures that restarting, scaling, or crashing the web application server will not interrupt scheduled pipeline jobs.
* **Zombie Minimization:** If a script process crashes at the system container layer, OS signals allow `sys.exit()` hooks to capture the termination event and prevent zombie lock states.

### 4.3 Production Cron Reference Expression
To run the script every night at 01:00 AM UTC (allowing time for late-arriving telemetry events from the US and UK clinics to settle), configure the crontab entry as follows:
```cron
0 1 * * * /workspaces/Jenefa-Company/.venv/bin/python /workspaces/Jenefa-Company/scripts/nightly_export.py >> /workspaces/Jenefa-Company/data/logs/nightly_telemetry.log 2>&1
```

---

## 5. Observability & Logging Standards

All logging output must use standard Python structures directed to `stdout` and logged at an `INFO` level for standard operations, or an `ERROR` level for exceptions.

### 5.1 Mandated Log Output Syntax
Every logged event line must include a standard, scannable format containing a **Timestamp**, **Job Identity Token**, and the **Resulting State**:

[2026-09-16T01:00:01Z] [nightly_export] [INFO] Starting execution for target_date: 2026-09-15.[2026-09-16T01:00:03Z] [nightly_export] [WARNING] Execution locked by an active process. Aborting silently.[2026-09-16T01:01:05Z] [nightly_export] [INFO] Target date 2026-09-15 already processed. Skipping duplicate execution.[2026-09-16T01:05:42Z] [nightly_export] [INFO] Export complete. 4230 rows written to data/raw/telemetry_2026-09-15.csv.[2026-09-16T01:07:11Z] [nightly_export] [ERROR] Subprocess failed. Status updated to FAILED. Trace: ValueError: Database authentication timeout.
### 5.2 Pull Request (PR) Validation Checklist
Before merging changes into the primary branch, you must verify the following items:
* [ ] The script executes without importing or triggering FastAPI application routing code.
* [ ] Simultaneously firing two script instances confirms that the second instance aborts silently without creating a duplicate database row.
* [ ] Artificially throwing an error inside the script transitions the `job_runs` table status to `failed` and records the error message.
* [ ] Running the script repeatedly for the same `target_date` leaves the data state unchanged after the initial successful run.