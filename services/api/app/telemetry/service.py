"""Per-event partial validation + single bulk insert into `telemetry_events`.

`TelemetryEvent` (schemas.py) is reused unchanged as the per-item validator.
`service` and `environment` are not part of the client envelope — they are
derived server-side, per productContext-storageTelemetry.md.
"""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError
from sqlmodel import Session

from .config import get_deployment_environment
from .models import TelemetryEventRecord
from .schemas import TelemetryBatchResult, TelemetryEvent

# Maps the closed event_type vocabulary (event-schemas.json) to the emitting
# module, for the `service` analytical dimension.
EVENT_TYPE_SERVICE_MAP: dict[str, str] = {
    "appointment_booked": "scheduling_module",
    "appointment_noshow_predicted": "scheduling_module",
    "billing_claim_compiled": "billing_module",
    "revenue_stream_reconciled": "billing_module",
    "patient_data_accessed": "compliance_module",
    "system_health_checked": "platform_health",
    "clinical_documentation_abandoned": "clinical_documentation_module",
    "client_navigation_tracked": "web_client",
}
DEFAULT_SERVICE = "unknown_module"


def _derive_service(event_type: str) -> str:
    return EVENT_TYPE_SERVICE_MAP.get(event_type, DEFAULT_SERVICE)


def ingest_batch(session: Session, raw_events: list[dict[str, Any]]) -> TelemetryBatchResult:
    environment = get_deployment_environment()
    records: list[TelemetryEventRecord] = []
    rejected = 0

    for raw_item in raw_events:
        try:
            event = TelemetryEvent.model_validate(raw_item)
        except ValidationError:
            rejected += 1
            continue
        records.append(
            TelemetryEventRecord(
                event_type=event.event_type,
                timestamp=event.timestamp,
                service=_derive_service(event.event_type),
                tags=event.properties,
                user_id=event.userId,
                session_id=event.sessionId,
                environment=environment,
            )
        )

    if records:
        session.add_all(records)
        session.commit()

    return TelemetryBatchResult(
        received=len(raw_events),
        stored=len(records),
        rejected=rejected,
    )
