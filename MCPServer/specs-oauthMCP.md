 # Technical Specification: HealthCore Digital MCP Server Migration with OAuth Protection

## 1. System Architecture & Transport Strategy
* **Transport Protocol:** **Streamable HTTP (Server-Sent Events / SSE)** is deployed to handle secure remote consumption by multi-tenant external agents, distributed clinical platforms, and the **MCP Playground** interface.
* **Hosting Environment:** Runs within **GitHub Codespaces**. Port forwarding must be configured with **public visibility** to generate an accessible external URL (`https://*.app.github.dev`) for remote client discovery and tool invocation. Localhost boundaries are strictly invalid for this ecosystem pattern.
* **Directory Structure:** Fabricated inside the monorepo's **`mcps/`** directory using `FastMCP`. It acts as an abstraction over HealthCore's data systems but must never reside under `services/`.
* **Cross-Border Upstream Targets:** This MCP Server unifies and communicates directly with the underlying **Incidents Manager backend** and the cross-border **Inventory module** built in previous milestones. It bridges data across HealthCore's regional networks (9 US clinics using a US billing platform/EHR and 3 UK clinics operating via separate EHRs and manual diaries).

## 2. Authentication & Authorization Framework (`mcpauth`)
* **Layer Isolation:** The implementation must utilize the **`mcpauth` Python package** to wire provider-agnostic OAuth 2.1 / OIDC. It **must not** use FastMCP's built-in auth layers or local helper objects.
* **Enforcement State:** An unauthenticated client **cannot list or execute any tool**. Requests lacking a valid Bearer JWT access token must be rejected at the gateway level before exposing any company capabilities.
* **Least Privilege Scopes & Multi-Jurisdiction Compliance:** Scopes are validated deterministically per tool using `mcpauth` validation (`required_scopes`). To support **Claire Whitfield's Compliance and Data Governance** requirements, tokens must match the target jurisdiction's context to safeguard data regulated under **HIPAA (US)** and **UK GDPR (UK)**.
* **Error Handling Matrix:** Error states must return distinct, explicit codes and custom messages instead of generic "error" payloads:
  * **Authentication Failure:** Missing/Malformed token (e.g., Code `401`, Unauthenticated).
  * **Authorization Failure:** Insufficient scope privileges for the targeted tool (e.g., Code `403`, Unauthorized).
  * **Validation Failure:** Schema mismatches, cross-border access mismatches, or write violations (e.g., Code `400`, Bad Request).

## 3. Tool Specifications & Discovery Contracts
Every tool must be documented natively via FastMCP so that external or cross-functional agents parse capabilities and schemas purely through standard MCP discovery without human code reviews.

### A. HealthCore Ticket Management Tool (Incidents Manager)
* **Functionality:** Create tickets, check ticket status, and update ticket states across HealthCore Digital systems.
* **Backend Constraint:** All entity IDs, field names, and domain-specific values must natively match the operational schemas of the company's real Incidents Manager API ecosystem.
* **Lifecycle Rules:** Modifying an incident status **must** execute requests against the exact lifecycle endpoint: **`PATCH /api/incidents/{id}/status`**. Generic `PATCH` updates targeting the base incident resource are strictly rejected.

### B. HealthCore Inventory Query Tool
* **Functionality:** Read-only retrieval of clinical assets, equipment, and medical stock data across the 12 clinic locations.
* **Strict Read-Only Enforcement:** Omitting mutation methods from discovery is insufficient. The tool must evaluate query intent and **actively reject any write attempt** with an explicit, controlled validation error code, ensuring that raw inventory figures cannot be manipulated outside authorized channels.

## 4. Observability & Audit Logging
* **Traceability Requirement:** The server must log every single tool invocation to deliver a consolidated audit trail matching the standards mandated by HealthCore's compliance division.
* **Log Payload Structure:** Every entry must capture exactly:
  * `client_id` / Caller identity (parsed from JWT claim)
  * `tool_name`
  * `execution_result` (Success, Parameter Validation Error, or Access Denied)

## 5. Agent Graph Refactoring (LangGraph Migration)
[ Legacy Flow ]  LangGraph Node ──(Direct API Calls)──> HealthCore Incidents Manager
[ Migrated Flow ] LangGraph Node ──(langchain-mcp-adapters)──> Protected MCP Server ──> Incidents Manager
* **Adapter Integration:** The existing graph node that speaks directly to the Incidents Manager API must be replaced using **`langchain-mcp-adapters`** to call the new MCP Server.
* **Path Deprecation:** The previous direct tool implementation must be removed or explicitly deprecated. There can be no parallel routing paths to the Incidents Manager outside of the MCP connection.
* **Routing Stability:** The orchestrator's upstream routing dynamics between the Knowledge-Retrieval RAG nodes and Tool execution nodes must remain identical to prior milestones.