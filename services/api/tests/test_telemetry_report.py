"""Tests for `GET /telemetry/report`: Pandas analysis pipeline, window
resolution, and the 60-second in-memory cache."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session


@pytest.fixture()
def report_client(
    auth_db: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[TestClient]:
    db_file = tmp_path / "inventory.db"
    monkeypatch.setenv("DB_URL", f"sqlite:///{db_file}")
    from app.main import app
    from app.telemetry import router as telemetry_router

    telemetry_router._report_cache.clear()
    with TestClient(app) as client:
        yield client
    telemetry_router._report_cache.clear()


def _seed_row(
    client: TestClient,
    *,
    event_type: str,
    timestamp: str,
    tags: dict[str, object],
) -> None:
    from app.telemetry.models import TelemetryEventRecord

    engine = client.app.state.inventory_engine
    with Session(engine) as session:
        session.add(
            TelemetryEventRecord(
                event_type=event_type,
                timestamp=datetime.fromisoformat(timestamp),
                service="platform_health",
                tags=tags,
                session_id="session-1",
                environment="sandbox",
            )
        )
        session.commit()


def test_report_defaults_to_last_7_days(report_client: TestClient) -> None:
    response = report_client.get("/telemetry/report")
    assert response.status_code == 200
    body = response.json()
    period_from = datetime.fromisoformat(body["period"]["from"])
    period_to = datetime.fromisoformat(body["period"]["to"])
    assert (period_to - period_from).days == 7
    assert set(body["metrics"]) == {
        "events_per_day",
        "error_rate_by_type",
        "average_latency_by_day",
    }


def test_events_per_day_groups_by_date(report_client: TestClient) -> None:
    _seed_row(
        report_client,
        event_type="client_navigation_tracked",
        timestamp="2026-09-01T10:00:00+00:00",
        tags={"origin_route": "/a", "destination_route": "/b", "user_type": "patient"},
    )
    _seed_row(
        report_client,
        event_type="client_navigation_tracked",
        timestamp="2026-09-01T15:00:00+00:00",
        tags={"origin_route": "/a", "destination_route": "/b", "user_type": "patient"},
    )
    _seed_row(
        report_client,
        event_type="client_navigation_tracked",
        timestamp="2026-09-02T09:00:00+00:00",
        tags={"origin_route": "/a", "destination_route": "/b", "user_type": "patient"},
    )

    response = report_client.get(
        "/telemetry/report",
        params={"start_date": "2026-09-01T00:00:00Z", "end_date": "2026-09-03T00:00:00Z"},
    )
    assert response.status_code == 200
    events_per_day = {row["date"]: row["event_count"] for row in response.json()["metrics"]["events_per_day"]}
    assert events_per_day == {"2026-09-01": 2, "2026-09-02": 1}


def test_error_rate_by_type_derived_from_status_state(report_client: TestClient) -> None:
    _seed_row(
        report_client,
        event_type="system_health_checked",
        timestamp="2026-09-01T10:00:00+00:00",
        tags={"target_subsystem": "us_billing_api", "status_state": "healthy", "latency_ms": 120},
    )
    _seed_row(
        report_client,
        event_type="system_health_checked",
        timestamp="2026-09-01T11:00:00+00:00",
        tags={"target_subsystem": "us_billing_api", "status_state": "unreachable", "latency_ms": 900},
    )

    response = report_client.get(
        "/telemetry/report",
        params={"start_date": "2026-09-01T00:00:00Z", "end_date": "2026-09-03T00:00:00Z"},
    )
    assert response.status_code == 200
    rates = {row["event_type"]: row["error_rate"] for row in response.json()["metrics"]["error_rate_by_type"]}
    assert rates["system_health_checked"] == 0.5


def test_average_latency_by_day(report_client: TestClient) -> None:
    _seed_row(
        report_client,
        event_type="system_health_checked",
        timestamp="2026-09-01T10:00:00+00:00",
        tags={"target_subsystem": "uk_booking_sheet", "status_state": "healthy", "latency_ms": 100},
    )
    _seed_row(
        report_client,
        event_type="system_health_checked",
        timestamp="2026-09-01T11:00:00+00:00",
        tags={"target_subsystem": "uk_booking_sheet", "status_state": "healthy", "latency_ms": 200},
    )

    response = report_client.get(
        "/telemetry/report",
        params={"start_date": "2026-09-01T00:00:00Z", "end_date": "2026-09-03T00:00:00Z"},
    )
    assert response.status_code == 200
    latency_rows = response.json()["metrics"]["average_latency_by_day"]
    assert latency_rows == [{"date": "2026-09-01", "avg_latency_ms": 150.0}]


def test_invalid_start_date_returns_400(report_client: TestClient) -> None:
    response = report_client.get("/telemetry/report", params={"start_date": "not-a-date"})
    assert response.status_code == 400


def test_start_after_end_returns_400(report_client: TestClient) -> None:
    response = report_client.get(
        "/telemetry/report",
        params={"start_date": "2026-09-05T00:00:00Z", "end_date": "2026-09-01T00:00:00Z"},
    )
    assert response.status_code == 400


def test_identical_window_served_from_cache(
    report_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    params = {"start_date": "2026-09-01T00:00:00Z", "end_date": "2026-09-03T00:00:00Z"}
    first = report_client.get("/telemetry/report", params=params)
    assert first.status_code == 200

    _seed_row(
        report_client,
        event_type="client_navigation_tracked",
        timestamp="2026-09-01T10:00:00+00:00",
        tags={"origin_route": "/a", "destination_route": "/b", "user_type": "patient"},
    )

    second = report_client.get("/telemetry/report", params=params)
    assert second.json() == first.json()

    from app.telemetry import router as telemetry_router

    telemetry_router._report_cache.clear()
    third = report_client.get("/telemetry/report", params=params)
    assert third.json()["metrics"]["events_per_day"] == [{"date": "2026-09-01", "event_count": 1}]
