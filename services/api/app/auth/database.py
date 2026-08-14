"""TinyDB connection for User and Profile collections only."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from tinydb import Query, TinyDB
from tinydb.storages import Storage
from tinydb.table import Table

from .config import get_settings

_db: TinyDB | None = None
USERS_TABLE = "users"
PROFILES_TABLE = "profiles"


class AtomicJSONStorage(Storage):
    """JSON storage that writes via temp file + replace to avoid partial corruption."""

    def __init__(self, path: str | Path, parse_float: type[float] | None = None) -> None:
        super().__init__()
        self.path = Path(path)
        self._parse_float = parse_float or float
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)

    def read(self) -> dict[str, Any] | None:
        if not self.path.exists() or self.path.stat().st_size == 0:
            return None
        raw = self.path.read_text(encoding="utf-8")
        try:
            data = json.loads(raw, parse_float=self._parse_float)
        except json.JSONDecodeError:
            repaired = _scrub_invalid_control_chars(raw)
            data = json.loads(repaired, parse_float=self._parse_float)
            self.write(data)
        return data

    def write(self, data: dict[str, Any] | None) -> None:
        serialized = json.dumps(data if data is not None else {})
        fd, tmp_name = tempfile.mkstemp(prefix=".", suffix=".tmp", dir=str(self.path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(serialized)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, self.path)
        except Exception:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise

    def close(self) -> None:
        return None


def _scrub_invalid_control_chars(raw: str) -> str:
    """Replace raw ASCII controls (except tab) that break JSON string literals."""
    return "".join(ch if (ch == "\t" or ord(ch) >= 32) else " " for ch in raw)


def get_db() -> TinyDB:
    global _db
    if _db is None:
        path = get_settings().auth_db_path
        path.parent.mkdir(parents=True, exist_ok=True)
        _db = TinyDB(path, storage=AtomicJSONStorage)
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


def insert_user(document: dict[str, Any]) -> int:
    return users_table().insert(document)


def update_user(user_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    User = Query()
    users_table().update(updates, User.id == user_id)
    return get_user_by_id(user_id)


def delete_user(user_id: str) -> bool:
    User = Query()
    removed = users_table().remove(User.id == user_id)
    return bool(removed)


def get_profile_by_user_id(user_id: str) -> dict[str, Any] | None:
    Profile = Query()
    return profiles_table().get(Profile.user_id == user_id)


def insert_profile(document: dict[str, Any]) -> int:
    return profiles_table().insert(document)


def update_profile(user_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    Profile = Query()
    profiles_table().update(updates, Profile.user_id == user_id)
    return get_profile_by_user_id(user_id)


def delete_profile_by_user_id(user_id: str) -> bool:
    Profile = Query()
    removed = profiles_table().remove(Profile.user_id == user_id)
    return bool(removed)
