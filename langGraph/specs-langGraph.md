# Technical Specification: Traceable RAG State Machine (LangGraph Migration)

## 1. System Architecture & Component Mapping
The agentic system transitions from a synchronous, monolithic execution loop to an explicitly defined state machine using **LangGraph**. This graph serves **HealthCore Digital** as the foundation for modernizing our intelligent tools. Existing business logic must be imported directly without modification.

*   **Logic Reuse Location:** `data/pipelines/` (Contains `setup()`, `embed()`, `retrieve()`, and `generate_answer()`).
*   **Graph & Endpoint Location:** `services/<agent-service>/`
*   **Test & Evaluation Location:** `tests/pipelines/`

[User Question]
│
▼
┌───────────────┐
│ receive_input │──(IsEmpty?)──► [Clear Error / END]
└───────────────┘
│ (Valid)
▼
┌───────────────┐
│   retrieve    │
└───────────────┘
│
├──(Context Below Threshold?)──► ┌──────────────────┐
│                                │  honest_refusal  │──► [END]
│                                └──────────────────┘
▼ (Sufficient Context)
┌─────────────────┐
│ generate_answer │──► [END]
└─────────────────┘

## 2. Graph State Definition
The State passed between nodes must be **minimal and explicit**. It acts as the single source of truth during an execution lifecycle and must not store unneeded conversation history.

```python
from typing_extensions import TypedDict
from typing import List, Optional

class AgentState(TypedDict):
    question: str                  # Original query (e.g., Compliance, Policy, EHR logic)
    retrieved_context: List[str]   # Text chunks fetched from knowledge bases (e.g., CONTEXT-company.md)
    answer: Optional[str]          # Generated response or error string
    error: Optional[str]           # Error messaging tracking
```

## 3. Node Contracts & Single Responsibility
Monolithic structures are strictly forbidden. The original `query()` loop must be separated into single-responsibility functional steps to accommodate HealthCore's dual EHR framework and disparate data boundaries:

*   **`receive_input_node`**: Captures and validates the inbound user question.
*   **`retrieve_node`**: Directly calls `retrieve()` from `data/pipelines/`. It parses data into `retrieved_context` and passes it onward. It *must not* perform answer generation.
*   **`generation_node`**: Invokes `generate_answer(question, context)` from the existing RAG pipeline using the state's `retrieved_context`. It *must not* execute secondary lookups or re-run retrieval workflows.
*   **`honest_refusal_node`**: Safely populates the answer state with a controlled fallback string (`"I don't have information about that."`) if thresholds aren't satisfied.

## 4. Edge & Routing Logic (Conditional Decisions)
Edges must be bound to explicit output conditions instead of executing as a hardcoded sequence.
1.  **Input Guardrail**: If `question` is empty or whitespace only, route directly to an error state or `END`.
2.  **Confidence Threshold**: Evaluate `retrieved_context`. If empty or below HealthCore's compliance-approved confidence threshold, divert the graph path to the `honest_refusal_node` instead of forcing generation on blank context.

## 5. Build-Time Compilation & Checkpointing
*   **Compile-Time Validation**: The graph must compile explicitly via `.compile()` before any execution loop runs. Structural breaks (e.g., dead-end nodes, unmapped state keys, or missing edges) must raise errors during build time.
*   **State Checkpointing**: Implement a persistent checkpointer (e.g., `MemorySaver`) at every state transition. This permits targeted post-run inspection, step-replays, or state resumption to satisfy internal technical auditing.

## 6. Endpoint Contract (`services/`)
Expose the compiled workflow through `POST /agent/query`.
*   The endpoint is a **pure pass-through proxy**. It must contain zero business logic or custom routing rules; its sole role is to trigger the graph.
*   If a node throws an exception, catch it gracefully inside the service layer and surface a clear, structured JSON error payload. **Never expose raw stack traces to the API client.**

## 7. Tracing & Evaluations (`tests/pipelines/`)
### Tracing Pipeline
Every execution run must generate a comprehensive, queryable trace (e.g., utilizing LangSmith or a robust, structured database-backed logger) detailing node execution orders and discrete input/output states. Standard console `print()` statement logs fail this requirement.

### Evaluation Criteria
Evals must live within `tests/pipelines/`, operate with a single runner command, and assert behaviors against the compiled execution trace rather than executing fresh live requests every run.

At least **three independent eval cases** must be configured:
1.  **Trace Route Verification**: Assert that for a standard valid query, the `retrieve` node executes and completes *before* the `query` / generation node is called.
2.  **Fallback Path Verification**: Confirm that sending an empty query or out-of-scope query routes exactly to its matching fallback or error node without executing generation workflows.
3.  **RAG Knowledge Grounding**: Assert that a known policy question returns matching facts extracted directly from the underlying knowledge base documentation (e.g., checking that a compliance query matches records in `CONTEXT-company.md`). Grounding remains a strict blocking deployment gate.