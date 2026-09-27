# Product Context: Traceable & Grounded RAG Agent

## 1. The Problem Space & HealthCore Context
**HealthCore** is an outpatient healthcare services network founded in 2011, operating **12 clinics** across the US and the UK, supporting **200 employees**, and generating **\$28 million in annual revenue**. Under the leadership of **Dr. Sandra Okonkwo**, the company is aggressively scaling but is currently constrained by an isolated technical landscape. Our US and UK clinics run on separate Electronic Health Record (EHR) platforms that do not communicate, leaving leadership without real-time global insights.

To solve this, **HealthCore Digital** was formed to establish a shared, intelligent data layer. Our initial RAG system prototype was functional but operated as a completely unobservable "black box." It accepted queries and generated answers without a queryable audit trail. In a high-stakes, highly regulated healthcare environment, an unverified black-box model is a severe operational risk.

## 2. Product Vision & Goals
Our goal is to convert the RAG pipeline into a formal state machine using **LangGraph**. This structural evolution unlocks three core competencies:
*   **Absolute Operational Trust**: Providing fully auditable, queryable execution traces for every run so stakeholders like **Claire Whitfield (Compliance and Data Governance)** can verify that data routing respects operational guardrails.
*   **Isolatable Evaluation**: Moving away from generalized black-box assertions to granular, trace-driven automated test suites. We can test node transitions and grounding independently.
*   **Agile Scalability (Part 2 Readiness)**: Establishing single-responsibility nodes and conditional edges creates a plug-and-play architecture. This prepares the system for Part 2, where we will add specialized tools—such as AI-assisted clinical documentation (saving clinicians 35 minutes/day), automated billing code suggestions to fix the 14% US claim denial rate, and appointment reminders to address the 22% network no-show rate.

## 3. Core Guardrails & User Experience Standards
*   **Deterministic Fallbacks over Hallucinations**: Users must never receive a fabricated response built on empty or ambiguous context. The system must recognize when information is missing and respond honestly (`"I don't have information about that."`).
*   **Unyielding Context Grounding**: Transitioning our execution flow to a graph structure must never degrade the accuracy of our answers. The agent's output must remain tightly anchored to our corporate data storage boundaries (such as `CONTEXT-company.md`). If a graph run passes its structural trace test but ignores corporate documentation policies, the run is categorized as a system failure.
*   **Strict Regulatory Alignment**: Because HealthCore operates across international borders, our software design must account for two completely distinct legal frameworks: **HIPAA** in the United States and **UK GDPR** in the United Kingdom. Traceability is a core requirement to prove data isolation and handling compliance.
*   **Fail-Safe Enterprise Endpoints**: API clients consuming the service endpoint must receive clean, predictable error structures rather than unhandled system tracebacks during execution errors.

## 4. Development & Environment Constraints
*   **Dependency Management**: All project dependencies must be added using `uv add langgraph`. Legacy managers (`pip`, `pipenv`) are prohibited.
*   **Code Duplication**: We must reuse the existing RAG pipeline code inside `data/pipelines/` managed by James Osei's team. Rewriting the underlying search, embedding generation, or extraction modules from scratch violates our codebase efficiency guidelines.
