# Product Context: Incident Management System (HealthCore Digital)

## Overview
An incident represents a tracked occurrence, operational failure, or reported issue within the HealthCore ecosystem. Shifting away from historical, file-bound analysis exports, this platform operates as a centralized, real-time tracking suite managed by **HealthCore Digital**. 

Anyone across the organization—whether deployed at one of the 12 international clinics, managing traffic from Austin headquarters, or processing a customer-reported issue—can log, query, and monitor issues dynamically from a single workspace.

## Lifecycle States & State Machine Transitions (`status`)
Incidents transition through a strict, controlled state-machine loop across their lifespan to preserve operational workflows. Any attempt to bypass these guardrails or perform invalid sequence jumps is blocked instantly with explicit bad request feedback to preserve data auditability:
* **`open`**: The incident has been newly submitted. It can proceed to **`in_progress`** for active handling, or directly to **`discarded`** if irrelevant.
* **`in_progress`**: A clinic agent, developer, or billing specialist is working on a resolution. It can advance to **`resolved`** once fixed, or **`discarded`** if abandoned.
* **`resolved`**: Operational fix complete. This is a terminal state.
* **`discarded`**: Handled as duplicate, spam, or false-positive. This is a terminal state.

## Reporting Streams (`origin`)
Issues can enter the system through three distinct channels:
* **`customer`**: Directly reported from consumer patient apps, support chats, or client portals.
* **`branch`**: Logged by medical personnel or administration on-site at one of the 12 clinics.
* **`internal`**: Automated alerts thrown by internal backend monitoring tools or system logs.

## Branch Responsibilities & Multi-Region Footprint
Every incident must explicitly track the clinic handling it. HealthCore operates across two different regulatory frameworks: **HIPAA in the United States** and **UK GDPR in the United Kingdom**. 

For system-wide backend infrastructure issues, central database sync dropouts, or cloud-layer bugs that do not point to a specific physical clinic site, the attribute defaults to **`central`**.

---

## System Resilience & User Experience Philosophy

### 1. High-Context Ingestion & Client Guardrails
The application user interface integrates client-side validation logic right at the input boundary. By evaluating requirements locally before data ever leaves the viewport, network strain is avoided, and users receive instantaneous input checking even if they leave fields blank. 

Furthermore, the form elements strictly track company blueprints down to individual branch naming conventions across US and UK territories to keep records consistent. When an operator tracks an item originating from a physical storefront, the UI applies localized highlights and utilizes company display labels to keep users anchored in their current operations.

### 2. Optimistic Operations and Asynchronous State Safety
The submission engine isolates long-running operations to guard against race conditions, connection latencies, or repeated transmissions. Button components lock automatically while background operations execute, backed by graceful translation modules that screen downstream systems from revealing technical or raw server text. Errors are intercepted, rewritten into human-readable plain language, and mapped directly onto relevant interface segments.

To provide a snappy experience, the incident dashboard employs optimistic visual states for inline updates. It assumes transitions succeed instantly but retains an error fallback mechanism to restore historical states and alert supervisors if an operation fails the backend state-machine rules.

### 3. Graceful Dashboard Degradation & Component Isolation
The interface isolates distinct widget boundaries to guarantee that a network timeout or a 500 error in one section does not crash the entire application viewport. The dashboard list view safely manages all edge states (`loading`, `empty`, or `active data streams`) seamlessly. 

Similarly, analytical metrics modules are isolated asynchronously. If a database query fails or a microservice times out, the summary panel catches the breakdown locally—rendering an appropriate isolated loading or error interface state—while keeping the main incident list completely interactive and functional for administrators.

### 4. Monorepo Structural Blueprint (Unified Validation Single Source)
To guarantee consistency across the entire ecosystem, the platform mandates a clean separation of concerns using a shared monorepo workspace. Central validation engines are decoupled from single deployment runtimes and reside in a universal shared library location. 

This single source of truth governs both offline analytical migration utilities (`/scripts`) and live api servers (`/services`), eliminating code duplication and ensuring that historical imports and live registrations obey identical semantic constraints.

---

## Strategic Product Vision: From Structure to Intelligence
The strict relational intake system established in this platform acts as the core baseline for data maturation. By ensuring that titles and descriptions are clean, validated, and consolidated in a central database in real time, the foundation is set to deploy **Semantic Vector Embeddings**.

Once exact matching and metric grouping requirements are fully satisfied, this data framework can natively expand into intelligent automation. Capturing these descriptions unlocks advanced downstream capabilities—such as searching for matching resolutions via similarity vectors, catching duplicated report floods before they reach dashboards, and automatically predicting categories based on legacy text patterns.
