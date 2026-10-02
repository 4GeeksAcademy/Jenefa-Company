# Product Context: HealthCore Security Alignment
**Context Focus:** Systemic Remediation & Regulatory Safety Compliance

---

## 1. Business Context & Strategic Necessity
HealthCore is an outpatient healthcare services provider operating a cross-border network of **12 clinical centers** (9 in the United States across Texas, Florida, and Georgia; 3 in the United Kingdom within London and Manchester). The company handles care services for thousands of patients, employing a workforce of 200 across clinical, operations, and technical teams, generating approximately \$28 million in annual revenue. 

Historically, HealthCore’s rapid expansion outpaced its core underlying technical infrastructure, leaving a patchwork of isolated operational systems: two conflicting electronic health record (EHR) instances, disconnected manual billing databases, and independent scheduling pipelines. To modernize, the company formed **HealthCore Digital**—an internal software development team tasked with building a shared data layer, unified booking gateways, and advanced automated workflows.

Because the applications process patient health information across international borders, security is an absolute legal and ethical requirement. The system must operate under two rigorous regulatory frameworks simultaneously:
1.  **HIPAA (United States):** Requires absolute data privacy, strict access controls, and verifiable audit tracking for Protected Health Information (PHI).
2.  **UK GDPR (United Kingdom):** Enforces data minimization, patient right-to-access tracking, and localized European data handling provisions.

A failure in application security doesn't just impact technical availability—it introduces severe legal liabilities, financial penalties from regulatory bodies, and directly risks patient trust and clinical outcomes.

---

## 2. Current Technical Debt Baseline
Prior to this structural security initiative, HealthCore's systems ran on a legacy infrastructure architecture characterized by high risk:
*   **Lack of Access Controls:** Services run on default system configurations, with widespread reliance on the system `root` user for daily operations and server access.
*   **Exposed Perimeter:** Multiple network ports remain wide open across development environments without documentation or clear architectural business justification.
*   **No Central Telemetry:** There is no uniform audit logging system, meaning data access trails across separate US and UK EHR boundaries are completely fractured and manually compiled.
*   **Unvetted Application Logic:** The newly deployed Monorepo platforms (Frontend, Central Patient API, and autonomous AI subsystems) have never undergone a formal, systematic web security review against standard industry threat vectors.

---

## 3. High-Level Monorepo Architecture & Scope
The remediation effort applies to the entire HealthCore Digital monorepo, which unifies the front-to-back operations of the clinical network:

[HealthCore Patient Frontend] ──> [Central Patient API (Backend)] ──> [US & UK EHR Networks]
│
└──> [Agentic Subsystem (AI Coding/Docs)]

### Component Breakdown & Risk Profiles
*   **The Frontend Application:** The entry point for online customer scheduling and patient portals. Vulnerabilities here expose patient identity vectors and session data.
*   **The Central Patient API (Backend):** The core router consolidating multi-market records, scheduling databases, and financial flows. This acts as the primary data gateway and must be insulated from unauthorized lateral movement.
*   **The Agentic Subsystem (AI Operations):** An autonomous system executing workflows like translating clinical documentation into structured billing codes or predicting booking patterns. This component carries an entirely unique risk profile. It cannot be treated as a passive chatbot or assumed secure by the backend layer. If compromised via prompt injection or unvetted tool authorization, the agent could be manipulated into executing unauthorized read operations across regulatory data boundaries.

---

## 4. Remediation Strategy & Execution Order
The technical lead’s directive outlines a strict, progressive workflow that the engineering squad must execute sequentially:

1.  **Establish the Security Baseline:** Prior to altering application environments, document the current configuration state (including active ports and running process IDs) to serve as a comparative baseline.
2.  **Infrastructure Hardening:** Secure the host layer immediately. Disable direct administrative root logins, provision low-privilege service operators, isolate critical data folder paths, and apply a strict firewall policy.
3.  **Comprehensive OWASP Top 10 Evaluation:** Systematically review the codebases of the Frontend, Backend, and Agentic integrations. Map every potential threat vector back to verifiable lines of code or routing logic.
4.  **Isolate & Audit Agent Tools:** Conduct a dedicated vulnerability assessment on the AI assistant, focusing on malicious tool invocation boundaries, prompt injection vectors, and secure API key storage.
5.  **Critical Resolution & Verification:** Every single identified vulnerability evaluated as a critical risk must be fixed. Engineers must supply explicit, reproducible evidence showcasing the system's security improvement before final production deployment approval is granted.
