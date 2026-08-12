# HealthCore Unified API

FastAPI service providing:

1. Incident CSV analysis (`scripts/incident_core`)
2. Stateless JWT authentication with TinyDB-backed `User` / `Profile` collections (AUTH-01)

## Run locally

```bash
cd services/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # or: uv pip install -r requirements.txt
cp .env.example .env              # set a strong SECRET_KEY
uvicorn app.main:app --reload --port 8000
```

Open interactive docs at `http://127.0.0.1:8000/docs`.

## Auth quick start

1. `POST /users` — register (`email`, `password`, optional `name` / `phone` / `address`)
2. Log in either way:
   - `POST /auth/login` JSON: `{ "email": "...", "password": "..." }`
   - Or click **Authorize** in `/docs` and enter **username = your email**, plus password (leave client id/secret empty)
3. Response / Authorize yields a Bearer token — then call protected routes such as `GET /auth/me`

Missing / invalid tokens return **401**. Ownership / role violations return **403**.

## Endpoints

| Method | Path | Auth | Description |
| ------ | ---- | ---- | ----------- |
| `POST` | `/auth/login` | public | Issue JWT (`sub` = TinyDB user id) |
| `GET` | `/auth/me` | bearer | Current email, role, nested profile |
| `POST` | `/users` | public | Register user + linked profile |
| `GET` | `/users` | bearer | List accounts |
| `GET` | `/users/{id}` | bearer | Fetch account |
| `PUT` | `/users/{id}` | bearer | Update email/role (owner or admin; role changes admin-only) |
| `DELETE` | `/users/{id}` | bearer | Delete user + cascade profile |
| `GET` | `/profiles/me` | bearer | Own profile |
| `PUT` | `/profiles/me` | bearer | Update own profile |
| `GET` | `/clinics/telemetry` | bearer | Clinic telemetry stub |
| `POST` | `/appointments/booking` | bearer | Booking stub |
| `PUT` | `/billing/claims/{id}` | bearer | Claims review stub |
| `GET` | `/compliance/audit-logs` | bearer | Audit query stub |
| `POST` | `/ai/clinical-documentation` | bearer | Clinical documentation stub |
| `POST` | `/api/incidents/analyze` | public* | multipart CSV → JSON metrics |
| `GET` | `/api/incidents/results/export` | public* | stream latest `results.csv` |
| `GET` | `/health` | public | liveness |

\*Incident routes remain public until frontend token injection ships (AUTH-01 out of scope).

## Storage & security

- `User` / `Profile` live only in TinyDB (`data/auth.json` by default). No user tables in SQL/Supabase.
- Passwords hashed with bcrypt via `passlib` (`libpass` on Python 3.14).
- `SECRET_KEY` and `ACCESS_TOKEN_EXPIRE_MINUTES` come from `.env` (never hardcode).
- Incident responses never include `patient_id` or other PHI.
