# Product Context: System Resilience & Unified Error Handling Strategy

## Business & Product Impact
As the company's platform has scaled across multiple milestones—expanding from a static corporate website to a live Next.js frontend, a Python/FastAPI backend, and complex automated data-processing scripts—the overall system surface area has increased dramatically. 

Currently, the lack of a cohesive error handling strategy undermines user confidence, operational visibility, and system security:
- **User Churn & Frustration:** Frontend API actions fail silently or drop users into unescaped white screens or broken, unclickable loops.
- **Support Inefficiency:** Displaying technical anomalies like `Error 500` or `Unexpected token <` forces users to contact support without context, lengthening resolution times.
- **Operational Blind Spots:** Background data scripts drop silent failures (`except: pass`), masking critical failures from engineering telemetry until data corruption occurs.
- **Security Exploits:** Raw stack traces, system paths, and database schema disclosures expose infrastructure footprints directly to clients.

###  Strict Scope Constraint
This is a cross-cutting engineering mandate to enforce platform-wide resilience—**it is not a feature update**. Engineers are strictly instructed **not to introduce new functionality** or refactor components for reasons unrelated to error handling. The scope of this project is exclusively fixed on the resilience and error communication mechanics of existing code pathways.

---

## The Core Product Principles

### 1. Zero Catastrophic Crashes
No runtime error or network failure should ever leave the client in an undefined UI state or crash an entire service process loop. Every failure must lead to an explicitly handled fallback state.

### 2. Radical UI Transparency
Every single asynchronous data operation visible to a user must cleanly move through three distinct pipeline stages:
- **Loading:** Deterministic visual anchors (spinners, skeleton frames) indicating network flight.
- **Fulfilled:** The clean presentation of targeted domain data.
- **Rejected:** A human-readable error container completely stripped of underlying technology semantics.

### 3. Clear Paths to Recovery
An error message without an interactive exit point is a dead end. Every frontend error container must serve a functional Call to Action (CTA)—providing a clear action like an in-place retry trigger, a safe global navigation link, or explicit support routes.

### 4. Granular Backend & Telemetry Scoping
We reject sweeping, top-level catch-alls that swallow or generalize individual exceptions. Backend processing routines must catch edge cases closest to the point of origin, ensuring context-rich logs are saved upstream while serving precise, validated response contracts to downstream consumers.

---

## Operational Execution: Agent-Driven Discovery
Before manual changes are implemented, engineers are required to run automated Coding Agents to map the repository's flaws. This proactive discovery mechanism ensures that engineering resources are targeted precisely at high-severity vulnerabilities first, eliminating guesswork and providing an auditable benchmark before final validation.
