"""HealthCore Business Performance Data Pipeline (Prefect 3).

[MAIN CLI ENTRYPOINT] Root flow: `healthcore_business_performance_pipeline_flow`.
Run standalone: `python data/pipelines/pipeline.py`.
Scheduled cadence + CLI invocation are documented in `PIPELINE_DESIGN.md`.

Data Core Isolation: this module and `data/process/` never import application
routes or frameworks from `services/`. `services/api/app/reporting/` imports
downward from here instead (see specs-implementation.md §2, §6).
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from prefect import flow, get_run_logger, task
from prefect.cache_policies import NO_CACHE
from prefect.states import State
from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    MetaData,
    String,
    Table,
    UniqueConstraint,
    text,
)
from sqlalchemy.engine import Engine
from sqlmodel import Field, Session, SQLModel, create_engine, select

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # data/ -> process/
from process.kpis import compute_executive_kpis  # noqa: E402

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Storage: standalone engine + models, deliberately NOT importing
# services/api/app/inventory|telemetry (data-core isolation rule).
# ---------------------------------------------------------------------------

_DEFAULT_SQLITE = Path(__file__).resolve().parent / "reporting.db"


def _normalize_url(url: str) -> str:
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


def reporting_database_url() -> str:
    explicit = (
        os.getenv("REPORTING_DATABASE_URL")
        or os.getenv("INVENTORY_DATABASE_URL")
        or os.getenv("SUPABASE_DB_URL")
        or os.getenv("DATABASE_URL")
        or ""
    ).strip()
    if explicit:
        return _normalize_url(explicit)
    return f"sqlite:///{_DEFAULT_SQLITE}"


def create_reporting_engine(url: str | None = None) -> Engine:
    resolved = url or reporting_database_url()
    connect_args: dict[str, object] = {}
    if resolved.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(resolved, pool_pre_ping=True, connect_args=connect_args)


# Read-only mirror of `telemetry_events` on its own MetaData instance so this
# module never registers a second `table=True` class for that table name on
# the shared SQLModel.metadata (which would collide when services/reporting/
# imports this module inside the same FastAPI process as app.telemetry).
_extract_metadata = MetaData()
_telemetry_events_table = Table(
    "telemetry_events",
    _extract_metadata,
    Column("id", String, primary_key=True),
    Column("event_type", String),
    Column("timestamp", DateTime(timezone=True)),
    Column("tags", JSON),
)


class ExecutiveKPI(SQLModel, table=True):
    """`reporting.executive_kpis` — one row per (reporting_window_timestamp, clinic_location_id)."""

    __tablename__ = "executive_kpis"
    __table_args__ = (
        UniqueConstraint(
            "reporting_window_timestamp", "clinic_location_id", name="uq_executive_kpis_window_clinic"
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    reporting_window_timestamp: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    clinic_location_id: str
    market_region: str
    network_appointment_volume: int | None = None
    global_no_show_rate: float | None = None
    claims_denial_rate: float | None = None
    revenue_currency: str | None = None
    revenue_net_settled: float | None = None
    patient_satisfaction_score: float | None = None
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class PipelineRunAudit(SQLModel, table=True):
    """5 mandatory audit fields (Phase 3) + a run id, per specs-implementation.md §4."""

    __tablename__ = "pipeline_run_audit"

    id: int | None = Field(default=None, primary_key=True)
    start_time: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    end_time: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    records_processed: int = 0
    status: str = "RUNNING"  # RUNNING | COMPLETED | FAILED
    errors: str | None = None  # JSON-serialized exception traces / validation failures


def init_reporting_schema(engine: Engine) -> None:
    SQLModel.metadata.create_all(engine, tables=[ExecutiveKPI.__table__, PipelineRunAudit.__table__])
    # checkfirst (default) is a no-op against the real Supabase project, where
    # app.telemetry already owns this table; it only bootstraps a fresh local
    # SQLite fallback so `python data/pipelines/pipeline.py` runs standalone.
    _extract_metadata.create_all(engine, tables=[_telemetry_events_table])


# ---------------------------------------------------------------------------
# Phase 2 — Tasks
# ---------------------------------------------------------------------------


@task(
    # Retries absorb transient network drops against the shared Supabase Postgres
    # project; 3 attempts / 15s backoff matches the inventory+telemetry modules'
    # existing operational tolerance for a weekly (non-latency-sensitive) batch job.
    retries=3,
    retry_delay_seconds=15,
    cache_policy=NO_CACHE,  # takes a live Engine handle, which cannot be hashed/serialized
)
def extract_telemetry_source_task(
    engine: Engine, window_start: datetime, window_end: datetime
) -> list[dict[str, Any]]:
    """Fetch the delta boundary window from `telemetry_events` (read-only, never written to).

    Applies the dual-timestamp late-arrival strategy (filters on `timestamp`, the event's own
    occurrence clock) and deduplicates by the envelope's unique `event_id` (stored as `id`),
    keeping only the first row seen per id within the window (PIPELINE_DESIGN.md §5).
    """
    run_logger = get_run_logger()
    with engine.connect() as connection:
        rows = connection.execute(
            select(
                _telemetry_events_table.c.id,
                _telemetry_events_table.c.event_type,
                _telemetry_events_table.c.timestamp,
                _telemetry_events_table.c.tags,
            ).where(
                _telemetry_events_table.c.timestamp >= window_start,
                _telemetry_events_table.c.timestamp < window_end,
            )
        ).mappings().all()

    seen_event_ids: set[str] = set()
    deduplicated: list[dict[str, Any]] = []
    for row in rows:
        event_id = row["id"]
        if event_id in seen_event_ids:
            continue
        seen_event_ids.add(event_id)
        deduplicated.append(
            {
                "event_id": event_id,
                "event_type": row["event_type"],
                "timestamp": row["timestamp"],
                "tags": row["tags"] or {},
            }
        )
    run_logger.info(
        "extracted %d telemetry rows (%d duplicates dropped) for window %s -> %s",
        len(deduplicated),
        len(rows) - len(deduplicated),
        window_start.isoformat(),
        window_end.isoformat(),
    )
    return deduplicated


def _kpi_cache_key(_context: Any, parameters: dict[str, Any]) -> str:
    # Cache key = the exact extracted row set (order-independent) so identical
    # re-runs over the same window within the TTL skip recomputation entirely.
    rows = parameters["rows"]
    return json.dumps(
        sorted(r["event_id"] for r in rows),
        sort_keys=True,
    )


@task(
    cache_key_fn=_kpi_cache_key,
    cache_expiration=timedelta(hours=1),  # matches weekly cadence: safe to reuse within a 1h retry window
)
def transform_business_kpis_task(
    rows: list[dict[str, Any]], window_start: datetime
) -> list[dict[str, Any]]:
    """Compile HealthCore executive metrics from the extracted telemetry rows."""
    run_logger = get_run_logger()
    kpi_rows = compute_executive_kpis(rows)
    for kpi_row in kpi_rows:
        kpi_row["reporting_window_timestamp"] = window_start
    run_logger.info("transformed %d executive KPI rows", len(kpi_rows))
    return kpi_rows


@task(
    retries=3,
    retry_delay_seconds=15,  # same transient-connectivity justification as extraction
    cache_policy=NO_CACHE,  # takes a live Engine handle, which cannot be hashed/serialized
)
def load_reporting_destination_task(engine: Engine, kpi_rows: list[dict[str, Any]]) -> int:
    """Idempotent upsert into `reporting.executive_kpis` keyed on the composite unique constraint.

    Re-running this task for the same window/clinic never duplicates or double-counts rows:
    an existing (reporting_window_timestamp, clinic_location_id) pair is updated in place.
    """
    if not kpi_rows:
        return 0

    dialect = engine.dialect.name
    with Session(engine) as session:
        for kpi_row in kpi_rows:
            existing = session.exec(
                select(ExecutiveKPI).where(
                    ExecutiveKPI.reporting_window_timestamp == kpi_row["reporting_window_timestamp"],
                    ExecutiveKPI.clinic_location_id == kpi_row["clinic_location_id"],
                )
            ).first()
            if existing is None:
                session.add(ExecutiveKPI(**kpi_row))
            else:
                for field, value in kpi_row.items():
                    setattr(existing, field, value)
                existing.updated_at = datetime.now(timezone.utc)
        session.commit()
    del dialect  # native ON CONFLICT is a straightforward upgrade path on Postgres; SQLite-safe today
    return len(kpi_rows)


@task(cache_policy=NO_CACHE)  # takes a live Engine handle, which cannot be hashed/serialized
def evaluate_pipeline_output_task(engine: Engine, window_start: datetime, kpi_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Optional/non-critical: writes a sanity-check snapshot to `data/eval/`. Never blocks the load path."""
    del engine
    eval_dir = Path(__file__).resolve().parents[1] / "eval"
    eval_dir.mkdir(parents=True, exist_ok=True)
    snapshot = {
        "window_start": window_start.isoformat(),
        "clinic_count": len(kpi_rows),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    (eval_dir / "latest_run_eval.json").write_text(json.dumps(snapshot, indent=2))
    return snapshot


# ---------------------------------------------------------------------------
# Phase 3 — Audit trail
# ---------------------------------------------------------------------------


def _record_audit_start(engine: Engine, start_time: datetime) -> int:
    with Session(engine) as session:
        audit = PipelineRunAudit(start_time=start_time, status="RUNNING")
        session.add(audit)
        session.commit()
        session.refresh(audit)
        return audit.id  # type: ignore[return-value]


def _record_audit_end(
    engine: Engine, audit_id: int, *, records_processed: int, status: str, errors: str | None
) -> None:
    with Session(engine) as session:
        audit = session.get(PipelineRunAudit, audit_id)
        if audit is None:
            return
        audit.end_time = datetime.now(timezone.utc)
        audit.records_processed = records_processed
        audit.status = status
        audit.errors = errors
        session.add(audit)
        session.commit()


def get_latest_manifest_status(engine: Engine | None = None) -> dict[str, Any] | None:
    """Returns the 5 core audit fields from the most recent pipeline run (services/reporting/status)."""
    owns_engine = engine is None
    engine = engine or create_reporting_engine()
    try:
        init_reporting_schema(engine)
        with Session(engine) as session:
            latest = session.exec(
                select(PipelineRunAudit).order_by(PipelineRunAudit.start_time.desc())
            ).first()
        if latest is None:
            return None
        return {
            "status": latest.status,
            "start_time": latest.start_time.isoformat(),
            "end_time": latest.end_time.isoformat() if latest.end_time else None,
            "records_processed": latest.records_processed,
            "errors": latest.errors,
        }
    finally:
        if owns_engine:
            engine.dispose()


def fetch_executive_metrics(engine: Engine | None = None) -> list[dict[str, Any]]:
    """Reads `reporting.executive_kpis` for the API's `GET /services/reporting/kpis`."""
    owns_engine = engine is None
    engine = engine or create_reporting_engine()
    try:
        init_reporting_schema(engine)
        with Session(engine) as session:
            rows = session.exec(select(ExecutiveKPI)).all()
        return [
            {
                "reporting_window_timestamp": row.reporting_window_timestamp.isoformat(),
                "clinic_location_id": row.clinic_location_id,
                "market_region": row.market_region,
                "network_appointment_volume": row.network_appointment_volume,
                "global_no_show_rate": row.global_no_show_rate,
                "claims_denial_rate": row.claims_denial_rate,
                "revenue_currency": row.revenue_currency,
                "revenue_net_settled": row.revenue_net_settled,
                "patient_satisfaction_score": row.patient_satisfaction_score,
            }
            for row in rows
        ]
    finally:
        if owns_engine:
            engine.dispose()


# ---------------------------------------------------------------------------
# Phase 1 — Root orchestrator flow
# ---------------------------------------------------------------------------


def _week_window(reference: datetime | None = None) -> tuple[datetime, datetime]:
    reference = reference or datetime.now(timezone.utc)
    window_end = reference.replace(hour=0, minute=0, second=0, microsecond=0)
    window_start = window_end - timedelta(days=7)
    return window_start, window_end


@flow(name="healthcore_business_performance_pipeline_flow")
def healthcore_business_performance_pipeline_flow(
    window_start: datetime | None = None,
    window_end: datetime | None = None,
    database_url: str | None = None,
) -> dict[str, Any]:
    run_logger = get_run_logger()
    engine = create_reporting_engine(database_url)
    init_reporting_schema(engine)

    default_start, default_end = _week_window()
    window_start = window_start or default_start
    window_end = window_end or default_end

    start_time = datetime.now(timezone.utc)
    audit_id = _record_audit_start(engine, start_time)

    try:
        extracted_rows = extract_telemetry_source_task(engine, window_start, window_end)
        kpi_rows = transform_business_kpis_task(extracted_rows, window_start)
        records_loaded = load_reporting_destination_task(engine, kpi_rows)

        # Non-critical evaluation step: state-checked so a failure here never
        # blocks the core extract -> transform -> load path from completing.
        eval_state: State = evaluate_pipeline_output_task(
            engine, window_start, kpi_rows, return_state=True
        )
        if eval_state.is_failed():
            run_logger.warning("optional evaluation snapshot task failed: %s", eval_state.message)
        else:
            run_logger.info("evaluation snapshot written to data/eval/latest_run_eval.json")

        _record_audit_end(
            engine, audit_id, records_processed=records_loaded, status="COMPLETED", errors=None
        )
        return {
            "status": "COMPLETED",
            "records_processed": records_loaded,
            "window_start": window_start.isoformat(),
            "window_end": window_end.isoformat(),
        }
    except Exception as exc:  # noqa: BLE001 — must record failure state before re-raising
        _record_audit_end(
            engine,
            audit_id,
            records_processed=0,
            status="FAILED",
            errors=json.dumps({"error": str(exc)}),
        )
        raise
    finally:
        engine.dispose()


if __name__ == "__main__":
    result = healthcore_business_performance_pipeline_flow()
    print(json.dumps(result, indent=2))
