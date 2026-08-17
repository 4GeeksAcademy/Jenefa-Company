"""Unit tests for login / credential verification decisions."""

from __future__ import annotations

import pytest
from fastapi import HTTPException
from jose import jwt

from app.auth import database as db
from app.auth import service
from app.auth.config import ALGORITHM, get_settings
from app.auth.schemas import LoginRequest


def test_login_returns_bearer_token_for_valid_credentials(sample_user) -> None:
    # Arrange
    payload = LoginRequest(
        email=sample_user["user"].email,
        password=sample_user["password"],
    )

    # Act
    token = service.authenticate_user(payload)

    # Assert — decision is to mint a JWT whose subject is the user id
    assert isinstance(token, str) and token.count(".") == 2
    claims = jwt.decode(
        token,
        get_settings().secret_key,
        algorithms=[ALGORITHM],
    )
    assert claims["sub"] == sample_user["user"].id


def test_login_rejects_incorrect_password(sample_user) -> None:
    # Arrange
    payload = LoginRequest(
        email=sample_user["user"].email,
        password="WrongPassword1",
    )

    # Act / Assert
    with pytest.raises(HTTPException) as exc_info:
        service.authenticate_user(payload)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Incorrect email or password"


def test_login_rejects_inactive_user(sample_user) -> None:
    # Arrange — HIPAA: disabled accounts must not receive sessions
    db.update_user(sample_user["user"].id, {"is_active": False})
    payload = LoginRequest(
        email=sample_user["user"].email,
        password=sample_user["password"],
    )

    # Act / Assert
    with pytest.raises(HTTPException) as exc_info:
        service.authenticate_user(payload)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Inactive user"


def test_login_rejects_unknown_email(auth_db) -> None:
    # Arrange
    payload = LoginRequest(
        email="missing@example.com",
        password="WhateverPass1",
    )

    # Act / Assert — same failure detail as bad password (no account enumeration)
    with pytest.raises(HTTPException) as exc_info:
        service.authenticate_user(payload)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Incorrect email or password"
