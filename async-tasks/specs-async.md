# Technical Specifications — Ticket #DEV-55

## System Architecture & Infrastructure
* **Containerized Redis:** Configured inside `docker-compose.yml` as a broker service using the official Redis image, exposing standard port `6379`.
* **Redis Memory Policy:** Must strictly use the `noeviction` memory policy to guarantee that task data, compliance states, and patient queue messages are never prematurely purged.
* **Connection Management:** Both the API and workers connect to this same Redis instance via a shared `REDIS_URL` environment variable.
* **Monitoring:** Flower must be added to `docker-compose.yml` as a tracking service accessible on port `5555`.

## Environment & Dependency Management
* **Dependency Installation:** The project explicitly utilizes `uv` for modern package tracking. Ensure required toolchain dependencies are installed via:
  ```bash
  uv add celery redis flower
  ```

## Celery Module Architecture (`services/`)
* **Module Initialization:** Create the foundational Celery orchestration file inside the HealthCore monorepo layout path at `services/celery_app.py`.
* **Backend Roles:** Configure the Celery instance to point to Redis as both the message broker and the result backend.
* **Task Definition:** Convert the slowest existing operational candidate in the HealthCore platform (e.g., cross-market data aggregation or bulk notification triggers) into an asynchronous task encapsulated via `@app.task`.
* **Payload Boundary:** Task messages must strictly contain only lightweight identifiers or data references (e.g., database IDs, specific cloud object paths). Moving raw blobs, unencrypted clinical health documents, or large raw data batches inside the message payload is strictly forbidden.
* **Worker Isolation:** Workers run as separate, independent processes. Stopping or restarting the FastAPI process must not terminate the worker process or drop queued tasks.

## Setup & Verification Pipeline
* **Pre-Flight Connection Check:** Before modifying or routing any production API endpoint code, spin up a local worker to verify seamless infrastructure communication:
  ```bash
  celery -A services.celery_app worker --loglevel=info
  ```
  Ensure the worker successfully registers, discovers the defined task space, and connects to the Redis broker without configuration errors.

## API Endpoints & Behavior

### 1. Trigger Async Operation
* **Method & Route:** Target resource endpoint (e.g., `POST /reports/generate` or `POST /notifications/bulk`).
* **Performance:** Must complete execution and return a response in **under 200ms**.
* **Response Code:** `202 Accepted`
* **Response Body:**
  ```json
  {"task_id": "<uuid_string>"}
  ```

### 2. Check Task Status
* **Method & Route:** `GET /tasks/{task_id}`
* **Behavior:** Queries the task status state directly in Redis.
* **Response Body:**
  ```json
  {
    "task_id": "<uuid_string>",
    "status": "<state>",
    "result": null
  }
  ```
* **Allowed States:** The `status` field must precisely map to standard Celery task states: `pending`, `started`, `success`, or `failure`.

## Reliability, Error Handling & DLQ
* **Retry Strategy:** Tasks must be configured with `max_retries=3`.
* **Backoff Configuration:** Retries must implement exponential backoff by dynamically increasing the `countdown` period between subsequent attempts. Immediate, consecutive retries are forbidden.
* **Acknowledgment Control (ACK):** Task message acknowledgement must only occur *after* successful execution completion.
* **Dead Letter Queue (DLQ) Database Logging:** When a task fails its final attempt and exceeds `max_retries`, a failure record must be automatically written to the database acting as a DLQ. The recorded schema must contain:
  * `task_id`
  * `attempt_number`
  * `error` (the full exception message/stack trace)
  * `timestamp`

## Regulatory, Observability & Documentation
* **Compliance Framework:** Task execution, storage logs, and data flows must be designed to adhere to **HIPAA** guidelines for US data and **UK GDPR** regulations for UK data.
* **Structured Logs:** Every executed task must log its `task_id`, `attempt_number`, resulting status, and total execution duration. Failed attempts must additionally append the full error message to the log stream to ensure strict, auditable tracking.
* **Demonstration Criteria:** The Flower dashboard must demonstrate visibility by showing at least one successfully completed task and one failed task during execution testing.
* **Runbook Documentation:** The monorepo `README.md` must clearly document explicit instructions on how to start and stop the independent worker processes.
