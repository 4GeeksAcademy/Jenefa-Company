# Progress - HealthCore

## Current State of Development
- The organization is currently operating in a highly manual, reactive, and fragmented state. The infrastructure has failed to keep pace with business growth, resulting in zero unified automation across the 12 locations.
### Infrastructure Status
- There is completely no shared data layer, no telemetry, and no centralized logging across the company. System failures are caught only when physical clinics call the Austin tech office to complain.
### Data & Software Estate
- Operations run on a fragmented patchwork of legacy software. This includes two non-communicating EHR platforms, a standalone US billing platform, a manual phone scheduling setup in the US, and manual diaries alongside spreadsheets for UK billing and booking.
### Operational Baseline
- Staff are heavily bogged down by administrative debt. Clinicians waste 35 minutes daily on manual documentation. Human resource tracking (CME medical licenses) and compliance logs are managed entirely on loose spreadsheets.
### Executive Reporting
- Reporting is static and lagging. The CEO receives unstandardized weekly reports from department heads that are based on data multiple days old. Critical real-time network metrics (like weekly no-show or denial rates) are completely inaccessible without manual phone polling.

### Milestone 4 completed (monorepo AI setup)
- Added `memory-bank/` (`projectbrief.md`, `techContext.md`, `progress.md`), root `AGENTS.md`, `.agents/rules/phi-data-residency.md`, and `.agents/skills/sync-memory-bank/`.
- Created `uis/web` with its own shell layout; `/` imports `healthcore-testing` and renders denial, no-show, and CME outputs on screen.
- Migrated Milestone 1 corporate site into `uis/website` as typed reusable React components (`/`, `/apply`) with the original teal/sky visual identity.

### Incident report processor completed (Phase 1 + Phase 2)
- Built shared validator in `scripts/incident_core/` and CLI `scripts/analyze.py` against HealthCore incident CSV rules (no `patient_id` in any output).
- Added sample dataset `scripts/incidents-healthcore.csv` (100 rows; 94 valid / 6 invalid) matching `scripts/context-fileIncident.md` targets.
- Added FastAPI service `services/api` with `POST /api/incidents/analyze` and `GET /api/incidents/results/export`.
- Mounted Incident Analysis upload/dashboard/export UI at `uis/web` `/incidents` (sidebar nav link).

### AUTH-088 completed (authentication unit test coverage)
- Document-first plan and results in root `TESTING.md` (matrix, run commands, AI/regression notes, coverage).
- FastAPI suite under `services/api/tests/` (`test_register.py`, `test_login.py`, `test_token.py`, plus `test_service_rules.py`); run via `cd services/api && uv run pytest` / `--cov=app.auth` — **84%** auth module coverage (gate ≥ 70%).
- Registration now enforces minimum 8-character passwords (aligned with reset/change-password); covered by `test_register_rejects_password_shorter_than_eight_chars`.
- Jest suite for clinic web auth utilities (`uis/web` `authStorage`, `userFacingError`, `api.readJson`) via `npx jest --coverage`.
- Auth API sources (`services/api/app/auth`, error handlers, web `lib` auth helpers) restored onto `auth-unittesting` so the suite exercises the implemented structure.

### Clinic supply inventory (SQLModel dual persistence)
- Extended `services/api` with a dual-store inventory layer: TinyDB remains the identity/`get_current_user` source; SQLModel persists `MedicalSupply`, `InboundEntry`, and `OutboundExit` on SQLite locally or Supabase Postgres via `INVENTORY_DATABASE_URL`.
- Stock is ledger-derived only (`inbound − outbound` by `clinic_id`). Outbound overdrafts return HTTP 400 before write. All `/inventory/*` routes require bearer auth and stamp `user_uuid` from the TinyDB session.
- Spec seed catalog (gloves `450`, sedative `35`) loads on empty databases. Covered by `services/api/tests/test_inventory.py` (8 cases). Staff UI at `uis/web` `/inventory` plus `/login`.
- Milestone 5 UI hardening completed in `uis/web`: all four backoffice inventory routes stay session-guarded; outbound dispersal resets and re-fetches stock immediately on item changes with stale-request protection; orders history now formats `created_at` by clinic timezone (UK -> `Europe/London`, TX -> `America/Chicago`, FL/GA -> `America/New_York`, fallback `UTC`) while preserving immutable audit columns and movement badges.
### AUTH-01 completed (JWT + TinyDB route protection)
- Specs captured in `authentication-context.md` / `authentication-specs.md`.
- Added zero-trust JWT layer under `services/api/app/auth/` (bcrypt via passlib/`libpass`, `python-jose`, env-driven `SECRET_KEY` + `ACCESS_TOKEN_EXPIRE_MINUTES`).
- User/Profile collections stored only in TinyDB (`services/api/data/auth.json`); dual-DB rule enforced (no user tables in SQL).
- Public `POST /users`, `POST /auth/login`; protected `GET /auth/me`, `/users`, `/profiles/me`, plus five hardened business stubs: `/clinics/telemetry`, `/appointments/booking`, `/billing/claims/{id}`, `/compliance/audit-logs`, `/ai/clinical-documentation`.
- Distinct `401` (missing/invalid token) vs `403` (ownership/role) responses verified with TestClient scenarios.

