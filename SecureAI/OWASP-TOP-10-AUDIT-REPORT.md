# HealthCore OWASP Top 10 Audit Report

**Assessment scope:** patient-facing frontend, central API, and LangGraph
agentic system in this repository.  
**Assessment status:** application controls reviewed; production host evidence
remains a deployment-owner responsibility.

## Executive summary

The repository has controls covering authentication, input validation, prompt
injection, untrusted retrieval isolation, outbound URL validation, telemetry,
and non-root container execution. Two critical application findings have
reproducible remediation evidence:

1. Agent-controlled outbound requests are restricted to safe HTTP(S) targets.
2. Direct and indirect prompt injection is rejected or isolated before agent
   execution and output delivery.

SSH configuration, host firewall state, production TLS, cloud encryption,
SBOM results, and regional data residency cannot be proven from source alone.
Deployment evidence must be attached before production sign-off.

## OWASP Top 10 findings matrix

| Category | Frontend | Backend | Agentic system | Finding and evidence |
| --- | --- | --- | --- | --- |
| **A01 Broken Access Control** | Applies | Applies | Applies | Frontend auth state and API access helpers are implemented in [`uis/web/src/lib/authApi.ts`](../uis/web/src/lib/authApi.ts) and [`uis/web/src/lib/authStorage.ts`](../uis/web/src/lib/authStorage.ts). API bearer validation and role/ownership checks are under [`services/api/app/auth`](../services/api/app/auth). Agent routes and WebSocket connections use the same JWT boundary. Cross-market authorization requires deployment integration tests. |
| **A02 Cryptographic Failures** | Applies | Applies | Applies | JWT signing uses configured secrets in [`services/api/app/auth/security.py`](../services/api/app/auth/security.py). Service credentials are environment-provided in [`services/langgraph_agent/tools.py`](../services/langgraph_agent/tools.py). TLS 1.3, AES-256 at rest, and secret-manager configuration require host/cloud evidence. |
| **A03 Injection** | Applies | Applies | Applies | Typed auth, inventory, telemetry, and RFP schemas validate inputs. Prompt-injection blocking, untrusted retrieval isolation, and output leakage validation are implemented in [`services/langgraph_agent/guardrails.py`](../services/langgraph_agent/guardrails.py), with regression coverage in [`tests/pipelines/test_guardrails.py`](../tests/pipelines/test_guardrails.py). |
| **A04 Insecure Design** | Applies | Applies | Applies | Protected-client `401` handling clears auth state, and JWT expiry is enforced server-side. Password reset/change workflows and cross-border authorization require continued integration review. |
| **A05 Security Misconfiguration** | Applies | Applies | Applies | The backend image creates and selects `hc-runtime` in [`services/Dockerfile`](../services/Dockerfile). Deployment hardening artifacts for SSH, UFW, runtime identity, and permissions are in [`SecureAI/host-hardening`](host-hardening). Production debug/reload and administrative-console settings require deployment verification. |
| **A06 Vulnerable and Outdated Components** | Applies | Applies | Applies | Dependency manifests are present. A CI-generated SBOM and a scan showing zero unresolved high/critical CVEs are still required before sign-off. |
| **A07 Identification and Authentication Failures** | Applies | Applies | Applies | JWT expiry, bcrypt password hashing, inactive-user rejection, and distinct `401`/`403` responses are implemented under [`services/api/app/auth`](../services/api/app/auth). Brute-force throttling remains a production control gap. |
| **A08 Software and Data Integrity Failures** | Applies | Applies | Applies | Pydantic/SQLModel validation protects service payloads; Celery uses bounded retries and a dead-letter record. Signed release/commit enforcement remains a repository/CI control. |
| **A09 Security Logging and Monitoring Failures** | Applies | Applies | Applies | Telemetry persistence/reporting is implemented under [`services/api/app/telemetry`](../services/api/app/telemetry), and guardrail triggers are logged and counted. Central immutable export and alert routing require environment verification. |
| **A10 Server-Side Request Forgery** | Does not apply | Applies | Applies | The frontend has no server-side URL fetcher. Agent service URLs are validated before clients are created by [`_validate_outbound_url`](../services/langgraph_agent/tools.py), covering non-HTTP(S), credentials, query/fragment injection, loopback, private, link-local, and reserved targets. |

## Critical remediation evidence

### Critical fix 1: SSRF protection

**Risk before remediation:** agent integrations accepted attacker-influenced
service URLs, allowing loopback/private-network access or protocol abuse.

**Control after remediation:** `_validate_outbound_url` is applied to MCP,
incident, and inventory base URLs before any outbound client is created.

Evidence:

- Implementation: [`services/langgraph_agent/tools.py`](../services/langgraph_agent/tools.py)
- Regression tests: [`tests/test_langgraph_external.py`](../tests/test_langgraph_external.py)
- Reproduce:

  ```bash
  python -m pytest tests/test_langgraph_external.py -q
  ```

Expected coverage includes rejection of loopback/private addresses and
non-HTTP targets.

### Critical fix 2: prompt-injection boundary

**Risk before remediation:** untrusted user or retrieved text could reach the
agent execution path without a deterministic instruction boundary.

**Control after remediation:** prompt-injection patterns are rejected,
retrieved content is explicitly isolated as untrusted data, and generated
output is checked for instruction or sensitive-data leakage.

Evidence:

- Implementation: [`services/langgraph_agent/guardrails.py`](../services/langgraph_agent/guardrails.py)
- Graph boundary: [`services/langgraph_agent/graph.py`](../services/langgraph_agent/graph.py)
- Regression tests: [`tests/pipelines/test_guardrails.py`](../tests/pipelines/test_guardrails.py)
- Reproduce:

  ```bash
  python -m pytest tests/pipelines/test_guardrails.py -q
  ```

Expected coverage includes direct jailbreak variants, personal-task refusal,
malicious retrieval isolation, and guardrail trigger metrics.

## Host-hardening evidence

The repository includes guarded deployment and verification scripts, but they
must be executed on each production host:

- Apply reviewed controls with [`apply-host-hardening.sh`](host-hardening/apply-host-hardening.sh).
- Verify SSH, firewall, runtime UID, code permissions, log permissions, and
  environment-file permissions with
  [`verify-host-hardening.sh`](host-hardening/verify-host-hardening.sh).
- Retain the command output as `host-hardening-evidence.txt` in the deployment
  release record.

## Sign-off status

**Application audit:** complete for the repository scope.  
**Production sign-off:** pending host SSH/firewall evidence, runtime
permissions, TLS/encryption configuration, SBOM results, signed-release
verification, and regional data-residency evidence.
