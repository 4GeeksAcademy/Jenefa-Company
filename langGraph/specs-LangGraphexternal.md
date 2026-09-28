# Technical Specification: Real-Time Tool Integration & Graph Resilience (Part 2)
**Internal Unit:** HealthCore Digital [3]  
**Target Environment:** HealthCore Clinic Network (12 Locations: 9 US, 3 UK) [1]  
**Governance Framework:** HIPAA (US) & UK GDPR (UK) Multi-Jurisdiction Compliance [2, 3]

## 1. System Dependencies & Architectural Setup
This project extends the compiled LangGraph architecture built in Part 1 for HealthCore Digital.
- **Data Freshness Requirement:** All tools must pull live operational data from the running HealthCore microservices ecosystem. Fake datasets, mocked file systems, or parallel hardcoded databases are strictly prohibited.
- **Transport Mechanisms (Architectural Choice):** 
  - **Option A:** Over-the-wire HTTP API calls to the active HealthCore central services.
  - **Option B:** In-process invocations through the repository layer if coexisting inside the HealthCore monorepo package.

---

## 2. Tool-Specific Interface Contracts

### 2.1 Required Tool: Clinical Incident / Support Ticket Lookup
- **HTTP Endpoint:** `GET /api/incidents` or `GET /api/incidents/{id}`
- **Operations:** Strictly **Read-Only (`GET`)**. The tool must never mutate, create, or delete system ticket states.
- **Typed Interface Contract:**
  - **Inputs:** A strongly typed payload accepting a target identifier (`ticket_id`) or structural search filters.
  - **Outputs:** An object reflecting the exact domain fields exposed by the live incident service backend (e.g., `status`, `category`, `source`, `dates`).
- **Security & Compliance Constraints:** Authenticating mechanisms (JWT/API keys) must be resolved securely from runtime environment configs (`process.env` or `os.environ`). Access logs must map to clinical compliance audit criteria managed under Claire Whitfield's data governance rules.

### 2.2 Stretch Tool: Cross-Border Inventory Lookup
- **HTTP Endpoint:** `GET /inventory/products`
- **Operations:** Strictly **Read-Only (`GET`)**. 
- **Interface & Rules:** Implements an identical typed interface pattern to retrieve stock levels by product across international boundaries. Follows the same isolation, runtime, and timeout safeguards as the incident tool.

---

## 3. LangGraph Workflow Routing & Fault Tolerance

### 3.1 Graph Topology Modifications
- **New Execution Blocks:** Incorporate explicit node configurations for each external tool integrated into the LangGraph network.
- **Conditional Branching Rules:** Implement a conditional edge that decides when the agent should branch to the localized regulatory RAG repository (e.g., HIPAA / UK GDPR knowledge bases), execute live tool lookups, or stream both actions sequentially.

### 3.2 Single Responsibility Pattern
- **Strict Separation:** Every tool must own a single technical capability. Combining logic into a single multi-purpose tool (e.g., trying to resolve both tickets and inventory in one routine) is prohibited. They must exist as separate, decoupled tools.

### 3.3 Latency Guardrails & Fallbacks
- **Numeric Timeout Threshold:** All backend network requests must be wrapped in a hard numeric timeout (**3–5 seconds**). The runtime graph execution sequence must never hang on a slow cross-border socket connection.
- **Deterministic Failure Recovery Node:** If a tool execution encounters a network timeout, experiences an unhandled HTTP exception, or receives a 404 resource-not-found error, the state graph must transition to an explicit fallback recovery routine.
- **Response Guardrail:** Under failure states, the LLM must emit a transparent context response such as *"I couldn't confirm that ticket's status right now"*. It is completely prohibited to output fabricated data or make up an arbitrary status.

---

## 4. Observability & Evaluation Standards (Part 1 Extension)

### 4.1 Tracing Context
- Execution traces must explicitly map out exactly which system sources were contacted during a run loop, and document the explicit ordering of execution (e.g., `User Query -> Agent Node -> Ticket Tool Node -> RAG Retrieval Node -> Response Generation`).

### 4.2 Automated Testing Evaluation Suites (Minimum 2 New Tests)
- **Eval Scenario 1 (Tool Assert):** A target test question requiring real-time updates (e.g., specific ticket statuses) that must evaluate through a tool call while explicitly avoiding RAG pathways.
- **Eval Scenario 2 (RAG Assert):** A static compliance or structural company policy question (e.g., HIPAA timelines or UK GDPR constraints) that must verify cleanly through the RAG engine without calling external operational tools.
- **Eval Scenario 3 (Optional Fallback Verify):** An automated pipeline step where external endpoints are simulated as offline to verify that the graph follows the error fallback logic cleanly without breaking.
