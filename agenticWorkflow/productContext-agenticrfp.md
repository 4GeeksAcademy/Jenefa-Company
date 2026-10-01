# Product Context: Agentic RFP Intake & Routing Workflow

## 1. Executive Summary & Core Problem Space
The commercial Sales operation receives dozens of complex, multi-page Request for Proposal (RFP) documents every week as heavy PDF attachments. Reviewing these files is currently a slow, manual process. The team frequently misses critical presentation and submission deadlines because they cannot figure out which teams need to review which parts of the document just by skimming it.

An RFP often contains complex requirements spanning several internal organizational units (e.g., Engineering, Legal, Information Security, Finance). Today, a human has to read the entire document to map these requirements to the right teams. This creates a severe operational bottleneck. 

This initiative addresses this problem by building an automated, agentic intake and routing workflow. The goal is to triage inbound files immediately, break them down into separate areas of responsibility, and give the Sales team an organized breakdown showing exactly **what is needed from each department and who to ask** without forcing them to manually read through a heavy source document.

---

## 2. Product Boundaries & Architecture Constraints
To keep the system highly reliable and maintainable, development must strictly adhere to the following product boundaries:

*   **No Fragmented Ecosystems**: No new standalone frontend applications or decoupled web servers are allowed. All user interfaces must be built directly as responsive extensions inside the existing `uis/backoffice` dashboard tool.
*   **Unified Processing Engine**: The API routing mechanisms must run inside the current backend framework (`services/`). All deep agent execution states belong completely within a dedicated `rfp_intake` graph in `data/pipelines/`.
*   **Deterministic Validation Triggers**: The corporate departments, vocabulary, processing guidelines, and intake parameters must strictly mirror the structural configurations specified in `CONTEXT-company.md`.
*   **Data Preservation First**: Loose file logging or volatile runtime environments (such as `TinyDB` memory arrays or untracked JSON file dumps) are unacceptable for source-of-truth data. All ticket lifecycles, file metrics, and department breakdowns must use PostgreSQL (Supabase) tracking systems.

---

## 3. User Experience & Lifecycle State Machine
The system operates as an asynchronous "Ticket-Mode" interface built into the existing backoffice console. The user path is designed around a fast, non-blocking upload loop:

[User Selects File] ──> Immediate API Ingestion (202 ID Return) ──> UI Polling ──> [Success / Discard State]

### The State Machine Lifecycle Rules
The system tracks the progress of each request using three distinct statuses:
1.  **`analyzing`**: Applied immediately when the upload handshake succeeds. The user sees a processing spinner on the UI. Behind the scenes, the document is normalized into Markdown, token readability costs are computed, and the multi-agent graph runs background evaluations.
2.  **`discarded`**: Applied automatically if the **Classifier Agent** determines the uploaded document is completely unrelated to real business RFPs or fails basic validation criteria. The UI flags the item clearly to prevent cluttering the team's dashboard.
3.  **`intake_complete`**: Applied when the **Synthesizer Agent** finishes merging the parallel worker outputs. The UI updates to show a clean breakdown of department requirements and internal contact points.

---

## 4. Key Design Decisions & Operational Safeguards

### Question 1: Unmapped Department Handling
*   **Scenario**: What happens if an incoming RFP mentions a department that doesn't exist in `CONTEXT-company.md`?
*   **Resolution Strategy**: The Orchestrator agent flags the unmapped department section and groups it into a specialized category called `Unassigned / General Review`. The Synthesizer then flags this category on the UI to warn the Sales Lead that an anomalous operational requirement needs manual assignment. The pipeline will never crash or discard a valid document due to unmapped corporate terms.

### Question 2: Shared State Isolation vs. Full Document Exposure
*   **Scenario**: What does each worker actually see from the shared state, and what happens if a required figure is missing?
*   **Resolution Strategy**: To minimize token costs and prevent cross-domain confusion, workers do not process the full document. The Orchestrator splits the text up so each worker only receives its specific department-relevant text snippets and basic document metadata. If a critical figure or expected data point is missing from the document, the worker is **strictly forbidden from inventing or hallucinating data**. Instead, it logs an explicit, structured warning in the database: `"Required parameter [X] missing from source document."`

### Question 3: Triage Criteria and Misclassification Safeguards
*   **Scenario**: How do we decide a document "isn't an RFP", and how do we handle false negatives?
*   **Resolution Strategy**: The Classifier agent evaluates documents against strict structural guidelines (e.g., presence of submission timelines, project scope overviews, or explicit evaluation criteria) configured in `CONTEXT-company.md`. If a document is marked `discarded` by mistake (a false negative), the Sales team can click a **"Force Reprocess"** button on the backoffice UI. This triggers a dedicated administrative script under `scripts/` to bypass the classifier and force the orchestrator to run the full document.

### Question 4: Resolving Inter-Worker Contradictions
*   **Scenario**: What happens if two workers return contradictory information about the same section?
*   **Resolution Strategy**: The **Synthesizer Agent** acts as the primary resolution engine. It compares all worker outputs. If it detects conflicting data points (e.g., conflicting delivery dates or security compliance requirements across different sections), it merges both entries into the final summary and appends a warning tag: `[CONTRADICTION DETECTED]`. This tells the Sales team that the client's RFP contains conflicting statements that need to be cleared up during the proposal phase.

### Question 5: Pipeline Crash Mitigation & Async Execution Durability
*   **Scenario**: Where does async work run, and how does the ticket stay truthful if the job crashes mid-pipeline?
*   **Resolution Strategy**: Asynchronous work runs via localized background workers within the primary API process. To prevent tickets from getting permanently stuck in an `analyzing` state if a server crashes mid-pipeline, the database uses a timestamped heartbeat check. If a ticket remains stuck in `analyzing` for longer than a specified timeout without active updates, the UI flags it as `System Error / Failed`. The user can then click a re-try option, or an administrator can safely clean it up using manual runners located in `scripts/`.

---

## 5. Verification Framework & Evaluation Standards
A successful implementation will be evaluated against these clear metrics:
*   **Operational Completeness**: The final backoffice screen must display comprehensive, department-by-department breakdowns along with internal contacts without requiring team members to open the original source PDF.
*   **Strict Context Adherence**: Department mappings and classification paths must perfectly match the internal organization guidelines documented in `CONTEXT-company.md`.
*   **Data Integrity Verification**: The system must pass all internal integration smoke testing loops using the real sample verification files stored under `rfp-requests/<company>/`.