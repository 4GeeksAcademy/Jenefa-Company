# Product Context: HealthCore Agent Defensive Harness

## 1. Executive Summary & Company Identity
**HealthCore** is an outpatient healthcare services provider founded in 2011 in Austin, Texas, operating a multi-national network of **12 clinics** (9 in the United States across Texas, Florida, and Georgia; 3 in the United Kingdom across London and Manchester) [cite: 1]. The company generates **$28 million in annual revenue** and employs **200 people** [cite: 1]. 

Led by founder **Dr. Sandra Okonkwo**, the company has established the **HealthCore Digital** business unit to build integrated intelligent tools to modernize its operation [cite: 2, 3]. This agent serves as the core natural-language workspace interface meant to unify departmental visibility, streamline staff operations, and assist leadership with real-time KPI evaluations [cite: 3, 6].

## 2. Cross-Border Operations & Core Domain Boundaries
HealthCore operates across separate geopolitical, clinical, and billing infrastructures that dictate the precise domain boundaries of this agent [cite: 1]:
*   **Clinical Operations (Dr. Marcus Reid):** Directs ~120 clinical staff across 12 locations [cite: 1, 3]. US clinics use a completely separate Electronic Health Record (EHR) platform from UK clinics, and they do not communicate [cite: 1, 3]. 
*   **Patient Experience (Priya Nair):** Manages scheduling. US bookings are exclusively phone-based, while UK bookings utilize local front desks, causing a crippling **22% network-wide no-show rate** costing $1.8M annually [cite: 1, 2, 4].
*   **Revenue Cycle & Billing (Tom Callahan):** Processes complex claims frameworks. The US arm navigates commercial insurance, Medicare, and Medicaid with a high **14% claim denial rate** [cite: 1, 4]. The UK arm processes private pay and small NHS contracts via distinct tools [cite: 1, 4].
*   **Compliance & Data Governance (Claire Whitfield):** Enforces absolute legal containment [cite: 2, 5]. Patient data handling must comply perfectly with **HIPAA** regulations in the United States and **UK GDPR** in the United Kingdom [cite: 2, 5]. 

The agent is legally restricted to retrieving, synthesizing, and executing commands tightly bounded within these corporate data parameters [cite: 5, 7].

## 3. The Vulnerability of Persistent Memory
From prior development phases, the agent possesses long-term memory capabilities allowing it to propose, update, and persist behavioral and operational facts across continuous user interaction cycles. 

Without defensive constraints, this architecture creates a compounding security vulnerability: **Persistent Memory Poisoning**. If an adversarial user successfully executes a prompt injection or a system jailbreak, they can force the agent to store corrupted or malicious operational constraints directly into its long-term memory layer. This poisoned state then sticks across subsequent user sessions, indefinitely neutralizing its safety protocols and turning a multi-tenant business tool into an unaligned rogue entity.

## 4. The Defensive Harness Paradigm
To prevent systemic failure, the system enforces a strict operational separation: **The model decides, but the programmatic harness controls, executes, and contains.** 
```
  [ External User Input ]
             │
             ▼
┌────────────────────────────────────────────────────────┐
│               PROGRAMMATIC DEFENSIVE HARNESS           │
│                                                        │
│ ┌───────────────────┐  ┌─────────────────────────────┐ │
│ │ Layer 1: Input    │  │ Layer 2: Retrieval          │ │
│ │ Guardrails        │  │ Isolation                   │ │
│ │ - Injection Block │  │ - Sanitizes RAG/Tool Blocks │ │
│ └─────────┬─────────┘  └──────────────┬──────────────┘ │
└───────────┼───────────────────────────┼────────────────┘
            │                           ▲
            ▼                           │
┌───────────────────────────────────────┴────────────────┐
│                   CORE LLM SYSTEM                      │
│                                                        │
│   [ Secure System Prompt with Strict Block Formats ]   │
└───────────────────────────────────────┬────────────────┘
                                        │
                                        ▼
┌────────────────────────────────────────────────────────┐
│               PROGRAMMATIC DEFENSIVE HARNESS           │
│                                                        │
│ ┌────────────────────────────────────────────────────┐ │
│ │ Layer 3: Output Structural & Content Validation    │ │
│ │ - Block Rule Leakage & Raw Internal Context Data   │ │
│ └────────────────────────────────────────────────────┘ │
└───────────────────────────────────────┬────────────────┘
                                        │
                                        ▼
                              [ Verified Output ]
```
The Core Model is explicitly treated as an unverified execution engine. The wrapping harness is the absolute source of truth responsible for sanitizing incoming vectors, containing runtime errors, and validating outgoing messages.

## 5. The Three Agents Failures Framework
The defensive architecture is programmatically structured to intercept three distinct modalities of agent breakdown:

*   **Structural Failures:** Malformed payloads or missing required payload parameters emerging from tools or MCP (Model Context Protocol) interactions trying to fetch disconnected EHR platforms or billing streams [cite: 6].
*   **Content Failures:** Model hallucinations regarding network statistics, exposure of internal compliance rule files, or unauthorized leakage of protected patient health information across the US/UK regulatory boundary [cite: 2, 5].
*   **Security Failures:** Intentional prompt injections or jailbreaks where adversarial inputs attempt to trick the underlying model into ignoring its core corporate deployment instructions or operating as an unaligned third-party assistant.