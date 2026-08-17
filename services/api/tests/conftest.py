"""Shared fixtures: isolated TinyDB + SECRET_KEY for auth unit tests."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest

# Configure auth settings before app.auth modules cache AuthSettings.
os.environ["SECRET_KEY"] = "unit-test-secret-key-not-for-production"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["PASSWORD_RESET_EXPIRE_MINUTES"] = "60"
os.environ.pop("EMAIL_PROVIDER", None)
os.environ.pop("RESEND_API_KEY", None)
os.environ.pop("SENDGRID_API_KEY", None)


@pytest.fixture()
def auth_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """Point AUTH_DB_PATH at a temp file and reset TinyDB / settings caches."""
    db_path = tmp_path / "auth-test.json"
    db_path.write_text("{}", encoding="utf-8")
    monkeypatch.setenv("AUTH_DB_PATH", str(db_path))

    from app.auth import config, database

    config.get_settings.cache_clear()
    database.close_db()
    yield db_path
    database.close_db()
    config.get_settings.cache_clear()


@pytest.fixture()
def sample_user(auth_db: Path):
    """Register a baseline active clinical operator and return the public user + password."""
    from app.auth.schemas import UserCreate
    from app.auth import service

    password = "ClinicPass1"
    created = service.register_user(
        UserCreate(
            email="operator@example.com",
            password=password,
            name="Clinic Operator",
            phone="+15550001111",
            address="Austin HQ",
        )
    )
    return {"user": created, "password": password}
