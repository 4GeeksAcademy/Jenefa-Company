# Product Context: AUTH-088 - Unit Test Coverage

## Background & Rationale
HealthCore operates 12 clinics across the US and UK under a patchwork of disconnected legacy platforms, including two separate Electronic Health Record (EHR) platforms and localized billing environments. Last week, a minor refactor pushed by the Austin engineering team bypassed manual validation checks and broke token expiration rules. This caused clinical operators and staff to experience a severe two-hour lockout, disrupting patient coordination and operational workflows. 

To enforce systemic reliability, CTO James Osei has declared that untested code is not production code. This unit test initiative establishes an immediate safety gate to prevent regressions on core authentication business infrastructure.

## Compliance and Data Governance Constraints
HealthCore's authentication systems serve as the entry gateway for critical, highly regulated medical infrastructure. All code paths must remain airtight to satisfy internal data governance standards under Compliance Lead Claire Whitfield:
*   **US Operations:** Must satisfy strict HIPAA security rules regarding user access controls and session termination.
*   **UK Operations:** Must remain fully compliant with UK GDPR restrictions regarding secure data access and multi-region credentials.

## Core Mandates & Strategy

### 1. Document-First Test Planning & Evaluation Criteria
Engineers must complete the `TESTING.md` architecture blueprint *before* generating test modules. This document acts as our single source of truth for test design and must explicitly describe:
*   Exact steps to execute the test runners.
*   A clear taxonomy of what each individual test suite covers.
*   A matrix listing planned happy paths, edge cases, and failure modes for every endpoint, detailing why specific scenarios were prioritized.
*   **Evident AI Workflow / Bug Tracking:** The markdown file must explicitly call out at least one unique test case found via AI cooperation or detail a production bug exposed during test suite execution.
*   **Coverage Reporting:** A dedicated section capturing final verified coverage metrics.

### 2. Isolated Business Logic Coverage
This initiative targets core function behaviors and endpoint-specific rules. Do not expend effort testing built-in framework features like HTTP serialization, routing layers, or web plumbing. Focus entirely on deterministic logic checks. Assertions must reflect what the application logic *decides*, not simply how the network transport layer *responds*.

### 3. Human-in-the-Loop AI Engineering
While AI coding agents are highly encouraged to accelerate development, developers must maintain strict ownership of the code. 
*   Leverage AI to expand your test matrix and discover subtle, hidden failure modes.
*   Use AI to draft verbose test boilerplates quickly.
*   Never blindly commit AI-written tests; every line, mock, and assertion must be manually validated for correctness.

### 4. Code Standards & Professionalism
Junior developers write code that functions under ideal scenarios; professional engineers write clean, maintainable suites that safeguard the codebase. Tests must have intuitive names, follow a consistent blueprint, and feature targeted code comments explaining non-obvious business requirements or mathematical token checks.

### 5. Acceptance Quality Bar
A pull request cannot be merged unless it meets all quality metrics:
*   Zero failing tests under `uv run pytest` and `jest --coverage`.
*   Strict compliance with the minimum **70% test coverage** benchmark for the FastAPI auth module.
