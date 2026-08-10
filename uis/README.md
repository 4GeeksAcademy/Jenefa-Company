# `uis` folder

This folder contains **all the user interfaces** related to the company for the cross-functional AI Engineering project (for example: web applications, internal dashboards, customer portals, Streamlit/Gradio apps, etc.).

Each subfolder inside `uis/` must correspond to **one specific user interface** (for example: `website`, `web`) and include its own technical and functional documentation.

- **Main purpose**: to centralize in a single place all the frontend applications that support the company's use cases.
- **Recommendation**: document in this file (or in sub-READMEs) the applications you add, their objective, the technology used, and how to run them.

## Applications

| App | Path | Stack | Purpose |
| --- | ---- | ----- | ------- |
| Backoffice (Home) | [`backoffice/`](./backoffice/) | Next.js | Supplier directory at `/suppliers` (shell branded Home) |
| Web | [`web/`](./web/) | Next.js | Ops workspace + incident analysis |
| Website | [`website/`](./website/) | Next.js | Public corporate site |

> _Spanish version: [README.es.md](./README.es.md)._
