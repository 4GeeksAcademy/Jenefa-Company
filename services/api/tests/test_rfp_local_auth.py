"""RFP's opt-in loopback auth bypass is restricted to local development."""

from __future__ import annotations

from pathlib import Path

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