### AUTH-02 completed (frontend JWT session + protected views)
- Client token lifecycle in `uis/web`: `localStorage` key `hc_auth_token`, `Authorization: Bearer` on outbound API calls, and immediate token clear + `/login` redirect on protected `401`s.
- Public staff views `/login` and `/register` (register chains `POST /users` then `POST /auth/login`); protected `/`, `/incidents`, and `/account/profile` sit behind a zero-flash client route guard + `WebShell`.
- Profile UI maps email from `User` (`GET /auth/me`) and name/phone/address from `Profile` (`GET`/`PUT /profiles/me`), with explicit logout.
- `uis/website` is unchanged — no token checks on the public marketing site.
- Restored AUTH-01 FastAPI modules under `services/api/app/auth/` (sources had been missing; bytecode/TinyDB store remained) so the frontend can hit live auth routes.

### Telemetry storage (Phase 3) completed — real Supabase-backed ingestion
- Replaced the Phase 1 `/telemetry/events` stub with a real pipeline in `services/api/app/telemetry/`: `models.py` (`TelemetryEventRecord` SQLModel table `telemetry_events`, 8 columns, B-Tree indexes on `timestamp`/`event_type`, GIN index on `tags`), `database.py` (reuses the existing inventory SQLModel engine/session so the table is created via the same `init_inventory_schema(engine)` lifespan step), `service.py` (per-event `TelemetryEvent.model_validate` loop, derives `service` from an `event_type → module` map and `environment` from `TELEMETRY_ENVIRONMENT`, single `session.add_all` + commit bulk insert), and `router.py`/`schemas.py` (loose `{"events": list[dict]}` envelope, response `{received, stored, rejected}`).
- Zero frontend changes: `uis/web` and `uis/backoffice` `TelemetryService` clients are untouched; they only read the HTTP status code.
- `services/api/tests/test_telemetry.py` rewritten for the real contract (partial validation, persistence assertions via `client.app.state.inventory_engine`); full suite `python -m pytest` in `services/api` — **39 passed**.
- Manually verified end-to-end against a scratch SQLite DB: mixed valid/invalid batch returned `{"received": 2, "stored": 1, "rejected": 1}` and the valid row persisted with correct `event_type`, `timestamp`, derived `service`, `tags`, `user_id`, `session_id`, `environment`.
- Documented `TELEMETRY_ENVIRONMENT` env var and the `/telemetry/events` endpoint in `services/api/README.md`.

### Telemetry report endpoint completed — Pandas analysis pipeline + TTL cache
- Added `services/api/app/telemetry/analysis.py`: three independent, side-effect-free Pandas pipelines (`events_per_day`, `error_rate_by_type`, `average_latency_by_day`), each loading its own `telemetry_events` SQL window via SQLModel, converting `timestamp` with `pd.to_datetime(..., utc=True)` before any `groupby()`, and returning `.to_dict(orient="records")` (no manual loops).
- `error_rate_by_type` derives a boolean error flag from `tags.is_error` when present, otherwise from `system_health_checked`'s `status_state != "healthy"` (the only failure signal in the current event catalogue); `average_latency_by_day` reads `tags.latency_ms`.
- Added `GET /telemetry/report` to `services/api/app/telemetry/router.py`: optional `start_date`/`end_date` ISO 8601 query params (default last 7 days, UTC, resolved once by the route and passed into every analysis function), `400` on invalid dates or `start_date > end_date`, and a 60-second in-memory TTL cache keyed by the resolved `(start_date, end_date)` pair to avoid recomputation.
- Response contract: `{"period": {"from", "to"}, "metrics": {"events_per_day", "error_rate_by_type", "average_latency_by_day"}}` per `specs-reportTelemetry.md`.
- Added `pandas>=2.2.0` to `services/api/requirements.txt` / `pyproject.toml`.
- New `services/api/tests/test_telemetry_report.py` (7 cases: default window, grouping, error-rate derivation, latency averaging, invalid/inverted dates, cache hit/clear); full suite `python -m pytest` in `services/api` — **46 passed**.
- Documented `GET /telemetry/report` in `services/api/README.md`.

