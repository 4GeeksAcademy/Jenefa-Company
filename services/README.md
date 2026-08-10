# `services` folder

This folder contains **all the backend services** (APIs and background workers) related to the company for the cross-functional AI Engineering project.

Each subfolder inside `services/` must correspond to **one specific service** (for example: `admin-api`, `data-processor-worker`) and include its own technical and functional documentation.

- **Main purpose**: to centralize all the backend logic, APIs, and queue consumers that support the company's use cases.
- **Recommendation**: document in this file (or in sub-READMEs) the services you add, their objective, the technology used, and how to run them.

## Services

| Service | Path | Stack | Purpose |
| ------- | ---- | ----- | ------- |
| HealthCore API | [`api/`](./api/) | FastAPI + TinyDB | Supplier directory (`/suppliers`) and incident analysis (`/api/incidents/*`) per [`directory.md`](./directory.md) |

# To Run
## Termina 1:

`cd services/api && source .venv/bin/activate

python seed.py

uvicorn main:app --reload --port 8000`

## Terminal 2 : 

`cd uis/backoffice

npm run dev `

> _Spanish version: [README.es.md](./README.es.md)._
