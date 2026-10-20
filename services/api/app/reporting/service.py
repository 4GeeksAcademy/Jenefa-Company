"""Reporting delivery service: delegates all ETL behavior to data/pipelines."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from sqlalchemy.engine import Engine

# The reporting adapter is the only application layer allowed to import the
# standalone data-core pipeline from the monorepo root.
_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from data.pipelines.pipeline import (
    get_latest_manifest_status as _get_latest_manifest_status,
    healthcore_business_performance_pipeline_flow,
)

from data.pipelines.pipeline import ExecutiveKPI
from sqlmodel import Session, select


def get_latest_manifest_status(engine: Engine | None) -> dict[str, Any] | None:
    return _get_latest_manifest_status(engine)


def fetch_executive_metrics(engine: Engine | None) -> list[dict[str, Any]]:
    """Return the persisted KPI rows produced by the reporting pipeline."""
    if engine is None:
        raise RuntimeError("Reporting database is not initialized")
    with Session(engine) as session:
        rows = session.exec(
            select(ExecutiveKPI).order_by(ExecutiveKPI.reporting_window_timestamp.desc())
        ).all()
    return [row.model_dump(mode="json") for row in rows]


def trigger_batch_execution(engine: Engine | None) -> dict[str, Any]:
    """Run the same flow used by the CLI against the application's database."""
    database_url = str(engine.url) if engine is not None else None
    return healthcore_business_performance_pipeline_flow(database_url=database_url)
