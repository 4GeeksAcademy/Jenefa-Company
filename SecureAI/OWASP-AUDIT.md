# HealthCore OWASP Top 10 Audit

**Scope:** patient-facing frontend, central API, and LangGraph agent.  
**Status:** repository review completed; host/deployment evidence remains required before production sign-off.

## Findings Matrix

| Category | Frontend | Backend | Agentic system | Evidence and disposition |
| --- | --- | --- | --- | --- |
| A01 Broken Access Control | Applies | Applies | Applies | Frontend route guards use `uis/web/lib/auth`; API bearer validation is in `services/api/app/auth/deps.py`; protected agent WebSocket and agent routes require the existing JWT boundary. Cross-market authorization remains a deployment/integration test requirement. |
| A02 Cryptographic Failures | Applies | Applies | Applies | JWT signing uses configured `SECRET_KEY` in `services/api/app/auth/security.py`; service credentials are environment-provided in `services/langgraph_agent/tools.py`. TLS 1.3 and AES-256 at-rest settings require cloud/host evidence and are not asserted by application code. |
| A03 Injection | Applies | Applies | Applies | Input validation is present in auth, inventory, telemetry, and RFP schemas. Agent prompt injection, untrusted retrieval isolation, and output leakage checks are enforced by `services/langgraph_agent/guardrails.py` and covered by `tests/pipelines/test_guardrails.py`. |
| A04 Insecure Design | Applies | Applies | Applies | Client auth state is cleared on protected `401`; JWT expiry is enforced server-side. Reset/change-password and cross-border workflow review require continued integration coverage. |
| A05 Security Misconfiguration | Applies | Applies | Applies | `services/Dockerfile` creates and selects the non-root `hc-runtime` user. Production debug/reload settings, SSH policy, firewall policy, and administrative console exposure require deployment verification. |
| A06 Vulnerable and Outdated Components | Applies | Applies | Applies | Dependency manifests exist, but a clean SBOM and zero-high/critical-CVE scan must be generated in CI before sign-off. |
| A07 Identification and Authentication Failures | Applies | Applies | Applies | JWT expiry, bcrypt password hashing, inactive-user rejection, and distinct `401`/`403` handling are implemented under `services/api/app/auth/` and covered by auth tests. Brute-force throttling remains a production control gap. |
| A08 Software and Data Integrity Failures | Applies | Applies | Applies | Pydantic/SQLModel validation protects service payloads; Celery tasks use bounded retries and an audit DLQ. Signed release/commit enforcement remains a repository and CI control. |
| A09 Logging and Monitoring Failures | Applies | Applies | Applies | Telemetry persistence/reporting is implemented under `services/api/app/telemetry/`; agent guardrail triggers are counted and logged. Central immutable log export and alert routing require environment verification. |
| A10 SSRF | Does Not Apply | Applies | Applies | Frontend has no server-side URL fetcher. `services/langgraph_agent/tools.py` now rejects non-HTTP(S), credential-bearing, query-bearing, loopback, private, link-local, and reserved service URLs before requests; regression coverage is in `tests/test_langgraph_external.py`. Network egress policy remains required in production. |

## Critical Remediation Evidence

The critical agent outbound-request finding was remediated by `_validate_outbound_url` in `services/langgraph_agent/tools.py`. It is applied to MCP, incident, and inventory base URLs before an HTTP client is created.

Reproduce the application-level verification from the repository root:

```bash
python -m pytest tests/test_langgraph_external.py -q
```

Expected result: all five tests pass, including rejection of loopback/private and non-HTTP targets.

## Deployment Sign-Off Gates

The following evidence cannot be established safely by application tests and must be attached by the deployment owner:

- `PermitRootLogin no` and public-key-only SSH configuration, with a rejected root-login attempt.
- Active default-deny firewall rules showing only approved HTTPS and SSH ports.
- Runtime UID/process evidence proving deployed services are not UID 0.
- File permission evidence showing code is read-only to the runtime user and logs are the only writable application target.
- TLS 1.3, AES-256 at-rest, secret-manager, and regional data-residency configuration evidence.
- SBOM output with no unresolved high/critical CVEs.
- CI evidence for signed commits/releases and production debug/reload settings.
