# `scripts` folder

This folder contains **helper scripts** for the monorepo: development automation, maintenance utilities, repetitive tasks (setup, lint, migrations, data generation, etc.), and internal tooling.

- **Main purpose**: group support tools that do not belong to a specific app, agent, or pipeline but make the team’s work easier.
- **Recommendation**: document each script (what it does, parameters, requirements, usage examples) and keep them reproducible (and safe) across environments.

## Incident analysis (Phase 1)

| Script | Purpose |
| ------ | ------- |
| `analyze.py` | Terminal engine: `python analyze.py <path_to_csv>` |
| `incident_core/` | Shared validator + metrics (also used by `services/api`) |
| `generate_incidents_csv.py` | Builds sample `incidents-healthcore.csv` |
| `incidents-healthcore.csv` | 100-row sample matching `context-fileIncident.md` |
| `context-fileIncident.md` / `specs.md` | Product context and build specs |

Outputs never include `patient_id` (HIPAA / UK GDPR).

> _Spanish version: [README.es.md](./README.es.md)._
