"""Regression coverage for executive KPI aggregation."""

from datetime import datetime, timezone

from services.api.app.reporting.kpi_contract import compute_executive_kpis


def test_compute_executive_kpis_returns_serializable_kpi_mapping() -> None:
    events = [
        {
            "event_type": "appointment_booked",
            "timestamp": datetime(2026, 10, 20, 12, 0, tzinfo=timezone.utc),
            "tags": {"region": "US"},
        },
        {
            "event_type": "billing_claim_compiled",
            "timestamp": datetime(2026, 10, 20, 12, 0, tzinfo=timezone.utc),
            "tags": {"error": True},
        },
    ]

    rows = compute_executive_kpis(events)
    result = rows[0].model_dump(mode="json")

    assert result == {
        "reporting_window_timestamp": "2026-10-20T00:00:00Z",
        "clinic_location_id": "NETWORK",
        "market_region": "GLOBAL",
        "network_appointment_volume": 1,
        "global_no_show_rate": 0.0,
        "claims_denial_rate": 1.0,
        "revenue_currency": None,
        "revenue_net_settled": None,
        "patient_satisfaction_score": None,
    }
