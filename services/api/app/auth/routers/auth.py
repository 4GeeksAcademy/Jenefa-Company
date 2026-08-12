"""Authentication routes: login and current session."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import ValidationError

from ..deps import get_current_user
from ..schemas import LoginRequest, MeResponse, TokenResponse
from .. import service

router = APIRouter(prefix="/auth", tags=["auth"])


async def parse_login_credentials(request: Request) -> LoginRequest:
    """Accept JSON `{email,password}` or OAuth2 form `{username,password}` (Swagger Authorize)."""
    content_type = (request.headers.get("content-type") or "").lower()
    try:
        if "application/json" in content_type:
            data = await request.json()
            if not isinstance(data, dict):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail="JSON body must be an object",
                )
            email = data.get("email") or data.get("username")
            password = data.get("password")
        else:
            # Swagger "Authorize" password flow posts form-urlencoded fields.
            form = await request.form()
            email = form.get("username") or form.get("email")
            password = form.get("password")

        return LoginRequest(email=email, password=str(password or ""))
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
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
                            "password": {"type": "string", "format": "password"},
                        },
                        "required": ["email", "password"],
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
                            "password": {"type": "string", "format": "password"},
                        },
                        "required": ["username", "password"],
                    }
                },
            },
        }
    },
)
async def login(
    payload: LoginRequest = Depends(parse_login_credentials),
) -> TokenResponse:
    token = service.authenticate_user(payload)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=MeResponse)
def read_me(current_user: dict[str, Any] = Depends(get_current_user)) -> MeResponse:
    return MeResponse(**service.get_me(current_user))
