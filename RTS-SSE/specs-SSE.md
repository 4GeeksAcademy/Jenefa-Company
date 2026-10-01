# Technical Specifications: Real-Time RFP Notification Push Layer

## 1. Objective & Scope
The goal of this implementation is to eliminate manual dashboard polling across the **HealthCore** internal network and replace it with a robust, unidirectional real-time data stream using **Server-Sent Events (SSE)**. The frontend must immediately display a notification when a new Request for Proposal (RFP) / contract processing ticket is registered by the multi-agent system.

### In-Scope
* Extending the existing **HealthCore Central API** (`services/`) with an authenticated SSE streaming endpoint.
* Refactoring the existing **HealthCore Digital Dashboard** view (`uis/`) to consume and render the real-time event pipeline.
* Engineering a resilient streaming consumer utilizing `fetch` and a streaming reader interface to handle custom authorization vectors cleanly.
* Validating stability, headers, connection loss resilience, and data structures inside automated test frameworks (`tests/`).

### Out-of-Scope
* Executing any downstream calls to generative LLMs, clinical documentation assistants, or automated coding models during this milestone. This deliverable focuses exclusively on the real-time communication transport and state presentation layer.
* Altering overall file structures or starting isolated app bundles outside the existing workspace routes.

---

## 2. Architecture & File Placement
All components must be injected directly into the active monorepo paths. Do not create parallel app directories or isolated delivery folders:
* **Backend SSE Endpoints & Event Distribution:** `services/`
* **Frontend Component Views & Streaming Consumers:** `uis/`
* **Automated End-to-End & Integration Suites:** `tests/`

---

## 3. Package & Dependency Management
* **Backend Additions:** Any newly introduced packages or utilities required for async streaming event streams must be installed using `uv add` inside the designated directory. 
* **Frontend Additions:** Any required script or stream consumption library adjustments must use the native package manager lockfile rules already specified in the monorepo.
* **Strict Constraint:** Never execute unmanaged `pip install`, `pipenv`, or standard global environment changes.

---

## 4. Backend Implementation Requirements (`services/`)

### 4.1. SSE Endpoint Mechanics
* **Event Core:** The endpoint must expose a persistent streaming channel that explicitly writes and flushes an event every time a new RFP ticket registers in the workspace.
* **Event Categorization:** The stream must emit an explicitly named event string (e.g., `event: rfp_ticket_created`). Implementations that fall back onto a generic, un-typed fallback stream block will fail evaluation.
* **Stream Packaging Headers:** The stream response payload must explicitly yield and maintain the following protocol attributes:
  * `Content-Type: text/event-stream`
  * `Cache-Control: no-cache`
  * `Connection: keep-alive`
* **Keep-Alive Protection:** Implement empty comment frame pinging sequences (`:\n\n` or equivalent) on a regular cadence to keep intermediate routers, firewalls, and gateways from preemptively clipping the long-running socket connection.

### 4.2. Token Verification & Healthcare Regulatory Guardrails
* **Stream Access Control:** The backend endpoint must actively validate and protect the event stream utilizing the **exact same JWT validation routine** enforced across standard backoffice REST endpoints.
* **Access Rejection:** Any anonymous or unauthenticated requests must be immediately dropped with standard verification error codes before establishing the streaming buffer.
* **Compliance Alignment:** In accordance with **HealthCore’s obligations under US HIPAA and UK GDPR**, the SSE endpoint must be fully audited. It must log access parameters securely, ensuring that unauthenticated clients never receive access to protected data structures.

---

## 5. Frontend Implementation Requirements (`uis/`)

### 5.1. View Refactoring
* **Zero-Action Updates:** Refactor the existing dashboard interface so that incoming ticket data instantly displays visually on the screen without demanding an explicit manual mouse interaction, polling cycle, or full page reload.

### 5.2. Stream Consumption Protocols
* **Constraint (No Bare EventSource):** Standard browser `EventSource` interfaces do not allow clean custom authentication header attachment. 
* **Mandated Approach:** The client application must consume the real-time stream via a standard `fetch` call combined with an active `ReadableStream` reader (or your frontend environment's equivalent stream parser).
* **Credential Injection:** Pass the active user context token through authentic, secure request headers:
Authorization: Bearer <JWT_TOKEN>

### 5.3. Disconnect Resilience & Connection Recovery
* **Progressive Backoff Loops:** If the socket transport fails, drops, or faces an unexpected exception, the application must initiate an auto-reconnection loop featuring a clear progressive backoff algorithm to avoid hammering infrastructure nodes.
* **State Recovery Strategy:** To guarantee that events fired during a temporary drop are not silently discarded, the client application must implement an explicit recovery strategy:
* *Strategy Selection:* **Refetch-on-Reconnect**. Upon successful stream re-establishment, the application triggers a targeted fetch to sync items since the disconnection time, and uses the real-time stream exclusively for all subsequent arrivals.
* **Airtight Deduplication Engine:** The client-side UI data store must cross-reference arriving identifiers against its localized memory footprint. If an incoming `ticket_id` matches an item already registered or rendered during the reconnect window, the system must filter it out to prevent twin duplicate alerts from populating on the screen.

### 5.4. UX Visibility Requirements
* **Visual Isolation:** The new RFP arrival notification must be instantly and visually distinguishable from general ambient dashboard changes or system metric tickers.
* **Data-Efficient State Changes:** Processing the arriving payload must execute localized state updates. It must **not** force a heavy, global re-fetch of every single dataset on the screen or cause an intrusive page flicker.

---

## 6. Testing & Validation Checklist (`tests/`)

### 6.1. Endpoint Testing Matrix
* Assert that the streaming response headers explicitly contain `text/event-stream`.
* Verify that the raw wire payload outputs the named event type correctly (e.g., `event: rfp_ticket_created`).
* Validate that the payload data string parses into valid JSON conforming exactly to the core property shapes and business naming fields specified inside `CONTEXT.md`. (Abstract, keyless dictionary validation blocks disconnected from the actual wire stream format are invalid).

### 6.2. Reconnection & Resilience Validation
* Provide explicit automated assertions or highly documented manual verification playbooks tracking the drop lifecycle.
* Confirm that the backoff mechanism triggers as expected upon socket breakdown.
* Verify that missing tickets are safely recovered without causing visual layout duplicate artifacts for an identical `ticket_id`.