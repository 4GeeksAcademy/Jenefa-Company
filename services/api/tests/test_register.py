"""Unit tests for clinical operator registration decisions."""

from __future__ import annotations

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.auth import database as db
from app.auth import service
from app.auth.schemas import UserCreate


def test_register_creates_active_user_with_profile(auth_db) -> None:
    # Arrange
    payload = UserCreate(
        email="new.ops@example.com",
        password="SecurePass9",
        name="New Operator",
        phone="+15550002222",
        address="London Clinic",
    )

    # Act
    created = service.register_user(payload)

    # Assert — application decides the account is active with a linked profile
    assert created.is_active is True
    assert created.role == "user"
    assert created.email == "new.ops@example.com"
    assert created.profile is not None
    assert created.profile.name == "New Operator"
    stored = db.get_user_by_id(created.id)
    assert stored is not None
    assert "hashed_password" in stored
    assert stored["hashed_password"] != payload.password


def test_register_rejects_duplicate_email(sample_user) -> None:
    # Arrange — same email as fixture operator
    duplicate = UserCreate(
        email=sample_user["user"].email,
        password="AnotherPass1",
        name="Duplicate",
    )

    # Act / Assert — business rule: one account per email
    with pytest.raises(HTTPException) as exc_info:
        service.register_user(duplicate)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Email already registered"


def test_register_normalizes_email_to_lowercase(auth_db) -> None:
    # Arrange / Act
    created = service.register_user(
        UserCreate(
            email="Mixed.Case@Example.com",
            password="SecurePass9",
            name="Case Check",
        )
    )

    # Assert — login lookups are lowercase; registration must store canonical form
    assert created.email == "mixed.case@example.com"
    assert db.get_user_by_email("MIXED.CASE@EXAMPLE.COM") is not None


def test_register_rejects_password_shorter_than_eight_chars(auth_db) -> None:
    # Arrange / Act / Assert — weak passwords must fail before any TinyDB write
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(email="weak@example.com", password="short")
    assert "Password must be at least 8 characters" in str(exc_info.value)
    assert db.get_user_by_email("weak@example.com") is None
