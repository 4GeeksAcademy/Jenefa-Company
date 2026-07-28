# Healthcore 

### 1. Session Initialization & Memory Bank Reads

At the absolute start of every single user session, before executing any commands or writing any code, you must read the following memory bank files to establish context:

- `memory-bank/projectbrief.md` - To understand HealthCore's business goals, HealthCore Digital scope, and the operational problems this monorepo solves.
- `memory-bank/techContext.md` - To review the target tech stack, architectural decisions (unified API, FHIR, telemetry, RAG compliance), and HIPAA / UK GDPR guardrails.
- `memory-bank/progress.md` - To sync on current development status across clinics and the immediate next steps for each workstream.



### 2. Mandatory Pre-Commit Workflow

You must strictly execute this exact 4-step ordered workflow before making or staging any git commit. Do not skip any steps:

1. Run local validation scripts, compilers, or test suites to ensure zero syntax or runtime errors.
2. Generate an automated visual diff or run a structural linting check to verify formatting consistency.
3. Conduct a targeted code-review pass to verify that security, HIPAA / UK GDPR compliance, and architectural guardrails are fully met.
4. Document all changed components and update `memory-bank/progress.md` to reflect the new state.



### 3. Protected Directories & Modification Constraints

You are strictly prohibited from modifying, deleting, or overwriting the following directories and files without receiving explicit, written developer confirmation in the chat:

- `/infra/` - Core cloud deployment and infrastructure-as-code scripts (Docker, Terraform, deployment manifests).
- `/data/raw/` - Raw source datasets and dumps that may contain PHI/PII under HIPAA and UK GDPR.
- `.env.production` - Active production environment configuration variables and secrets.
- `/internal/` - Internal CLIs, packaged migration scripts, and utilities that can alter shared or production systems.

Instructions for Execution:

- Maintain clean markdown syntax.
- Do not alter any pre-existing, unrelated rules in `agents.md`.
- Confirm once the file has been successfully updated and saved.

