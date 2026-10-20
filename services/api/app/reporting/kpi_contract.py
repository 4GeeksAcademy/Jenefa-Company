"""API-owned executive KPI aggregation contract.

Telemetry events map to KPI cards using these rules:
- Volume: count of appointment_booked.
- No-show rate: count of appointment_noshow_predicted / total booked.
- Denial rate: count of billing_claim_compiled flagged with errors / total compiled.
- Revenue: sum of net_settled_amount in revenue_stream_reconciled.

Telemetry rows carry no user_id or session_id, so no PHI reaches this layer.
"""

from __future__ import annotations

import ast
import json
from collections import defaultdict
from datetime import datetime
from typing import Any
from sqlalchemy import text

from .schemas import ExecutiveKPIResponse

NETWORK_LOCATION = "NETWORK"
GLOBAL_REGION = "GLOBAL"

def load_telemetry_events(engine: Any | None) -> list[dict[str, Any]]:
    """Return raw telemetry events from the live reporting database."""
    if engine is None:
        raise RuntimeError("Reporting database is not initialized")
    query = text("""
            SELECT id, event_type, timestamp, service, tags 
            FROM telemetry_events 
            ORDER BY timestamp DESC
        """)
    with engine.connect() as connection:
        return [dict(row._mapping) for row in connection.execute(query)]


def _tags(event: dict[str, Any]) -> dict[str, Any]:
    tags = event.get("tags") or {}
    if isinstance(tags, dict):
        return tags
    if isinstance(tags, str):
        try:
            tags = json.loads(tags)
        except Exception:
            try:
                tags = ast.literal_eval(tags)
            except Exception:
                print("CRITICAL ERROR: Unable to parse telemetry tags")
                tags = {}
    return tags if isinstance(tags, dict) else {}


def _is_error_flagged(tags: dict[str, Any]) -> bool:
    return bool(tags.get("error")) or tags.get("status") == "error"


def _rate(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 4) if denominator else None


def compute_executive_kpis(events: list[dict[str, Any]]) -> list[ExecutiveKPIResponse]:
    """Aggregate telemetry events into one network KPI row per reporting day."""
    buckets: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "booked": 0,
            "noshow": 0,
            "compiled": 0,
            "claim_errors": 0,
            "revenue": 0.0,
            "revenue_seen": False,
            "currency": None,
        }
    )

    for event in events:
        try:
            timestamp = event["timestamp"]
            if isinstance(timestamp, datetime):
                day = timestamp.date().isoformat()
            else:
                ts_str = str(timestamp).replace(" ", "T")
                day = datetime.fromisoformat(ts_str).date().isoformat()
        except Exception as e:
            print(f"CRITICAL ERROR: {e}")
            continue

        bucket = buckets[day]
        tags = _tags(event)
        event_type = event.get("event_type")

        if event_type == "appointment_booked":
            bucket["booked"] += 1
        elif event_type == "appointment_noshow_predicted":
            bucket["noshow"] += 1
        elif event_type == "billing_claim_compiled":
            bucket["compiled"] += 1
            if _is_error_flagged(tags):
                bucket["claim_errors"] += 1
        elif event_type == "revenue_stream_reconciled":
            bucket["revenue_seen"] = True
            bucket["revenue"] += float(tags.get("net_settled_amount") or 0.0)
            bucket["currency"] = bucket["currency"] or tags.get("currency")

    rows: list[ExecutiveKPIResponse] = []
    for day in sorted(buckets):
        bucket = buckets[day]
        rows.append(
            ExecutiveKPIResponse(
                reporting_window_timestamp=datetime.fromisoformat(f"{day}T00:00:00+00:00"),
                clinic_location_id=NETWORK_LOCATION,
                market_region=GLOBAL_REGION,
                network_appointment_volume=bucket["booked"],
                global_no_show_rate=_rate(bucket["noshow"], bucket["booked"]),
                claims_denial_rate=_rate(bucket["claim_errors"], bucket["compiled"]),
                revenue_currency=bucket["currency"],
                revenue_net_settled=round(bucket["revenue"], 2) if bucket["revenue_seen"] else None,
                patient_satisfaction_score=None,
            )
        )
    return rows
