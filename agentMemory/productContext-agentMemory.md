# Product Context: Cross-Border Episodic Memory Agent Extension
## Company: HealthCore Inc.

### 1. Executive Summary & Problem Statement
HealthCore operates a network of **12 outpatient clinics** across two distinct regulatory markets: **9 in the United States** (Texas, Florida, Georgia) and **3 in the United Kingdom** (London, Manchester). The company manages a highly complex ecosystem spanning multiple disparate platforms, including two isolated Electronic Health Record (EHR) systems that do not natively communicate, separate billing structures, and fragmented scheduling setups. 

Under the internal initiative **HealthCore Digital**, the company deployed an intelligent assistant built on LangGraph to automate cross-functional tasks using Model Context Protocol (MCP) servers and read-only Retrieval-Augmented Generation (RAG) collections (`*_knowledge`). 

However, as highlighted in **Ticket #MEM-092**, a critical operational bottleneck remains: **the agent maintains zero state across conversational boundaries**. Every conversation resets to zero. Clinicians, administrators, and patients are forced to repeat data updates or corrections multiple times in a single week. For instance, two different clients recently had to repeat identical data corrections three separate times because the agent completely lacked an episodic memory mechanism. This flaw degrades clinical documentation efficiency, compounds administrative fatigue (where staff spend 35 minutes daily on paperwork), and introduces severe execution friction across patient experience, billing, and workforce tracking workflows.

---

### 2. Product Scope & Functional Division
To resolve Ticket #MEM-092, this milestone extends the current LangGraph assistant with a self-evaluating episodic memory architecture. It strictly balances interactive learning with rigid data governance. The agent retains its dedicated workspace identities (e.g., Manager Support, Patient Experience & Access, Revenue Cycle & Billing, or Compliance & Data Governance) and interacts with surrounding resources through a strict division of labor:

*   **Company Knowledge (RAG Stores):** Stays entirely read-only within the system. The corporate Qdrant knowledge bases (`*_knowledge`) contain static enterprise references, local market operational guidelines, and legal source texts. The agent calls RAG solely as an informational tool; it never writes to these indexes, nor does it serve as a simple, commercial "Q&A search interface."
*   **Episodic Memory Engine:** A decoupled, dedicated, writable cache (`*_agent_memory`) designed to record validated user preferences, recurring administrative adjustments, and confirmed cross-border operational context across independent historical sessions.
*   **Identity Guardrails:** The agent must remain a unified processing entity. Self-evaluation and interactive storage optimization occur within its own single-agent execution flow using targeted structured outputs, completely bypassing the need for complex multi-agent synchronization or graph-based relational overhauls.

---

### 3. Cross-Border Regulatory & Data Context
Operating a medical network across the United States and United Kingdom introduces strict compliance guardrails that directly govern this memory architecture:

*   **US Market Context (HIPAA Compliance):** Governed by the Health Insurance Portability and Accountability Act. Writable memory must rigorously protect Protected Health Information (PHI). Any memory string containing patient identifiers, clinical claims metadata, or manual billing coding exceptions must be cryptographically sandboxed and audited.
*   **UK Market Context (UK GDPR Compliance):** Governed by the UK General Data Protection Regulation. Crucially, UK GDPR enforces the **"Right to Be Forgotten" (Article 17)** and the **Right to Rectification (Article 16)**. The persistent memory architecture must support explicit data purging, selective forgetting, and absolute transparency regarding how a data item entered the database.
*   **Target Organizational Vectors:**
    *   *Clinical Operations (Dr. Marcus Reid):* Caching recurring workflow documentation paths to decrease the 35-minute administrative burden.
    *   *Patient Experience (Priya Nair):* Reminiscing historical patient scheduling bottlenecks to lower the 22% network no-show rate.
    *   *Revenue Cycle (Tom Callahan):* Preserving specific manual coding interpretations to permanently decrease the 14% US claims denial rate.
    *   *Compliance & Governance (Claire Whitfield):* Constructing cohesive, fully traceable logs to allow immediate cross-jurisdictional auditing without manual data gathering.

---

### 4. Memory Poisoning & Security Defenses
Allowing an agent to update its own runtime memory introduces a high-risk vector for malicious or erroneous state manipulation. If a user inputs a false or conflicting policy update, an unmitigated agent might permanently corrupt its baseline operational guidelines. 

This architecture implements a multi-tiered defense matrix:
1.  **Human-in-the-Loop Isolation:** The agent is physically blocked from executing autonomous database writes. Every proposed memory payload must be explicitly presented to the human operator for validation, modification, or rejection.
2.  **Explicit Intent Classification Engine:** The next user turn is parsed via strict classification boundaries. The system will discard any text that does not confidently map to an affirmative validation state, preventing vague or manipulative conversations from sliding passive overrides into persistent memory.
3.  **Governance Control Chain Mapping:** While real-world production networks channel memory changes through modification request tickets reviewed by dedicated governance teams, this project condenses the lifecycle into an in-turn loop: `Proposal → User Classification → Immediate Store Write/Consolidation`. However, full security traceability is maintained by writing all rejected, approved, or edited states into an unalterable audit ledger containing timestamps and full message hashes.