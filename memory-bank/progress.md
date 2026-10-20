# Progress - HealthCore

### Back Office live reporting and layout fixes completed
- Reporting now reads persisted `ExecutiveKPI` rows from the reporting database instead of rebuilding telemetry rows or falling back to mock data. The API route remains authenticated and the UI displays live `clinic_location_id` values and the latest row timestamp without a static date.
- Removed the Flower monitor link from Business Reporting and consolidated the page around the dynamic `ReportingRefresh` table.
- Reordered clinic selection before target-item selection in inbound and outbound inventory forms, and corrected the Back Office sidebar icons and header classes.
- Touched `services/api/app/reporting/service.py`, `services/api/app/reporting/kpi_contract.py`, `uis/web/src/app/(app)/reporting/page.tsx`, `uis/web/src/components/ReportingRefresh.tsx`, `uis/web/src/lib/reporting.ts`, `uis/web/src/components/inventory/InventoryInboundView.tsx`, `uis/web/src/components/inventory/InventoryOutboundView.tsx`, and `uis/web/src/components/WebShell.tsx`.
- Status: completed. Validation: 17 focused API tests passed, Python compilation passed, and `uis/web` production build passed.

### Business reporting KPI type-safety fix completed
- Updated `services/api/app/reporting/kpi_contract.py` to preserve and aggregate native SQLAlchemy `datetime` and JSON/dict telemetry values, prefer the caller-provided database engine, and emit `CRITICAL ERROR` diagnostics for extraction, timestamp, and tag parsing failures.
- Added `services/tests/test_reporting_kpi.py` covering native datetime/dict input and the serialized KPI dictionary consumed by the frontend.
- Validation: focused KPI test passes (1 passed), the API on port 8000 returns valid KPI JSON, and the dashboard on port 3001 responds. Full browser automation was unavailable because Playwright is not installed; the reporting page is client-rendered.
- Renamed the Prefect extraction, transformation, and load subflows to `fetch_network_telemetry_flow`, `compute_executive_kpi_matrix_flow`, and `load_central_reporting_db_flow`; added explicit no-show, US denial, and clinical documentation delta taxonomy functions with `market_us`/`market_uk` segmentation.
- Added exact 22% no-show and 14% US denial benchmark coverage; the Prefect pipeline suite passes (5 tests).

### Spec phase 3: Overview ledger, shared incident result, inventory clinic dropdowns (historical validation note)
- Overview: `(app)/page.tsx` renders `OperationsLedger` (`src/components/OperationsLedger.tsx`), which replaces the earlier KPI overview. `OverviewDashboard.tsx` and `(app)/operations/page.tsx` were deleted. The sidebar "Operations Ledger" item was removed. `/operations` and `/backoffice` redirect to `/`.
- Incident analysis: the latest result is kept in memory on the API (`state.py`) and served by `GET /api/incidents/latest` (404 when none exists). The upload panel and the Overview ledger both load it and render through `IncidentResults.tsx`. The result stays until the next successful upload. It is not persisted and holds aggregates only. The upload filename is no longer displayed.
- Inventory: `SUPPLY_SEED` adds 3 SKUs (`HC-SYR-010` at CLINIC-TX-03, `HC-PPE-050` and `HC-INS-300` at CLINIC-UK-04). `_add_missing_supplies` adds them by SKU on every start, so existing databases get them. Ledger rows still seed only on a fresh catalog, so new SKUs start at zero stock. Inbound and outbound clinic IDs are now dropdowns built from the product list. These SKU and clinic values were chosen by the assistant and need confirming.
- Reporting: the former Flower monitor link was removed by the later live reporting fix documented above.
- Corrected: the earlier note that Overview is a live KPI page was wrong. The spec asks for the Operations Ledger on Overview.
- Validation: `tsc --noEmit` passes for source files. The only errors come from stale `.next/types` entries for the removed `analysis` and `operations` pages, which clear on the next build. `tests/test_inventory.py` and `tests/test_agent_websocket.py` pass (13/13). The `/api/incidents/latest` route returns 404, then 200 after a save. `npm run build:web` and browser checks were not run in this sandbox.

