# HealthCore Backoffice

Internal Next.js app for HealthCore Digital staff tools (clinical ops, appointments, billing, compliance).

Incident management UI:
- [`app/incidents/register`](./app/incidents/register) → route `/incidents/register`
- [`app/incidents/list`](./app/incidents/list) → route `/incidents/list`
- [`app/incidents/summary`](./app/incidents/summary) → route `/incidents/summary`

## Getting started

```bash
cd uis/backoffice
npm install
npm run dev
```

Open [http://localhost:3001](http://localhost:3001) for overview plus:
- [http://localhost:3001/incidents/register](http://localhost:3001/incidents/register)
- [http://localhost:3001/incidents/list](http://localhost:3001/incidents/list)
- [http://localhost:3001/incidents/summary](http://localhost:3001/incidents/summary)

From the monorepo root:

```bash
npm run dev:backoffice
```

Requires the FastAPI service at `services/api` (`uvicorn app:app --port 8000`).
