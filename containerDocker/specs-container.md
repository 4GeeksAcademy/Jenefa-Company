# Project Context: Ticket #infra-40 & HealthCore Monorepo Dockerization

## UI Service Configuration (`/uis/Dockerfile`)
### Base Image: 
- Official Node.js Alpine image (`node:alpine`).
### Dependency Isolation
- Install dependencies for `/uis/website` and `/uis/backoffice` separately within the build process to guarantee isolation.
### Orchestration Entrypoint (`start.sh`)
  - Configured as the default container execution payload (`CMD ["/bin/sh", "/uis/start.sh"]`).
  - Concurrently starts the two Next.js frontend applications on dedicated local virtual hosts.
  - Directs traffic over explicitly isolated infrastructure ports:
    - `website` maps to internal port **`3000`** (Public-facing patient portal).
    - `backoffice` maps to internal port **`3001`** (Internal clinical administration panel).
### Workspace Exclusion (`/uis/.dockerignore`)
  - Minimally strips local artifacts before context copies.
  - Target arrays: `node_modules`, `.next`, `.env*`, and `*.log`.

## Backend Service Configuration (`/services/Dockerfile`)
### Base Image
- Official Python image (`python:3.12-slim` or similar official stream).
### Dependency Orchestration Engine
- Must explicitly bundle and run Astrals' high-speed package manager `uv`.
### Build Executable Chain
- Installs internal components via `uv pip install -r requirements.txt`.
### Runtime Strategy
- Leverages the continuous development framework via hot-reloading hooks: `uvicorn main:app --host 0.0.0.0 --port 8000 --reload`.
### Workspace Exclusion (`/services/.dockerignore`)
  - Drops tracking caches, tests, and temporary storage vectors before layer compilation.
  - Target arrays: `__pycache__`, `*.pyc`, `.env*`, `tests/`, and `*.log`.

## Service Orchestration (`docker-compose.yml`)
### Repository Root Deployment
 - Placed strictly at the repository root level to spin up the multi-language ecosystem dynamically.
### Service Blueprint Definitions
  - `ui` :  Built from the `/uis/` context path, establishing local directory bind mounts to enable instant UI code changes without image rebuilds. Launches the dual apps using development hooks (`next dev`).
   - `backend` : Built from the `/services/` context path, binding local changes directly into the container filesystem while passing the runtime `--reload` argument.
### Network Enclosure
  - Services are isolated into a dedicated, explicitly named Docker network fabric (e.g., `healthcore-network`).
### Zero-Localhost Mandate 
- Forbids inter-service routing via `localhost` or hardcoded IPs. 
  - Services must route across internal proxies via explicit container host discovery labels (`http://backend:8000` or `http://ui:3000`).
### Environment and Identity Security
  - Injects all local environment variables using a central, decoupled root `.env` document.
  - Explicitly bans hardcoding API tokens, credentials, or secrets inside any `Dockerfile` or `docker-compose.yml`.
  - Mandates that the root-level `.env` profile is explicitly tracked under the monorepo's `.gitignore` asset and completely omitted from source control history.

---

## Evaluation and Automated Verification Checklist

### Unified Startup Sequence
- Execution of `docker compose up` from the workspace root boots both language spaces into active health matrices with zero manual configurations or errors.
### Active Code Reflection (Hot Reloading)
- Modifications saved within local host directories immediately register within active browser targets without provoking full build cycles.
### Single-Container Frontend Multi-Hosting
- The `ui` layer service successfully runs and isolates the public web node and internal backoffice dashboard over parallel targets (`3000` and `3001`).
### Host-Name DNS Validation
- All endpoint configurations connect internally utilizing Docker service network name aliases rather than fallback IP structures or loopback hosts (`localhost`).
### Zero-Leak Compliance Inspection
- Automated reviews guarantee no plaintext secrets cross path files, checking that the base tracking index `.gitignore` correctly excludes the root `.env` layout.
### Ignore-Matrix Assertions 
- Proper validation checks that valid `.dockerignore` filters isolate intermediate folders across both `/uis/` and `/services/`.
