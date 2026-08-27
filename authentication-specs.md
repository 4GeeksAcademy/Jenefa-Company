# Technical Specifications: JWT Auth Layer & TinyDB Storage

## System Architecture Flow
[Client Request]│▼[FastAPI Router] ──( Reads Authorization: Bearer  Header )──► [get_current_user Dependency]│                                                                      │├─► Valid Token / Matching Ownership ──────────────────────────────────┼─► [Proceed to Route]├─► Missing, Malformed, or Expired Token ──────────────────────────────┼─► HTTP 401 Unauthorized└─► Valid Token but Insufficient Permissions (Resource Mis-match) ─────┴─► HTTP 403 Forbidden
## Database Schema (TinyDB Only)
`User` and `Profile` collections must reside exclusively within TinyDB. Do not create user or profile tables in Supabase/SQLModel. Other transactional or analytical Postgres/Supabase tables must reference the user by mapping the TinyDB user `id` field into a `user_uuid` string column.

### 1. User Model
Stored in the TinyDB users collection. Do not store display name or contact data fields here.
```json
{
  "id": "string (UUIDv4)",
  "email": "string",
  "hashed_password": "string",
  "is_active": "boolean",
  "role": "string (admin | manager | user)",
  "created_at": "string (ISO 8601 timestamp)"
}
```

### 2. Profile Model
Stored in the TinyDB profiles collection. Maintains a strict 1-to-1 relationship with the user record.
```json
{
  "id": "string (UUIDv4)",
  "user_id": "string (TinyDB User ID mapping anchor)",
  "name": "string",
  "phone": "string",
  "address": "string"
}
```

## Security & Cryptography Rules
*   **Password Hashing**: Passwords must never be stored or evaluated in plain text. Hashing operations must use `passlib` configured with the `bcrypt` scheme.
*   **Secret Management**: The cryptographic signing secret must be injected dynamically via runtime environment configurations (`.env`). Hardcoding strings into logic modules is strictly forbidden.
*   **Token Expiration**: Lifespan limits must be parsed from the configuration key `ACCESS_TOKEN_EXPIRE_MINUTES`.

## Endpoint & Routing Matrix

### Auth Module (`/auth`)
*   `POST /auth/login` [PUBLIC]: Validates a plain text payload (`email`, `password`) against database hashes. Returns a signed stateless JWT token structure containing the user's ID within the `sub` claim.
*   `GET /auth/me` [PROTECTED]: Decodes incoming token data. Returns the current user's `email`, `role`, and their complete nested `Profile` metadata structure.

### Users Module (`/users`)
*   `POST /users` [PUBLIC]: Registers a new system user, defaulting the role field to `user`. Accepts optional inline profile fields (`name`, `phone`, `address`) and handles the creation of the linked TinyDB Profile collection entry within a single atomic service transaction.
*   `GET /users` [PROTECTED]: Lists all registered system accounts.
*   `GET /users/{id}` [PROTECTED]: Retrieves a target account record matching the identifier argument.
*   `PUT /users/{id}` [PROTECTED]: Modifies core credential properties like `email` or `role`. Restricted to the account owner themselves or a user carrying an `admin` role. Returns a `403 Forbidden` error response if a non-admin tries to mutate an account entity that they do not own.
*   `DELETE /users/{id}` [PROTECTED]: Completely purges a target user record and runs a cascading operation to delete the associated profile item from the system.

### Profiles Module (`/profiles`)
*   `GET /profiles/me` [PROTECTED]: Fetches the calling user's personal profile information.
*   `PUT /profiles/me` [PROTECTED]: Modifies specific profile text properties (`name`, `phone`, `address`). Restricted exclusively to the verified owner of that profile entity.

### Cross-Functional Route Hardening Baseline
The `get_current_user` restriction boundary must be explicitly applied as a path dependency to at least 5 preexisting monorepo endpoints that expose or manipulate data structures outside `/auth` or `/users`.
1.  `GET /clinics/telemetry` [PROTECTED]: Operational tracking across locations.
2.  `POST /appointments/booking` [PROTECTED]: Appointment reservation processing engine.
3.  `PUT /billing/claims/{id}` [PROTECTED]: Insurance claim record coding evaluations.
4.  `GET /compliance/audit-logs` [PROTECTED]: Centralized audit data query layer.
5.  `POST /ai/clinical-documentation` [PROTECTED]: LLM documentation assistance pipeline.

## Implementation Guide: Authentication Dependency
```python
import os
from datetime import datetime, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

# Cryptographic context configs
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_uuid: str = payload.get("sub")
        if user_uuid is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    # Query TinyDB for the target user entity
    user = db_users.get(where("id") == user_uuid)
    if user is None:
        raise credentials_exception
    return user
```

## Verification & Manual Testing Scenarios
Verify full endpoint isolation and security controls using the FastAPI interactive documentation framework (`/docs`):

1.  **Happy Path Registration & Login Flow**:
    *   Execute an unauthenticated call to `POST /users` with profile fields.
    *   Submit those identical login criteria to `POST /auth/login` and copy the returned string value.
    *   Inject that text block into the Authorize lock interface within `/docs`.
    *   Execute queries against a protected path (e.g., `GET /auth/me`) to confirm success.
2.  **Missing Authorization Token Vector**:
    *   Clear all browser test tokens or open a separate clean environment session.
    *   Submit a direct query call targeting any protected routing path.
    *   Validate that the server intercept yields a clean `401 Unauthorized` status response.
3.  **Invalid Session Vector**:
    *   Pass a deliberately malformed token string or a token where timestamp expiration metrics have passed.
    *   Submit a query tracking against protected routing paths.
    *   Validate that the route rejects the entry attempt with a `401 Unauthorized` status response.
4.  **Resource Ownership Cross-Over Vector**:
    *   Authenticate an active session using an standard user profile credentials parameter.
    *   Attempt an update operation using `PUT /users/{id}` or `PUT /profiles/me` specifying an external user's unique identification parameters.
    *   Validate that the engine halts execution and yields an explicit `403 Forbidden` error status response.