# Technical Specification: Monorepo Containerization (Ticket #infra-40)

## 1. Architecture Overview
The local monorepo topology transitions into an isolated, explicitly named internal Docker bridge network. 

[ Local Browser / Host Machine ]
│               │
(Port 3000)     (Port 3001)   (Port 8000)
│               │               │
▼               ▼               ▼
┌────────────────────────────────┐   ┌────────────────────────────────┐
│ ui service                     │   │ backend service                │
│ (UI Container - Node Alpine)   │   │ (Python Container)             │
│                                │   │                                │
│  /website (3000)   [next dev]  │   │  FastAPI Application (8000)    │
│  /backoffice (3001) [next dev] │   │  [uvicorn --reload]            │
│                                │   │                                │
│       Sends Network Requests   │   │  Accessible over network via:  │
│       using service name ──────┼───►  http://backend:8000           │
└────────────────────────────────┘   └────────────────────────────────┘

## 2. Component Specifications

### 2.1 Configuration & Security Boundaries (`/.env` & `.gitignore`)
Operating inside a high-stakes medical domain governed strictly by **HIPAA** (US) and **UK GDPR** (UK), security compliance requires an absolute separation of secrets from the container configurations.
* **Variables Layer**: Define all required environment variables for each service inside a root-level `.env` file. No environment variables, medical systems metadata, or credentials may be hardcoded inside YAML or Dockerfile files.
* **Repository Safety**: Ensure `.env` is explicitly documented in the root `.gitignore` file. It must never be committed to Git history to preserve data governance protocols.

### 2.2 Frontend Infrastructure (`/uis/`)
The frontend service wraps two decoupled Next.js projects inside a singular Node.js Alpine container abstraction.

* **Target Paths**: `/uis/website` (Public-facing patient portal) and `/uis/backoffice` (Internal clinical/admin panel).
* **Output Artifacts**: `/uis/Dockerfile` and `/uis/.dockerignore`
* **Execution Requirements**:
  * **Base Image**: Official Node Alpine image.
  * **Dependencies**: Build steps must isolate and install the dependencies for `/uis/website` and `/uis/backoffice` separately.
  * **Container Lifecycle**: The default `CMD` must invoke an internal `start.sh` script. This script orchestrates and kicks off both Next.js applications on separate ports concurrently (`website` on `3000`, `backoffice` on `3001`) via `next dev`.
  * **Exclusion Control**: The `/uis/.dockerignore` file must exclude at a minimum: `node_modules`, `.next`, `.env*`, and `*.log`.

### 2.3 Backend Infrastructure (`/services/`)
The service API wrapper runs as an independent container service using fast dependency management tools to drive HealthCore’s centralized API pipeline.

* **Target Path**: `/services` (FastAPI core instance wrapping EHR integrations, scheduling backends, and billing layers).
* **Output Artifacts**: `/services/Dockerfile` and `/services/.dockerignore`
* **Execution Requirements**:
  * **Base Image**: Official Python image.
  * **Package Management**: The build layer must explicitly install `uv`, then install backend requirements using `uv pip install -r requirements.txt`.
  * **Container Lifecycle**: Launches the API runtime with an active Uvicorn server running with `--reload` enabled.
  * **Exclusion Control**: The `/services/.dockerignore` file must exclude at a minimum: `__pycache__`, `*.pyc`, `.env*`, `tests/`, and `*.log`.

### 2.4 Orchestration Platform (`/docker-compose.yml`)
Located strictly at the repository root, the orchestration file ties the HealthCore Digital infrastructure layers together.

* **Service Declarations**:
  * `ui`: Constructed out of the `/uis/` build context.
  * `backend`: Constructed out of the `/services/` build context.
* **Port Mapping**: Expose and bind the correct ports explicitly (`3000`, `3001`, and `8000`) so they are fully accessible from the local host system machine.
* **Hot Reloading via Bind Mounts**: Map host directories to container paths using bind mounts on both services. Code changes made on the host machine must instantly reflect in the browser runtime without rebuilding container layers.
* **Networking**: Connect both services together on an explicitly named Docker network. Inter-service connection URLs must use the service name as the host (e.g., `http://backend:8000`) instead of `localhost` or hardcoded internal IP strings.
* **Environment Extraction**: Seamlessly pipe variable context from the root `.env` configuration file down to the target microservices dynamically without hardcoding values in the YAML markup.

## 3. Evaluation & Acceptance Criteria
* [ ] The command `docker compose up` executed from the repository root successfully builds and boots the full platform without errors or manual baseline adjustments.
* [ ] Code updates on the host are reflected live in the browser without container image rebuild events (bind mounts validated).
* [ ] The UI service starts up both decoupled Next.js projects on independent target ports (`3000` and `3001`) simultaneously from one running container runtime.
* [ ] Cross-service request bindings route exclusively via internal Docker service name DNS, rejecting any `localhost` or static IP configuration hooks.
* [ ] Absolutely zero secrets, passwords, or API tokens are checked into `Dockerfile` files or the main `docker-compose.yml` block.
* [ ] The configuration target `.env` file safely exists inside `.gitignore` and is entirely clean from the git commit footprint.
* [ ] Both subfolders `/uis/` and `/services/` contain active, configured `.dockerignore` filters.