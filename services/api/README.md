# HealthCore Incident Management API

FastAPI service for centralized incident CRUD, lifecycle transitions, and summary metrics.

**Entry point:** [`app.py`](./app.py) — `uvicorn app:app --reload --port 8000`

## Run locally

```bash
cd services/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```

Swagger UI: http://127.0.0.1:8000/docs

Database: SQLite file at `services/api/incidents.db` (override with `INCIDENTS_DB_PATH`).

## Endpoints

| Method | Path | Description |
| ------ | ---- | ----------- |
| `POST` | `/api/incidents` | create a validated incident (`201`, `400`) |
| `GET` | `/api/incidents` | list incidents with optional `status`, `origin`, `branch`, `category` filters |
| `GET` | `/api/incidents/{id}` | get one incident (`404` if missing) |
| `PATCH` | `/api/incidents/{id}/status` | apply state-machine status transition (`400` invalid transition) |
| `GET` | `/api/incidents/summary` | grouped counts by status/category/origin/branch (with zero-count keys) |
| `GET` | `/health` | liveness |

## Historical seed

From the repo root:

```bash
python3 scripts/seed_incidents.py
```

The script maps legacy CSV values into the central model, hardcodes `origin=customer`, and is idempotent (`source_key` unique constraint).
