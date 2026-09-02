# Health Core Project Brief

## Business Description
- HealthCore is an outpatient healthcare services company founded in 2011 in Austin, Texas. The company operates a cross-border network of 12 clinics, with 9 located in the United States (Texas, Florida, Georgia) and 3 in the United Kingdom (London, Manchester). Generating approximately $28 million in annual revenue and employing 200 people, HealthCore provides primary care, specialist consultations, chronic disease management, and preventive health programmes. The brand differentiates itself through accessible, high-quality care featuring same-day bookings, extended operational hours, and bilingual staff.

## Project Description
- HealthCore Digital is a newly formed internal technology unit tasked with modernizing the company's fragmented infrastructure. The project focuses on building a unified, secure, and intelligent ecosystem that spans both the US and UK markets. Key technical initiatives include developing a centralized data API layer, automating cross-border compliance workflows (HIPAA and UK GDPR), and deploying high-stakes AI applications. These AI applications specifically target predictive scheduling, clinical documentation assistance, automated billing code suggestions, and executive operational dashboards.

## Problems It Solves
- The project directly addresses critical operational, financial, and technical inefficiencies across the organization:

### Siloed Patient Data: 
- Connects independent, non-communicating Electronic Health Record (EHR) platforms so patient histories can follow them across locations.

### High Appointment No-Shows:
- Tackles a costly 22% network-wide no-show rate (costing $1.8M annually) through online booking and predictive AI reminder models.

### Administrative Burnout:
- Reduces the 35 minutes per day clinical staff spend on manual documentation using AI-assisted charting tools.

### Revenue Leakage: 
- Combats a severe 14% US insurance claims denial rate (double the industry average) using automated coding suggestions and pre-submission AI reviews.

### Regulatory & Administrative Overhead: 
- Replaces slow, manual spreadsheets used for compliance auditing, staff credentialing, and tracking mandatory continuing education.

### Executive Decision-Making: 
- Eliminates lagging, unstandardized weekly reporting by delivering a real-time executive dashboard for the CEO.
---

# Technical Context - HEALTH CORE

## Target Tech Stack
- Since the internal technology unit is building these systems from scratch to replace manual tracking and disconnected legacy software, the target engineering stack must prioritize cross-border scalability, secure data ingestion, and heavy AI integration.
### API & Core Backend: 
- RESTful/GraphQL microservices architecture built with modern backend frameworks capable of handling high concurrency and secure API exposure (e.g., Python FastAPI or Node.js/TypeScript).
### Healthcare Integration Interoperability 
- HL7 FHIR (Fast Healthcare Interoperability Resources) data standard protocol. This is mandatory to cleanly map, structure, and translate data fetched from the two distinct, siloed EHR systems.
### AI & Machine Learning Layer 
- Python ecosystem using standard enterprise ML libraries (e.g., PyTorch, scikit-learn). Large Language Models (LLMs) used via secure enterprise APIs or open-source weights to manage Natural Language Processing (NLP) tasks.
### Data Pipeline & Warehousing
- Event-driven architecture (e.g., Apache Kafka) for streaming telemetry data from all 12 clinics into a secure, centralized cloud Data Warehouse (e.g., Snowflake).
### Frontend & Dashboards
- Single-page applications (React or Vue.js) to compile role-based metrics for the executive, clinical, compliance, and billing portals.

## Architectural Decisions
- MadeTo safely bridge operations across the US and UK while keeping independent workflows intact, the technology team must enforce specific high-level design principles.
### Federated Hub-and-Spoke API Architecture 
- Instead of forcing an immediate, highly disruptive migration to a single brand-new Electronic Health Record (EHR) system across two continents, the team is building a centralized HealthCore Unified API. This API acts as an abstraction hub, pulling data in real time from the separate local EHR platforms on demand.
### Retrieval-Augmented Generation (RAG) for Jurisdictional Compliance: 
-To scale Claire Whitfield's data governance needs, compliance documentation, HIPAA regulations, and UK GDPR statutes will be indexed into a semantic search Vector Database. This allows localized automated workflows to parse regulations contextually without cross-pollinating legally sensitive regional data.
### Predictive Edge Telemetry & Monitoring
- Moving away from a reactive "wait for a clinic to call when things break" support model, the team is opting for distributed server and application telemetry agent scripts deployed locally across all 12 physical networks to stream logs up to an automated cloud alerting system.
### Async Human-in-the-Loop Revenue Protection
- The automated coding suggestions and AI billing claim engines will run asynchronously. They will intercept manual submissions to evaluate denial risks prior to external transmission, routing high-risk outliers directly to Tom Callahan's billing team for confirmation.

