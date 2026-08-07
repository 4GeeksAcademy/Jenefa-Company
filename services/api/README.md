# HealthCore Incident Analysis API

FastAPI service that runs the shared `scripts/incident_core` validator on uploaded incident CSVs.

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

## Endpoints

| Method | Path | Description |
| ------ | ---- | ----------- |
| `POST` | `/api/incidents/analyze` | multipart file upload → JSON metrics |
| `GET` | `/api/incidents/results/export` | stream latest `results.csv` |
| `GET` | `/health` | liveness |

Responses never include `patient_id` or other PHI — only aggregate counts and rule labels.
