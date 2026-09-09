"""Real telemetry ingestion pipeline (Phases 1-3): loose envelope acceptance,
per-event partial validation, and a single bulk insert to `telemetry_events`.
Also hosts the read-side operational report endpoint (`GET /telemetry/report`).
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from . import analysis, service
from .database import get_session
from .schemas import TelemetryBatchResult, TelemetryIngestRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telemetry", tags=["telemetry"])

# Phase 3 in-memory cache: (start_date, end_date) ISO key -> (cached_at, payload).
_REPORT_CACHE_TTL_SECONDS = 60
_report_cache: dict[tuple[str, str], tuple[float, dict[str, Any]]] = {}


@router.post(
    "/events",
    response_model=TelemetryBatchResult,
    status_code=status.HTTP_200_OK,
    summary="Ingest a telemetry event batch with per-event partial validation",
)
def ingest_telemetry_batch(
    payload: TelemetryIngestRequest,
    session: Session = Depends(get_session),
) -> TelemetryBatchResult:
    if len(payload.events) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch must contain at least one event",
        )

    result = service.ingest_batch(session, payload.events)
    logger.info(
        "telemetry batch processed: received=%d stored=%d rejected=%d",
        result.received,
        result.stored,
        result.rejected,
    )
    return result


def _parse_report_boundary(value: str, *, field_name: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} must be a valid ISO 8601 timestamp",
        ) from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


@router.get(
    "/report",
    summary="Aggregate operational telemetry metrics (volume, error rate, latency) over a date window",
)
def get_telemetry_report(
    start_date: str | None = Query(
        None, description="ISO 8601 window start; defaults to (end_date - 7 days), UTC"
    ),
    end_date: str | None = Query(None, description="ISO 8601 window end; defaults to now, UTC"),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    resolved_end = (
        _parse_report_boundary(end_date, field_name="end_date")
        if end_date
        else datetime.now(timezone.utc)
    )
    resolved_start = (
        _parse_report_boundary(start_date, field_name="start_date")
        if start_date
        else resolved_end - timedelta(days=7)
    )
    if resolved_start > resolved_end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must not be after end_date",
        )

    cache_key = (resolved_start.isoformat(), resolved_end.isoformat())
    cached = _report_cache.get(cache_key)
    now = time.monotonic()
    if cached is not None and (now - cached[0]) < _REPORT_CACHE_TTL_SECONDS:
        return cached[1]

    payload: dict[str, Any] = {
        "period": {"from": resolved_start.isoformat(), "to": resolved_end.isoformat()},
        "metrics": {
            "events_per_day": analysis.events_per_day(session, resolved_start, resolved_end),
            "error_rate_by_type": analysis.error_rate_by_type(session, resolved_start, resolved_end),
            "average_latency_by_day": analysis.average_latency_by_day(
                session, resolved_start, resolved_end
            ),
        },
    }
    _report_cache[cache_key] = (now, payload)
    return payload

