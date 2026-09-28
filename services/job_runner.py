"""Database-backed lifecycle tracking for unattended background jobs.

This module deliberately contains no FastAPI imports.  It is safe to use from
an OS-scheduled process as well as from application-side maintenance tools.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Literal

from sqlalchemy import Index
from sqlmodel import Field, Session, SQLModel, select

from app.inventory.database import create_inventory_engine, inventory_database_url
from app.telemetry import models as _telemetry_models  # noqa: F401 - register metadata

JobStatus = Literal["pending", "processing", "completed", "failed"]
VALID_STATUSES = frozenset({"pending", "processing", "completed", "failed"})


class JobRunRecord(SQLModel, table=True):
    """One execution attempt of a scheduled job."""

    __tablename__ = "job_runs"
    __table_args__ = (Index("idx_job_runs_name_date", "job_name", "target_date"),)

    id: int | None = Field(default=None, primary_key=True)
    job_name: str = Field(max_length=255, nullable=False)
    target_date: date = Field(nullable=False)
    status: str = Field(default="pending", max_length=50, nullable=False)
    started_at: datetime | None = Field(default=None)
    finished_at: datetime | None = Field(default=None)
    error_message: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)


def _engine(engine=None):
    return engine or create_inventory_engine(inventory_database_url())


def _ensure_schema(engine) -> None:
    # Importing the telemetry model above keeps this table in the same
    # SQLModel metadata/schema layer as telemetry_events and inventory tables.
    SQLModel.metadata.create_all(engine, tables=[JobRunRecord.__table__])


def create_job_run(job_name: str, target_date: date, *, engine=None) -> JobRunRecord:
    """Create and persist a new execution in the ``pending`` state."""
    db = _engine(engine)
    _ensure_schema(db)
    owns_engine = engine is None
    try:
        with Session(db) as session:
            record = JobRunRecord(job_name=job_name, target_date=target_date, status="pending")
            session.add(record)
            session.commit()
            session.refresh(record)
            return record
    finally:
        if owns_engine:
            db.dispose()


def has_processing_lock(job_name: str, *, engine=None) -> bool:
    """Return whether any execution of ``job_name`` currently owns the lock."""
    db = _engine(engine)
    _ensure_schema(db)
    owns_engine = engine is None
    try:
        with Session(db) as session:
            return session.exec(
                select(JobRunRecord.id).where(
                    JobRunRecord.job_name == job_name,
                    JobRunRecord.status == "processing",
                )
            ).first() is not None
    finally:
        if owns_engine:
            db.dispose()


def has_completed_for_date(job_name: str, target_date: date, *, engine=None) -> bool:
    """Return whether this job already completed successfully for a date."""
    db = _engine(engine)
    _ensure_schema(db)
    owns_engine = engine is None
    try:
        with Session(db) as session:
            return session.exec(
                select(JobRunRecord.id).where(
                    JobRunRecord.job_name == job_name,
                    JobRunRecord.target_date == target_date,
                    JobRunRecord.status == "completed",
                )
            ).first() is not None
    finally:
        if owns_engine:
            db.dispose()


def update_job_status(
    job_id: int,
    status: JobStatus | str,
    error_message: str | None = None,
    *,
    engine=None,
) -> JobRunRecord:
    """Persist a lifecycle transition and its corresponding timestamps."""
    if status not in VALID_STATUSES:
        raise ValueError(f"Unsupported job status: {status}")

    db = _engine(engine)
    _ensure_schema(db)
    owns_engine = engine is None
    try:
        with Session(db) as session:
            record = session.get(JobRunRecord, job_id)
            if record is None:
                raise ValueError(f"Job run {job_id} does not exist")
            record.status = status
            if status == "processing" and record.started_at is None:
                record.started_at = datetime.now(timezone.utc)
            if status in {"completed", "failed"}:
                record.finished_at = datetime.now(timezone.utc)
                record.error_message = error_message
            elif error_message is not None:
                record.error_message = error_message
            session.add(record)
            session.commit()
            session.refresh(record)
            return record
    finally:
        if owns_engine:
            db.dispose()


__all__ = [
    "JobRunRecord",
    "create_job_run",
    "has_processing_lock",
    "has_completed_for_date",
    "update_job_status",
]
