# Product Context: Continuous Pricing Proposal Experience

## 1. The Core Problem & Value Proposition
An automated multi-agent system can easily parse RFPs and generate clean financial drafts, but it lacks corporate and clinical accountability. Within **HealthCore**, a pricing proposal represents a binding operational, legal, and financial engagement. Before a proposal or clinical services contract goes out the door to a client, real human department heads must own and sign off on their respective sections.

The main challenge for **HealthCore Digital** is converting this complex multi-stage sign-off into a seamless, **single continuous experience**. Users must not experience disjointed state transitions, missing context, or breaking handoffs as the file travels from raw ingestion to client delivery.

## 2. Departmental Workstream Mapping
Based on our operational design, responsibilities are cleanly bifurcated to allocate roles and manage independent validation tasks before final compilation:

* **Department: Revenue Cycle and Billing**
  * **Owner:** Tom Callahan
  * **Focus:** Commercial insurance navigation, US claims denial mitigations, UK private pay rates, and NHS contract alignment.
* **Department: Clinical Operations**
  * **Owner:** Dr. Marcus Reid
  * **Focus:** Clinical staffing overhead, multi-location EHR capacity management, and provider allocation across our 12 locations.
* **Department: Compliance and Data Governance**
  * **Owner:** Claire Whitfield
  * **Focus:** Safeguarding strict **HIPAA** boundaries in the US and **UK GDPR** parameters in the UK to ensure privacy compliance is non-negotiable.

## 3. Product Principles & Lifecycle Guardrails

### 3.1 Eliminating "Fake Parallelism"
In practice, different business units operate at different speeds. If Claire Whitfield's team is locked in an extended review of a cross-border UK GDPR data boundary, it should not stall Tom Callahan from confirming US revenue cycle numbers. Pauses are tightly scoped to their individual graph tracks so that work can progress asynchronously and independently until converging on the final assembly station.

### 3.2 Strict Status Lifecycle Alignment
To prevent orphan states or system desynchronization, the ticket tracking mechanics on the central database record map directly to these three verified lifecycle stages:

| Status | Trigger Condition |
| :--- | :--- |
| `under_evaluation` / `needs_human_review` | Ticket enters the queue holding the automated drafts and evaluation results forwarded from Part 2. |
| `waiting_for_approval` | Applied the exact moment any department's individual execution track enters an active Human-in-the-Loop pause. |
| `done` | The final consolidated document is synthesized, safely archived, and made accessible to the Executive Leadership team. |

## 4. Key Architectural & Design Decisions

### 4.1 Post-Interruption Rejections
* **Design Decision:** If a human reviewer rejects a section or requests a change during review, the state must not crash or wipe out the run. The flow loops back to the generation mechanics defined in Part 2 to adjust the specific section using feedback data stored in the checkpoint, maintaining full historical context within the ticket's state history.

### 4.2 Cognitive Load Minimization
* **Design Decision:** The approval interface inside `uis/backoffice` will not force reviewers to re-read the entire client RFP. The human-in-the-loop point must present a concise summary showing: the original requirement snippet, the generated proposed terms, any warnings flagged by automated guardrails, and a changelog summarizing previous iterations.

### 4.3 Production Traceability
* **Design Decision:** Guesswork during system incidents is unacceptable. The state log tracks exact data lineages. Operations teams can inspect any run to pinpoint precisely which node executed, what inputs it received, what output it produced, and exactly when the event occurred.
