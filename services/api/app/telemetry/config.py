"""Runtime telemetry configuration loaded from environment variables."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(_ENV_PATH)

DEFAULT_TELEMETRY_ENDPOINT = "/telemetry/events"


def get_telemetry_endpoint() -> str:
    """Return the configured ingestion route, read from `TELEMETRY_ENDPOINT`.

    Declared explicitly from day one (Phase 1) so downstream clients and
    infra config anchor to a single source of truth instead of a hardcoded path.
    """
    return os.getenv("TELEMETRY_ENDPOINT", DEFAULT_TELEMETRY_ENDPOINT)
