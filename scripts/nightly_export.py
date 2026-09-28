"""OS-scheduled nightly telemetry archive and pipeline orchestrator."""

from __future__ import annotations

import csv
import logging
import os
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from sqlmodel import Session, select

REPO_ROOT = Path(__file__).resolve().parents[1]
API_ROOT = REPO_ROOT / "services" / "api"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.inventory.database import create_inventory_engine, inventory_database_url  # noqa: E402
from app.telemetry.models import TelemetryEventRecord  # noqa: E402
from services.job_runner import (  # noqa: E402
    create_job_run,
    has_completed_for_date,
    has_processing_lock,
    update_job_status,
)

JOB_NAME = "nightly_export"
RAW_DIR = REPO_ROOT / "data" / "raw"
logger = logging.getLogger(JOB_NAME)


class JobLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        return f"[{timestamp}] [{JOB_NAME}] [{record.levelname}] {record.getMessage()}"


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JobLogFormatter())
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


def resolve_target_date() -> date:
    raw = os.getenv("TARGET_DATE")
    if raw:
        try:
            return date.fromisoformat(raw)
        except ValueError as exc:
            raise ValueError("TARGET_DATE must use YYYY-MM-DD format") from exc
    return datetime.now(timezone.utc).date() - timedelta(days=1)


def export_telemetry(target_date: date, engine) -> tuple[Path, int]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    destination = RAW_DIR / f"telemetry_{target_date.isoformat()}.csv"
    if destination.exists():
        with destination.open(newline="", encoding="utf-8") as stream:
            return destination, max(sum(1 for _ in csv.reader(stream)) - 1, 0)

    with Session(engine) as session:
        rows = session.exec(
            select(TelemetryEventRecord)
            .where(TelemetryEventRecord.timestamp >= datetime.combine(target_date, datetime.min.time(), tzinfo=timezone.utc))
            .where(TelemetryEventRecord.timestamp < datetime.combine(target_date + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc))
            .order_by(TelemetryEventRecord.timestamp)
        ).all()

    with destination.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["id", "event_type", "timestamp", "service", "tags", "user_id", "session_id", "environment"])
        writer.writeheader()
        for row in rows:
            writer.writerow({"id": row.id, "event_type": row.event_type, "timestamp": row.timestamp.isoformat(), "service": row.service, "tags": row.tags, "user_id": row.user_id, "session_id": row.session_id, "environment": row.environment})
    return destination, len(rows)


def run() -> int:
    configure_logging()
    target_date = resolve_target_date()
    logger.info("Starting execution for target_date: %s.", target_date)

    engine = create_inventory_engine(inventory_database_url())
    try:
        if has_processing_lock(JOB_NAME, engine=engine):
            logger.warning("Execution locked by an active process. Aborting silently.")
            return 0
        if has_completed_for_date(JOB_NAME, target_date, engine=engine):
            logger.info("Target date %s already processed. Skipping duplicate execution.", target_date)
            return 0

        record = create_job_run(JOB_NAME, target_date, engine=engine)
        update_job_status(record.id, "processing", engine=engine)
        try:
            path, count = export_telemetry(target_date, engine)
            logger.info("Export complete. %s rows written to %s.", count, path.relative_to(REPO_ROOT))
            subprocess.run(
    [sys.executable, "-m", "data.pipelines.pipeline"],
    cwd=REPO_ROOT,
    check=True,
)

            update_job_status(record.id, "completed", engine=engine)
            logger.info("Execution completed successfully.")
            return 0
        except Exception as exc:
            update_job_status(record.id, "failed", str(exc), engine=engine)
            logger.exception("Subprocess failed. Status updated to FAILED. Trace: %s", exc)
            raise
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(run())
