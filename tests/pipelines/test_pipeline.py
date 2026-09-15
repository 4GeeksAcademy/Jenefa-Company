from datetime import datetime, timezone

import pytest

from data.process.kpis import (
    claims_denial_rate,
    global_no_show_rate,
    network_appointment_volume,
)


@pytest.fixture
def realistic_us_uk_telemetry():
    return [
        {"event_id": "a1", "event_type": "appointment_booked", "tags": {"location_id": "US-01", "region": "US"}},
        {"event_id": "a2", "event_type": "appointment_booked", "tags": {"location_id": "US-01", "region": "US"}},
        {"event_id": "a3", "event_type": "appointment_booked", "tags": {"location_id": "US-01", "region": "US"}},
        {"event_id": "n1", "event_type": "appointment_noshow_predicted", "tags": {"location_id": "US-01", "region": "US"}},
        {"event_id": "c1", "event_type": "billing_claim_compiled", "tags": {"region": "US", "pre_check_denial_risk": 0.10}},
        {"event_id": "c2", "event_type": "billing_claim_compiled", "tags": {"region": "US", "pre_check_denial_risk": 0.20}},
        {"event_id": "uk1", "event_type": "appointment_booked", "tags": {"location_id": "UK-01", "region": "UK"}},
    ]


def test_network_appointment_volume_is_deterministic(realistic_us_uk_telemetry):
    assert network_appointment_volume(realistic_us_uk_telemetry) == [
        {"clinic_location_id": "US-01", "market_region": "US", "network_appointment_volume": 3},
        {"clinic_location_id": "UK-01", "market_region": "UK", "network_appointment_volume": 1},
    ]


def test_global_no_show_rate_matches_hand_calculation(realistic_us_uk_telemetry):
    assert global_no_show_rate(realistic_us_uk_telemetry)[0]["global_no_show_rate"] == pytest.approx(1 / 3, abs=0.0001)


def test_claims_denial_rate_averages_regional_risk(realistic_us_uk_telemetry):
    assert claims_denial_rate(realistic_us_uk_telemetry) == [
        {"clinic_location_id": "US", "market_region": "US", "claims_denial_rate": 0.15}
    ]


def test_malformed_records_are_skipped_defensively():
    malformed = [{"event_id": "bad", "event_type": None, "tags": "not-a-mapping"}, {"event_id": "bad2", "tags": None}]
    assert network_appointment_volume(malformed) == []
    assert global_no_show_rate(malformed) == []
    assert claims_denial_rate(malformed) == []
