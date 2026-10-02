# Technical Specification: Basic Server Hardening & OWASP Top 10 Security Audit
**Target System:** HealthCore Monorepo Applications (Frontend, Central Patient API, Document/Billing Agentic System)

---

## 1. Objective & Scope
This specification mandates the baseline server hardening and security audit protocols required before exposing HealthCore's unified platforms to live healthcare traffic. The target environment orchestrates cross-border healthcare data pipelines connecting isolated electronic health record (EHR) endpoints across 12 clinic networks (US & UK). All components must pass validation to safeguard Protected Health Information (PHI) under HIPAA and UK GDPR.

---

## 2. Component Architecture under Review
The security audit must evaluate the following components within the monorepo independently:
*   **HealthCore Patient-Facing Frontend:** Client application handling appointment bookings and personal data access.
*   **HealthCore Central Patient API (Backend):** The core routing layer consolidating multi-market EHR systems and billing databases.
*   **Agentic System (AI Documentation & Claims Assistant):** Autonomous LLM-driven pipelines consuming clinical text, outputting medical codes, and predicting appointment patterns.

---

## 3. Core Server Hardening Requirements

The infrastructure hosting HealthCore components must be systematically locked down according to the following matrix.

| Hardening Focus | Requirement Specification | Verification Criteria |
| :--- | :--- | :--- |
| **User Access Management** | Create a dedicated, unprivileged operating system user (e.g., `hc-runtime`) for day-to-day application execution. | Application processes do not run with UID 0 (`root`). |
| **SSH Configuration** | Modify SSH daemon configurations to completely disable direct `root` login (`PermitRootLogin no`). Enforce cryptographic public key authentication only. | Direct login attempts via `ssh root@<ip>` are strictly rejected by the host. |
| **Directory/File Security** | Apply rigid file permission boundaries to separate application code repositories, active log directories, and sensitive environment secrets (`.env`). | Runtime users hold read-only permissions to application code; write permissions are restricted strictly to log targets. |
| **Network Firewall** | Configure a host-level firewall (e.g., UFW or iptables) to implement a default-deny incoming posture. | Only ports explicitly designated for application delivery (e.g., `443` for HTTPS, non-standard SSH port) are open. All unmonitored ports are closed. |

---

## 4. OWASP Top 10 Audit & Vulnerability Matrix

Every category listed below must be independently investigated across the **Frontend**, **Backend**, and **Agentic System**. A definitive status of **[Applies / Does Not Apply]** must be assigned alongside traceable evidence (such as exact API routes, source code paths, or line-level configurations).

### A01:2021 – Broken Access Control
*   **System Vector:** Ensure a user or clinic operator in the US market cannot view or modify UK patient datasets without explicit authorization.
*   **Agentic Specifics:** Verify that the autonomous assistant cannot invoke clinical tools or data access vectors outside the requesting user’s specific role permissions.
*   **Evidence Required:** Code paths verifying authorization token scopes during cross-border routing.

### A02:2021 – Cryptographic Failures
*   **System Vector:** Protection of PHI in transit and at rest.
*   **Agentic Specifics:** Audit how the LLM framework retrieves and caches external EHR platform API keys, integration credentials, and LLM provider secrets.
*   **Evidence Required:** Verification of AES-256 encryption at rest for environment storage and TLS 1.3 enforcement for external network connections.

### A03:2021 – Injection
*   **System Vector:** SQL/NoSQL sanitization on search endpoints.
*   **Agentic Specifics:** Direct and indirect **Prompt Injection** mitigation. System must prove that untrusted input (e.g., text filled in by a patient or nested inside unstructured clinical notes) cannot trick the agent into executing systemic commands or bypassing security boundaries.
*   **Evidence Required:** Implementation of strict output parsers, LLM system prompt boundaries, and input filtering layers.

### A04:2021 – Insecure Design
*   **System Vector:** Flaws in workflow architectures.
*   **Evidence Required:** Architectural reviews proving state tokens cannot be re-used to bypass multi-factor authentication steps during login.

### A05:2021 – Security Misconfiguration
*   **System Vector:** Disabling default software capabilities, debug logs in production, and standard cloud platform setups.
*   **Agentic Specifics:** Ensure the runtime container housing the autonomous agent executes with minimal host privileges and lacks system-level administrative access.
*   **Evidence Required:** Hardened Dockerfile configurations and disabled default administrative consoles.

### A06:2021 – Vulnerable and Outdated Components
*   **System Vector:** Analysis of third-party dependencies.
*   **Evidence Required:** Automated Software Bill of Materials (SBOM) scanning logs (e.g., Snyk or Trivy outputs) confirming zero unresolved high/critical CVEs.

### A07:2021 – Identification and Authentication Failures
*   **System Vector:** Session management safety.
*   **Evidence Required:** Configuration profiles enforcing session timeouts and preventing brute-force authentication vectors on patient accounts.

### A08:2021 – Software and Data Integrity Failures
*   **System Vector:** Secure plugin updates and data payload ingestion.
*   **Evidence Required:** Signed code commits and secure serialization validation checks during object transfers between services.

### A09:2021 – Security Logging and Monitoring Failures
*   **System Vector:** Centralized telemetry to resolve HealthCore's lack of system visibility.
*   **Evidence Required:** Unified audit trails routing error states and sensitive data access logs to an isolated monitoring target.

### A10:2021 – Server-Side Request Forgery (SSRF)
*   **System Vector:** Restricting untrusted URL parameters.
*   **Agentic Specifics:** Ensure that an agent processing external URLs or webhooks cannot be manipulated into performing internal port scans or hitting local infrastructure loopback addresses (`127.0.0.1`).
*   **Evidence Required:** Network egress firewalls and strict URL domain whitelisting on all agent tool integrations.

---

## 5. Formal Engineering Acceptance Criteria
Before an application receives sign-off to handle live production workloads, the engineering squad must verify the following items:
*   [ ] **Server Access Hardening:** Direct SSH root logins are rejected; access occurs exclusively through low-privilege operational users via public-key pairs.
*   [ ] **Firewall Enforcement:** A strict firewall is active; only explicitly approved network ports are open; all historical or default ports are removed.
*   [ ] **Comprehensive Evaluation Matrix:** All 10 OWASP categories have an explicit finding (`Applies` / `Does Not Apply`) backed by file, endpoint, or line-of-code evidence.
*   [ ] **Isolated Agentic Audit:** The autonomous document and billing agent has been audited independently as its own primary architectural layer rather than assumed secure by the surrounding backend infrastructure.
*   [ ] **Critical Remediation Evidence:** Every vulnerability flagged as "Critical" is fully patched, with explicit reproducible evidence (before/after script execution logs, test outputs, or scanning screenshots) documented in the repository.
