# Product Context: Agentic RFP Intake & Routing Workflow

## 1. Executive Summary & Core Problem Space
HealthCore operates a high-value network of 12 outpatient healthcare clinics across the US and UK, generating \$28 million in annual revenue. As the company grows, it frequently receives complex Requests for Proposals (RFPs) from corporate clients, health insurance networks, and enterprise healthcare vendors. 

Reviewing these multi-page documents is currently a slow, manual process. HealthCore Digital is struggling to meet critical response deadlines because inbound documents require specialized operational input from multiple split departments — and it is impossible to tell, just by skimming the document, who needs to review what.

An RFP often contains complex requirements spanning several specialized areas of care, cross-border regulations, and disjointed systems. For example, a single vendor contract might require **James Osei (CTO)** to review API interoperability across two separate EHR platforms, **Claire Whitfield** to audit HIPAA and UK GDPR data residency rules, and **Tom Callahan** to evaluate commercial insurance reimbursement paths. 

This project automates that initial analysis and triage layer. The goal is to ingest inbound RFPs, run automatic validation, extract key constraints, and isolate departmental tasks immediately, providing a clear executive roadmap showing exactly **what is needed from each department and who to ask** before a manual proposal generation loop begins.

---

## 2. Product Boundaries & Architecture Constraints
To maintain strict data security and compliance within a highly regulated healthcare framework, development must strictly adhere to the following product boundaries:

*   **No Fragmented Ecosystems**: No new standalone frontend applications or decoupled web servers are allowed. All user interfaces must be built directly as responsive extensions inside the existing `uis/backoffice` dashboard tool.
*   **Unified Processing Engine**: The API routing mechanisms must run inside the current backend framework (`services/`). All deep agent execution states belong completely within a dedicated `rfp_intake` graph in `data/pipelines/`.
*   **Strict Structural Alignment**: The taxonomy of departments, workflows, and evaluation criteria must strictly match the designated corporate heads and divisions defined by CEO **Dr. Sandra Okonkwo**.
*   **Regulated Data Protection**: Loose file logging or volatile runtime environments (such as `TinyDB` memory arrays or untracked JSON file dumps) are unacceptable. All ticket lifecycles, file metrics, and departmental structures must be safely persisted within PostgreSQL (Supabase) tracking systems to maintain clean audit logs under HIPAA and UK GDPR requirements.

---

## 3. User Experience & Lifecycle State Machine
The system operates as an asynchronous "Ticket-Mode" interface built into the existing backoffice console. The user path is designed around a fast, non-blocking upload loop:

[User Selects File] ──> Immediate API Ingestion (202 ID Return) ──> UI Polling ──> [Success / Discard State]

### The State Machine Lifecycle Rules
The system tracks the progress of each request using three distinct statuses:
1.  **`analyzing`**: Applied immediately when the upload handshake succeeds. The user sees a processing spinner on the UI. Behind the scenes, the document is normalized into Markdown via MarkItDown, token readability costs are computed via `py-readability-metrics`, and the multi-agent graph runs background evaluations.
2.  **`discarded`**: Applied automatically if the **Classifier Agent** determines the uploaded document is completely unrelated to real business RFPs or fails basic validation criteria. The UI flags the item clearly to prevent cluttering the team's dashboard.
3.  **`intake_complete`**: Applied when the **Synthesizer Agent** finishes merging the parallel worker outputs. The UI updates to show a clean breakdown of department requirements and internal contact points.

---

## 4. Key Design Decisions & Operational Safeguards

### Question 1: Unmapped Department Handling
*   **Scenario**: What happens if an incoming RFP mentions an operational domain that doesn't map to HealthCore's six core departments?
*   **Resolution Strategy**: The Orchestrator agent flags the unmapped department section and groups it into a specialized category called `Unassigned / Executive Leadership Review`. The Synthesizer then flags this category on the UI to warn the operator that an anomalous requirement needs manual evaluation by Dr. Okonkwo's office.

### Question 2: Shared State Isolation vs. Full Document Exposure
*   **Scenario**: What does each worker actually see from the shared state, and what happens if a required figure is missing?
*   **Resolution Strategy**: To minimize token costs and prevent cross-domain confusion, workers do not process the full document. The Orchestrator splits the text up so each worker only receives its specific department-relevant text snippets (e.g., the Compliance worker only receives sections dealing with data privacy, HIPAA, or GDPR). If a critical figure or expected data point is missing from the document, the worker is **strictly forbidden from inventing or hallucinating data**. Instead, it logs an explicit, structured warning in the database: `"Required parameter [X] missing from source document."`

### Question 3: Triage Criteria and Misclassification Safeguards
*   **Scenario**: How do we decide a document "isn't an RFP", and how do we handle false negatives?
*   **Resolution Strategy**: The Classifier agent evaluates documents against strict structural guidelines (e.g., presence of submission timelines, project scope overviews, or explicit evaluation criteria). If a document is marked `discarded` by mistake (a false negative), the admin team can click a **"Force Reprocess"** button on the backoffice UI. This triggers a dedicated administrative script under `scripts/` to bypass the classifier and force the orchestrator to run the full document.

### Question 4: Resolving Inter-Worker Contradictions
*   **Scenario**: What happens if two workers return contradictory information about the same section?
*   **Resolution Strategy**: The **Synthesizer Agent** acts as the primary resolution engine. It compares all worker outputs. If it detects conflicting data points (e.g., conflicting delivery dates or security compliance requirements across different sections), it merges both entries into the final summary and appends a warning tag: `[CONTRADICTION DETECTED]`. This tells the Sales team that the client's RFP contains conflicting statements that need to be cleared up during the proposal phase.

### Question 5: Pipeline Crash Mitigation & Async Execution Durability
*   **Scenario**: Where does async work run, and how does the ticket stay truthful if the job crashes mid-pipeline?
*   **Resolution Strategy**: Asynchronous work runs via localized background tasks within the primary API process. To prevent tickets from getting permanently stuck in an `analyzing` state if a server crashes mid-pipeline, the database uses a timestamped heartbeat check. If a ticket remains stuck in `analyzing` for longer than a specified timeout without active updates, the UI flags it as `System Error / Failed`. The user can then click a re-try option, or an administrator can safely clean it up using manual runners located in `scripts/`.

---

## 5. Verification Framework & Evaluation Standards
A successful implementation will be evaluated against these clear metrics:
*   **Operational Completeness**: The final backoffice screen must display comprehensive, department-by-department breakdowns along with internal contacts without requiring team members to open the original source PDF.
*   **Strict Context Adherence**: Department mappings, assigned leads, and classification paths must perfectly match the internal organization guidelines documented in HealthCore's structural manual.
*   **Data Integrity Verification**: The system must pass all internal integration smoke testing loops using the real sample verification files stored under `rfp-requests/healthcore/`.
