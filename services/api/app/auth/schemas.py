"""Pydantic request/response schemas for auth, users, and profiles."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

Role = Literal["admin", "manager", "user"]


def _collapse_whitespace(value: str) -> str:
    """Normalize profile text so newlines/control chars cannot corrupt TinyDB JSON."""
    return " ".join(value.split())


class ProfileBase(BaseModel):
    name: str = ""
    phone: str = ""
    address: str = ""

    @field_validator("name", "phone", "address", mode="before")
    @classmethod
    def normalize_text(cls, value: object) -> object:
        if isinstance(value, str):
            return _collapse_whitespace(value)
        return value


class ProfileOut(ProfileBase):
    id: str
    user_id: str


class ProfileUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    address: str | None = None

    @field_validator("name", "phone", "address", mode="before")
    @classmethod
    def normalize_text(cls, value: object) -> object:
        if isinstance(value, str):
            return _collapse_whitespace(value)
        return value


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str = ""
    phone: str = ""
    address: str = ""

    @field_validator("name", "phone", "address", mode="before")
    @classmethod
    def normalize_text(cls, value: object) -> object:
        if isinstance(value, str):
            return _collapse_whitespace(value)
        return value


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    role: Role | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    email: EmailStr
    is_active: bool
    role: Role
    created_at: str


class UserWithProfile(UserOut):
    profile: ProfileOut | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    email: EmailStr
    role: Role
    profile: ProfileOut | None = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str = "If that address is registered, you'll receive a link shortly"


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class MessageResponse(BaseModel):
    message: str
