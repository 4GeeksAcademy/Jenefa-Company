# HealthCore API

Unified FastAPI service for HealthCore Digital.

Layout follows [`../directory.md`](../directory.md):

```text
services/api/
  main.py              # FastAPI application
  models.py            # Pydantic supplier models
  database.py          # TinyDB initialisation
  routes/suppliers.py  # supplier directory endpoints
  seed.py              # initial data loading script
  routes/incidents.py  # incident analysis (existing)
  app/                 # shared incident state + legacy entrypoint
```

## Run locally

```bash
cd services/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Idempotent supplier seed (skips if db.json already has rows)
uv run seed
# or: python seed.py

uvicorn main:app --reload --port 8000
```

`uv run seed` / `python seed.py` read `db.json` first. If any suppliers exist, they print `Inserted 0 records.` and do not write duplicates.


- API docs: http://127.0.0.1:8000/docs
- Supplier Jinja UI: http://127.0.0.1:8000/home
- React page: `uis/backoffice` → `/suppliers` (Home shell)

Legacy incident-only entrypoint remains: `uvicorn app.main:app --port 8000`.

## Endpoints

| Method | Path | Description |
| ------ | ---- | ----------- |
| `POST` | `/suppliers` | Create supplier |
| `GET` | `/suppliers` | List; optional `country`, `category` |
| `GET` | `/suppliers/{id}` | Fetch one |
| `PATCH` | `/suppliers/{id}/rate` | Update monthly rate + `updated_at` |
| `PATCH` | `/suppliers/{id}/status` | Set `active` / `suspended` |
| `DELETE` | `/suppliers/{id}` | Hard-delete |
| `POST` | `/api/incidents/analyze` | Incident CSV analysis |
| `GET` | `/api/incidents/results/export` | Export latest results CSV |
| `GET` | `/health` | Liveness |
