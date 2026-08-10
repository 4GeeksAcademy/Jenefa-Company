# HealthCore Backoffice (Home)

Internal Next.js backoffice for People & Compliance workflows. The shell labels this surface **Home**.

## Supplier directory

Route: [`/suppliers`](./app/suppliers) — create, filter, update rates, and activate/suspend vendors against `services/api`.

```bash
cd uis/backoffice
npm install
NEXT_PUBLIC_SUPPLIER_API_URL=http://127.0.0.1:8000 npm run dev
```

Open http://localhost:3002/suppliers (API must be running via `uvicorn main:app --port 8000` in `services/api`).
