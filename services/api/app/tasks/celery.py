"""Celery application and HealthCore background tasks.

Lives inside the ``app`` package so the FastAPI process and the worker
process resolve the SQLModel metadata (and every other module) under one
identical import path.
"""

from __future__ import annotations

import logging
import os
import time
import traceback
from datetime import datetime, timezone
from typing import Any

from celery import Celery, Task
from sqlmodel import Field, Session, SQLModel

from app.inventory.database import create_inventory_engine, inventory_database_url
from app.reporting.service import trigger_batch_execution

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

app = Celery("healthcore", broker=REDIS_URL, backend=REDIS_URL)
app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
    result_expires=86400,
    worker_send_task_events=True,
    task_send_sent_event=True,
)


class AsyncTaskFailure(SQLModel, table=True):
    """Auditable dead-letter record for tasks that exhausted their retries."""

    __tablename__ = "async_task_failures"

    id: int | None = Field(default=None, primary_key=True)
    task_id: str = Field(index=True, max_length=255)
    attempt_number: int
    error: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def _record_terminal_failure(task_id: str, attempt_number: int, error: str, database_url: str | None) -> None:
    engine = create_inventory_engine(database_url or inventory_database_url())
    try:
        SQLModel.metadata.create_all(engine, tables=[AsyncTaskFailure.__table__])
        with Session(engine) as session:
            session.add(
                AsyncTaskFailure(
                    task_id=task_id,
                    attempt_number=attempt_number,
                    error=error,
                )
            )
            session.commit()
    finally:
        engine.dispose()


class AuditedTask(Task):
    """Common retry policy and structured execution logging."""

    autoretry_for: tuple[type[Exception], ...] = ()
    max_retries = 3


@app.task(bind=True, base=AuditedTask, name="healthcore.reporting.generate", max_retries=3)
def generate_reporting_task(self: AuditedTask, database_url: str | None = None) -> dict[str, Any]:
    """Generate executive reporting from a database reference, never a raw data blob."""
    started = time.perf_counter()
    attempt = self.request.retries + 1
    task_id = self.request.id or "unknown"
    engine = create_inventory_engine(database_url or inventory_database_url())
    try:
        result = trigger_batch_execution(engine)
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        logger.info(
            "async_task_completed task_id=%s attempt_number=%s status=success duration_ms=%s",
            task_id,
            attempt,
            duration_ms,
        )
        return result
    except Exception as exc:
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        error = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        if self.request.retries >= self.max_retries:
            _record_terminal_failure(task_id, attempt, error, database_url)
            logger.error(
                "async_task_failed task_id=%s attempt_number=%s status=failure duration_ms=%s error=%s",
                task_id,
                attempt,
                duration_ms,
                error,
            )
            raise
        countdown = 2 ** attempt
        logger.warning(
            "async_task_retry task_id=%s attempt_number=%s status=retry duration_ms=%s countdown=%s error=%s",
            task_id,
            attempt,
            duration_ms,
            countdown,
            error,
        )
        raise self.retry(exc=exc, countdown=countdown)
    finally:
        engine.dispose()


__all__ = ["app", "AsyncTaskFailure", "generate_reporting_task"]
