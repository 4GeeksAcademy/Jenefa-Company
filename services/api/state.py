"""SQLite persistence for HealthCore incident tracking."""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from incidents import empty_summary

_DB_PATH = Path(
    os.environ.get(
        "INCIDENTS_DB_PATH",
        str(Path(__file__).resolve().parent / "incidents.db"),
    )
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                category TEXT NOT NULL,
                status TEXT NOT NULL,
                origin TEXT NOT NULL,
                branch TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                source_key TEXT UNIQUE
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_incidents_category ON incidents(category)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_incidents_origin ON incidents(origin)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_incidents_branch ON incidents(branch)"
        )
        conn.commit()


def _to_public(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "category": row["category"],
        "status": row["status"],
        "origin": row["origin"],
        "branch": row["branch"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def create_incident(
    payload: dict[str, str],
    *,
    created_at: str | None = None,
    source_key: str | None = None,
) -> dict[str, Any]:
    now = _utc_now()
    created = created_at or now

    with _connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO incidents
            (title, description, category, status, origin, branch, created_at, updated_at, source_key)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload["title"],
                payload["description"],
                payload["category"],
                payload["status"],
                payload["origin"],
                payload["branch"],
                created,
                now,
                source_key,
            ),
        )
        incident_id = int(cursor.lastrowid)
        row = conn.execute(
            "SELECT * FROM incidents WHERE id = ?",
            (incident_id,),
        ).fetchone()
        conn.commit()

    if row is None:
        raise RuntimeError("Failed to read inserted incident.")
    return _to_public(row)


def create_incident_if_missing(
    payload: dict[str, str],
    *,
    source_key: str,
    created_at: str | None = None,
) -> bool:
    now = _utc_now()
    created = created_at or now

    with _connect() as conn:
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO incidents
            (title, description, category, status, origin, branch, created_at, updated_at, source_key)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload["title"],
                payload["description"],
                payload["category"],
                payload["status"],
                payload["origin"],
                payload["branch"],
                created,
                now,
                source_key,
            ),
        )
        conn.commit()
        return cursor.rowcount > 0


def list_incidents(filters: dict[str, str | None]) -> list[dict[str, Any]]:
    sql = "SELECT * FROM incidents"
    where: list[str] = []
    params: list[str] = []
    for field in ("status", "origin", "branch", "category"):
        value = filters.get(field)
        if value:
            where.append(f"{field} = ?")
            params.append(value)

    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY created_at DESC, id DESC"

    with _connect() as conn:
        rows = conn.execute(sql, tuple(params)).fetchall()
    return [_to_public(row) for row in rows]


def get_incident(incident_id: int) -> dict[str, Any] | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM incidents WHERE id = ?",
            (incident_id,),
        ).fetchone()
    if row is None:
        return None
    return _to_public(row)


def update_incident_status(incident_id: int, next_status: str) -> dict[str, Any] | None:
    now = _utc_now()
    with _connect() as conn:
        conn.execute(
            "UPDATE incidents SET status = ?, updated_at = ? WHERE id = ?",
            (next_status, now, incident_id),
        )
        row = conn.execute(
            "SELECT * FROM incidents WHERE id = ?",
            (incident_id,),
        ).fetchone()
        conn.commit()

    if row is None:
        return None
    return _to_public(row)


def summary() -> dict[str, dict[str, int]]:
    totals = empty_summary()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT status, category, origin, branch FROM incidents"
        ).fetchall()

    for row in rows:
        status = row["status"]
        category = row["category"]
        origin = row["origin"]
        branch = row["branch"]
        if status in totals["status"]:
            totals["status"][status] += 1
        if category in totals["category"]:
            totals["category"][category] += 1
        if origin in totals["origin"]:
            totals["origin"][origin] += 1
        if branch in totals["branch"]:
            totals["branch"][branch] += 1
    return totals