## Technical Constraints & Guardrails
-Developing inside a heavily audited health sector creates rigid boundaries that standard software projects do not have to manage.
### Geographic Sovereignty & Data Residency Constraints
- HIPAA (US) and UK GDPR laws dictate strict boundaries on how patient data can cross physical borders. The cloud database architecture must implement localized geographic partitioning. Patient records must remain stored inside their respective legal jurisdictions (e.g., AWS US regions vs. AWS UK regions), using the abstraction layer strictly to securely pipe temporary data views when a patient explicitly crosses the cross-border boundaries.
### EHR Integration Limitations (No Shared Native Layer)
- The underlying, pre-existing EHR architectures are static legacy platforms that cannot natively speak to one another. The team cannot modify the core data schemas of those vendor systems directly, limiting development to whatever webhooks or data extracts those systems legally and technically expose.
### AI Model Verifiability & Bias Risk
- Because errors inside medical documentation or automated health processes yield heavy legal liabilities, any utilized AI model cannot operate as an unvetted "black box". All algorithmic outputs must feature rigorous access audit logs, complete user-verification stamps, and explicit documentation traceability.
### Severe Talent & Resource Constraints 
- The entire digital transformation effort is backed by a tight, 6-person technology team stationed out of Austin. This core team must maintain everyday legacy uptime across 12 distributed properties while concurrently attempting to deploy this massive, multi-tiered data framework
---

# Progress - HealthCore

## Current State of Development
- The organization is currently operating in a highly manual, reactive, and fragmented state. The infrastructure has failed to keep pace with business growth, resulting in zero unified automation across the 12 locations.
### Infrastructure Status
- There is completely no shared data layer, no telemetry, and no centralized logging across the company. System failures are caught only when physical clinics call the Austin tech office to complain.
### Data & Software Estate
- Operations run on a fragmented patchwork of legacy software. This includes two non-communicating EHR platforms, a standalone US billing platform, a manual phone scheduling setup in the US, and manual diaries alongside spreadsheets for UK billing and booking.
### Operational Baseline
- Staff are heavily bogged down by administrative debt. Clinicians waste 35 minutes daily on manual documentation. Human resource tracking (CME medical licenses) and compliance logs are managed entirely on loose spreadsheets.
### Executive Reporting
- Reporting is static and lagging. The CEO receives unstandardized weekly reports from department heads that are based on data multiple days old. Critical real-time network metrics (like weekly no-show or denial rates) are completely inaccessible without manual phone polling.

### Milestone 4 completed (monorepo AI setup)
- Added `memory-bank/` (`projectbrief.md`, `techContext.md`, `progress.md`), root `AGENTS.md`, `.agents/rules/phi-data-residency.md`, and `.agents/skills/sync-memory-bank/`.
- Created `uis/web` with its own shell layout; `/` imports `healthcore-testing` and renders denial, no-show, and CME outputs on screen.
- Migrated Milestone 1 corporate site into `uis/website` as typed reusable React components (`/`, `/apply`) with the original teal/sky visual identity.

### Incident report processor completed (Phase 1 + Phase 2)
- Built shared validator in `scripts/incident_core/` and CLI `scripts/analyze.py` against HealthCore incident CSV rules (no `patient_id` in any output).
- Added sample dataset `scripts/incidents-healthcore.csv` (100 rows; 94 valid / 6 invalid) matching `scripts/context-fileIncident.md` targets.
- Added FastAPI service `services/api` with `POST /api/incidents/analyze` and `GET /api/incidents/results/export`.
- Mounted Incident Analysis upload/dashboard/export UI at `uis/web` `/incidents` (sidebar nav link).

