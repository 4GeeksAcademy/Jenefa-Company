"""Runtime auth configuration loaded from environment variables."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(_ENV_PATH)

ALGORITHM = "HS256"
DEFAULT_TOKEN_EXPIRE_MINUTES = 30
DEFAULT_PASSWORD_RESET_EXPIRE_MINUTES = 60
DEFAULT_AUTH_DB = Path(__file__).resolve().parents[2] / "data" / "auth.json"
DEFAULT_FRONTEND_BASE_URL = "http://localhost:3001"
DEFAULT_AUTH_DB = Path(__file__).resolve().parents[2] / "data" / "auth.json"


class AuthSettings:
    """Validated auth settings derived from process environment."""

    def __init__(self) -> None:
        secret = os.getenv("SECRET_KEY")
        if not secret:
            raise RuntimeError(
                "SECRET_KEY is not set. Copy .env.example to .env and set a strong secret."
            )
        self.secret_key = str(secret)

        raw_expire = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
        try:
            self.access_token_expire_minutes = (
                DEFAULT_TOKEN_EXPIRE_MINUTES if raw_expire is None else int(raw_expire)
            )
        except ValueError as exc:
            raise RuntimeError(
                "ACCESS_TOKEN_EXPIRE_MINUTES must be an integer minute count."
            ) from exc

        raw_reset_expire = os.getenv("PASSWORD_RESET_EXPIRE_MINUTES")
        try:
            self.password_reset_expire_minutes = (
                DEFAULT_PASSWORD_RESET_EXPIRE_MINUTES
                if raw_reset_expire is None
                else int(raw_reset_expire)
            )
        except ValueError as exc:
            raise RuntimeError(
                "PASSWORD_RESET_EXPIRE_MINUTES must be an integer minute count."
            ) from exc

        db_override = os.getenv("AUTH_DB_PATH")
        self.auth_db_path = (
            Path(db_override).expanduser().resolve()
            if db_override
            else DEFAULT_AUTH_DB
        )

        frontend = os.getenv("FRONTEND_BASE_URL", DEFAULT_FRONTEND_BASE_URL).rstrip("/")
        self.frontend_base_url = frontend

        # Email: Resend or SendGrid — keys only from environment (never hardcoded).
        self.email_provider = (os.getenv("EMAIL_PROVIDER") or "").strip().lower()
        self.resend_api_key = os.getenv("RESEND_API_KEY") or ""
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY") or ""
        self.email_from = os.getenv("EMAIL_FROM") or "HealthCore <onboarding@resend.dev>"


@lru_cache(maxsize=1)
def get_settings() -> AuthSettings:
    return AuthSettings()
