"""User and profile business logic over TinyDB."""

from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, status

from . import database as db
from .config import get_settings
from .email import send_password_reset_email
from .schemas import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    MeResponse,
    ProfileOut,
    ProfileUpdate,
    ResetPasswordRequest,
    UserCreate,
    UserOut,
    UserUpdate,
    UserWithProfile,
)
from .security import create_access_token, hash_password, verify_password

logger = logging.getLogger(__name__)

FORGOT_PASSWORD_MESSAGE = "If that address is registered, you'll receive a link shortly"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_now_iso() -> str:
    return _utc_now().isoformat().replace("+00:00", "Z")


def _parse_iso(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _public_user(user: dict[str, Any]) -> UserOut:
    return UserOut(
        id=user["id"],
        email=user["email"],
        is_active=user["is_active"],
        role=user["role"],
        created_at=user["created_at"],
    )


def _public_profile(profile: dict[str, Any] | None) -> ProfileOut | None:
    if profile is None:
        return None
    return ProfileOut(
        id=profile["id"],
        user_id=profile["user_id"],
        name=profile.get("name", ""),
        phone=profile.get("phone", ""),
        address=profile.get("address", ""),
    )


def register_user(payload: UserCreate) -> UserWithProfile:
    email = str(payload.email).lower()
    if db.get_user_by_email(email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    user_id = str(uuid4())
    user = {
        "id": user_id,
        "email": email,
        "hashed_password": hash_password(payload.password),
        "is_active": True,
        "role": "user",
        "created_at": _utc_now_iso(),
    }
    db.insert_user(user)
    profile = {
        "id": str(uuid4()),
        "user_id": user_id,
        "name": payload.name,
        "phone": payload.phone,
        "address": payload.address,
    }
    db.insert_profile(profile)
    public = _public_user(user)
    return UserWithProfile(**public.model_dump(), profile=_public_profile(profile))


def authenticate_user(payload: LoginRequest) -> str:
    user = db.get_user_by_email(str(payload.email).lower())
    if user is None or not verify_password(payload.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return create_access_token(subject=user["id"])


def get_me(current_user: dict[str, Any]) -> MeResponse:
    profile = db.get_profile_by_user_id(current_user["id"])
    return MeResponse(
        email=current_user["email"],
        role=current_user["role"],
        profile=_public_profile(profile),
    )


def list_all_users() -> list[UserOut]:
    return [_public_user(user) for user in db.list_users()]


def get_user(user_id: str) -> UserOut:
    user = db.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return _public_user(user)


def update_user(
    target_user_id: str,
    payload: UserUpdate,
    current_user: dict[str, Any],
) -> UserOut:
    target = db.get_user_by_id(target_user_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    is_admin = current_user.get("role") == "admin"
    is_owner = current_user.get("id") == target_user_id
    if not is_admin and not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to modify this user",
        )

    updates: dict[str, Any] = {}
    if payload.email is not None:
        new_email = str(payload.email).lower()
        existing = db.get_user_by_email(new_email)
        if existing is not None and existing["id"] != target_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        updates["email"] = new_email
    if payload.role is not None:
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can change roles",
            )
        updates["role"] = payload.role

    updated = db.update_user(target_user_id, updates) if updates else target
    assert updated is not None
    return _public_user(updated)


def delete_user(target_user_id: str, current_user: dict[str, Any]) -> None:
    target = db.get_user_by_id(target_user_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    is_admin = current_user.get("role") == "admin"
    is_owner = current_user.get("id") == target_user_id
    if not is_admin and not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete this user",
        )
    db.delete_profile_by_user_id(target_user_id)
    db.delete_user(target_user_id)


def get_my_profile(current_user: dict[str, Any]) -> ProfileOut:
    profile = db.get_profile_by_user_id(current_user["id"])
    public = _public_profile(profile)
    if public is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return public


def update_my_profile(current_user: dict[str, Any], payload: ProfileUpdate) -> ProfileOut:
    existing = db.get_profile_by_user_id(current_user["id"])
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    updates = payload.model_dump(exclude_unset=True)
    updated = db.update_profile(current_user["id"], updates) if updates else existing
    public = _public_profile(updated)
    assert public is not None
    return public


def request_password_reset(payload: ForgotPasswordRequest) -> ForgotPasswordResponse:
    """Always return the same message; only registered emails receive a dispatch."""
    response = ForgotPasswordResponse(message=FORGOT_PASSWORD_MESSAGE)
    email = str(payload.email).lower()
    user = db.get_user_by_email(email)
    if user is None or not user.get("is_active", True):
        return response

    settings = get_settings()
    token = secrets.token_urlsafe(32)
    expires_at = _utc_now() + timedelta(minutes=settings.password_reset_expire_minutes)
    db.invalidate_unused_reset_tokens_for_user(user["id"])
    db.insert_password_reset_token(
        {
            "id": str(uuid4()),
            "token": token,
            "user_id": user["id"],
            "expires_at": expires_at.isoformat().replace("+00:00", "Z"),
            "used": False,
            "created_at": _utc_now_iso(),
        }
    )
    try:
        send_password_reset_email(email, token)
    except Exception:
        # Do not leak account existence via email-provider failures.
        logger.exception("Failed to dispatch password reset email for registered user")
    return response


def reset_password_with_token(payload: ResetPasswordRequest) -> dict[str, str]:
    record = db.get_password_reset_token(payload.token)
    if record is None or record.get("used"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or already-used reset token",
        )
    try:
        expires_at = _parse_iso(str(record["expires_at"]))
    except (KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        ) from exc
    if _utc_now() >= expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired",
        )
    if not payload.new_password or len(payload.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters",
        )

    user = db.get_user_by_id(record["user_id"])
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    db.update_user(user["id"], {"hashed_password": hash_password(payload.new_password)})
    db.update_password_reset_token(payload.token, {"used": True})
    return {"message": "Password updated successfully"}


def change_password(
    current_user: dict[str, Any],
    payload: ChangePasswordRequest,
) -> dict[str, str]:
    if not verify_password(payload.current_password, current_user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    if not payload.new_password or len(payload.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters",
        )
    db.update_user(
        current_user["id"],
        {"hashed_password": hash_password(payload.new_password)},
    )
    return {"message": "Password changed successfully"}
