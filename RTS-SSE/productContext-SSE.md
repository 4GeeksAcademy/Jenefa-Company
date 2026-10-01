# Product Context: Real-Time RFP Dashboard Push

## 1. The Business Problem & Urgency
**HealthCore** is an outpatient healthcare services provider managing a network of **12 clinics** across the United States and the United Kingdom. While the company has earned deep trust from its patients, its underlying infrastructure is a highly fragmented patchwork of legacy software—spanning two separate EHR systems, split billing tracks, and un-integrated scheduling pipelines. 

To modernize operations and reclaim severe leakage (such as a 22% network no-show rate costing $1.8 million annually and a 14% US claims denial rate), CEO **Dr. Sandra Okonkwo** established **HealthCore Digital**. This engineering squad is tasked with building unified, real-time tracking and intelligence layers.

Last week, HealthCore Digital successfully shipped a multi-agent RFP generation framework to systematically capture and process high-value commercial and network contracts. However, an operational breakdown was surfaced via a formal Request for Information (RFI) filed by the sales and operations desk: **nobody knows a new RFP ticket has arrived until an employee manually updates their browser out of curiosity.**

In a high-stakes clinical network generating **$28 million in annual revenue**, these response bottlenecks delay commercial partnerships, stall regional pipeline capacity, and leave money on the table.

---

## 2. Core Solution Vision
We are migrating our foundational operating layout from a pulling workflow to an intentional, **push-driven real-time operations engine** embedded into the HealthCore Central API. 

[System Registers Ticket] ──> [Authenticated Backend Stream]
│
▼ (Instant Delivery via SSE)
[HealthCore Digital Cockpit] <── [fetch + ReadableStream Consumer]
(Immediate Visual Feedback)

The system upgrade must provide:
1. **Instant Operational Visibility:** The workspace dashboard must reflect live RFP tickets automatically the moment they are logged. No human clicks, page reloads, or polling actions are required.
2. **Resilient Data Transport:** If an employee loses connection or moves between clinic Wi-Fi zones, the system must handle the drop gracefully, leverage intelligent backoff intervals to pick up dropped items, and update the workspace securely without visual degradation.

---

## 3. Product Quality Guardrails & Context Constraints

* **Strict Context Synchronization:** The entity models, field definitions, and domain properties utilized in this notification pipeline must mirror the exact conventions outlined in our central business guidelines (`CONTEXT.md`). Generic implementations that decouple from these established schemas will fail validation.
* **Dual-Jurisdiction Data Security:** Because HealthCore handles Protected Health Information (PHI) across international borders, this real-time transport layer must respect strict isolation guardrails. The streaming endpoint must mandate rigorous token verification to satisfy both **US HIPAA and UK GDPR** privacy baselines.
* **Operational Distinctiveness:** Incoming RFP alerts must possess strong visual distinction to capture immediate attention from the operations desk. They cannot blend in as common metric lines or standard event logs.
* **Performance Control:** The frontend must process and update individual incoming items natively. Forcing full-page layout rehydration or triggering heavy batch queries of unchanged dashboard tables is prohibited.
* **Isolated Infrastructure Phase:** This update focuses strictly on transport, visibility, and security pipelines under CTO James Osei's architecture. No machine learning models, clinical notes processing, or agent inference logic should be invoked within this layer.