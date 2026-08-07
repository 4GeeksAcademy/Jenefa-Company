# HealthCore Backoffice

Internal Next.js app for HealthCore Digital staff tools (clinical ops, appointments, billing, compliance).

Incident analysis UI: [`app/incidents`](./app/incidents) → route `/incidents`.

## Getting started

```bash
cd uis/backoffice
npm install
npm run dev
```

Open [http://localhost:3001](http://localhost:3001) — overview dashboard — and [http://localhost:3001/incidents](http://localhost:3001/incidents) for CSV upload analysis.

From the monorepo root:

```bash
npm run dev:backoffice
```

Requires the FastAPI service at `services/api` (`uvicorn app:app --port 8000`).
