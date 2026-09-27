# Product Context: Enhancing Agent Capability with Live Operational Data

## 1. Operational Overview
At **HealthCore**, we operate an international outpatient healthcare network spanning **12 clinics** (9 in the US across Texas, Florida, and Georgia; 3 in the UK across London and Manchester). Under the leadership of **Dr. Sandra Okonkwo**, our internal unit—**HealthCore Digital**—is tasked with building the intelligent systems and tools necessary to transform our historically fragmented patchwork of legacy platforms into an integrated, efficient ecosystem.

Our customer support agent currently has a functional gap: it can explain documentation perfectly via its RAG framework, but it remains blind to real-time events. When operational queries arise (e.g., *"What's the status of ticket 482?"*), the agent hallucinates data because it does not have a real-time bridge to active system events. This update shifts the agent from a static documentation reader into an integrated support assistant with live system visibility.

---

## 2. Product Objectives & Boundaries

### 2.1 Core User Experiences
- **Live System Transparency:** Direct integration allows clinical staff, operators, and administrative team members to query current ticket workflows instantly without switching browser tabs.
- **Stock & Inventory Lookup (Stretch Goal):** Enables conversational lookup of warehouse product counts directly through natural conversation text, breaking down data silos across markets.

### 2.2 Intent Routing Philosophy
Frontline workers shouldn't need to manually configure the agent or select a data source. The software must automatically infer whether the answer lives in the documentation library, require querying a live database tracker, or calls for a combined response.

### 2.3 Strict Separation of Responsibilities
To preserve systemic reliability, we explicitly treat general information retrieval and transactional status retrieval as completely separate behaviors:
- **Single-Scope Tools:** If a query needs ticket status, it runs the ticket tool. If it needs inventory information, it runs the inventory tool. We do not blend these scopes together.
- **Live Over Static:** Real-time data changes dynamically. Indexing tickets or stock items directly into the RAG vector store is disallowed because the values go stale the moment a technician changes a ticket status or an item is shipped.

---

## 3. Reliability & Failure Standards
Operating in healthcare adds an immense layer of responsibility. Patient care and system synchronization are governed by rigid legal structures (**HIPAA** in the US and **UK GDPR** in the UK) overseen by Claire Whitfield's compliance team. System crashes are not merely inconvenient—they cause real operational drag for our 200 cross-border employees trying to coordinate patient care.

[User Request] ---> [LangGraph Routing Edge]
|
+--------------+--------------+
|                             |
[Service Healthy]             [Service Outage]
|                             |
[Execute Live Tool]           [Hard 3-5s Timeout]
|                             |
[Return Real-time State]                 v
[Resilient Fallback Node]
|
["I couldn't confirm that
ticket status right now"]

### UX Failure Handling Requirements
- **Guardrails Over Silence:** If an internal tracking endpoint times out or drops a packet, the chat engine must never hang indefinitely or freeze up. 
- **Transparent Boundaries:** The workflow engine handles errors gracefully by admitting a system limitation (e.g., *"I couldn't confirm that ticket's status right now"*). The bot must never guess, assume, or hallucinate an unverified state to the support desk.