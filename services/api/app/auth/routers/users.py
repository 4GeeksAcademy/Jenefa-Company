"""User registration and account management routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Response, status

from ..deps import get_current_user
from ..schemas import UserCreate, UserOut, UserUpdate, UserWithProfile
from .. import service

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserWithProfile, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate) -> UserWithProfile:
    return service.register_user(payload)


@router.get("", response_model=list[UserOut])
def list_users(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> list[UserOut]:
    _ = current_user
    return service.list_all_users()


@router.get("/{user_id}", response_model=UserOut)
def read_user(
    user_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> UserOut:
    _ = current_user
    return service.get_user(user_id)


@router.put("/{user_id}", response_model=UserOut)
def update_user(
    user_id: str,
    payload: UserUpdate,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> UserOut:
    return service.update_user(
        target_user_id=user_id,
        payload=payload,
        current_user=current_user,
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> Response:
    service.delete_user(target_user_id=user_id, current_user=current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
