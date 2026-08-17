"""Additional auth service decisions for coverage of session and recovery rules."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from app.auth import database as db
from app.auth import service
from app.auth.schemas import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    ProfileUpdate,
    ResetPasswordRequest,
    UserCreate,
    UserUpdate,
)


def test_get_me_includes_profile(sample_user) -> None:
    user = db.get_user_by_id(sample_user["user"].id)
    assert user is not None
    me = service.get_me(user)
    assert me.email == sample_user["user"].email
    assert me.profile is not None
    assert me.profile.name == "Clinic Operator"


def test_update_user_owner_can_change_email_but_not_role(sample_user) -> None:
    owner = db.get_user_by_id(sample_user["user"].id)
    assert owner is not None

    updated = service.update_user(
        sample_user["user"].id,
        UserUpdate(email="renamed@example.com"),
        owner,
    )
    assert updated.email == "renamed@example.com"

    with pytest.raises(HTTPException) as exc_info:
        service.update_user(
            sample_user["user"].id,
            UserUpdate(role="admin"),
            owner,
        )
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Only admins can change roles"


def test_update_user_rejects_non_owner(sample_user, auth_db) -> None:
    other = service.register_user(
        UserCreate(email="other@example.com", password="OtherPass1", name="Other")
    )
    other_row = db.get_user_by_id(other.id)
    assert other_row is not None

    with pytest.raises(HTTPException) as exc_info:
        service.update_user(
            sample_user["user"].id,
            UserUpdate(email="hijack@example.com"),
            other_row,
        )
    assert exc_info.value.status_code == 403


def test_forgot_password_same_message_for_unknown_and_known(sample_user) -> None:
    # Anti-enumeration: identical message whether or not the mailbox exists
    known = service.request_password_reset(
        ForgotPasswordRequest(email=sample_user["user"].email)
    )
    unknown = service.request_password_reset(
        ForgotPasswordRequest(email="nobody@example.com")
    )
    assert known.message == unknown.message == service.FORGOT_PASSWORD_MESSAGE
    tokens = db.password_reset_tokens_table().all()
    assert len(tokens) == 1
    assert tokens[0]["user_id"] == sample_user["user"].id


def test_reset_password_rejects_expired_token(sample_user) -> None:
    service.request_password_reset(ForgotPasswordRequest(email=sample_user["user"].email))
    token = db.password_reset_tokens_table().all()[0]["token"]
    db.update_password_reset_token(
        token,
        {
            "expires_at": (datetime.now(timezone.utc) - timedelta(minutes=1))
            .isoformat()
            .replace("+00:00", "Z")
        },
    )

    with pytest.raises(HTTPException) as exc_info:
        service.reset_password_with_token(
            ResetPasswordRequest(token=token, new_password="BrandNewPass1")
        )
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Reset token has expired"


def test_reset_password_happy_path_then_rejects_reuse(sample_user) -> None:
    service.request_password_reset(ForgotPasswordRequest(email=sample_user["user"].email))
    token = db.password_reset_tokens_table().all()[0]["token"]

    result = service.reset_password_with_token(
        ResetPasswordRequest(token=token, new_password="BrandNewPass1")
    )
    assert result["message"] == "Password updated successfully"

    # New password authenticates; old password does not
    assert service.authenticate_user(
        LoginRequest(email=sample_user["user"].email, password="BrandNewPass1")
    )
    with pytest.raises(HTTPException):
        service.authenticate_user(
            LoginRequest(email=sample_user["user"].email, password=sample_user["password"])
        )

    with pytest.raises(HTTPException) as exc_info:
        service.reset_password_with_token(
            ResetPasswordRequest(token=token, new_password="AnotherPass2")
        )
    assert exc_info.value.detail == "Invalid or already-used reset token"


def test_change_password_rejects_wrong_current(sample_user) -> None:
    user = db.get_user_by_id(sample_user["user"].id)
    assert user is not None
    with pytest.raises(HTTPException) as exc_info:
        service.change_password(
            user,
            ChangePasswordRequest(
                current_password="NotThePassword",
                new_password="BrandNewPass1",
            ),
        )
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Current password is incorrect"


def test_change_password_happy_path(sample_user) -> None:
    user = db.get_user_by_id(sample_user["user"].id)
    assert user is not None
    result = service.change_password(
        user,
        ChangePasswordRequest(
            current_password=sample_user["password"],
            new_password="BrandNewPass1",
        ),
    )
    assert result["message"] == "Password changed successfully"
    assert service.authenticate_user(
        LoginRequest(email=sample_user["user"].email, password="BrandNewPass1")
    )


def test_profile_update_and_get(sample_user) -> None:
    user = db.get_user_by_id(sample_user["user"].id)
    assert user is not None
    updated = service.update_my_profile(
        user,
        ProfileUpdate(name="Updated Name", phone="+15559998888", address="Manchester"),
    )
    assert updated.name == "Updated Name"
    assert service.get_my_profile(user).address == "Manchester"


def test_delete_user_owner(sample_user) -> None:
    user = db.get_user_by_id(sample_user["user"].id)
    assert user is not None
    user_id = user["id"]
    service.delete_user(user_id, user)
    assert db.get_user_by_id(user_id) is None
    assert db.get_profile_by_user_id(user_id) is None


def test_get_user_not_found(auth_db) -> None:
    with pytest.raises(HTTPException) as exc_info:
        service.get_user("missing-id")
    assert exc_info.value.status_code == 404


def test_list_all_users_returns_public_rows(sample_user) -> None:
    users = service.list_all_users()
    assert len(users) == 1
    assert users[0].email == sample_user["user"].email
