"""Celery orchestration entry point (``services/celery_app.py``).

Thin bootstrap that makes ``services/api`` importable, then re-exports the
real application from ``app.tasks.celery`` so the worker and the FastAPI
process always share one module identity (and one SQLModel metadata).
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent

# The worker is its own OS process: it must see the same environment as the
# API (DB_URL, REDIS_URL, ...) or task payloads and DLQ writes resolve to a
# different database than the one the API validated against.
try:
    from dotenv import load_dotenv

    load_dotenv(_REPO_ROOT / ".env")
except ImportError:  # pragma: no cover - dotenv ships with the API deps
    pass

_API_ROOT = Path(__file__).resolve().parent / "api"
if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))

from app.tasks.celery import (  # noqa: E402,F401
    AsyncTaskFailure,
    app,
    generate_reporting_task,
)

__all__ = ["app", "AsyncTaskFailure", "generate_reporting_task"]
