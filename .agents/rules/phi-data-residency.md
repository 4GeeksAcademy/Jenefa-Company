---
description: Enforce HIPAA and UK GDPR data-handling conventions across the HealthCore monorepo
scope: always-active
---

# PHI & Cross-Border Data Residency

HealthCore handles protected health information under HIPAA (US) and UK GDPR. Patient records must stay in their legal jurisdiction unless a cross-border view is explicitly required.

## Rules

- Never commit real PHI/PII, production secrets, or live EHR extracts into the repository.
- Prefer synthetic or anonymized fixtures under `data/` for local development and tests.
- Do not modify `/infra/`, `/data/raw/`, `/internal/`, or `.env.production` without explicit developer confirmation in chat.
- Keep US and UK patient data logically partitioned; do not design features that permanently store UK records in US regions (or the reverse).
- Any AI or automation output that touches clinical, billing, or compliance data must remain auditable (who ran it, what input was used, what was changed).
- When a change could expose patient data, stop and ask the developer before proceeding.

## Examples

```text
# ❌ BAD — commit a raw clinic export with patient names
data/raw/us-tx-001-patients.csv

# ✅ GOOD — use anonymized sample rows for demos and tests
data/process/sample-appointments.json
```
