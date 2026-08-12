"""Runtime auth configuration loaded from environment variables."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

# Load services/api/.env when present (never commit secrets).
_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(_ENV_PATH)

ALGORITHM = "HS256"
DEFAULT_TOKEN_EXPIRE_MINUTES = 30
DEFAULT_AUTH_DB = Path(__file__).resolve().parents[2] / "data" / "auth.json"


class AuthSettings:
    """Validated auth settings derived from process environment."""

    def __init__(self) -> None:
        secret = os.getenv("SECRET_KEY")
        if not secret:
            raise RuntimeError(
                "SECRET_KEY is not set. Copy .env.example to .env and set a strong secret."
            )
        self.secret_key: str = secret

        raw_expire = os.getenv(
            "ACCESS_TOKEN_EXPIRE_MINUTES", str(DEFAULT_TOKEN_EXPIRE_MINUTES)
        )
        try:
            self.access_token_expire_minutes: int = int(raw_expire)
        except ValueError as exc:
            raise RuntimeError(
                "ACCESS_TOKEN_EXPIRE_MINUTES must be an integer minute count."
            ) from exc

        db_override = os.getenv("AUTH_DB_PATH")
        self.auth_db_path: Path = (
            Path(db_override).expanduser().resolve()
            if db_override
            else DEFAULT_AUTH_DB
        )


@lru_cache(maxsize=1)
def get_settings() -> AuthSettings:
    return AuthSettings()
