# AUTH-088 — Authentication Unit Test Plan

Document-first blueprint for HealthCore authentication coverage (FastAPI + TypeScript utilities). This file is the source of truth for what we test, why, how to run it, and verified coverage.

## Why this suite exists

A recent Austin refactor bypassed token-expiration checks and locked clinical operators out for two hours. Untested auth is not production-ready: these suites guard register, login, and JWT session decisions that gate HIPAA / UK GDPR access across 12 clinics.

## How to run

### FastAPI (`pytest`)

From the FastAPI project root (`services/api`):

```bash
cd services/api
uv sync --extra test   # first time / after dependency changes
uv run pytest
uv run pytest --cov=app.auth --cov-report=term-missing
```

Coverage gate: **≥ 70%** on the `app.auth` package.

### TypeScript (`Jest`)

From the staff web app (`uis/web`):

```bash
cd uis/web
npm install
npx jest --coverage
```

Or via the package script: `npm test`.

## Scope & design rules

| In scope | Out of scope |
| -------- | ------------ |
| Auth business decisions in `app.auth.service`, `security`, `deps` | HTTP serialization / OpenAPI plumbing |
| Register (`POST /users`), login (`POST /auth/login`), token decode / expiry | Full incident CSV analysis |
| Clinic web utilities: token storage, API error parsing, user-facing messages | Next.js page rendering / E2E browser flows |

Assertions focus on **what the application decides** (accept / reject / expire / normalize), not framework routing internals.

## Test matrix

### A. FastAPI — `tests/test_register.py`

| Case | Type | Why prioritized |
| ---- | ---- | --------------- |
| `test_register_creates_active_user_with_profile` | Happy path | Baseline clinical operator onboarding |
| `test_register_rejects_duplicate_email` | Edge / failure | Prevents duplicate clinic accounts |
| `test_register_normalizes_email_to_lowercase` | Edge | Cross-region login must not fail on casing |
| `test_register_rejects_password_shorter_than_eight_chars` | Failure / AI | Empty or weak passwords must not become sessions |

### B. FastAPI — `tests/test_login.py`

| Case | Type | Why prioritized |
| ---- | ---- | --------------- |
| `test_login_returns_bearer_token_for_valid_credentials` | Happy path | Staff must obtain a session JWT |
| `test_login_rejects_incorrect_password` | Failure | Credential stuffing / typo safety |
| `test_login_rejects_inactive_user` | Edge / failure | HIPAA session termination for disabled accounts |
| `test_login_rejects_unknown_email` | Failure | No account enumeration via distinct success paths (same 401) |

### C. FastAPI — `tests/test_token.py`

| Case | Type | Why prioritized |
| ---- | ---- | --------------- |
| `test_access_token_round_trip_embeds_subject` | Happy path | Subject (`sub`) is the user id used by deps |
| `test_expired_token_fails_validation` | Failure / regression | **Production lockout root cause** — expiry must be enforced |
| `test_token_with_missing_subject_fails_current_user` | Failure | Malformed JWT must not authenticate |
| `test_password_hash_verify_rejects_wrong_secret` | Failure | Password helper integrity |

### Supplementary service rules (`tests/test_service_rules.py`)

Extra business-logic cases (profile update, password reset expiry/reuse, role permission denials, account deletion) keep `app.auth.service` above the coverage gate without asserting HTTP router plumbing.

### D. TypeScript utilities (`uis/web`)

| Module | Happy path | Failure mode |
| ------ | ---------- | ------------ |
| `authStorage` | Persist / read token | SSR (`window` undefined) returns `null`; clear removes key |
| `userFacingError` | Status → operator-safe copy | Technical / connection errors never leak raw stack text |
| `api` (`readJson`) | Parse successful JSON body | Non-OK detail / invalid JSON becomes `ApiRequestError` |

## AI-assisted discovery / regression note

**AI-assisted case:** While reviewing `create_access_token` / `decode_access_token` against the product incident (broken expiry), an intentionally expired JWT (`expires_delta` in the past) was added as `test_expired_token_fails_validation`. This locks in the rule that `jose` must reject `exp` in the past before `get_current_user` can load a clinic user.

**Bug caught by the suite:** `UserCreate.password` previously accepted empty / sub-8-character passwords (unlike reset/change-password). Registration now enforces a minimum of 8 characters; covered by `test_register_rejects_password_shorter_than_eight_chars`.

## Coverage results

Verified on 2026-08-16 after suite execution.

| Suite | Command | Result |
| ----- | ------- | ------ |
| FastAPI auth module | `cd services/api && uv run pytest --cov=app.auth --cov-report=term-missing` | **24 passed**, **84%** total coverage on `app.auth` (gate ≥ 70%) |
| TypeScript utilities | `cd uis/web && npx jest --coverage` | **8 passed** across `authStorage`, `userFacingError`, `api.readJson` |

### FastAPI coverage detail (auth business modules)

| Module | Cover |
| ------ | ----- |
| `app/auth/config.py` | 85% |
| `app/auth/database.py` | 84% |
| `app/auth/deps.py` | 53% |
| `app/auth/schemas.py` | 93% |
| `app/auth/security.py` | 92% |
| `app/auth/service.py` | 84% |
| **TOTAL** | **84%** |

Thin HTTP routers and email dispatch are omitted from the coverage denominator (wiring / third-party I/O); assertions target service and security decisions instead.

