# HealthCore API

FastAPI service for incident CSV analysis, staff JWT authentication (TinyDB),
and clinic supply inventory (SQLModel ledger on SQLite or Supabase PostgreSQL).

## Run locally

```bash
cd services/api
cp .env.example .env
# Set SECRET_KEY (required). Optionally configure email keys for password reset.
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Environment variables

| Variable | Required | Description |
| -------- | -------- | ----------- |
| `SECRET_KEY` | Yes | JWT signing secret |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No (default `30`) | Access token lifetime |
| `PASSWORD_RESET_EXPIRE_MINUTES` | No (default `60`) | Reset token lifetime |
| `FRONTEND_BASE_URL` | No (default `http://localhost:3001`) | Base URL used in reset email links (`/reset-password?token=…`) |
| `AUTH_DB_PATH` | No | Override TinyDB path (default `data/auth.json`) |
| `INVENTORY_DATABASE_URL` | No | SQLModel engine URL. Accepts `SUPABASE_DB_URL` / `DATABASE_URL`. Default: SQLite `data/inventory.db` |
| `INVENTORY_SEED_PASSWORD` | No | Password for seeded clinic operators (`usr-hc-9901`, `usr-hc-2544`) |
| `EMAIL_PROVIDER` | No | `resend`, `sendgrid`, or omit (auto / console fallback) |
| `RESEND_API_KEY` | For Resend | Resend API key — never hardcode |
| `SENDGRID_API_KEY` | For SendGrid | SendGrid API key — never hardcode |
| `EMAIL_FROM` | No | From header (default `HealthCore <onboarding@resend.dev>`) |

Without a provider API key, password-reset emails are logged to the API console (dev fallback) so the token pipeline can still be tested. With Resend or SendGrid configured, registered addresses receive a real message containing the reset link.

## Endpoints

| Method | Path | Auth | Description |
| ------ | ---- | ---- | ----------- |
| `GET` | `/health` | Public | Liveness |
| `POST` | `/api/incidents/analyze` | Public | Multipart incident CSV → JSON metrics |
| `GET` | `/api/incidents/results/export` | Public | Stream latest `results.csv` |
| `POST` | `/users` | Public | Register |
| `POST` | `/auth/login` | Public | Issue JWT |
| `GET` | `/auth/me` | Bearer | Current user + profile |
| `POST` | `/auth/forgot-password` | Public | Always `200`; emails link only if registered |
| `POST` | `/auth/reset-password` | Public | Consume reset token; `400` if expired/used |
| `POST` | `/auth/change-password` | Bearer | Change password while signed in |
| `GET`/`PUT` | `/profiles/me` | Bearer | Profile read/update |
| `GET` | `/inventory/products` | Bearer | Catalog with computed `current_stock` |
| `POST` | `/inventory/products` | Bearer | Register supply (stock starts at `0`) |
| `GET` | `/inventory/products/{id}` | Bearer | Supply plus clinic partition quantities |
| `POST` | `/inventory/orders/inbound` | Bearer | Ledger inbound; stamps TinyDB `user_uuid` |
| `POST` | `/inventory/orders/outbound` | Bearer | Ledger outbound; `400` if partition would go negative |
| `GET` | `/inventory/orders` | Bearer | Unified inbound/outbound log with preloaded supplies |

On first boot, empty catalog databases are seeded to the HealthCore spec balances (gloves `450`, sedative `35`). Stock is never stored on `MedicalSupply` rows.

Incident responses never include `patient_id` or other PHI — only aggregate counts and rule labels.

## Tests

Full plan, matrix, and coverage notes live in the repo-root [`TESTING.md`](../../TESTING.md).

From the repository root:

```bash
uv sync
uv run pytest
```

From this directory:

```bash
uv sync --extra test
uv run pytest
uv run pytest --cov=app.auth --cov-report=term-missing
```
