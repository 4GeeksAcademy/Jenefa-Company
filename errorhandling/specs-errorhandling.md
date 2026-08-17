# Technical Specification: Platform-Wide Error Handling Audit & Architecture

## 1. Pre-Implementation Agent Audit Protocol
Before making any changes manually, engineers **must** use their coding agent of choice (Cursor, Copilot, Claude Code, etc.) to scan the codebase and surface critical gaps. 

Copy, adapt, and run the reference prompt template below by filling in the bracketed codebase details.

### Mandatory Agent Prompt Template
```text
You are a senior software engineer auditing a codebase for error handling quality.

Analyse the entire repository located at [insert path/describe structure, e.g. "a Next.js frontend in /apps/web, a FastAPI backend in /apps/api, and Python scripts in /scripts"].

For each file or module you review, identify and report:

1. MISSING TRY/CATCH — async operations (fetch, await, file I/O, JSON parsing) that have no error handling at all.
2. OVERLY BROAD CATCH — try/catch or try/except blocks that wrap entire functions or large sections of code instead of the specific dangerous operation.
3. SILENT FAILURES — caught errors that are swallowed (empty catch blocks, bare `except: pass`).
4. RAW ERROR EXPOSURE — places where a raw exception message, stack trace, or status code could reach the user interface or API response.
5. SENSITIVE DATA LEAKS — error outputs or logs that may include secrets, database connection strings, internal paths, or personal data.
6. MISSING LOADING/ERROR UI STATES — frontend components that fetch data but render nothing (or crash) when the request is loading or fails.
7. NO USER CALL TO ACTION — error states that display a message but offer no way forward (no retry, no navigation, no support contact).
8. MISSING sys.exit ON SCRIPT FAILURE — Python scripts that encounter a critical error but exit with code 0 or no explicit exit code.

For each finding, report:
- File path and line number (or range)
- Category (from the list above)
- A one-line description of the problem
- Suggested fix (brief — implementation is the developer's responsibility)

Do not make any changes. Output only the audit report.
Prioritise findings by severity: CRITICAL > HIGH > MEDIUM > LOW.
Run the audit, read the report carefully, and use the checklist below to track your fixes.
```

---

## 2. Layer Implementation Specifications

### Layer A: Frontend (Next.js / TypeScript)
- **Scoped Network Protections:** Every network transmission or upstream API trigger must run wrapped within a distinct, micro-scoped `try/catch` block.
- **The Three-State UI Architecture:** Every asynchronous call must manage state hooks explicitly confirming:
  - **Loading:** Visual indicators like spinners or content skeletons.
  - **Fulfilled:** Data renders cleanly to the view tree.
  - **Rejected:** The interface safely intercepts the error and displays a readable alert.
- **Human-Readable Interface String Replacement:** Raw technical messages (e.g., `Error 500`, `Unexpected token <`, `NetworkError`) are strictly prohibited in user-facing components. Replace them with clear explanations (e.g., *"We're experiencing temporary connection issues. Your data hasn't been lost."*).
- **Mandatory User Call-to-Actions (CTA):** Every user-facing failure block must display at least one functional exit mechanism:
  - An interactive **Retry Button** to re-fire the failed API method.
  - A navigation link returning the user securely to the home page (`/`).
  - Highly visible fallback instructions for contacting support.
- **Structural Code Safety:**
  - **Optional Chaining (`?.`):** Must be used when checking deep, nested, or unstable client/server structures whose parent nodes could be `undefined` or `null`.
  - **Safe Defaults/Fallbacks:** Render explicit, safe default values (`|| ""` or `?? DEFAULT_ARRAY`) when parsing unstable API values into UI components to prevent rendering crashes.
  - **Deterministic Cleanup (`finally`):** You must use a `finally` block at the end of async requests to ensure loading variables are safely reset, no matter if the request succeeded or failed.

---

### Layer B: Backend (Python / FastAPI)
- **Granular Error Capture:** Individual route handlers must avoid wrapping whole code blocks in single, generic `try/except Exception` targets. Isolate distinct system events (e.g., database lookups vs. external microservice connections) into independent, specific exception blocks.
- **Standardized API Response Contracts:** All operational exceptions must return structured JSON objects accompanied by correct HTTP Status Codes (`400 Bad Request`, `404 Not Found`, `422 Unprocessable Entity`, `500 Internal Server Error`). Under no circumstances should unparsed Python traces or raw system logs exit the application routing boundary.
- **Sensitive Infrastructure Sanitization:** Database connection URLs, absolute host paths, environment definitions, and private authorization strings must never be included in consumer-facing response models.
- **Third-Party Integrations Protection:** All external dependencies—including third-party payment endpoints, telemetry systems, or LLM API calls—must be wrapped in defensive exceptions to ensure external downtimes do not bring down your core API process.

---

### Layer C: Automation Scripts (Python)
- **Defensive Input Validation Checkpoints:** Before scripts begin execution or data loop cycles, add strict validation guardrails to intercept missing, truncated, or malformed input data structures early.
- **File System & Parser Isolations:** Wrap all file I/O operations, local volume operations, and automated CSV/JSON serialization workflows within robust `try/except` constructs.
- **Standard Error Telemetry Output:** All runtime script errors must be logged directly to `sys.stderr` with clear, informative contextual strings, rather than polluting standard operational outputs (`stdout`).
- **Explicit Non-Zero Exit Code Execution:** Scripts that experience structural failures or fatal exceptions must interrupt processing and execute an explicit non-zero exit code (`sys.exit(1)`). This guarantees that connected deployment triggers, orchestration layers, and automated GitHub Action runners recognize the workflow run as failed.

---

### Layer D: General Global Standard (Telemetry & Logging)
- **Sanitization of Logs:** Review the entire repository explicitly for any stray `console.error` (Frontend) or `print` (Backend/Scripts) statements. 
- **Remediation Action:** Completely remove or replace logs that accidentally output connection credentials, environment properties, absolute user machine file trees, token variables, or customer PII data.

---

## 3. Evaluation Rubric & Quality Gate
The Tech Lead will evaluate the pull request strictly against compliance with the patterns listed below. Consistency and pattern correctness—**not features**—determine evaluation success:

| Metric | Target Standard | Evaluation Criteria |
| :--- | :--- | :--- |
| **Async Operations** | Three-state UI architecture | Verified presence of discrete loading, fulfilled, and rejected UI hooks for every async call. |
| **UX Cleanliness** | Human-readable messages + CTA | Zero occurrences of raw tech strings (`Error 500`, JSON errors); presence of clear retries/links. |
| **Try/Catch Scope** | Micro-scoped statements | Zero monolithic blocks wrapping entire controller loops; scoped narrowly around unsafe actions. |
| **State Reset** | Native `finally` blocks | Mandatory application of `finally` to cleanly release loading states across success and failures. |
| **Component Safety** | Null/Undefined protection | Exhaustive deployment of optional chaining (`?.`) and safe default primitives across rendering templates. |
| **Backend Responses** | Clean structured JSON | Strict maps of exceptions to clean JSON payloads paired with valid HTTP status codes (`400`, `404`, `422`, `500`). |
| **Data Protection** | Sanitized client interfaces | Absolutely zero metadata, server directory leaks, database schema text, or secrets exposed to clients. |
| **Automation Scripts** | File/IO and Exit Code integrity | Presence of entry-level malformed input pre-checks, logging targets to `stderr`, and `sys.exit(1)` exits. |
