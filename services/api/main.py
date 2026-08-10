"""HealthCore API — FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import incidents, suppliers

app = FastAPI(
    title="HealthCore API",
    description=(
        "Unified HealthCore Digital API: supplier directory (TinyDB) and "
        "incident analysis (no PHI in responses)."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(suppliers.router)
app.include_router(incidents.router)
