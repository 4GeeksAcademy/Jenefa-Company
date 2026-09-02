"""Phase 1 stub telemetry ingestion: schema acceptance and count-only response."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient


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


def test_batch_returns_received_count(telemetry_client: TestClient) -> None:
    response = telemetry_client.post(
        "/telemetry/events", json={"events": [_event(), _event()]}
    )
    assert response.status_code == 200
    assert response.json() == {"received": 2}


def test_empty_batch_rejected(telemetry_client: TestClient) -> None:
    response = telemetry_client.post("/telemetry/events", json={"events": []})
    assert response.status_code == 400


def test_unknown_event_type_rejected(telemetry_client: TestClient) -> None:
    response = telemetry_client.post(
        "/telemetry/events", json={"events": [_event(event_type="not_a_real_event")]}
    )
    assert response.status_code == 422


def test_anonymous_user_id_allows_null(telemetry_client: TestClient) -> None:
    response = telemetry_client.post(
        "/telemetry/events", json={"events": [_event(userId=None)]}
    )
    assert response.status_code == 200
    assert response.json() == {"received": 1}


def test_no_storage_side_effect(telemetry_client: TestClient) -> None:
    """Phase 1 stub must not persist events across requests."""
    first = telemetry_client.post("/telemetry/events", json={"events": [_event()]})
    second = telemetry_client.post(
        "/telemetry/events", json={"events": [_event(), _event()]}
    )
    assert first.json() == {"received": 1}
    assert second.json() == {"received": 2}
