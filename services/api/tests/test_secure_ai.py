"""Governance registry coverage for the SecureAI NIST/MIST slice."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def secure_ai_client(
    auth_db: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[TestClient]:
    monkeypatch.setenv("DB_URL", f"sqlite:///{tmp_path / 'inventory.db'}")
    from app.main import app

    with TestClient(app) as client:
        yield client


def _register_and_login(client: TestClient, email: str) -> str:
    client.post(
        "/users",
        json={"email": email, "password": "AdminPass1", "name": "Governance"},
    )
    from app.auth import database

    user = database.get_user_by_email(email)
    assert user is not None
    database.update_user(user["id"], {"role": "admin"})
    response = client.post(
        "/auth/login", json={"email": email, "password": "AdminPass1"}
    )
    return response.json()["access_token"]


def test_registry_requires_authentication(secure_ai_client: TestClient) -> None:
    response = secure_ai_client.get("/governance/ai-systems")
    assert response.status_code == 401


def test_admin_can_register_list_and_suspend_system(secure_ai_client: TestClient) -> None:
    token = _register_and_login(secure_ai_client, "governance@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    listed = secure_ai_client.get("/governance/ai-systems", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 5

    payload = {
        "system_key": "booking-risk-review",
        "name": "Booking Risk Review",
        "architecture_type": "supervised decision support",
        "data_traversal_surface": "appointment metadata",
        "provider": "internal model",
        "owner": "Priya Nair",
        "risk_tier": "high",
        "jurisdiction": "US",
        "status": "pending_review",
    }
    created = secure_ai_client.post(
        "/governance/ai-systems", json=payload, headers=headers
    )
    assert created.status_code == 201
    assert created.json()["status"] == "pending_review"

    duplicate = secure_ai_client.post(
        "/governance/ai-systems", json=payload, headers=headers
    )
    assert duplicate.status_code == 409

    suspended = secure_ai_client.post(
        "/governance/ai-systems/booking-risk-review/suspend", headers=headers
    )
    assert suspended.status_code == 200
    assert suspended.json()["status"] == "suspended"


def test_non_admin_cannot_register_system(secure_ai_client: TestClient) -> None:
    secure_ai_client.post(
        "/users",
        json={"email": "operator@example.com", "password": "Operator1", "name": "Operator"},
    )
    token = secure_ai_client.post(
        "/auth/login", json={"email": "operator@example.com", "password": "Operator1"}
    ).json()["access_token"]
    response = secure_ai_client.post(
        "/governance/ai-systems",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "system_key": "unsafe-system",
            "name": "Unsafe",
            "architecture_type": "agent",
            "data_traversal_surface": "none",
            "provider": "internal",
            "owner": "James Osei",
            "risk_tier": "low",
            "jurisdiction": "US",
        },
    )
    assert response.status_code == 403


def test_registry_rejects_invalid_risk_tier(secure_ai_client: TestClient) -> None:
    token = _register_and_login(secure_ai_client, "validation@example.com")
    response = secure_ai_client.post(
        "/governance/ai-systems",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "system_key": "invalid-risk",
            "name": "Invalid Risk",
            "architecture_type": "agent",
            "data_traversal_surface": "none",
            "provider": "internal",
            "owner": "James Osei",
            "risk_tier": "unknown",
            "jurisdiction": "US",
        },
    )
    assert response.status_code == 422