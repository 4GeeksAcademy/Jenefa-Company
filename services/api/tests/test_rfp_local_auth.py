"""RFP's opt-in loopback auth bypass is restricted to local development."""

from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import Request
from fastapi.testclient import TestClient


def _client(auth_db: Path, tmp_path: Path, monkeypatch, bypass: bool) -> TestClient:
    monkeypatch.setenv("DB_URL", f"sqlite:///{tmp_path / 'rfp-auth.db'}")
    monkeypatch.setenv("RFP_LOCAL_AUTH_BYPASS", "true" if bypass else "false")
    from app.main import app

    return TestClient(app, client=("127.0.0.1", 50000))


def test_local_bypass_allows_anonymous_ticket_polling(auth_db, tmp_path, monkeypatch) -> None:
    with _client(auth_db, tmp_path, monkeypatch, bypass=True) as client:
        response = client.get("/rfp/tickets")

    assert response.status_code == 200
    assert response.json() == []


def test_local_bypass_allows_anonymous_pdf_upload(auth_db, tmp_path, monkeypatch) -> None:
    from app.rfp import router as rfp_router

    monkeypatch.setattr(rfp_router._executor, "submit", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(rfp_router, "UPLOAD_DIR", tmp_path / "uploads")
    with _client(auth_db, tmp_path, monkeypatch, bypass=True) as client:
        response = client.post(
            "/rfp/tickets",
            files={"file": ("request.pdf", b"%PDF-1.7\nRFP test", "application/pdf")},
        )

    assert response.status_code == 202, response.text
    assert response.json()["status"] == "analyzing"


def test_anonymous_ticket_polling_still_requires_auth_without_bypass(
    auth_db, tmp_path, monkeypatch
) -> None:
    with _client(auth_db, tmp_path, monkeypatch, bypass=False) as client:
        response = client.get("/rfp/tickets")

    assert response.status_code == 401


def test_local_bypass_rejects_non_loopback_requests(auth_db, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DB_URL", f"sqlite:///{tmp_path / 'rfp-remote.db'}")
    monkeypatch.setenv("RFP_LOCAL_AUTH_BYPASS", "true")
    from app.main import app

    with TestClient(app, client=("203.0.113.10", 50000)) as client:
        response = client.get("/rfp/tickets")

    assert response.status_code == 401


def test_local_bff_credential_allows_forwarded_anonymous_polling(
    auth_db, tmp_path, monkeypatch
) -> None:
    monkeypatch.setenv("DB_URL", f"sqlite:///{tmp_path / 'rfp-proxy.db'}")
    monkeypatch.setenv("RFP_LOCAL_AUTH_BYPASS", "true")
    monkeypatch.setenv("RFP_LOCAL_PROXY_SECRET", "test-only-proxy-secret")
    from app.main import app

    with TestClient(app, client=("203.0.113.10", 50000)) as client:
        response = client.get(
            "/rfp/tickets",
            headers={"x-healthcore-local-rfp-proxy": "test-only-proxy-secret"},
        )

    assert response.status_code == 200


def test_local_bff_credential_is_rejected_when_missing_or_incorrect(
    auth_db, tmp_path, monkeypatch
) -> None:
    monkeypatch.setenv("DB_URL", f"sqlite:///{tmp_path / 'rfp-proxy-denied.db'}")
    monkeypatch.setenv("RFP_LOCAL_AUTH_BYPASS", "true")
    monkeypatch.setenv("RFP_LOCAL_PROXY_SECRET", "test-only-proxy-secret")
    from app.main import app

    with TestClient(app, client=("203.0.113.10", 50000)) as client:
        missing = client.get("/rfp/tickets")
        incorrect = client.get(
            "/rfp/tickets",
            headers={"x-healthcore-local-rfp-proxy": "incorrect-secret"},
        )

    assert missing.status_code == 401
    assert incorrect.status_code == 401


def test_rfp_event_stream_requires_authentication(auth_db, tmp_path, monkeypatch) -> None:
    with _client(auth_db, tmp_path, monkeypatch, bypass=False) as client:
        response = client.get("/rfp/events")

    assert response.status_code == 401


def test_rfp_event_stream_has_sse_headers_and_initial_frame(auth_db, tmp_path, monkeypatch) -> None:
    from app.rfp.router import stream_rfp_events

    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/rfp/events",
            "headers": [],
            "client": ("127.0.0.1", 50000),
            "server": ("testserver", 80),
            "scheme": "http",
            "query_string": b"",
        }
    )
    response = asyncio.run(stream_rfp_events(request, {}))

    assert response.media_type == "text/event-stream"
    assert response.headers["cache-control"] == "no-cache"
    assert response.headers["connection"] == "keep-alive"
    assert asyncio.run(response.body_iterator.__anext__()) == ": connected\n\n"


def test_rfp_event_stream_emits_named_json_event() -> None:
    from app.rfp.events import RFPEventHub

    async def read_event() -> str:
        hub = RFPEventHub()
        stream = hub.stream()
        await stream.__anext__()
        await hub.publish({"ticket_id": "ticket-1", "status": "analyzing"})
        event = await stream.__anext__()
        await stream.aclose()
        return event

    assert asyncio.run(read_event()) == (
        'event: rfp_ticket_created\ndata: {"ticket_id":"ticket-1","status":"analyzing"}\n\n'
    )