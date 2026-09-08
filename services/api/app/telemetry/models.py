"""SQLModel definition for the immutable `telemetry_events` audit ledger (Supabase Postgres).

Write-only table: no update/delete code paths exist anywhere in this module,
per the HIPAA/UK GDPR audit-trail requirement in specs-storageTelemetry.md.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import Column, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON
from sqlmodel import Field, SQLModel


class TelemetryEventRecord(SQLModel, table=True):
    __tablename__ = "telemetry_events"
    __table_args__ = (
        Index("idx_telemetry_events_timestamp", "timestamp"),
        Index("idx_telemetry_events_type", "event_type"),
        Index("idx_telemetry_events_tags", "tags", postgresql_using="gin"),
    )

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    event_type: str
    timestamp: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    service: str
    tags: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON().with_variant(JSONB, "postgresql"), nullable=False),
    )
    user_id: str | None = Field(default=None)
    session_id: str | None = Field(default=None)
    environment: str | None = Field(default=None)
