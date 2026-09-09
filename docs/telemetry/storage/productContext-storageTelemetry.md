# Product Context & Design Philosophy: Real Telemetry Storage

## 1. Intent & Problem Statement
HealthCore operates a rapid-growth cross-border healthcare network consisting of **12 clinics** across the US and UK, managing an approximate annual revenue of **$28 million**. Historically, the underlying technological estate has evolved into a disconnected patchwork of standalone EHR platforms, fragmented billing systems, and localized scheduling diaries. This lack of centralized logging leaves the engineering team dependent on clinics calling by phone to report system critical failures.

To solve this, executive leadership under **Dr. Sandra Okonkwo** established **HealthCore Digital** to construct a modern, integrated intelligent infrastructure. This telemetry service transformation bridges the gap, upgrading the original validation stub into a highly resilient, enterprise-ready data sink that provides authentic structural validation, real-time logging, and efficient relational bulk persistence across eight target data columns in Supabase.

---

## 2. Core Architectural Pillars

### Zero Client Footprint Disruptions
A central rule of this migration is that **the frontend client must not change a single line of code**. The substitution of the stub endpoint with the functional real engine must be completely transparent. The endpoint URL, structural payload configurations, and request headers remain entirely static. Because the frontend's underlying `TelemetryService` isolates network confirmations strictly by watching the **HTTP status code** rather than checking response body structures, returning an enriched validation breakdown safely optimizes backend analytics without breaking production app flows.

### Immutable Architecture & Regulated Invariants
Telemetry data captures permanent snapshots of historical context at an exact millisecond in time. Because history cannot change, the `telemetry_events` storage layer functions exclusively as a **write-only ledger**. 
*   Data points are written once and never updated or deleted. This aligns with rigorous medical audit trail requirements under **HIPAA** in the United States and **UK GDPR** in the United Kingdom.
*   Fixed structural analytics columns (`event_type`, `timestamp`, `service`) provide the architectural backbone for time-series analysis, tracking clinic performance, and driving executive dashboards.
*   The `tags` JSONB column stores user context variations cleanly—preserving allowlists and operational dimensions (e.g., `warehouse`, `office`, location parameters) from our `telemetry-plan.md`—without demanding unpredictable database table schema updates over time.

---

## 3. Operational Mechanics: Scale vs. Stability

### Why Single-Transaction Bulk Inserts Matter
Standard CRUD applications write data sequentially (e.g., updating a patient’s address profile). Telemetry engines, by contrast, operate under a heavy batch model where multiple concurrent app sessions across a 200-person organization might upload clusters of twenty events every ten seconds.

*   **The Row-by-Row Risk**: Running individual `INSERT` lines loops through separate round-trip database queries and transaction locks. Under trivial production volumes across 12 distributed facilities, this pattern easily exhausts connection pools, leading to system outages that disrupt active clinical operations.
*   **The Bulk Insertion Fix**: Gathering all clean entities and pushing them downstream via a **single transactional bulk operation per batch** minimizes active transaction lifecycles and shields core storage systems from performance degradation.

### Fault Tolerance via Partial Acceptance
In vast data-collection architectures, an application must never allow a single improperly formatted event to ruin an entire payload transmission. 

By applying **per-event parsing** via isolated `TelemetryEvent.model_validate` calls inside an iterative handler loop—rather than enforcing a strict overall request schema type hint on the gateway router signature—the endpoint successfully isolates faulty items. It records every legitimate telemetry datapoint, rejects broken structural rows independently without triggering global `422` response codes, and maintains data continuity for the rest of the batch.

---

## 4. End-to-End Verification Strategy
System integrity is proven through pragmatic verification across business operations and programmatic failure simulation:
*   **Real Business Exercises**: Triggering concrete operational tasks—such as inbound and outbound inventory movements—ensures that actual business data generates telemetry predictably across the module stack.
*   **Simulated Failures**: Using direct REST injection tests allows developers to confirm that partial failures (mixed valid/invalid bodies) do not block good metrics data from finding its way into our data streams.
