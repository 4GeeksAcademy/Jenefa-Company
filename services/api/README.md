# HealthCore API

FastAPI service for incident CSV analysis and staff JWT authentication (TinyDB).

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

Incident responses never include `patient_id` or other PHI — only aggregate counts and rule labels.
