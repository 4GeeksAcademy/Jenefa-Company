"""Personal profile routes (owner-only mutations)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from ..deps import get_current_user
from ..schemas import ProfileOut, ProfileUpdate
from .. import service

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("/me", response_model=ProfileOut)
def read_my_profile(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> ProfileOut:
    return service.get_my_profile(current_user)


@router.put("/me", response_model=ProfileOut)
def update_my_profile(
    payload: ProfileUpdate,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> ProfileOut:
    return service.update_my_profile(current_user=current_user, payload=payload)
