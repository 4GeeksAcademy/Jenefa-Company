# Product Context: Natural Language Internal Knowledge Assistant

## 1. Problem Statement
**HealthCore Digital** is building a natural language knowledge assistant to solve an acute operational problem. Our multi-jurisdictional network comprises **12 clinics across the US and the UK**, employing approximately **200 staff members**. While answers to critical compliance, procedure, and clinical operations questions exist within our internal records, this documentation is siloed across separate EHR architectures, manual spreadsheets, and legal files.

Currently, our **Executive Leadership (led by CEO Dr. Sandra Okonkwo)** and frontline administration teams are forced to manually dig through disjointed reports or place physical phone calls to uncover operational facts. This results in lost time, high administrative overhead, and friction. While our centralized API and real-time telemetry dashboards handle structured metrics, we lack a semantic layer that lets leadership query corporate policies, medical licensing guidelines, and multi-country operational frameworks using natural language.

## 2. Target Audience & Voice Guidelines
* **Primary User:** **Dr. Sandra Okonkwo (CEO)** and authorized operational leads (e.g., Compliance Manager, Patient Experience Coordinators).
* **Persona & Voice:** The assistant must speak precisely in the voice of an executive-level, data-driven, and compliance-aware healthcare chief of staff. It must be direct, evidence-based, and highly professional. It must respect the constraints of a highly regulated clinical network. It should present clear answers with zero artificial conversational filler or raw, unformatted code blocks.

## 3. Core Acceptance Criteria
* **Mandatory Context Synthesis:** The system must *never* return raw vector database search outputs, unparsed code strings, or mathematical similarity indices to Dr. Okonkwo. Every response must pass through the generation model step.
* **Model Separation Guardrail:** To protect operational integrity, embedding generation and text response synthesis must be entirely isolated. The generation engine must never be reused to compute vector weights.
* **Strict Failure Honesty:** In accordance with healthcare data safety, if the retrieval step yields no verified internal documentation chunks scoring above the designated similarity threshold, the assistant **must state honestly** that it cannot find the relevant information within current documentation. It is explicitly prohibited from hallucinating or fabricating facts.

## 4. Architectural Fundamentals: RAG is Not Memory
This application is built as a stateless Retrieval-Augmented Generation (RAG) platform. It dynamically pulls verified document fragments based on active administrative queries. It does not store long-term conversational memory or permanently alter the underlying foundation model's weights. If international regulations (HIPAA/UK GDPR) prompt an immediate update or deletion of files inside the knowledge directory, the model's outputs change instantly.
