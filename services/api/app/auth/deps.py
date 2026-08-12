"""FastAPI dependencies for bearer-token authentication."""

from __future__ import annotations

from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from . import database as db
from .security import JWTError, decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict[str, Any]:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_uuid = payload.get("sub")
        if not user_uuid or not isinstance(user_uuid, str):
            raise credentials_exception
    except JWTError as exc:
        raise credentials_exception from exc

    user = db.get_user_by_id(user_uuid)
    if user is None:
        raise credentials_exception
    if not user.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_owner_or_admin(
    *,
    current_user: dict[str, Any],
    target_user_id: str,
    detail: str = "Not enough permissions",
) -> None:
    if current_user.get("role") == "admin":
        return
    if current_user.get("id") == target_user_id:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
