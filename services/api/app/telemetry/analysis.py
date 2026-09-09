"""Pure Pandas analysis pipeline for `GET /telemetry/report` (Phase 1).

Every function follows the mandated formula order — load (SQL) -> refine
(Pandas) -> convert types -> group -> aggregate — and is side-effect free:
calling a function twice with the same session state and window always
yields the same result. Functions never resolve their own default window;
the caller (router) always supplies a resolved `start_date`/`end_date`.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
from sqlmodel import Session, select

from .models import TelemetryEventRecord


def _load_window(session: Session, start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """Load raw rows for the window into a DataFrame (columns: event_type, timestamp, tags)."""
    statement = select(TelemetryEventRecord).where(
        TelemetryEventRecord.timestamp >= start_date,
        TelemetryEventRecord.timestamp <= end_date,
    )
    rows = session.exec(statement).all()
    records = [
        {"event_type": row.event_type, "timestamp": row.timestamp, "tags": row.tags or {}}
        for row in rows
    ]
    return pd.DataFrame(records, columns=["event_type", "timestamp", "tags"])


def events_per_day(session: Session, start_date: datetime, end_date: datetime) -> list[dict[str, Any]]:
    """Volume Metric over Time Vector: total rows grouped by calendar date."""
    df = _load_window(session, start_date, end_date)
    if df.empty:
        return []
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df["date"] = df["timestamp"].dt.date.astype(str)
    grouped = df.groupby("date").size().reset_index(name="event_count")
    return grouped.to_dict(orient="records")


def _is_error_flag(tags: dict[str, Any]) -> bool:
    # Explicit tags.is_error wins; otherwise a non-healthy system_health_checked
    # status_state is the only failure signal in the current event catalogue.
    if "is_error" in tags:
        return bool(tags["is_error"])
    return tags.get("status_state") not in (None, "healthy")


def error_rate_by_type(session: Session, start_date: datetime, end_date: datetime) -> list[dict[str, Any]]:
    """Failure Profiling Vectors: share of error rows grouped by event_type."""
    df = _load_window(session, start_date, end_date)
    if df.empty:
        return []
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df["is_error"] = df["tags"].apply(_is_error_flag)
    grouped = df.groupby("event_type")["is_error"].mean().reset_index(name="error_rate")
    grouped["error_rate"] = grouped["error_rate"].round(4)
    return grouped.to_dict(orient="records")


def average_latency_by_day(session: Session, start_date: datetime, end_date: datetime) -> list[dict[str, Any]]:
    """Cross-Border System Latency Analysis: mean tags.latency_ms grouped by date."""
    df = _load_window(session, start_date, end_date)
    if df.empty:
        return []
    df["latency_ms"] = df["tags"].apply(lambda tags: tags.get("latency_ms", tags.get("latency")))
    df = df.dropna(subset=["latency_ms"])
    if df.empty:
        return []
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df["date"] = df["timestamp"].dt.date.astype(str)
    grouped = df.groupby("date")["latency_ms"].mean().reset_index(name="avg_latency_ms")
    grouped["avg_latency_ms"] = grouped["avg_latency_ms"].round(2)
    return grouped.to_dict(orient="records")
