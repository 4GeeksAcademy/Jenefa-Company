"""Shared HealthCore incident domain rules and validation helpers."""

from .domain import (
    ALLOWED_BRANCHES,
    ALLOWED_CATEGORIES,
    ALLOWED_ORIGINS,
    ALLOWED_STATUSES,
    TERMINAL_STATUSES,
    empty_summary,
    is_valid_status_transition,
    sanitize_incident_payload,
)

__all__ = [
    "ALLOWED_BRANCHES",
    "ALLOWED_CATEGORIES",
    "ALLOWED_ORIGINS",
    "ALLOWED_STATUSES",
    "TERMINAL_STATUSES",
    "empty_summary",
    "is_valid_status_transition",
    "sanitize_incident_payload",
]
