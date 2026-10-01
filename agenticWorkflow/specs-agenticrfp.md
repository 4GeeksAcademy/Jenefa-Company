# Technical Specification: Agentic RFP Intake & Routing Pipeline (Part 1)

## 1. System Architecture & Monorepo Layout
The system is built as an extension of the existing corporate monorepo codebase. It does not introduce new microservices, detached API processes, or standalone frontend applications.

### Directory Structure Alignment
*   **`services/`**: Houses the new HTTP endpoints for handling uploads and status polling. Routes invoke the agent graph via non-blocking background executors within the same runtime process.
*   **`data/pipelines/rfp_intake/`**: Ground zero for the dedicated LangGraph implementation. Contains graph topology, custom nodes, routers, state definitions, and agent instructions. It is explicitly separated from existing customer experience (`CX`) or general knowledge graphs.
*   **`data/raw/`**: The runtime storage location where original incoming PDF binaries are dumped immediately during request ingestion.
*   **`scripts/`**: Contains standalone command-line scripts for manual reprocessing, system health smoke runs, and administrative pipeline triggers. No HTTP logic belongs here.
*   **`tests/pipelines/`**: Stores discrete unit testing modules specifically targeting the validation logic of the classifier agent and isolated worker agents.

---

## 2. Ingestion, Conversion & Readability Metrics Pipeline
Processing large PDFs directly within LLM loops creates massive token overhead and introduces formatting noise. This pipeline ensures early normalization and strict measurement.

[Inbound PDF Upload] ──> Save to data/raw/ ──> Convert via MarkItDown ──> Compute Readability ──> Save Metrics & Metadata

### Step 2.1: Asynchronous Handshake
1. The user uploads a PDF through the interface.
2. The endpoint validates the magic bytes to confirm the file is a PDF.
3. The system generates a `ticket_id` (UUIDv4) and records a new row in PostgreSQL with a state of `analyzing`.
4. The raw binary is written to `data/raw/{ticket_id}.pdf`.
5. The HTTP thread immediately returns a `202 Accepted` response alongside the `ticket_id` payload, handing off execution to an internal background task worker thread.

### Step 2.2: Structural Normalization
*   **Engine**: `MarkItDown` (or documented markdown conversion middleware).
*   **Execution**: The raw PDF is fully parsed into clean Markdown text, stripping structural bloat while preserving tables, headings, and lists. This text serves as the foundation for all downstream agent evaluations.

### Step 2.3: Readability & Cost Estimation
To let the Sales team anticipate processing and cognitive evaluation friction, the system evaluates the generated Markdown string before invoking any LLM calls.
*   **Engine**: `py-readability-metrics`
*   **Metrics Tracked**: Flesch-Kincaid Grade Level, Gunning Fog Index, and token scale estimations.
*   **Storage**: Written immediately to the `rfp_tickets` table in PostgreSQL to ensure cost tracking is transparent even if downstream agent nodes fail.

---

## 3. Database Schema Blueprint (PostgreSQL / Supabase)
Data must be strictly persisted across explicit tables using relational integrity via SQLModel/SQLAlchemy mapping layers. No schema-less `TinyDB` instances or loose `JSON` files are permitted as source-of-truth datastores.

### 3.1 `rfp_tickets` Table
Tracks lifecycle states, physical locations, and primary document footprints.

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `ticket_id` | `UUID` | `PRIMARY KEY`, Default: `gen_random_uuid()` | Unique system identifier. |
| `status` | `VARCHAR` | `CHECK (status IN ('analyzing', 'discarded', 'intake_complete'))` | Exact state machine token. |
| `file_path` | `VARCHAR` | `NOT NULL` | Path to binary (`data/raw/{id}.pdf`). |
| `raw_metadata`| `JSONB` | Default: `'{}'::jsonb` | Extracted title, submission dates, issuer. |
| `metrics` | `JSONB` | Default: `'{}'::jsonb` | Flesch-Kincaid score, word count, token footprint. |
| `created_at` | `TIMESTAMPTZ`| Default: `NOW()` | Audit timeline tracking. |
| `updated_at` | `TIMESTAMPTZ`| Default: `NOW()` | State modification audit timeline. |

