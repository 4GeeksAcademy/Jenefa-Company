"""Unit tests for JWT issuance, expiry, and password hashing helpers."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from jose import JWTError, jwt

from app.auth import database as db
from app.auth.config import ALGORITHM, get_settings
from app.auth.deps import get_current_user
from app.auth.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_access_token_round_trip_embeds_subject(auth_db) -> None:
    # Arrange / Act
    token = create_access_token(subject="user-subject-123")
    claims = decode_access_token(token)

    # Assert — business payload is the subject claim used by protected routes
    assert claims["sub"] == "user-subject-123"
    assert "exp" in claims


def test_expired_token_fails_validation(sample_user) -> None:
    # Arrange — regression for the production lockout: expired JWTs must not authenticate
    expired = create_access_token(
        subject=sample_user["user"].id,
        expires_delta=timedelta(seconds=-30),
    )

    # Act / Assert — decode layer rejects past `exp` before user lookup
    with pytest.raises(JWTError):
        decode_access_token(expired)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(get_current_user(token=expired))
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials"


def test_token_with_missing_subject_fails_current_user(sample_user) -> None:
    # Arrange — forge a JWT without `sub` so deps must refuse the session
    _ = sample_user
    forged = jwt.encode(
        {"exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        get_settings().secret_key,
        algorithm=ALGORITHM,
    )

    # Act / Assert
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(get_current_user(token=forged))
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials"


def test_password_hash_verify_rejects_wrong_secret(auth_db) -> None:
    # Arrange
    hashed = hash_password("ClinicPass1")

    # Act / Assert
    assert verify_password("ClinicPass1", hashed) is True
    assert verify_password("OtherPass99", hashed) is False
    # Ensure hashes are not stored/returned as plaintext
    assert hashed != "ClinicPass1"
    assert db.list_users() == []
