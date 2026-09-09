# Technical Specification: HealthCore Telemetry Pipeline & Endpoint

## 1. Architectural Pipeline Sequence & Design
To guarantee zero-regressions, resource safety, and data consistency across HealthCore's multi-regional infrastructure, developers must implement components following this strict structural order:
1. **Phase 1: Analysis Functions (`services/telemetry/analysis.py`):** Code independent, modular Pandas processing engines that ingest SQL streams.
2. **Phase 2: Report Endpoint:** Set up the routing mechanism (`GET /telemetry/report`) to accept, parse, and validate uniform window boundaries.
3. **Phase 3: Cache Layer:** Inject an in-memory Time-To-Live (TTL) structural guard to intercept duplicate payload processing.
+-----------------------+|  Supabase DB Layer    |+-----------+-----------+|SQL (Time Windowed)v+-----------------------+| 1. Analysis Pipeline  |  <--- Pandas Formula:|    (Pure Functions)   |       Load -> Refine -> Convert -> Group -> Agg+-----------+-----------+|JSON Recordsv+-----------------------+
| 2. In-Memory Cache    |  <--- Key: (start_date, end_date)|    (60-Second TTL)    |       Prevents DB Re-computation+-----------+-----------+|Server Fetchv+-----------------------+| 3. GET /telemetry/... |  <--- FastAPI Route Handler+-----------------------+

## 2. Phase 1: Analysis Pipeline Implementation (`services/telemetry/analysis.py`)
The file `services/telemetry/analysis.py` must contain **at least three independent metric functions**. Every calculation function must strictly execute a linear data processing pipeline adhering to this precise structural formula order:

$$\text{load (SQL)} \longrightarrow \text{refine (Pandas)} \longrightarrow \text{convert types} \longrightarrow \text{group} \longrightarrow \text{aggregate}$$

### Mandatory Processing Rules
* **Functional Independence:** Every pipeline function must be completely independent and side-effect free. Calling a function multiple times with identical parameters must yield identical data results.
* **Vectorized Computations (No Loops):** Do not use iterative loops or manual row processing (`for`, `while`, `.iterrows()`) to calculate operational metrics. You must strictly use native, highly optimized Pandas expressions: `.groupby()`, `.agg()`, `.count()`, `.sum()`, and `.mean()`.
* **Type Safety Constraint:** Timestamps must be converted using `pd.to_datetime(df['timestamp'], utc=True)` **before any temporal `groupby()` operation** is attempted. Grouping directly against raw strings or unvalidated types will lead to silent, corrupted grouping boundaries.
* **Output Format:** Each individual analysis function must return a standard list of dictionaries directly serializable to native JSON via `.reset_index().to_dict(orient='records')`.

## 3. Mandatory Metric Calculations (Minimum 3 Functions)
Each function tracks a distinct operational or technical dimension from your event catalogue (`telemetry-plan.md`), accompanied by context-driven grouping dimensions.

### A. Volume Metric over Time Vector (`events_per_day`)
Tracks absolute processing velocity profiles over time to isolate system spikes or throughput failure vectors across the regional clinics.

$$\text{Volume}_d = \sum (\text{rows}) \quad \text{grouped by} \quad \text{Date}_d$$

### B. Failure Profiling Vectors (`error_rate_by_type`)
Tracks real-time system failure rates broken down by context-driven metadata to uncover buggy subsystems or broken EHR data-sync hooks.

$$\text{Error Rate}_t = \frac{\sum [\text{tags.is\_error} = \text{True}]}{\text{Total Events}_t} \quad \text{grouped by} \quad \text{Event Type}_t$$

### C. Cross-Border System Latency Analysis
Computes raw processing performance averages across distinct operational vectors to isolate latency differentials between the US and UK networks.

$$\mu_{\text{latency}} = \frac{1}{N} \sum_{i=1}^{N} \text{tags.latency}_i \quad \text{grouped by} \quad \text{Date}_d$$

## 4. Phase 2 & 3: FastAPI Routing & In-Memory Caching Strategy
The FastAPI route handler under `GET /telemetry/report` manages request parameters, coordinates the underlying analysis pipeline, and shields infrastructure using an explicit caching system.

### Route Behavior & Query Resolution
* **Optional Parameters:** The endpoint accepts optional `start_date` and `end_date` parameters in strict **ISO 8601** format.
* **Temporal Fallbacks:** If query params are omitted, the endpoint defaults the parameters to the **last 7 days** ($\text{start\_date} = \text{now} - 7\text{d}$, $\text{end\_date} = \text{now}$, both calculated in **UTC**).
* **Date Window Isolation:** Metric functions do not calculate their own default windows. The parent endpoint resolves the period once and passes `start_date` and `end_date` down into every individual analytical pipeline query.

### Simple Cache Specification
* **Mechanism:** An in-memory dictionary cache tracking composite inputs.
* **Cache Key:** Built explicitly from the unique `(start_date, end_date)` parameter combination.
* **Expiration Protocol:** Evaluates an atomic **60-second Time-To-Live (TTL)**. If a request hits the endpoint with an identical date boundary within the 60-second window, the app immediately serves the pre-compiled JSON payload without re-running data extraction or calculation pipelines.

## 5. Contract Schema (JSON)
The endpoint must return valid JSON precisely conforming to the following structure:

```json
{
  "period": {
    "from": "2026-09-01T10:58:00Z",
    "to": "2026-09-08T10:58:00Z"
  },
  "metrics": {
    "events_per_day": [
      { "date": "2026-09-01", "event_count": 1420 },
      { "date": "2026-09-02", "event_count": 1510 }
    ],
    "error_rate_by_type": [
      { "event_type": "backoffice_action", "error_rate": 0.05 },
      { "event_type": "api_request", "error_rate": 0.01 }
    ]
  }
}
```