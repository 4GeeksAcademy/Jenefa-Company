# Specifications - RFP Response Generation

1. System Pipeline Architecture
The workflow runs as a parallel execution pipeline integrated into HealthCore's existing backend architecture under data/pipelines/.
[Part 1 Handoff: status == intake_complete]
                    │
                    ▼
          ┌───────────────────┐
          │    Assignment     │
          │   Orchestrator    │
          └─────────┬─────────┘
                    │
  ┌─────────────────┼──────────────────┐ (Parallel Departmental Streams)
  ▼                 ▼                  ▼
[Sales & Billing] [Compliance/Legal] [Clinical Operations]
  │                 │                  │
  └─────────────────┼──────────────────┘
                    │
                    ▼
          ┌───────────────────┐
          │ Final Deliverable │
          │    Synthesizer    │
          └─────────┬─────────┘
                    │
                    ▼
  ┌────────────────────────────────────────────────────────┐
  │         Generator-Evaluator Multi-Agent Loop          │
  │                                                        │
  │   ┌───────────────┐          ┌───────────────────┐     │
  │   │  Generator    │◄─────────┤ Parallel Evaluators│     │
  │   │  Agent        ├─────────►│  (Readability,    │     │
  │   └───────────────┘  Draft   │   Relevance,      │     │
  │                       Text   │   Compliance)     │     │
  │                              └─────────┬─────────┘     │
  │                                        │               │
  │                                        ▼               │
  │                               [EvaluationResult]       │
  └────────────────────────────────────────┬───────────────┘
                                           │
                    ┌──────────────────────┴──────────────────────┐
                    ▼                                             ▼
          [All Evaluators Pass]                        [Iteration Limit Hit]
                    │                                             │
                    ▼                                             ▼
         [Status: under_evaluation]                 [Status: needs_human_review]
                    │                                             │
                    └──────────────────────┬──────────────────────┘
                                           │
                                           ▼
                                [Part 3 Storage & Handoff]
2. HealthCore Departmental Mapping Matrix
The Assignment Orchestrator maps tasks derived from the Part 1 workstream structure to specific HealthCore domains:
Target Department	Mapped Functional Scope & Systems Touched
Sales, Revenue Cycle & Billing	Value Propositions, Commercial Pricing, Payer Models (US Commercial/Medicare/Medicaid vs. UK Private/NHS), and Collection Metrics.
Compliance & Data Governance	Cross-border Data Privacy Boundaries, HIPAA Audit Trails, UK GDPR Consent Layouts, and Data Sovereignty Safeguards.
Clinical Operations & Delivery	Multi-location Resource Allocation, Cross-EHR History Visibility, Clinical Note Documentation, and SLA Commitments.
3. Data Schemas & Persistence
Ticket Lifecycle States
The pipeline mutates the PostgreSQL ticket record using the following precise state values:
• intake_complete: Entry status inherited from Part 1 routing handoff.
• drafting: Set as soon as departmental generator agents spin up.
• under_evaluation: Set during active evaluation execution loop.
• needs_human_review: Set if any section exhausts the maximum iteration limit without passing.
EvaluationResult Schema Shape
Every section evaluation must be compiled and persisted as a structured JSONB object in PostgreSQL adhering to this structure:
json
{
  "section_id": "string",
  "department_id": "string",
  "readability": {
    "pass": "boolean",
    "score": "float",
    "details": "string"
  },
  "relevance": {
    "pass": "boolean",
    "missing_aspects": ["string"]
  },
  "compliance": {
    "pass": "boolean",
    "rule_ids": ["string"],
    "violations": ["string"]
  },
  "overall_pass": "boolean",
  "feedback_for_generator": "string"
}

4. Execution & Orchestration Loop Logic
python
def execute_generator_evaluator_loop(ticket_id, department_id, key_aspects):
    iteration = 0
    max_iterations = 3
    feedback = ""
    
    update_ticket_status(ticket_id, "drafting")
    
    while iteration < max_iterations:
        # Generate section text draft
        draft = call_department_generator(department_id, key_aspects, feedback)
        update_ticket_status(ticket_id, "under_evaluation")
        
        # Parallel Execution of Evaluators
        eval_result = run_parallel_evaluators(department_id, draft, key_aspects)
        persist_evaluation_to_postgres(ticket_id, department_id, draft, eval_result)
        
        if eval_result.overall_pass:
            return draft, eval_result
            
        feedback = eval_result.feedback_for_generator
        iteration += 1
        
    # Iteration limit reached without passing
    update_ticket_status(ticket_id, "needs_human_review")
    return draft, eval_result

5. Architectural Design Answers
Q1: What state information does each evaluator agent actually need?
• Answer: Evaluators receive the specific section draft alongside the department-scoped key_aspects context extracted during Part 1. The full, global unified document is not passed to individual evaluators to optimize token performance and prevent cross-context confusion. However, the Compliance Evaluator is explicitly provided with the complete static lookup matrix from CONTEXT-company.md to ensure all checks map to hard organizational rules.
Q2: How do you prevent two parallel evaluators from conflicting when writing their results to the shared state?
• Answer: Evaluators run as isolated, concurrent processes. They do not write to the live row state concurrently. Instead, their execution futures are gathered asynchronously via an orchestration engine. The master coordinator aggregates their outputs into a single, immutable EvaluationResult document before committing a single transactional write to PostgreSQL.
Q3: When a section hits needs_human_review after exhausting iterations, how do you surface that to Sales so they know which draft is provisional?
• Answer: The row in the database keeps the final draft text and sets the specific section flag to needs_human_review. When the Part 3 interface or payload presents this to Sales, it uses the overall_pass: false field to highlight the section with visual alerts and displays the compiled violations[] array alongside the actionable feedback_for_generator string to show exactly why the section is provisional.
Q4: Is the feedback the generator receives after a failure specific enough to fix the real problem, or is it generic?
• Answer: The feedback is completely deterministic and specific. It is built programmatically by combining the missing_aspects[] from the relevance checker and the exact rule strings from the violations[] array caught by the compliance checker. This ensures the generator receives precise instructions on what text to insert or fix on its next loop attempt.
6. Testing Framework Requirements
All test files must be positioned inside tests/pipelines/.
• Unit Test Coverage: Implement focused unit tests validating at least one specific department generator agent and one evaluator agent.
• Failure Execution Test: Write a test case modeling an evaluation rejection, verifying that an invalid payload correctly yields overall_pass == false and populates actionable feedback text.
• Concrete Compliance Failure Test: Provide one small, self-contained test fixture tied directly to an explicit rule within CONTEXT-company.md. For example, if a draft explicitly promises an unbacked SLA or forbidden discount option, assert that compliance.pass == false and that the correct rule identifier is populated inside the rule_ids[] tracker array. No looping orchestration is required for this isolated case.
