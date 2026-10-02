# Product Context: Secure AI Multi-Agent Operations & Enterprise Governance Framework

## 1. Executive Summary & Core Mission
**HealthCore**, founded in 2011 in Austin, Texas, is an outpatient healthcare services provider operating a cross-border network of **12 clinics** (9 in the US across Texas, Florida, and Georgia; 3 in the UK across London and Manchester). The network employs approximately **200 people**, services a **$28 million annual revenue** footprint, and is managed by CEO **Dr. Sandra Okonkwo**. 

As part of the **HealthCore Digital** internal unit, we are designing the systems, intelligent tools, and unified APIs required to modernize our healthcare infrastructure. While we have successfully prototyped autonomous agents to classify support traffic, remember patient interactions, and surface real-time telemetry, this system has never undergone a formal security review. This document contextualizes our AI operations to satisfy the urgent audit request opened by our Compliance and Data Governance lead, **Claire Whitfield**. The core mission is to transition our AI architecture into a **Security-by-Design production environment** that safely bridges our fragmented EHR platforms, automated billing suggestions, and patient scheduling loops.

---

## 2. Market Sector, Target Audience, and Trust Posture
* **Market Sector:** Outpatient healthcare services, chronic disease management, and cross-border clinical workflows.
* **Target Audience:** Patients seeking friction-free booking, clinical staff seeking to cut down on 35-minute daily documentation hurdles, and internal executives requiring real-time network visibility.
* **Trust Posture:** We operate under a strict **Zero-Trust AI Archetype**. Because our agents process raw clinical notes, patient scheduling requests, and multi-country operational workflows, we treat all data boundaries as hostile. Every point where a Language Model (LLM) consumes input—whether via the Model Context Protocol (MCP) or our semantic vector space—is a potential threat vector.

---

## 3. Applicable Regulatory Framework & Legal Mandates
A generic compliance report that ignores HealthCore’s unique cross-border landscape will not be accepted. Our platform operates simultaneously across two strict legal frameworks:

### A. Health Insurance Portability and Accountability Act (HIPAA) - United States
* **Applicability:** Applies to all 9 US clinics across Texas, Florida, and Georgia. Protects Protected Health Information (PHI) processed by our US EHR platform, scheduling pipelines, and billing systems.

### B. UK General Data Protection Regulation (UK GDPR) - United Kingdom
* **Applicability:** Applies to our 3 UK clinics across London and Manchester. Enforces strict data sovereignty, data minimization, and right-to-erasure guidelines on patient records handled via our UK EHR system and billing spreadsheets.

### C. Notification Deadlines & Data Restrictions
* **Notification Window:** In the event of a confirmed data breach involving exposed system API keys or a leak of unencrypted patient data, a maximum **72-hour notification window** applies under UK GDPR to report the infraction to supervisory authorities (such as the ICO) and affected patients.
* **Restricted Data Profiles:** Under no circumstances are agents permitted to log, parse, or store unencrypted national identification numbers (e.g., SSN or National Insurance numbers), raw authorization tokens, or financial payment info within vector memory or plaintext log streams.

---

## 4. Systems Definition & Core Assets
The HealthCore Digital framework evaluates five core AI assets built to unify our disconnected technology estate:
1. **Classification Agent:** Parses inbound user messages, emails, or scheduling requests to determine intent and route payloads to specific clinics or staff.
2. **Response Agent:** Drafts context-aware clinical documentation assistance, billing updates, or patient booking reminders.
3. **Escalation Workflow Engine:** Coordinates multi-step operations such as patient promotions, scheduling modifications, and notifying clinic front desks.
4. **Semantic Memory Module:** Embeds and retrieves localized compliance playbooks, historical multi-location data trends, and conversation histories.
5. **Model Context Protocol (MCP) Tool Gateway:** Connects our LLMs directly to our patchwork tech stack, including the US EHR platform, the UK EHR system, the US billing system, and scheduling diaries.

---

## 5. Security & Operational Boundaries

### Definition of Sensitive Data
Within HealthCore Digital, **Sensitive Data** is strictly defined as:
* Protected Health Information (PHI) and Personally Identifiable Information (PII) including patient medical histories, clinical notes, names, addresses, and appointment details.
* System secrets including LLM provider API tokens, internal EHR database access credentials, and MCP tool authorization keys.
* Downstream execution formats such as generated code snippets, SQL strings targeting patient tables, or automated API call payloads.

### Definition of Irreversible Actions
An action is classified as **Irreversible** if its execution changes a persistent database record or pushes data outside of HealthCore's internal network control loop. This explicitly covers:
* **Deleting Data:** Removing patient histories, clinical documentation records, vector index embeddings, or billing line items.
* **Sending Communications:** Pushing live emails, SMS reminders, or app notifications to real patients in the US or UK.
* **Approving Processes:** Finalizing automated insurance claims submissions, updating medical licensing records, or executing data export requests under GDPR/HIPAA.

### Incident Response Service Level Agreements (SLAs)
When an anomaly or security gap is detected by our monitoring loops, HealthCore enforces the following mitigation windows:
* **Critical (e.g., Active Prompt Injection leaking PHI, or exposed EHR API keys):** Immediate automated containment within **1 hour**, with complete engineering resolution within **4 hours**.
* **High (e.g., Systematic rate limiting bypass on clinical documentation endpoints or unauthorized read attempts to the semantic memory base):** Containment within **4 hours**, with complete engineering resolution within **12 hours**.
* **Medium/Low (e.g., Incomplete audit trail logs on non-clinical data tools or missing component tags):** Mitigation scheduled within the current sprint cycle (**72 hours**).
