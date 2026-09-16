"""Pure, reusable HealthCore executive KPI calculators (no I/O, no Prefect).

Every function takes a list of raw `telemetry_events` rows (already
deduplicated/windowed by the extraction task) and returns a list of dict rows
shaped for `reporting.executive_kpis`, keyed by `(clinic_location_id,
market_region)`. Field vocabulary matches `docs/telemetry/event-schemas.json`
exactly (`location_id`, `region`, `calculated_risk_score`, `pre_check_denial_risk`,
`currency`, `net_settled_amount`) — no synthetic fields are inserted.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, TypedDict


class RawTelemetryRow(TypedDict):
    event_id: str
    event_type: str
    timestamp: Any
    tags: dict[str, Any]


def _tags(row: RawTelemetryRow) -> dict[str, Any]:
    tags = row.get("tags")
    return tags if isinstance(tags, dict) else {}


def _event_type(row: RawTelemetryRow) -> str:
    """Return a safe event type for malformed telemetry rows."""
    event_type = row.get("event_type")
    return event_type if isinstance(event_type, str) else ""


def network_appointment_volume(rows: list[RawTelemetryRow]) -> list[dict[str, Any]]:
    """Absolute `appointment_booked` counts per clinic, addressing capacity/traffic tracking."""
    counts: dict[str, int] = defaultdict(int)
    regions: dict[str, str] = {}
    for row in rows:
        if _event_type(row) != "appointment_booked":
            continue
        tags = _tags(row)
        location_id = tags.get("location_id")
        if not location_id:
            continue
        counts[location_id] += 1
        regions[location_id] = tags.get("region", regions.get(location_id, ""))
    return [
        {
            "clinic_location_id": location_id,
            "market_region": regions.get(location_id, ""),
            "network_appointment_volume": count,
        }
        for location_id, count in counts.items()
    ]


def global_no_show_rate(rows: list[RawTelemetryRow]) -> list[dict[str, Any]]:
    """Predicted no-show proxy: `appointment_noshow_predicted` count / `appointment_booked` count.

    No `appointment_noshow_predicted` value confirms an *actual* no-show ever happened, so this
    is explicitly a leading-indicator rate against the network's 22% target, not a lagging one.
    """
    booked: dict[str, int] = defaultdict(int)
    predicted_noshow: dict[str, int] = defaultdict(int)
    regions: dict[str, str] = {}
    for row in rows:
        tags = _tags(row)
        location_id = tags.get("location_id")
        if not location_id:
            continue
        if _event_type(row) == "appointment_booked":
            booked[location_id] += 1
            regions[location_id] = tags.get("region", regions.get(location_id, ""))
        elif _event_type(row) == "appointment_noshow_predicted":
            predicted_noshow[location_id] += 1

    results = []
    for location_id, booked_count in booked.items():
        noshow_count = predicted_noshow.get(location_id, 0)
        rate = round(noshow_count / booked_count, 4) if booked_count else None
        results.append(
            {
                "clinic_location_id": location_id,
                "market_region": regions.get(location_id, ""),
                "global_no_show_rate": rate,
            }
        )
    return results


def claims_denial_rate(rows: list[RawTelemetryRow]) -> list[dict[str, Any]]:
    """Average `pre_check_denial_risk` from `billing_claim_compiled`, grouped by `region`.

    `billing_claim_compiled` only carries `region` (no `location_id`), so the composite key's
    `clinic_location_id` falls back to the region code (`US`/`UK`) for this metric.
    """
    risk_totals: dict[str, float] = defaultdict(float)
    risk_counts: dict[str, int] = defaultdict(int)
    for row in rows:
        if _event_type(row) != "billing_claim_compiled":
            continue
        tags = _tags(row)
        region = tags.get("region")
        risk = tags.get("pre_check_denial_risk")
        if not region or risk is None:
            continue
        try:
            risk_value = float(risk)
        except (TypeError, ValueError):
            continue
        risk_totals[region] += risk_value
        risk_counts[region] += 1

    return [
        {
            "clinic_location_id": region,
            "market_region": region,
            "claims_denial_rate": round(risk_totals[region] / risk_counts[region], 4),
        }
        for region in risk_totals
    ]


def revenue_by_location(rows: list[RawTelemetryRow]) -> list[dict[str, Any]]:
    """Net settled revenue from `revenue_stream_reconciled`, grouped by `currency`.

    `revenue_stream_reconciled` only carries `currency` (no `location_id`/`region`), so the
    composite key's `clinic_location_id` falls back to the currency-implied market
    (`USD` -> `US`, `GBP` -> `UK`) for this metric.
    """
    currency_to_region = {"USD": "US", "GBP": "UK"}
    totals: dict[str, float] = defaultdict(float)
    for row in rows:
        if _event_type(row) != "revenue_stream_reconciled":
            continue
        tags = _tags(row)
        currency = tags.get("currency")
        net_amount = tags.get("net_settled_amount")
        if not currency or net_amount is None:
            continue
        try:
            totals[currency] += float(net_amount)
        except (TypeError, ValueError):
            continue

    return [
        {
            "clinic_location_id": currency_to_region.get(currency, currency),
            "market_region": currency_to_region.get(currency, ""),
            "revenue_currency": currency,
            "revenue_net_settled": round(total, 2),
        }
        for currency, total in totals.items()
    ]


def patient_satisfaction_scores(rows: list[RawTelemetryRow]) -> list[dict[str, Any]]:
    """Placeholder KPI: no `telemetry_events` event type currently carries a satisfaction score.

    Per `event-schemas.json`, no event contributes this metric today. Returns an empty list
    (never a fabricated value) so the reporting contract keeps the field, staying `null`
    downstream until a real source event is added — see productContext-implementation.md §2.
    """
    del rows  # unused: no source signal exists yet
    return []


def compute_executive_kpis(rows: list[RawTelemetryRow]) -> list[dict[str, Any]]:
    """Merge all per-metric KPI slices into one row per `clinic_location_id`."""
    merged: dict[str, dict[str, Any]] = {}
    for kpi_fn in (
        network_appointment_volume,
        global_no_show_rate,
        claims_denial_rate,
        revenue_by_location,
        patient_satisfaction_scores,
    ):
        for entry in kpi_fn(rows):
            key = entry["clinic_location_id"]
            merged.setdefault(
                key,
                {"clinic_location_id": key, "market_region": entry.get("market_region", "")},
            ).update(entry)
    return list(merged.values())
