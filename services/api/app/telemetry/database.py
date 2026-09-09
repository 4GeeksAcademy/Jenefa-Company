"""Session dependency for the telemetry ingestion pipeline.

Reuses the same SQLModel engine as `app.inventory` (single Supabase Postgres
project); `telemetry_events` is a distinct table registered on the shared
`SQLModel.metadata` so it is created alongside the inventory tables during
the app lifespan's `init_inventory_schema(engine)` call.
"""

from __future__ import annotations

from . import models as _models  # noqa: F401 — register table metadata

from ..inventory.database import get_session

__all__ = ["get_session"]
