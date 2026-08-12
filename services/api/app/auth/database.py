"""TinyDB connection for User and Profile collections only."""

from __future__ import annotations

from typing import Any

from tinydb import Query, TinyDB
from tinydb.table import Table

from .config import get_settings

_db: TinyDB | None = None

USERS_TABLE = "users"
PROFILES_TABLE = "profiles"


def get_db() -> TinyDB:
    global _db
    if _db is None:
        path = get_settings().auth_db_path
        path.parent.mkdir(parents=True, exist_ok=True)
        _db = TinyDB(path)
    return _db


def users_table() -> Table:
    return get_db().table(USERS_TABLE)


def profiles_table() -> Table:
    return get_db().table(PROFILES_TABLE)


def close_db() -> None:
    global _db
    if _db is not None:
        _db.close()
        _db = None


def get_user_by_id(user_id: str) -> dict[str, Any] | None:
    User = Query()
    return users_table().get(User.id == user_id)


def get_user_by_email(email: str) -> dict[str, Any] | None:
    User = Query()
    return users_table().get(User.email == email.lower())


def list_users() -> list[dict[str, Any]]:
    return list(users_table().all())


def insert_user(document: dict[str, Any]) -> dict[str, Any]:
    users_table().insert(document)
    return document


def update_user(user_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    User = Query()
    if not users_table().update(updates, User.id == user_id):
        return None
    return get_user_by_id(user_id)


def delete_user(user_id: str) -> bool:
    User = Query()
    removed = users_table().remove(User.id == user_id)
    return bool(removed)


def get_profile_by_user_id(user_id: str) -> dict[str, Any] | None:
    Profile = Query()
    return profiles_table().get(Profile.user_id == user_id)


def insert_profile(document: dict[str, Any]) -> dict[str, Any]:
    profiles_table().insert(document)
    return document


def update_profile(user_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    Profile = Query()
    if not profiles_table().update(updates, Profile.user_id == user_id):
        return None
    return get_profile_by_user_id(user_id)


def delete_profile_by_user_id(user_id: str) -> bool:
    Profile = Query()
    removed = profiles_table().remove(Profile.user_id == user_id)
    return bool(removed)
