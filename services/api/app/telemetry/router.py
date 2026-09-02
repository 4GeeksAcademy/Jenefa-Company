"""Phase 1 stub ingestion route. Validates and logs batches; performs no storage."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status

from .schemas import TelemetryBatchRequest, TelemetryBatchResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


@router.post(
    "/events",
    response_model=TelemetryBatchResponse,
    status_code=status.HTTP_200_OK,
    summary="Ingest a telemetry event batch (Phase 1 stub)",
)
async def ingest_telemetry_batch(payload: TelemetryBatchRequest) -> TelemetryBatchResponse:
    batch_size = len(payload.events)
    if batch_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch must contain at least one event",
        )

    event_types = [event.event_type for event in payload.events]
    logger.info("telemetry batch received: size=%d event_types=%s", batch_size, event_types)

    return TelemetryBatchResponse(received=batch_size)