### 3.2 `department_section_aspects` Table
Persists independent department assignments isolated by the multi-worker architecture.

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `BIGINT` | `PRIMARY KEY`, `GENERATED ALWAYS AS IDENTITY` | Row tracking key. |
| `ticket_id` | `UUID` | `FOREIGN KEY REFERENCES rfp_tickets(ticket_id) ON DELETE CASCADE` | Link to the parent workflow ticket. |
| `department` | `VARCHAR` | `NOT NULL` | Aligned name matching `CONTEXT-company.md`. |
| `key_aspects` | `TEXT` | `NOT NULL` | Extracted departmental requirements. |
| `contacts` | `JSONB` | Default: `'[]'::jsonb` | Identified internal experts or client contacts. |

---

## 4. Multi-Agent Orchestration Graph Layout
The `rfp_intake` execution graph utilizes an **Orchestrator-Worker-Synthesizer** design topology to enforce domain isolation and context optimization.

┌─── [Worker: Dept A] ───┐
[Classifier] ──> [Orchestrator] ──┼─── [Worker: Dept B] ──┼──> [Synthesizer] ──> [Handoff Contract]
└─── [Worker: Dept C] ───┘

### 4.1 State Schema Model
```python
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class DepartmentTask(BaseModel):
    department_name: str
    relevant_markdown_extract: str

class RFPGraphState(BaseModel):
    ticket_id: str
    markdown_content: str
    is_valid_rfp: Optional[bool] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tasks: List[DepartmentTask] = Field(default_factory=list)
    worker_outputs: List[Dict[str, Any]] = Field(default_factory=list)
    final_summary: Optional[str] = None
```

### 4.2 Graph Node Functional Matrix

#### Node 1: Classifier Agent
*   **Role**: Triage gatekeeper. Reads the converted Markdown content and evaluates it against validation rules sourced from `CONTEXT-company.md`.
*   **Conditional Routing**:
    *   If **Valid**: Sets `is_valid_rfp = True` and routes directly to the **Orchestrator Node**.
    *   If **Invalid**: Sets `is_valid_rfp = False`, writes state to PostgreSQL, flips `rfp_tickets.status` to `discarded`, and halts execution safely.

#### Node 2: Orchestrator Agent
*   **Role**: Decomposes the primary, large document into isolated workstreams based on the corporate structural configuration in `CONTEXT-company.md`.
*   **Behavior**: Maps text regions to relevant departments. It populates the `tasks` list inside the state object, establishing independent structural parallel tracks.

#### Node 3: Parallel Workers (Map-Reduce Node Group)
*   **Role**: Individual, dedicated worker instances triggered concurrently for each task emitted by the Orchestrator.
*   **Rule Engine**: Each worker *only* receives its department-relevant text snippets and global metadata. Workers are **strictly forbidden from inventing metrics, numbers, or SLA targets** absent from the source document.
*   **Storage Entry**: Every worker writes its output directly into the `department_section_aspects` database table.

#### Node 4: Synthesizer Agent
*   **Role**: Compilation engine. Collects all completed parallel worker notes, normalizes cross-department overlap, and builds a consolidated, Sales-facing overview.
*   **Outcome**: Generates a unified overview outlining clear department handoffs and actions. Flips `rfp_tickets.status` to `intake_complete`.

---

## 5. Part 2 Downstream Handoff Contract
To guarantee that Part 2 (Proposal Generation) can spin up efficiently without re-parsing raw PDF files or running expensive text extraction tools a second time, the workflow issues a structured handoff contract.

On graph success, an event payload or database record is constructed carrying:
```json
{
  "ticket_id": "f81d4fae-7dec-11d0-a765-00a0c91e6bf6",
  "status": "intake_complete",
  "synthesizer_payload": {
    "sales_summary": "Unified brief outlining critical response parameters...",
    "workstream_structure": [
      {
        "department": "Engineering",
        "key_aspects": "Extracted software constraints and target platform parameters.",
        "contacts": ["engineering_lead@company.local"]
      }
    ]
  }
}
```
This payload is committed directly to a designated handoff column or pushed to a light internal message broker channel to establish a clear architectural boundary.

---

## 6. Testing Strategy
*   **Unit Verification**: Tests housed under `tests/pipelines/` use mock markdown fixtures to verify the Classifier's routing choices and confirm that Worker agents do not invent hallucinations when presented with sparse text.
*   **Integration Smoke Testing**: Run via local files in `scripts/` using real source files housed under `rfp-requests/<company>/` to confirm the end-to-end reliability metrics computation, DB persistence layer, and graph execution flow work perfectly.