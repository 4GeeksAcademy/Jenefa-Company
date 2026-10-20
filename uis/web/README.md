# HealthCore Web

Internal Next.js app for HealthCore Digital staff tools (clinical ops, appointments, billing, compliance).

This app uses its **own shell layout** (sidebar + operations header) and is separate from the public corporate website in `uis/website`.

## Getting started

```bash
cd uis/web
npm install
npm run dev
```

Open [http://localhost:3001](http://localhost:3001) — route `/` runs the shared `healthcore-testing` business logic and renders denial, no-show, and CME outputs on the dashboard.

From the monorepo root you can also link workspaces with `npm install`, then:

```bash
npm run dev:web
```

### Candidate sourcing (talent pipeline)

The former `uis/talent-pipeline-tracker` app now lives inside this app at `/talent`. Its components, hooks, and services are in `src/features/talent/`, and its spec is in [docs/talent-pipeline-spec.md](./docs/talent-pipeline-spec.md). The talent data still comes from the external API set by `NEXT_PUBLIC_API_BASE_URL`.
