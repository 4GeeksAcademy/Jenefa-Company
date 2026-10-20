"""Metadata-only history records (no row-level or message content, per PHI policy)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import Column, DateTime
from sqlmodel import Field, Session, SQLModel, delete

RETENTION_DAYS = 10


def _now() -> datetime:
    return datetime.now(timezone.utc)


class IncidentAnalysisRun(SQLModel, table=True):
    __tablename__ = "incident_analysis_runs"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    source_file: str = Field(max_length=255)
    total_records: int = 0
    valid_records: int = 0
    invalid_records: int = 0
    created_at: datetime = Field(
        default_factory=_now,
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
    )


def purge_expired(session: Session) -> None:
    cutoff = _now() - timedelta(days=RETENTION_DAYS)
    session.exec(delete(IncidentAnalysisRun).where(IncidentAnalysisRun.created_at < cutoff))
