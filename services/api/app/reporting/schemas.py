"""Explicit response contracts for reporting endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ReportingStatus(BaseModel):
    status: str
    start_time: datetime
    end_time: datetime | None
    records_processed: int
    errors: str | None


class ReportingTriggerResponse(BaseModel):
    status: str


class ExecutiveKPIResponse(BaseModel):
    reporting_window_timestamp: datetime
    clinic_location_id: str
    market_region: str
    network_appointment_volume: int | None = None
    global_no_show_rate: float | None = None
    claims_denial_rate: float | None = None
    revenue_currency: str | None = None
    revenue_net_settled: float | None = None
    patient_satisfaction_score: float | None = None
