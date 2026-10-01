# Technical Specification: Agentic RFP Intake & Routing Pipeline (Part 1)
**Enabling Unit**: HealthCore Digital  
**Target Enterprise**: HealthCore Outpatient Network (US & UK)  

## 1. System Architecture & Monorepo Layout
The system is built as an extension of the existing HealthCore Digital repository. It does not introduce new standalone microservices, detached API processes, or independent frontends.

### Directory Structure Alignment
*   **`services/`**: Houses the new HTTP endpoints for handling vendor RFP uploads and status polling. Routes invoke the agent graph via non-blocking background executors within the same FastAPI runtime process.
*   **`data/pipelines/rfp_intake/`**: Ground zero for the dedicated LangGraph implementation. Contains graph topology, custom nodes, routers, state definitions, and agent instructions. It is explicitly separated from the existing clinical documentation or Patient Experience (`CX`) knowledge graphs.
*   **`data/raw/`**: The runtime storage location where original incoming PDF binaries are dumped immediately during request ingestion.
*   **`scripts/`**: Contains standalone command-line scripts for manual reprocessing, system health smoke runs, and administrative pipeline triggers. No HTTP logic belongs here.
*   **`tests/pipelines/`**: Stores discrete unit testing modules specifically targeting the validation logic of the classifier agent and isolated worker agents.

---

## 2. Ingestion, Conversion & Readability Metrics Pipeline
Processing large enterprise RFPs directly within LLM loops creates massive token overhead and introduces formatting noise. This pipeline ensures early normalization and strict measurement.

[Inbound PDF Upload] ──> Save to data/raw/ ──> Convert via MarkItDown ──> Compute Readability ──> Save Metrics & Metadata

### Step 2.1: Asynchronous Handshake
1. An administrator uploads a commercial RFP through the backoffice interface.
2. The endpoint validates the magic bytes to confirm the file is a PDF.
3. The system generates a `ticket_id` (UUIDv4) and records a new row in PostgreSQL with a state of `analyzing`.
4. The raw binary is written to `data/raw/{ticket_id}.pdf`.
5. The HTTP thread immediately returns a `202 Accepted` response alongside the `ticket_id` payload, handing off execution to an internal background task worker thread.

### Step 2.2: Structural Normalization
*   **Engine**: `MarkItDown` (or documented markdown conversion middleware).
*   **Execution**: The raw PDF is fully parsed into clean Markdown text, stripping structural bloat while preserving tables, headings, and lists. This text serves as the foundation for all downstream agent evaluations.

### Step 2.3: Readability & Cost Estimation
To let the team anticipate processing and cognitive evaluation friction, the system evaluates the generated Markdown string before invoking any LLM calls.
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
| `department` | `VARCHAR` | `CHECK (department IN ('Clinical Operations', 'Patient Experience', 'Revenue Cycle', 'Compliance & Governance', 'Workforce & People', 'Technology'))` | Strict structural department alignment. |
| `key_aspects` | `TEXT` | `NOT NULL` | Extracted departmental requirements and SLAs. |
| `assigned_head`| `VARCHAR` | `NOT NULL` | Automatically assigned manager name. |
| `contacts` | `JSONB` | Default: `'[]'::jsonb` | Identified internal experts or client contacts. |

---

## 4. Multi-Agent Orchestration Graph Layout
The `rfp_intake` execution graph utilizes an **Orchestrator-Worker-Synthesizer** design topology to enforce domain isolation and context optimization.

┌─── [Worker: Clinical Operations]
├─── [Worker: Patient Experience]
[Classifier] ──> [Orchestrator] ──┼─── [Worker: Revenue Cycle] ──────> [Synthesizer] ──> [Handoff Contract]
├─── [Worker: Compliance & Governance]
└─── [Worker: Technology]

### 4.1 State Schema Model
```python
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class HealthCoreDepartmentTask(BaseModel):
    department_name: str
    assigned_head: str
    relevant_markdown_extract: str

class RFPGraphState(BaseModel):
    ticket_id: str
    markdown_content: str
    is_valid_rfp: Optional[bool] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tasks: List[HealthCoreDepartmentTask] = Field(default_factory=list)
    worker_outputs: List[Dict[str, Any]] = Field(default_factory=list)
    final_summary: Optional[str] = None
```

### 4.2 Graph Node Functional Matrix

#### Node 1: Classifier Agent
*   **Role**: Triage gatekeeper. Reads the converted Markdown content and evaluates whether it is a legitimate commercial RFP (e.g., medical equipment procurement, clinic software vendor proposals, cross-border insurance network agreements) or noise.
*   **Conditional Routing**:
    *   If **Valid**: Sets `is_valid_rfp = True` and routes directly to the **Orchestrator Node**.
    *   If **Invalid**: Sets `is_valid_rfp = False`, writes state to PostgreSQL, flips `rfp_tickets.status` to `discarded`, and halts execution safely.

#### Node 2: Orchestrator Agent
*   **Role**: Decomposes the primary, large document into isolated workstreams based on HealthCore's actual corporate divisions.
*   **Behavior**: Maps text regions to relevant departments and dynamically injects target accountability keys:
    *   `Clinical Operations` ──> Assigned to: **Dr. Marcus Reid**
    *   `Patient Experience and Access` ──> Assigned to: **Priya Nair**
    *   `Revenue Cycle and Billing` ──> Assigned to: **Tom Callahan**
    *   `Compliance and Data Governance` ──> Assigned to: **Claire Whitfield**
    *   `People and Workforce` ──> Assigned to: **Diane Foster**
    *   `Technology` ──> Assigned to: **James Osei**

#### Node 3: Parallel Workers (Map-Reduce Node Group)
*   **Role**: Individual, dedicated worker instances triggered concurrently for each task emitted by the Orchestrator.
*   **Rule Engine**: Each worker *only* receives its department-relevant text snippets and global metadata. Workers are **strictly forbidden from inventing metrics, numbers, or regulatory compliance metrics** absent from the source document (e.g., falsifying HIPAA or UK GDPR parameters).
*   **Storage Entry**: Every worker writes its output directly into the `department_section_aspects` database table.

#### Node 4: Synthesizer Agent
*   **Role**: Compilation engine. Collects all completed parallel worker notes, normalizes cross-department overlap, and builds a consolidated, executive-ready overview for leadership.
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
    "executive_summary": "Unified brief outlining critical response parameters for Dr. Okonkwo's review...",
    "workstream_structure": [
      {
        "department": "Compliance and Data Governance",
        "assigned_head": "Claire Whitfield",
        "key_aspects": "Cross-border data transit provisions identified requiring explicit UK GDPR and HIPAA balancing frameworks.",
        "contacts": ["c.whitfield@healthcore.local"]
      }
    ]
  }
}
```

---

## 6. Testing Strategy
*   **Unit Verification**: Tests housed under `tests/pipelines/` use mock markdown fixtures to verify the Classifier's routing choices and confirm that Worker agents do not invent hallucinations when presented with sparse text.
*   **Integration Smoke Testing**: Run via local files in `scripts/` using real source files housed under `rfp-requests/healthcore/` to confirm the end-to-end reliability metrics computation, DB persistence layer, and graph execution flow work perfectly.