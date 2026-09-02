# Product Context: Telemetry Ingestion Service (HealthCore Digital)

## 1. Overview
This document outlines the business context, architectural milestones, and strict data governance policies for the unified telemetry and validation platform serving HealthCore Digital's cross-border healthcare network.

## 2. Problem & Value Proposition
HealthCore operates a network of 12 clinics across the US and UK. Its technology landscape is currently an unintegrated patchwork: two conflicting Electronic Health Record (EHR) systems, separated US and UK billing modules, split scheduling workflows, and an absolute lack of unified monitoring or data layers. System failures are currently detected only when a clinic manually calls the 6-person technology team. 

To build a modern, data-driven provider network, HealthCore Digital is establishing an end-to-end telemetry pipeline:
- **Phase 1 (Backend Stub Implementation):** Validates incoming routing envelopes safely. This lets us verify payload formats and stream architectures before deploying localized persistent data layers.
- **Phase 2 (Frontend Client Service):** Implements a resilient client tracking engine within the backoffice to capture application behaviors while protecting clinic workflows from performance drops or network issues.
- **Phase 3 (Broad Instrumentation & Performance Vitals):** Tracks system health markers (such as error spikes or booking tool latencies) alongside critical business events. This provides real-time operations dashboards for leadership.

## 3. Project Scope
- **Phase 1:** Configure a dedicated backend ingestion endpoint using FastAPI and environment-driven variables.
- **Phase 2:** Implement the centralized `TelemetryService` inside `uis/backoffice/` to process background queues with Zero UI-blocking overhead.
- **Phase 3 (Current):** Expand metrics tracking to baseline clinic app behaviors and primary user workflows across all 12 operational sites.

## 4. Constraints & System Patterns
- **Vocabulary Grounding:** All metrics, `event_type` signatures, and payload property keys must strictly reflect HealthCore's actual healthcare domain terms (e.g., matching structures for clinics, appointments, claims, and certifications) as derived from `CONTEXT-company.md`. Generic templates are non-compliant.
- **Profile vs. Usage Separation:** Patient profiles, medical histories, and administrative state data must remain strictly isolated inside secure primary healthcare databases. Telemetry only tracks append-only usage and technical health events.
- **Data Privacy & Compliance (Strict No-PII):** HealthCore operates under both HIPAA (US) and UK GDPR (UK). Telemetry streams must never process Personally Identifiable Information (PII) or Protected Health Information (PHI). User names, patient identities, cleartext emails, passwords, or raw medical text are strictly banned from entering telemetry event payloads.
