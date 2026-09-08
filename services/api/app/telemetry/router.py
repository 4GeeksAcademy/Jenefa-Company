"""Real telemetry ingestion pipeline (Phases 1-3): loose envelope acceptance,
per-event partial validation, and a single bulk insert to `telemetry_events`.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from . import service
from .database import get_session
from .schemas import TelemetryBatchResult, TelemetryIngestRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


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
