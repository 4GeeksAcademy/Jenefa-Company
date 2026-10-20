"""Authenticated reporting routes delegating to the data pipeline core."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status

from ..auth.deps import get_current_user
from . import service

router = APIRouter(prefix="/services/reporting", tags=["reporting"])
_TASK_STATES = {"PENDING", "STARTED", "RETRY", "SUCCESS", "FAILURE"}


@router.get("/status")
def reporting_status(
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any] | None:
    """Return the latest execution manifest's five mandatory audit fields."""
    del current_user
    return service.get_latest_manifest_status(_engine_from_request(request))


@router.post("/trigger", status_code=status.HTTP_202_ACCEPTED)
def trigger_reporting(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, str]:
    """Queue a reporting run on the Celery worker (Redis broker) without blocking the API."""
    from ..tasks.celery import generate_reporting_task

    del current_user
    try:
        task = generate_reporting_task.delay(None)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Reporting worker is unavailable. Start Redis and the Celery worker.",
        ) from exc
    return {"task_id": task.id, "status": "queued"}


@router.get("/trigger/{task_id}")
def reporting_run_status(
    task_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Report the state of a queued reporting run (no task payload is returned)."""
    from celery.result import AsyncResult

    from ..tasks.celery import app as celery_app

    del current_user
    try:
        state = AsyncResult(task_id, app=celery_app).state
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Reporting worker is unavailable. Start Redis and the Celery worker.",
        ) from exc
    return {"task_id": task_id, "status": state.lower() if state in _TASK_STATES else "pending"}


@router.get("/kpis")
def reporting_kpis(
    request: Request
) -> list[dict[str, Any]]:
    """Deliver rows to dashboards. Bypasses JWT check for local dev testing."""
    return service.fetch_executive_metrics(_engine_from_request(request))


def _engine_from_request(request: Request) -> Any:
    """Use the existing application engine so reporting reads the same database."""
    return getattr(request.app.state, "inventory_engine", None)
