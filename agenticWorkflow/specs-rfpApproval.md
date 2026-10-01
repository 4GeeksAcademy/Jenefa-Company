# Technical Specifications: Human-in-the-Loop Approval & Document Synthesis (Part 3)

## 1. System Overview & Architecture
This specification outlines the technical implementation for incorporating scoped Human-in-the-Loop (HITL) approval, parallel state persistence, compliance arbitration, and final pricing proposal document synthesis for the **HealthCore Digital** unit. It directly extends the multi-agent graph architecture established in Parts 1 and 2 to support cross-border commercial configurations across our 12 clinics.

┌───────────────────────────┐
│   Assignment Orchestrator │
└─────────────┬─────────────┘
│
┌──────────────────────────┼──────────────────────────┐
▼                          ▼                          ▼
[Revenue Stream Track]       [Clinical Ops Track]       [Compliance & Data Track]
Owner: Tom Callahan          Owner: Dr. Marcus Reid     Owner: Claire Whitfield
State: under_evaluation      State: under_evaluation    State: under_evaluation
│                          │                          │
[HITL Interrupt Point]       [HITL Interrupt Point]     [HITL Interrupt Point]
State: waiting_for_approval  State: waiting_for_approval State: waiting_for_approval
│                          │                          │
▼                          ▼                          ▼
Billing Approved           Clinical Approved          Compliance Approved
│                          │                          │
└──────────────────────────┼──────────────────────────┘
│
▼
┌───────────────────────────┐
│    Conflict Arbitration   │◄─── Iteration Limit Safeguard
│  Fixed Arbiter: Okonkwo   │
└─────────────┬─────────────┘
│ (No Conflicts / Resolved)
▼
┌───────────────────────────┐
│ Ultimate Doc Synthesizer  │
└─────────────┬─────────────┘
▼
State: done

## 2. Checkpointer & Namespacing Execution
* **State Persistence:** Right before a department's section is considered approved, the state machine must execute an explicit `interrupt()` point using a persistent storage saver (`SqliteSaver` or `PostgresSaver`). 
* **Checkpoint Isolation:** To prevent concurrent cross-border proposal runs from sharing or corrupting state, every graph execution's `thread_id` must be explicitly namespaced by its unique database `ticket_id` and sub-department identifier:
  * Format: `rfp-{ticket_id}` or `rfp-{ticket_id}:{department}`

## 3. Scoped Interrupts & Resume Entry Points
* **Branch Isolation:** The `interrupt()` point must only freeze the individual execution branch corresponding to that specific department. Other branches whose sections are already completed or undergoing evaluation must continue moving forward in parallel without getting cross-blocked.
* **Resume Strategy:** Implement `resume` as an explicit, targeted entry point into the graph state. It must resume exactly where it was suspended rather than restarting the entire flow or re-running upstream nodes.
* **Input Validation:** Prior to transitioning out of the interrupt back into active graph processing, the system must programmatically validate the structure of the incoming human response to ensure it maps exactly to permitted tokens: `approve`, `reject`, or `request_changes`.
* **Interface Extension:** The `uis/backoffice` dashboard built during Part 1 must be extended to provide explicit controls for each departmental approver to log their choice.

## 4. Guardrails, Conflict Tracking, & Arbitration
* **Iteration Limits:** To prevent infinite negotiation loops between departments, the graph state must track modification counters. A verified runtime maximum iteration ceiling must be strictly enforced in code.
* **Structured Conflict Detection:** The graph must look for specific structured criteria in the state (e.g., cross-border operational mismatches, unauthorized cross-system data transfer requests, or unverified regulatory compliance scopes) rather than relying solely on fuzzy free-text logs to identify friction.
* **Deterministic Arbitration:** When a conflict trigger fires, the flow routes to an explicit arbitration node. This node resolves disputes using the named fixed human arbiter—**CEO Dr. Sandra Okonkwo**—**LLM agent voting or freestyle consensus is completely prohibited**.

## 5. Document Synthesis Node
* **Convergence Criterion:** The `Ultimate Document Synthesizer` node executes automatically **if and only if** every assigned department branch has successfully submitted a verified human sign-off status.
* **Compilation:** It compiles and consolidates the finalized individual sections into a unified sales-ready deliverable.
* **Format Compliance:** The output deliverable must match the schema and layout configuration dictated by the **HealthCore Digital** guidelines, maintaining dual pricing structures for US commercial streams and UK private pay/NHS contracts.

## 6. Observability & Traceability
To ensure production debuggability, every node execution within the state machine must automatically append an entry to an immutable lineage log containing:
* `agent_id` / Node Name
* `input_payload`
* `output_payload`
* `timestamp`

## 7. Testing & Quality Gates
All code paths must be fully validated under `tests/pipelines/` via automated suites:
* **Unit Tests:** Must explicitly cover successful interruption/resume cycles, breaking on maximum iteration limits, arbitration behavior on departmental disagreements, and a dedicated test/trace proving that Department B can be successfully approved while Department A remains cleanly suspended under an interrupt.
* **E2E / Integration Path:** Ship a fully reproducible programmatic script or fixture-driven test that simulates a complete RFP journey from the initial Part 1 document upload, through Part 2 generation, and ending with programmatic resumes driving the Part 3 compilation without relying on manual interface interactions.