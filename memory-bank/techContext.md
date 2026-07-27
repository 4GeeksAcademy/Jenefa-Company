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