### AUTH-088 completed (authentication unit test coverage)
- Document-first plan and results in root `TESTING.md` (matrix, run commands, AI/regression notes, coverage).
- FastAPI suite under `services/api/tests/` (`test_register.py`, `test_login.py`, `test_token.py`, plus `test_service_rules.py`); run via `cd services/api && uv run pytest` / `--cov=app.auth` — **84%** auth module coverage (gate ≥ 70%).
- Registration now enforces minimum 8-character passwords (aligned with reset/change-password); covered by `test_register_rejects_password_shorter_than_eight_chars`.
- Jest suite for clinic web auth utilities (`uis/web` `authStorage`, `userFacingError`, `api.readJson`) via `npx jest --coverage`.
- Auth API sources (`services/api/app/auth`, error handlers, web `lib` auth helpers) restored onto `auth-unittesting` so the suite exercises the implemented structure.

### Clinic supply inventory (SQLModel dual persistence)
- Extended `services/api` with a dual-store inventory layer: TinyDB remains the identity/`get_current_user` source; SQLModel persists `MedicalSupply`, `InboundEntry`, and `OutboundExit` on SQLite locally or Supabase Postgres via `INVENTORY_DATABASE_URL`.
- Stock is ledger-derived only (`inbound − outbound` by `clinic_id`). Outbound overdrafts return HTTP 400 before write. All `/inventory/*` routes require bearer auth and stamp `user_uuid` from the TinyDB session.
- Spec seed catalog (gloves `450`, sedative `35`) loads on empty databases. Covered by `services/api/tests/test_inventory.py` (8 cases). Staff UI at `uis/web` `/inventory` plus `/login`.
- Milestone 5 UI hardening completed in `uis/web`: all four backoffice inventory routes stay session-guarded; outbound dispersal resets and re-fetches stock immediately on item changes with stale-request protection; orders history now formats `created_at` by clinic timezone (UK -> `Europe/London`, TX -> `America/Chicago`, FL/GA -> `America/New_York`, fallback `UTC`) while preserving immutable audit columns and movement badges.

## Planned Next Steps
- Dr. Sandra Okonkwo has newly commissioned HealthCore Digital as an internal unit specifically to build out modern, intelligent systems from scratch. The target deployment roadmap spans across six primary operational fronts:

### Core Engineering & Integration (James Osei)
#### Central API Build
- Build the unified HealthCore central API to aggregate patient, appointment, financial, and staffing data directly from the siloed EHRs.
#### Telemetry Deployment
- Establish real-time telemetry protocols and automated software health checks across all 12 properties to instantly flag outages.
#### Data Pipeline
- Construct a reliable data pipeline to feed streaming data to departmental and executive analytics dashboards.

### Clinical Workflow Optimization (Dr. Marcus Reid)
#### AI Charting Assistants
- Deploy AI-assisted clinical documentation software to automate note-taking and reclaim the 35 lost minutes per day per clinician.
#### Cross-Border Portability
- Enable cross-location patient history visibility so records securely follow individuals traveling between the US and UK.

### Patient Experience & Revenue Protection (Priya Nair & Tom Callahan)
#### Patient Booking Engine 
- Launch a unified online booking platform across both the US and UK markets to replace manual phone diaries.
#### Predictive Scheduling
- Implement a machine learning no-show prediction model paired with automated SMS/email outreach to target at-risk appointments.
#### AI Claims Scrubbing
- Build an automated pre-submission coding assistant and claims review engine to catch systematic errors before they hit insurance providers, cutting down the 14% denial rate.

### Workforce & Compliance Automation (Diane Foster & Claire Whitfield)
#### Automated Credentialing
- Replace manual onboarding with automated clinical verification checklists and license tracking systems featuring expiration triggers.
#### Compliance Data Retrieval
- Code an automated patient data request compilation tool to streamline legally mandated GDPR/HIPAA record requests.
#### Internal Chatbot
- Launch a basic employee HR portal alongside an internal chatbot to handle holiday booking and legal policy queries.

### Executive Intelligence (Dr. Sandra Okonkwo)
#### Unified KPI Dashboard 
- Roll out a singular executive dashboard tracking cross-border revenue, booking trends, patient satisfaction, and claim denial hotspots.
#### Automated Briefings 
- Configure an automated reporting protocol to compile and deliver localized operational summaries every Monday at 7:00 AM sharp.
#### Natural-Language Assistant
- Build a secure semantic search index over technical docs and integrate a natural-language AI interface allowing the CEO to query operational data using text.(.venv) 