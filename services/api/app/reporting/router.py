"""Authenticated reporting routes delegating to the data pipeline core."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, Request, status

from ..auth.deps import get_current_user
from . import service

router = APIRouter(prefix="/services/reporting", tags=["reporting"])


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
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, str]:
    """Queue a manual/backfill run without blocking the API request."""
    del current_user
    background_tasks.add_task(service.trigger_batch_execution, _engine_from_request(request))
    return {"status": "ACCEPTED"}


@router.get("/kpis")
def reporting_kpis(
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """Deliver rows from `reporting.executive_kpis` to executive dashboards."""
    del current_user
    return service.fetch_executive_metrics(_engine_from_request(request))


def _engine_from_request(request: Request) -> Any:
    """Use the existing application engine so reporting reads the same database."""
    return getattr(request.app.state, "inventory_engine", None)
