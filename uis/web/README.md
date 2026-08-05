# HealthCore Backoffice

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
