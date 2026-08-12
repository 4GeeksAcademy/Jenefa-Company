"""Authentication routes: login and current session."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from ..deps import get_current_user
from ..schemas import LoginRequest, MeResponse, TokenResponse
from .. import service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest) -> TokenResponse:
    token = service.authenticate_user(payload)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=MeResponse)
def read_me(current_user: dict[str, Any] = Depends(get_current_user)) -> MeResponse:
    return MeResponse(**service.get_me(current_user))
