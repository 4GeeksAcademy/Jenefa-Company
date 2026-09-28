# Engineering Specifications: Self-Evaluating Memory System
## Project Code: MEM-092 (HealthCore Digital Unit)

### 1. Architectural Memory Selection & Isolation
The episodic memory subsystem must avoid bloating runtime prompt structures or contaminating production knowledge stores. The implementation must adhere to the following infrastructure rules:

*   **Storage Isolation:** Persistent storage must utilize a distinct, dedicated database layer (e.g., Redis, a separate key-value store, or decoupled Qdrant collections labeled under the `*_agent_memory` suffix). 
*   **RAG Read-Only Sanitization:** Under no circumstances will memory routines execute write operations against company knowledge bases (`*_knowledge` / corporate Qdrant RAG layers). Mixing user-approved episodic data with static regulatory corporate assets breaks evaluation frameworks and poisons baseline control sets.
*   **Explicit Read/Write Interfaces:** The agent must interface with memory via structured, algorithmic lookups. It is strictly forbidden to accumulate historical state by appending raw conversation blocks to the system prompt context window.

---

### 2. Unified Single-Call Inference (Self-Evaluation & Proposal)
To prevent runtime latency spikes and optimize token usage, the agent must evaluate the current conversation and formulate its responses within a single execution block. 

*   **Structured Output Engine:** The model must be driven via a strict schema (e.g., Pydantic or JSON Schema) that forces a unified multi-field response during its regular generation pass.
*   **Schema Schema Output Fields:**
    1.  `visible_response` (string): The natural language response targeted directly to the clinician, administrator, or patient.
    2.  `memory_proposal` (object, optional): A structured payload generated only if a memorable interaction is identified. It must contain:
        *   `fact_to_remember` (string): The refined, concise operational piece of data or correction.
        *   `justification` (string): The specific business logic or clinical validation reasoning explaining *why* this fact warrants preservation.
*   **The Proposing Threshold:** The model must evaluate interactions against explicit criteria—such as a repeated administrative preference, an explicit clinical correction to an EHR data field, or a specific manual billing coding workaround. It must default to dismissing the vast majority of standard interactions.

#### Technical Baseline: Mandatory Non-Memorable Interactions
The agent must actively categorize the following scenarios as **"nothing to remember"** and return a null `memory_proposal` payload:
1.  *Routine Informational Lookups:* A user asking for standard clinic operating hours in London or Austin.
2.  *Static Regulatory Queries:* General inquiries concerning default HIPAA or UK GDPR retention rules found in read-only documentation.
3.  *Transitory Conversational Metadata:* Polite greetings, minor system navigation text, or casual sign-offs.

---

### 3. User Confirmation, State Routing, and The Audit Log
When a `memory_proposal` is generated, the agent must output its natural language response and embed an explicit confirmation request within the same interface (e.g., *"Would you like me to remember this preference for future sessions?"*). 

#### Explicit Intent Classification State Machine
The user's subsequent message must be channeled into a dedicated intent classification node before any execution or state routing takes place. The system must completely reject naive text matching or fuzzy substring searches (such as checking if the word "yes" exists in the sentence).

```
          [ User Next Message Received ]
                        │
                        ▼
         [ Intent Classification Engine ]
                        │
       ┌────────────────┼────────────────┐
       ▼                ▼                ▼
   [APPROVE]         [REJECT]         [EDIT]
       │                │                │
       ▼                ▼                ▼
Consolidate to    Discard Payload   Parse Modified
`*_agent_memory`  Keep Audit Trace  Fact & Update
       │                │                │
       └────────────────┼────────────────┘
                        │
                        ▼
          [ Standard LangGraph Router ]
```

*   **The Single-Flight Pending Rule:** There can only be **one single pending proposal** unresolved at any point in time. If a proposal is outstanding, the evaluation engine is completely locked from generating a secondary proposal until the primary flight is fully resolved.
*   **Discard-by-Default Fallback:** If the user shifts the topic, remains silent, or provides an ambiguous response, **approval is never assumed**. The state machine must automatically categorize the interaction as a rejection, discard the active payload from the write pipeline, and route back to standard conversational loops.
*   **Auditable Transaction Log:** Every single proposal lifecycle must be immutably recorded for legal compliance tracking under HIPAA and UK GDPR. The log must be structured as follows:

```json
{
  "timestamp": "ISO-8601 UTC Timestamp",
  "proposal_id": "UUIDv4",
  "fact_proposed": "The textual fact evaluated by the model",
  "originating_message_hash": "SHA-256 hash of the triggering conversation turn",
  "user_classification": "APPROVE | REJECT | EDIT | DISCARD_BY_DEFAULT",
  "final_stored_state": "The precise text committed to storage, or null if rejected/discarded",
  "authorizing_user_metadata": "Role-based credentials of the validating operator"
}
```
*Note: A tracking entry must be permanently saved to the ledger even if the proposal is rejected or abandoned by default.*

---

### 4. Memory Consolidation and Expiration Policy
To prevent memory stores from expanding exponentially and degrading semantic vector lookups over time, a strict cleanup pipeline must execute asynchronously or during off-peak operational boundaries.

*   **Deduplication & Summarization:** The consolidation engine must merge highly redundant data blocks and compress multiple distinct logs into unified operational preferences.
*   **Data Minimization & Expiration Policy:** In strict compliance with UK GDPR's data minimization mandates, an explicit Time-to-Live (TTL) ceiling of **90 days** is enforced across the episodic `*_agent_memory` database. 
*   **Justification:** A 90-day retention window perfectly spans HealthCore's typical quarterly clinical review cycle. It ensures that temporary administrative workarounds automatically expire, prevents long-term vector drift, and ensures outdated billing coding exceptions do not linger to cause systematic claims rejections.

---

### 5. Project Delivery Verification Lifecycle
The implementation will be verified by auditing two complete, documented verification cycles:

1.  **Cycle A (The Approved Loop):**
    *   *Turn 1:* User inputs an explicit billing exception due to a unique commercial insurance rule in Texas.
    *   *Evaluation:* Agent outputs response and structures a `memory_proposal`.
    *   *Turn 2:* User provides explicit approval. System writes to `*_agent_memory` and records the complete transactional log entry.
    *   *Turn 3 (New Session):* User initiates a separate discussion regarding Texas claims; agent proactively fetches from `*_agent_memory` to demonstrate contextual learning.
2.  **Cycle B (The Rejected / Discard-by-Default Loop):**
    *   *Turn 1:* User updates a clinic configuration option; agent flags it and proposes memory storage.
    *   *Turn 2:* User completely changes the subject to ask about London clinic staffing hours.
    *   *Evaluation:* System triggers the **discard-by-default** protocol. The payload is safely purged, memory remains completely unmutated, and a tracking log documenting the user's abandonment is permanently committed to the ledger.

---

### 6. Dependency Constraints
*   All new libraries, database drivers, or schema parsers must be explicitly added via the package manager utilizing the **`uv add <package>`** framework.
*   The use of `pip install`, `pipenv`, or raw `requirements.txt` manipulation is strictly forbidden.