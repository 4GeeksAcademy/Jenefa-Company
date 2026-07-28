

### 1. Session Initialization & Memory Bank Reads
At the absolute start of every single user session, before executing any commands or writing any code, you must read the following memory bank files to establish context:
* `memory_bank/project_brief.md` - To understand core business goals, tech stack, and scope.
* `memory_bank/product_context.md` - To review the current state, user personas, and systemic problems solved.
* `memory_bank/system_architecture.md` - To review architectural decisions, data flows, and infrastructure constraints.
* `memory_bank/progress_tracking.md` - To sync on current development status and immediate next steps.

### 2. Mandatory Pre-Commit Workflow
You must strictly execute this exact 4-step ordered workflow before making or staging any git commit. Do not skip any steps:
1. Run local validation scripts, compilers, or test suites to ensure zero syntax or runtime errors.
2. Generate an automated visual diff or run a structural linting check to verify formatting consistency.
3. Conduct a targeted code-review pass to verify that security, compliance, and architectural guardrails are fully met.
4. Document all changed components and update the internal progress tracking files to reflect the new state.

### 3. Protected Directories & Modification Constraints
You are strictly prohibited from modifying, deleting, or overwriting the following directories and files without receiving explicit, written developer confirmation in the chat:
* `/infrastructure/cloud/` - Core cloud deployment and infrastructure-as-code scripts.
* `/security/certificates/` - SSL, encryption keys, and cryptographic secrets.
* `.env.production` - Active production environment configuration variables.
* `/database/migrations/` - Database schema files and version history logs.

Instructions for Execution:
* Maintain clean markdown syntax.
* Do not alter any pre-existing, unrelated rules in `agents.md`.
* Confirm once the file has been successfully updated and saved.