### Spec fixes: sign-in link, redirects, incident privacy, Operations ledger, chat cleanup (pending build and browser checks)
- Inventory moved from `src/app/backoffice/inventory/` to `src/app/(app)/inventory/`, so it renders inside `WebShell` and the auth guard. Internal links now point to `/inventory/...`.
- Redirects in `uis/web/next.config.ts`: `/backoffice` → `/operations`, `/backoffice/inventory/*` → `/inventory/*`, `/backoffice/*` → `/*`, and `/analysis` → `/incidents`. The empty `/analysis` route was removed and the nav points to `/incidents`.
- Sign-in: the public "Staff Sign-in" link in `uis/website/src/components/SiteHeader.tsx` uses `NEXT_PUBLIC_STAFF_APP_URL` (default `http://localhost:3001`). The staff app must be running on that port.
- Assistant chat: added a "Try asking" row of four sample questions. Clicking one fills the input and does not send.
- Incident history: new `services/api/app/history/` with an `incident_analysis_runs` table, storing metadata only (timestamp and record counts). `POST /api/incidents/analyze` records each successful run. `GET /history/incidents` (auth required) lists runs. Retention is 10 days, purged on write and read.
- Incident privacy: uploaded filenames are no longer read or stored (`main.py` uses the generic label `incident-upload.csv`). The "Previous analyses" section was removed from the incident panel. Rows saved before this change may still hold real filenames until they expire.
- Chat: the "Previous sessions" section and chat-thread history were removed. The `chat_thread_records` table and the `/history/chat` endpoint were removed from code. `services/langgraph_agent/websocket.py` no longer records messages.
- Operations: `/operations` uses live data. Inventory SKUs and units come from `/inventory/products`, the inventory ledger from `/inventory/orders`, incident history from `/history/incidents`, and RFP tickets from `/rfp/tickets`. The communications log was removed. Duplicate React keys in `DataTable` were fixed. The incident table no longer has a source-file column. Each table shows its own error or empty state. The support terminal's canned "Simulation queued" replies are still demo text.
- Validation: `tests/test_agent_websocket.py` passes (5/5). Python files compile. `npm run build:web` could not finish in this sandbox (killed, memory). ESLint is blocked by organization content policy here.
- Reporting (Celery): `POST /services/reporting/trigger` now requires auth, queues `generate_reporting_task` on the Celery worker (Redis broker), and returns 202 `{task_id, status: "queued"}`. `GET /services/reporting/trigger/{task_id}` (auth required) returns the task state only. Both return 503 when Redis or the worker is unavailable. Celery imports are lazy to avoid a circular import through `app.reporting`. The `reporting/page.tsx` header has a `ReportingRefresh` control that polls until the run finishes, then refreshes the page.
- Overview (superseded by phase 3 above): an earlier version rendered `OverviewDashboard` (live KPI cards from the reporting endpoint, plus shortcuts to Operations, Reporting, Incidents, Inventory, and Assistant). The sample-data `OpsDashboard.tsx` was removed. Reporting KPIs show only after a successful worker run.
- Decisions: Celery and Redis for reporting. Overview uses live data. The stale `chat_thread_records` table and existing incident rows were left in place (cleanup deferred).
- Smoke test: with no Redis running, both reporting endpoints return 503. `tests/test_agent_websocket.py` passes (5/5).
- Open items: run `npm install` (root lockfile still lists the removed backoffice workspace). Start Redis and the Celery worker. Restart the API to load the new routes. Run `npm run build:web`, then check `/`, `/reporting`, `/operations`, `/inventory`, `/incidents`, and `/assistant` in a browser. Not verified: a full worker run that fills KPI rows (the KPI source in `data/pipelines/pipeline.py` could not be reviewed here). Pre-existing, not changed: `/services/reporting/kpis` and the `/reports/generate` and `/tasks/{id}` endpoints in `async_tasks.py` do not require auth. Review under HIPAA and UK GDPR.

