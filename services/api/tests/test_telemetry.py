"""Real telemetry ingestion: per-event partial validation + bulk persistence
to `telemetry_events`."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select


@pytest.fixture()
def telemetry_client(
    auth_db: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[TestClient]:
    db_file = tmp_path / "inventory.db"
    monkeypatch.setenv("DB_URL", f"sqlite:///{db_file}")
    from app.main import app

    with TestClient(app) as client:
        yield client


def _event(event_type: str = "client_navigation_tracked", **overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "eventId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "timestamp": "2026-09-02T12:00:00Z",
        "sessionId": "session-123",
        "userId": "user-456",
        "event_type": event_type,
        "schemaVersion": "1.0.0",
        "requestId": "req-789",
        "properties": {
            "origin_route": "/dashboard",
            "destination_route": "/inventory",
            "user_type": "operations_staff",
        },
    }
    base.update(overrides)
    return base


def _stored_rows(client: TestClient) -> list[Any]:
    from app.telemetry.models import TelemetryEventRecord

    engine = client.app.state.inventory_engine
    with Session(engine) as session:
        return list(session.exec(select(TelemetryEventRecord)))


def test_batch_returns_received_stored_rejected(telemetry_client: TestClient) -> None:
    response = telemetry_client.post(
        "/telemetry/events", json={"events": [_event(), _event()]}
    )
    assert response.status_code == 200
    assert response.json() == {"received": 2, "stored": 2, "rejected": 0}
    assert len(_stored_rows(telemetry_client)) == 2


def test_empty_batch_rejected(telemetry_client: TestClient) -> None:
    response = telemetry_client.post("/telemetry/events", json={"events": []})
    assert response.status_code == 400


def test_unknown_event_type_does_not_reject_whole_batch(telemetry_client: TestClient) -> None:
    response = telemetry_client.post(
        "/telemetry/events",
        json={"events": [_event(), _event(event_type="not_a_real_event")]},
    )
    assert response.status_code == 200
    assert response.json() == {"received": 2, "stored": 1, "rejected": 1}
    assert len(_stored_rows(telemetry_client)) == 1


def test_malformed_event_rejected_without_dropping_batch(telemetry_client: TestClient) -> None:
    response = telemetry_client.post(
        "/telemetry/events",
        json={
            "events": [
                _event(),
                {"event_type": "client_navigation_tracked", "timestamp": "not-a-date"},
            ]
        },
    )
    assert response.status_code == 200
    assert response.json() == {"received": 2, "stored": 1, "rejected": 1}


def test_anonymous_user_id_allows_null(telemetry_client: TestClient) -> None:
    response = telemetry_client.post(
        "/telemetry/events", json={"events": [_event(userId=None)]}
    )
    assert response.status_code == 200
    assert response.json() == {"received": 1, "stored": 1, "rejected": 0}
    rows = _stored_rows(telemetry_client)
    assert rows[0].user_id is None


def test_events_persist_across_requests(telemetry_client: TestClient) -> None:
    first = telemetry_client.post("/telemetry/events", json={"events": [_event()]})
    second = telemetry_client.post(
        "/telemetry/events", json={"events": [_event(), _event()]}
    )
    assert first.json() == {"received": 1, "stored": 1, "rejected": 0}
    assert second.json() == {"received": 2, "stored": 2, "rejected": 0}
    assert len(_stored_rows(telemetry_client)) == 3


def test_stored_row_maps_tags_and_derived_service(telemetry_client: TestClient) -> None:
    response = telemetry_client.post(
        "/telemetry/events",
        json={"events": [_event(event_type="billing_claim_compiled", properties={
            "claim_id": "CLM-1",
            "region": "US",
            "payer_type": "commercial",
            "coding_standard": "ICD-10-CM",
            "pre_check_denial_risk": 0.2,
        })]},
    )
    assert response.status_code == 200
    row = _stored_rows(telemetry_client)[0]
    assert row.event_type == "billing_claim_compiled"
    assert row.service == "billing_module"
    assert row.tags["claim_id"] == "CLM-1"
    assert row.session_id == "session-123"
