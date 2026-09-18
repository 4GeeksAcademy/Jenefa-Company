# Product Context — Ticket #DEV-55: Async Task Queue with Redis and Celery

## Business & User Problem
**HealthCore** is an international outpatient healthcare provider operating **12 clinics** across the US and UK (employing **200 people** with **\$28M in annual revenue**), led by **Dr. Sandra Okonkwo**. Currently, the infrastructure managed by **HealthCore Digital** is a patchwork of legacy systems. Heavy, long-running operations—such as processing batch clinical data across disconnected US and UK EHR systems, generating multi-market executive financial reports, or dispatching bulk patient notifications (vital for reducing the network's costly **22% appointment no-show rate**)—block the primary FastAPI request-response thread. While these synchronous jobs run, clinic application threads tie up, degrading performance and affecting real-time patient experience and access.

## Core Solution
Decouple heavy, cross-border data pipeline workflows from the immediate web request-response cycle using an asynchronous **Producer/Consumer Pattern** powered by **FastAPI (Producer)**, **Redis (Broker/Backend)**, and **Celery (Consumer Workers)**.

## User Experience & Performance Goals
* **Sub-200ms Response Latency:** When administrative or clinical staff trigger a report or a notification batch, the API must instantly return an HTTP `202 Accepted` response with a unique `task_id` in **under 200ms**, preserving UI responsiveness across all 12 clinics.
* **Asynchronous Visibility:** Operators and clinic managers can query task progression via a dedicated status endpoint (`GET /tasks/{task_id}`) that handles the entire task lifecycle.
* **Reliability & Observability:** The technology team led by **James Osei** gains live queue tracking via **Flower** showing queued, active, and completed tasks, while providing automated, structured telemetry to isolate processing exceptions without relying on manual phone escalations from clinic staff.

## Architectural Flow
Client ──> FastAPI (Producer) ──> Redis (Broker) ──> Celery Worker (Consumer) ──> Result/Database DLQ1. **Producer:** HealthCore API receives the request, validates lightweight record references (e.g., patient IDs, file paths), pushes the job to Redis, and instantly responds.
2. **Broker:** Redis securely holds messages in transit with a fail-safe persistence configuration, ensuring tasks are never lost even if the web API process stops.
3. **Consumer (Worker):** Independent background worker processes fetch tasks, execute them under strict timeout boundaries, and safely catch terminal errors.