### Backoffice specification consolidation completed
- Sign-in fix: the public site's `ECONNREFUSED 127.0.0.1:8000` came from the FastAPI API not running, not from a code defect. With the API up, `/health` returns 200 and `POST /backend/auth/login` returns the expected 401 for bad credentials.
- Removed `uis/backoffice`. Its RFP, reporting, and telemetry extras were ported into `uis/web` (`rfp/page.tsx`, `reporting/page.tsx`, `lib/reporting.ts`, `lib/telemetryAuth.ts`, `lib/telemetryInstrumentation.ts`, `lib/webVitals.ts`). The dashboard is now the `/operations` route, and `agent_memory.db` is at `uis/web/data/`. Root `package.json` no longer lists the backoffice workspace or its `dev`/`build` scripts, and the `.gitignore` entry is gone.
- Removed `uis/healthcore-website`. Its four unique images are in `uis/website/public/images/`. `uis/website/README.md` is updated.
- Removed `uis/talent-pipeline-tracker`. Its components, hooks, services, and types are in `uis/web/src/features/talent/`. Its pages are at `/talent`, `/talent/candidates/new`, and `/talent/candidates/[id]` (with `/edit`), inside the web shell and login guard. Its spec is at `uis/web/docs/talent-pipeline-spec.md`. `uis/web/README.md` has a talent section, and the nav has a "Candidate Sourcing" item.
- Validation: `uis/web` `tsc --noEmit` and `next build` both pass.
- Open items: the talent debug panel in `CandidateDetailPage.tsx` shows internal state to all signed-in users and fails 8 `react/no-unescaped-entities` lint rules (kept at the owner's request; flagged for removal). `/operations` uses demo data copied from the backoffice dashboard. The root `package-lock.json` still lists the removed workspace and must be refreshed with `npm install`. The `uis/website` build has a pre-existing `ServiceCard` `description` type error. Browser checks of `/talent`, `/rfp`, `/reporting`, and `/operations` are still pending.

### Backoffice blue palette alignment completed
- Updated `uis/backoffice/src/app/page.tsx`, `uis/backoffice/src/app/reporting/page.tsx`, and `uis/backoffice/src/app/rfp/page.tsx` from green/teal shell and highlight colors to the public website's blue/slate palette, including visible RFP success and live-status states.
- Validation: backoffice production build passes and no old green palette values remain under `uis/backoffice`.

### SecureAI NIST/MIST governance registry completed
- Added `services/api/app/secure_ai/` with a SQLModel, non-PHI AI-system registry covering owner, architecture, data traversal surface, provider, risk tier, jurisdiction, and lifecycle status.
- Seeded the five product-context baseline assets: Classification Agent, Response Agent, Escalation Workflow Engine, Semantic Memory Module, and MCP Tool Gateway.
- Added authenticated `GET /governance/ai-systems`, admin-only registration, duplicate-key protection, schema validation, and admin suspension for incident/governance response.
- Documented the registry contract in `services/api/README.md` and added `services/api/tests/test_secure_ai.py` coverage for auth, admin writes, duplicate prevention, suspension, and invalid risk tiers.
- Validation: focused SecureAI tests pass (**4 passed**), complete API suite passes (**66 passed**), and editor diagnostics are clean. Rate limiting, kill-switch orchestration, and incident playbook automation remain separate follow-up controls from the broader NIST action report.

### OWASP security audit and SSRF hardening completed
- Added `SecureAI/OWASP-AUDIT.md` with an explicit A01-A10 finding matrix across the frontend, central API, and agentic system, plus reproducible critical-remediation and deployment sign-off gates.
- Hardened `services/langgraph_agent/tools.py` so MCP, incident, and inventory endpoints reject non-HTTP(S), credential-bearing, query-bearing, loopback, private, link-local, and reserved targets before outbound requests; regression coverage in `tests/test_langgraph_external.py` passes (**5 passed**).
- Hardened `services/Dockerfile` with a dedicated non-root `hc-runtime` user and corrected stale build paths; `.dockerignore` permits only required `data` package sources while retaining raw/generated data exclusions. The image builds successfully and defaults to `hc-runtime`.
- Host SSH, firewall, TLS/at-rest encryption, SBOM, signed-release, and central log-export evidence remain deployment-owner gates and are documented rather than claimed as application-test results.

### Bidirectional agent WebSocket streaming foundation completed
- Added authenticated `GET /agent/ws` with query-token verification, required `session_id`/`thread_id` binding, structured `token_chunk`, `interrupt`, `generation_interrupted`, and `generation_completed` frames, progressive client reconnects, and non-destructive interrupted-turn rendering at `uis/web` `/chat`.
- Added focused handshake, frame serialization, and interruption coverage in `services/api/tests/test_agent_websocket.py`; editor diagnostics are clean, the focused WebSocket tests pass (**3 passed**), the full API suite passes with test-only MCP settings (**60 passed**), and the web production build passes.
- The transport task is cancellable and preserves the interrupted turn, but the current synchronous graph invocation runs in a worker thread; native cancellation inside the model/provider remains a follow-up when the generation adapter exposes an async cancellation handle.
- Fixed live chat startup with the local `QDRANT_URL=sqlite:///:memory:` configuration by selecting a safe empty retriever in the WebSocket adapter instead of passing the unsupported SQLite scheme to `QdrantClient`; added regression coverage, verified the real stream reaches `generation_completed`, and the full API suite now passes (**61 passed**).
- Expanded the local WebSocket fallback with a bounded non-PHI HealthCore context so known topics produce distinct answers for clinics, HIPAA/UK GDPR, leadership, hiring, revenue, and appointments; unknown topics retain the honest refusal. Focused chat tests pass (**5 passed**) and the full API suite passes (**62 passed**).

## Current State of Development
### Backoffice specification implementation completed
- Updated `uis/backoffice/src/app/page.tsx` with a centered unauthenticated sign-in gateway, admin and employee evaluator prefills, explicit public-site return link, read-only employee state, synchronized `HC` logo mark, seeded incident and RFP historical ledgers, support prompt simulations, and a 10-second central API refresh loop with an offline baseline fallback.
- Registered `uis/backoffice` as a root workspace with `dev:backoffice` and `build:backoffice` scripts in `package.json`; disabled Next telemetry for active website/backoffice development scripts.
- Validation: `npm run build:backoffice` passes and editor diagnostics are clean for the changed backoffice page. `npm run build:website` remains blocked by a pre-existing `description` property type error on `ServiceCard`.
- The requested purge of `uis/web` remains blocked because it is still referenced by the root workspace, Docker Compose, documentation, and the authenticated staff workflows; its chat, incident, inventory, and RFP components have not been discarded.

### Back-office portal linkage and guarded shell completed
- Replaced the public website's Apply Now action in `uis/website/src/components/SiteHeader.tsx` with the blue pill-shaped Staff Sign In link to `http://localhost:3001/sign-in`.
- Added the `/sign-in`, `/analysis`, and `/assistant` routes in `uis/web`; the existing auth guard now redirects unauthenticated app traffic to the sign-in sheet and keeps the shell unrendered until a token exists.
- Reworked `uis/web/src/components/WebShell.tsx` into the specified Knowledge Base, Business Logic, Technical Data, and Agent Systems groups with the required route map, pill links, and navy/sky states. Updated `uis/web/src/app/globals.css` to the synchronized palette.
- Added authenticated-app reporting and RFP intake pages at `/reporting` and `/rfp`, plus the typed reporting client in `uis/web/src/lib/reporting.ts`. Inventory continues through the existing `/inventory` redirect and detailed ledger routes.
- Validation: `uis/web` production build passes; Jest regression suite passes (**3 suites, 9 tests**); editor diagnostics are clean for the changed TypeScript/TSX files.

- The organization is currently operating in a highly manual, reactive, and fragmented state. The infrastructure has failed to keep pace with business growth, resulting in zero unified automation across the 12 locations.
### Infrastructure Status
- There is completely no shared data layer, no telemetry, and no centralized logging across the company. System failures are caught only when physical clinics call the Austin tech office to complain.
### Data & Software Estate
- Operations run on a fragmented patchwork of legacy software. This includes two non-communicating EHR platforms, a standalone US billing platform, a manual phone scheduling setup in the US, and manual diaries alongside spreadsheets for UK billing and booking.
### Operational Baseline
- Staff are heavily bogged down by administrative debt. Clinicians waste 35 minutes daily on manual documentation. Human resource tracking (CME medical licenses) and compliance logs are managed entirely on loose spreadsheets.
### Executive Reporting
- Reporting is static and lagging. The CEO receives unstandardized weekly reports from department heads that are based on data multiple days old. Critical real-time network metrics (like weekly no-show or denial rates) are completely inaccessible without manual phone polling.

### RTS-SSE completed (authenticated RFP notifications)
- Added `services/api/app/rfp/events.py` as an in-process bounded fan-out hub with `rfp_ticket_created` frames, initial connection comments, and 15-second keep-alives.
- Added authenticated `GET /rfp/events` streaming through the existing RFP JWT/local-development auth boundary, with `text/event-stream`, no-cache, and keep-alive headers. Ticket creation publishes only after its database commit succeeds.
- Replaced `uis/backoffice/src/app/rfp/page.tsx` five-second polling with an authenticated `fetch`/`ReadableStream` consumer, capped progressive reconnect backoff, reconnect refetch recovery, ticket ID deduplication, and a distinct live-arrival status banner.
- Added SSE auth and framing coverage in `services/api/tests/test_rfp_local_auth.py`; focused RFP tests pass (**8 passed**) and the backoffice production build passes.

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

### Security & guardrails harness verified (Ticket #SEC-114)
- Verified the existing `services/langgraph_agent/guardrails.py` boundary around the graph: deterministic prompt-injection blocking, personal-task refusal, casual-question redirection, explicit untrusted retrieval isolation, output leakage validation, and structural/content/security trigger counters.
- Verified `POST /agent/query` routes through the harness and `GET /agent/guardrails/summary` exposes local trigger metrics. Existing graph identity, checkpointing, and MCP OAuth controls remain unchanged.
- Verified live MCP/tool payload isolation in `services/langgraph_agent/tools.py` and deterministic coverage in `tests/pipelines/test_guardrails.py` for all three mandated jailbreak variants, personal tasks, malicious retrieval content, and summary metrics.
- Validation: `python -m compileall -q services/langgraph_agent tests/pipelines/test_guardrails.py` passed and editor diagnostics are clean. Pytest could not run because the container does not have the `pytest` module installed.

### MEM-092 completed — governed episodic agent memory
- Added the isolated SQLite `AgentMemoryStore` in `services/langgraph_agent/memory.py`; it writes only to the dedicated agent-memory tables and never to `*_knowledge` retrieval stores.
- Added strict proposal lifecycle handling: one pending proposal, complete-response intent classification for `APPROVE`, `REJECT`, `EDIT`, and discard-by-default ambiguity, plus immutable audit entries with SHA-256 originating-message hashes and role metadata.
- Enforced the 90-day episodic-memory TTL and loaded approved memory facts into new LangGraph invocations through `graph.py`, `guardrails.py`, and `router.py`.
- Exposed `/agent/memory/proposals`, `/agent/memory/pending`, `/agent/memory/resolve`, and `/agent/memory/audit`; documented `AGENT_MEMORY_DB_PATH` and the governance contract in `services/api/README.md`.
- Added `tests/pipelines/test_agent_memory.py` covering approved cross-session retrieval, rejected/ambiguous discard, edited facts, single-flight enforcement, TTL expiry, and audit persistence. Focused tests pass: **8 passed** with the existing LangGraph suite.

## Planned Next Steps
- LangGraph external live-data integration completed: `services/langgraph_agent/tools.py` provides separate, read-only incident and inventory HTTP clients with runtime token resolution and a hard 4-second timeout. The graph now routes live operational questions separately from compliance RAG, supports combined live-then-RAG flows, records contacted sources, and emits a deterministic no-hallucination fallback on service errors/404s/timeouts. Added `tests/test_langgraph_external.py` covering live ticket routing, RAG isolation, and outage recovery; focused tests pass.
- Sales forecasting feasibility prototype completed: added a reproducible Random Forest pipeline at `data/pipelines/sales_forecast.py` using the protected production extract, schema/null validation, robust scaling, first-eight/final-two temporal partitioning, MSE/PSI/Gini/K2 metrics, and an actual-vs-predicted error-band plot. Added split/leakage and artifact tests at `tests/pipelines/test_sales_forecast.py`; focused suite passes (`3 passed`).
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