### Async task queue completed (Ticket #DEV-55 — Redis + Celery)
- Added `services/api/app/tasks/celery.py` (Celery app: Redis broker/backend, `task_acks_late`, `task_track_started`) with `healthcore.reporting.generate` wrapping the existing reporting pipeline; `services/celery_app.py` is the spec-mandated entry point that loads the repo `.env`, adds `services/api` to `sys.path`, and re-exports `app.tasks.celery` so the API and worker share ONE module identity (avoids duplicate SQLModel `medicalsupply` metadata registration that crashed the API).
- Producer endpoints in `app/async_tasks.py` (router registered in `main.py`): `POST /reports/generate` → `202 {"task_id"}` (**83ms**, spec <200ms), payload accepts only an optional `database_url` reference (no data blobs); `GET /tasks/{task_id}` → lowercase Celery state (`pending`/`started`/`success`/`failure`) + result on success.
- Reliability: `max_retries=3` with exponential backoff (2s/4s/8s), late-ack + `task_reject_on_worker_lost`; engine creation kept INSIDE the try block so eager failures (bad URL/missing driver) still retry and log instead of escaping as unhandled worker errors.
- DLQ: `async_task_failures` table (`task_id`, `attempt_number`, `error` traceback, `timestamp`) written to the platform's own operational DB (`inventory_database_url()`), never the task's target DB, with the DLQ write failure swallowed + logged so the original task error still reaches the result backend/Flower.
- Structured logs per task: `async_task_completed|retry|failed` with `task_id`, `attempt_number`, `status`, `duration_ms`, full error text.
- `docker-compose.yml`: `redis` (7-alpine, `--maxmemory-policy noeviction`), independent `worker` (`celery -A services.celery_app worker`), `flower` on :5555; `services/Dockerfile` ships `celery_app.py` + `PYTHONPATH=/services:/services/api`. API deps gained `celery`/`redis`.
- README runbook: start/stop worker + Flower, trigger/poll endpoints. Verified end-to-end on real processes: 202 in 83ms, success result polled back (SQLite pipeline run COMPLETED), failure path retried 3× then `failure` + DLQ row persisted, Flower HTTP 200, worker pre-flight registered `healthcore.reporting.generate`; full suite **47 passed**.

## Planned Next Steps
- Dr. Sandra Okonkwo has newly commissioned HealthCore Digital as an internal unit specifically to build out modern, intelligent systems from scratch. The target deployment roadmap spans across six primary operational fronts:

### Core Engineering & Integration (James Osei)
#### Central API Build
- Build the unified HealthCore central API to aggregate patient, appointment, financial, and staffing data directly from the siloed EHRs.
#### Telemetry Deployment
- Establish real-time telemetry protocols and automated software health checks across all 12 properties to instantly flag outages.
#### Data Pipeline
- Construct a reliable data pipeline to feed streaming data to departmental and executive analytics dashboards.

### Clinical Workflow Optimization (Dr. Marcus Reid)
#### AI Charting Assistants
- Deploy AI-assisted clinical documentation software to automate note-taking and reclaim the 35 lost minutes per day per clinician.
#### Cross-Border Portability
- Enable cross-location patient history visibility so records securely follow individuals traveling between the US and UK.

### Patient Experience & Revenue Protection (Priya Nair & Tom Callahan)
#### Patient Booking Engine 
- Launch a unified online booking platform across both the US and UK markets to replace manual phone diaries.
#### Predictive Scheduling
- Implement a machine learning no-show prediction model paired with automated SMS/email outreach to target at-risk appointments.
#### AI Claims Scrubbing
- Build an automated pre-submission coding assistant and claims review engine to catch systematic errors before they hit insurance providers, cutting down the 14% denial rate.

### Workforce & Compliance Automation (Diane Foster & Claire Whitfield)
#### Automated Credentialing
- Replace manual onboarding with automated clinical verification checklists and license tracking systems featuring expiration triggers.
#### Compliance Data Retrieval
- Code an automated patient data request compilation tool to streamline legally mandated GDPR/HIPAA record requests.
#### Internal Chatbot
- Launch a basic employee HR portal alongside an internal chatbot to handle holiday booking and legal policy queries.

### Executive Intelligence (Dr. Sandra Okonkwo)
#### Unified KPI Dashboard 
- Roll out a singular executive dashboard tracking cross-border revenue, booking trends, patient satisfaction, and claim denial hotspots.
#### Automated Briefings 
- Configure an automated reporting protocol to compile and deliver localized operational summaries every Monday at 7:00 AM sharp.
#### Natural-Language Assistant
- Build a secure semantic search index over technical docs and integrate a natural-language AI interface allowing the CEO to query operational data using text.