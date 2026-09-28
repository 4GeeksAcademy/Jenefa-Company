"""Pydantic envelope mirroring docs/telemetry/event-schemas.json (HealthCoreTelemetryEnvelope).

`event-schemas.json` is the ground truth vocabulary; `event_type` is a closed
enum and must not be extended here without updating that file first.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

EventType = Literal[
    "appointment_booked",
    "appointment_noshow_predicted",
    "billing_claim_compiled",
    "revenue_stream_reconciled",
    "patient_data_accessed",
    "system_health_checked",
    "clinical_documentation_abandoned",
    "client_navigation_tracked",
]


class TelemetryEvent(BaseModel):
    eventId: str = Field(..., description="Unique event identifier UUID")
    timestamp: datetime = Field(..., description="ISO-8601 formatted event occurrence timestamp")
    sessionId: str = Field(..., description="Client session identifier token")
    userId: str | None = Field(
        ..., description="Authenticated clinic staff/user account key; null for anonymous actions"
    )
    event_type: EventType = Field(
        ..., description="Taxonomic domain category matching docs/telemetry/event-schemas.json"
    )
    schemaVersion: str = Field(..., description="Semantic version tracker for schema shifts")
    requestId: str = Field(..., description="Server tracking parameter for tracing request lifecycles")
    properties: dict[str, Any] = Field(..., description="Metadata container for context payload maps")


class TelemetryIngestRequest(BaseModel):
    """Loose envelope: `events` stays `list[dict]` so one corrupt row cannot
    trigger a global 422 and drop the whole batch (see specs-storageTelemetry.md).
    Each item is validated individually against `TelemetryEvent` in the router.
    """

    events: list[dict[str, Any]] = Field(
        ..., description="Array batch containing raw telemetry signal dictionaries"
    )


class TelemetryBatchResult(BaseModel):
    received: int = Field(..., description="Total number of events in the batch")
    stored: int = Field(..., description="Events that passed validation and were persisted")
    rejected: int = Field(..., description="Events that failed per-event validation")
