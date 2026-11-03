# Evidence Agent Memory
## Approved Memory Stream (Success Path)

1. Trigger: LangGraph identifies an explicit, valid recurring operational preference during an active session turn.
2. Proposal Generation: The system structures a split output: a visible_response for the user and a hidden memory_proposal.
3. Intent Classification: The system evaluates user confirmation feedback and classifies it as APPROVE.
4. Persistence & Injection: The approved memory fact is committed to the database, logged with an immutable audit entry, and automatically injected into subsequent LangGraph executions via graph.py and guardrails.py.
5. Evidence Check: Verified via successful test assertions for approved cross-session retrieval and edited facts.

## Rejected / Discarded Memory Stream (Failure & Privacy Paths)

1. Trigger: The agent interacts with routine clinic hours, casual conversation, or an instruction containing sensitive information.
2. Rejection Scenarios:
	• Explicit Rejection: User feedback explicitly signals a REJECT or EDIT intent to a proposal.
	• Ambiguity: Turn feedback fails classification thresholds, triggering a discard-by-default behavior.
	• Privacy Boundary Violation: Proactive scanner flags potential PHI within the candidate string.
3. Resolution: The proposal is dropped immediately at the evaluation boundary. It is never written to persistent memory tables.
4. Evidence Check: Verified via focused test failures/passes for rejected/ambiguous discard, routine lookup suppression, and PHI rejection logs.