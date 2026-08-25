"""HealthCore incident management API.

Run from this directory:
    uvicorn app:app --reload --port 8000
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import state

# Shared domain rules live in packages/shared and are reused by scripts + API.
_SHARED_DIR = Path(__file__).resolve().parents[2] / "packages" / "shared"
if str(_SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(_SHARED_DIR))

from incidents import (  # noqa: E402
    ALLOWED_BRANCHES,
    ALLOWED_CATEGORIES,
    ALLOWED_ORIGINS,
    ALLOWED_STATUSES,
    TERMINAL_STATUSES,
    is_valid_status_transition,
    sanitize_incident_payload,
)

app = FastAPI(
    title="HealthCore Incident Management API",
    description="Centralized incident tracking for HealthCore Digital.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

state.init_db()


class IncidentCreateRequest(BaseModel):
    title: str
    description: str
    category: str
    status: str
    origin: str
    branch: str


class IncidentStatusUpdateRequest(BaseModel):
    status: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/incidents", status_code=201)
def create_incident(payload: IncidentCreateRequest) -> dict[str, Any] | JSONResponse:
    normalized, errors = sanitize_incident_payload(payload.model_dump())
    if errors:
        return JSONResponse(
            status_code=400,
            content={
                "error": "Bad Request",
                "detail": "Validation failed for one or more fields.",
                "field_errors": errors,
            },
        )
    return state.create_incident(normalized)


@app.get("/api/incidents")
def list_incidents(
    status: str | None = Query(default=None),
    origin: str | None = Query(default=None),
    branch: str | None = Query(default=None),
    category: str | None = Query(default=None),
) -> dict[str, Any] | JSONResponse:
    if status is not None and status not in ALLOWED_STATUSES:
        return JSONResponse(
            status_code=400,
            content={"error": "Bad Request", "detail": "Invalid status filter."},
        )
    if origin is not None and origin not in ALLOWED_ORIGINS:
        return JSONResponse(
            status_code=400,
            content={"error": "Bad Request", "detail": "Invalid origin filter."},
        )
    if branch is not None and branch not in ALLOWED_BRANCHES:
        return JSONResponse(
            status_code=400,
            content={"error": "Bad Request", "detail": "Invalid branch filter."},
        )
    if category is not None and category not in ALLOWED_CATEGORIES:
        return JSONResponse(
            status_code=400,
            content={"error": "Bad Request", "detail": "Invalid category filter."},
        )

    incidents = state.list_incidents(
        {
            "status": status,
            "origin": origin,
            "branch": branch,
            "category": category,
        }
    )
    return {"items": incidents, "count": len(incidents)}


@app.get("/api/incidents/summary")
def get_summary() -> dict[str, Any]:
    return state.summary()


@app.get("/api/incidents/{incident_id}")
def get_incident(incident_id: int) -> dict[str, Any]:
    incident = state.get_incident(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found.")
    return incident


@app.patch("/api/incidents/{incident_id}/status")
def patch_incident_status(
    incident_id: int,
    payload: IncidentStatusUpdateRequest,
) -> dict[str, Any] | JSONResponse:
    next_status = payload.status.strip()
    if next_status not in ALLOWED_STATUSES:
        return JSONResponse(
            status_code=400,
            content={
                "error": "Bad Request",
                "detail": "Invalid status value.",
            },
        )

    incident = state.get_incident(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found.")

    current_status = str(incident["status"])
    if current_status in TERMINAL_STATUSES:
        return JSONResponse(
            status_code=400,
            content={
                "error": "Bad Request",
                "detail": "Status is terminal and cannot be changed.",
            },
        )
    if not is_valid_status_transition(current_status, next_status):
        return JSONResponse(
            status_code=400,
            content={
                "error": "Bad Request",
                "detail": (
                    f"Invalid transition from '{current_status}' to '{next_status}'."
                ),
            },
        )

    updated = state.update_incident_status(incident_id, next_status)
    if updated is None:
        raise HTTPException(status_code=404, detail="Incident not found.")
    return updated
