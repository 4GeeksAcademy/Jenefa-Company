# Product Context: Telemetry and Data Pipelines (Part 3)

## 1. Product Vision & Value Proposition
The goal of this initiative is to graduate HealthCore's telemetry-driven business performance pipeline from a working proof-of-concept into a reliable, enterprise-grade production workflow. 

While the previous iterations successfully proved that our software can read from raw telemetry inputs (`telemetry_events`) and compute complex internal key metrics without touching the legacy technical systems, it lacked the organizational design patterns required for continuous long-term operations. This milestone introduces a production-ready blueprint focusing on modular reliability, cross-border clinical workflow tracking, and absolute data transparency for HealthCore leadership.

## 2. Business Drivers & Stakeholder Alignment
* **Executive Leadership Focus:** Our CEO, **Dr. Sandra Okonkwo**, will never query raw API endpoints using command-line developer tools like `curl`. She manages a **$28M two-country clinical network** across **12 clinics** (9 in the US, 3 in the UK) and requires real-time operational answers without relying on manually compiled, asynchronous weekly updates.
* **The Dashboard Mandate:** Leadership requires an unambiguous, visually digestible view of real operational data. The emphasis is entirely on structural correctness, real numbers, and alignment with the cadences (weekly or monthly) defined in our strategic targets.
* **Zero Operational Disruption:** This entire pipeline refactor must happen transparently. The existing source tracking layer (`telemetry_events`) and core analytical infrastructure (`services/telemetry/analysis.py`) must remain completely unmodified.

## 3. User Personas & System Interactions
* **The Strategic Stakeholder (Dr. Sandra Okonkwo, CEO):** Needs to view data inside `uis/backoffice/` to instantly assess network trajectory. She expects every metric to mirror the specific terminology she uses in daily business tracking—such as exact no-show breakdowns or regional denial updates—without needing technical translation.
* **The Department Managers (Priya Nair & Tom Callahan):** Need direct operational visibility to proactively monitor and correct their respective domain failures (e.g., tracking the 22% network no-show rate or the 14% US claims denial rate).
* **The Technology Team (James Osei, CTO):** Responsible for maintaining the pipeline, expanding metrics, and triaging processing failures. They require isolated, highly structured execution patterns so they can fix breaking transformations before bad code or malformed event records reach the production analytical layers.

## 4. Architectural Domain Vocabularies
Generic system labels like `extract_data`, `transform_logic`, or `load_table` are strictly prohibited. The code architecture must directly speak the language of our business. All subflows, data tasks, processing files, and unit tests must explicitly derive their nomenclature from the specific domain entities and tracking categories established in the "KPIs to Measure" section of `CONTEXT-company.md`, mapping cleanly to:
* **Patient Experience and Access KPIs:** Tracking network-wide booking patterns, localized trends, and at-risk booking attributes.
* **Revenue Cycle and Billing KPIs:** Tracking regional claims submissions, coding behaviors, and financial collection rates.
* **Clinical Operations & Logistics:** Tracking documentation latency metrics and clinic-level appointment flows across US and UK jurisdictions.
