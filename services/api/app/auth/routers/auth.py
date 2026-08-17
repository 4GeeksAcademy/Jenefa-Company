"""Authentication routes: login, session, and password recovery."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import ValidationError

from ..deps import get_current_user
from ..schemas import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    MeResponse,
    MessageResponse,
    ResetPasswordRequest,
    TokenResponse,
)
from .. import service

router = APIRouter(prefix="/auth", tags=["auth"])


async def parse_login_credentials(request: Request) -> LoginRequest:
    """Accept JSON `{email,password}` or OAuth2 form `{username,password}` (Swagger Authorize)."""
    content_type = request.headers.get("content-type", "").lower()
    if "application/json" in content_type:
        try:
            data = await request.json()
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="JSON body must be an object",
            ) from exc
        if not isinstance(data, dict):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="JSON body must be an object",
            )
        email = data.get("email") or data.get("username")
        password = data.get("password")
    else:
        try:
            form = await request.form()
        except (ValueError, RuntimeError) as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Form body could not be read",
            ) from exc
        email = form.get("email") or form.get("username")
        password = form.get("password")
    try:
        return LoginRequest(email=str(email or ""), password=str(password or ""))
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.errors(),
        ) from exc


@router.post(
    "/login",
    response_model=TokenResponse,
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "email": {"type": "string", "format": "email"},
                            "password": {"type": "string"},
                        },
                    }
                },
                "application/x-www-form-urlencoded": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "username": {
                                "type": "string",
                                "description": "User email (OAuth2 username field)",
                            },
                            "password": {"type": "string"},
                        },
                    }
                },
            },
        }
    },
)
async def login(payload: LoginRequest = Depends(parse_login_credentials)) -> TokenResponse:
    token = service.authenticate_user(payload)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=MeResponse)
async def read_me(current_user: dict[str, Any] = Depends(get_current_user)) -> MeResponse:
    return service.get_me(current_user)


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(payload: ForgotPasswordRequest) -> ForgotPasswordResponse:
    return service.request_password_reset(payload)


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(payload: ResetPasswordRequest) -> MessageResponse:
    result = service.reset_password_with_token(payload)
    return MessageResponse(message=result["message"])


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    payload: ChangePasswordRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> MessageResponse:
    result = service.change_password(current_user, payload)
    return MessageResponse(message=result["message"])
