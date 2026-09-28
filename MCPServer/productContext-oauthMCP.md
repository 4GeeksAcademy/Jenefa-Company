# Product Context: Decentralized Model Context Protocol (MCP) Server for HealthCore Digital

## 1. Product Vision & Value Proposition
**HealthCore** is an outpatient healthcare services provider operating a network of **12 clinics** across the US and the UK. While our clinical operations successfully care for thousands of patients, our foundational technology stack functions as a fragmented patchwork of legacy software—including two conflicting EHR platforms, localized billing tools, and manual scheduling diaries. 

To solve this, **HealthCore Digital** was formed to build safe, efficient, and modern workflows. While our core LangGraph agent successfully automates targeted incident tracking workflows internally, its operational capabilities are tightly coupled within its private graph codebase. This monolithic setup forces any future automation—such as cross-department tools for **Priya Nair’s Patient Experience squad** or automated pipelines for **Tom Callahan’s Revenue Cycle division**—to duplicate and re-implement identical integration steps.

By translating these operational systems into an independent, standalone **Model Context Protocol (MCP) Server**, we decouple HealthCore's technical capabilities from specific frontend frameworks. Our tools become secure, standardized, plug-and-play resources consumable by any authorized agent in our global healthcare network.

## 2. Business Drivers & Security Imperatives
* **Ecosystem Scale without Redundancy:** Enables fluid tool sharing across distinct technical subdivisions (such as booking, billing, and workforce units) without maintaining fragmented codebase libraries.
* **High-Stakes Data Protection:** Operating in healthcare means that data security is a legal necessity, not a casual enhancement. Because our systems cross international boundaries, the MCP Server operates under strict regulatory constraints: **HIPAA** in the United States and **UK GDPR** in the United Kingdom. 
* **Mandatory OAuth Protection:** Exposing live clinical capabilities to LLMs introduces immediate vulnerability vectors. Securing the server with **OAuth 2.1 via `mcpauth`** and enforcing the **principle of least privilege** guarantees that unauthenticated calls are blocked from day one, keeping patient data safe.
* **Autonomous Discovery:** Tools must self-document via standard schema parameters. External agents or adjacent squads must parse capabilities instantly through automated discovery without requiring developer oversight or risking compliance errors.

## 3. Target User Personas
* **The Migrated LangGraph Agent:** Our internal core agent, evolving from a direct API consumer into a secure, authenticated MCP client node via standard integration adapters.
* **HealthCore Department Agents:** Future autonomous workflows representing Clinical Operations (led by Dr. Marcus Reid) or Revenue Cycle units that need real-time data access without bypassing corporate firewalls.
* **HealthCore Digital Engineers:** Team members operating under **James Osei (CTO)** using environments like **MCP Playground** within public-forwarded **GitHub Codespaces** to evaluate system stress boundaries, access controls, and logging protocols.

## 4. Product Boundaries & Scope

### In Scope
* **Secure Incidents Management:** Permitting authorized external entities to generate, track, and update ticket pipelines, forcing state changes explicitly through the **`PATCH /api/incidents/{id}/status`** endpoint.
* **Protected Multi-Jurisdiction Discovery:** Exposing standardized schema configurations detailing operational tools, necessary formats, and target scopes to any verified client querying the endpoint.
* **Defensive Asset Guarding:** Intercepting inbound parameters to actively reject and log any unauthorized write operations targeted at backend inventory modules.

### Out of Scope
* **Direct Inventory Modification:** Creating, deleting, or editing asset records through this interface; the tool remains strictly read-only by design to prevent data corruption.
* **Identity Provider Hosting:** Managing user credentials or token generation natively; the server relies entirely on a pre-configured, compliant external OAuth 2.1 / OIDC provider.

## 5. Core Definition of Done (DoD)
* **Monorepo Isolation:** All code lives completely under the `mcps/` directory, and dependencies are managed exclusively with `uv add` (never using direct `pip` execution).
* **Zero Direct Leaks:** The original LangGraph agent node completely stops contacting the Incidents Manager API directly; all communications flow securely through the `langchain-mcp-adapters` interface.
* **Proven Resistance:** Verification runs successfully inside the remote **MCP Playground** using a public GitHub Codespaces URL, confirming that write attempts to inventory fail with clean, structured error responses, and unauthenticated requests are successfully dropped.
