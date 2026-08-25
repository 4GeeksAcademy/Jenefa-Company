"""Shared HealthCore incident domain helpers used by scripts and API."""

from __future__ import annotations

from typing import Any

ALLOWED_CATEGORIES = (
    "clinical_operations",
    "patient_experience",
    "revenue_cycle",
    "compliance_governance",
    "people_workforce",
    "technology",
)

ALLOWED_STATUSES = (
    "open",
    "in_progress",
    "resolved",
    "discarded",
)

ALLOWED_ORIGINS = (
    "customer",
    "branch",
    "internal",
)

ALLOWED_BRANCHES = (
    "texas_clinic_1",
    "texas_clinic_2",
    "texas_clinic_3",
    "florida_clinic_1",
    "florida_clinic_2",
    "florida_clinic_3",
    "georgia_clinic_1",
    "georgia_clinic_2",
    "georgia_clinic_3",
    "london_clinic_1",
    "london_clinic_2",
    "manchester_clinic",
    "central",
)

TERMINAL_STATUSES = frozenset(("resolved", "discarded"))

_TRANSITIONS = {
    "open": frozenset(("in_progress", "discarded")),
    "in_progress": frozenset(("resolved", "discarded")),
    "resolved": frozenset(),
    "discarded": frozenset(),
}


def _normalize_required_text(value: Any, max_len: int | None = None) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    if max_len is not None and len(text) > max_len:
        return None
    return text


def sanitize_incident_payload(payload: dict[str, Any]) -> tuple[dict[str, str], dict[str, str]]:
    """Validate create payload and return sanitized values + field errors."""
    errors: dict[str, str] = {}

    title = _normalize_required_text(payload.get("title"), max_len=255)
    if title is None:
        errors["title"] = "Title is required and must be 255 characters or fewer."

    description = _normalize_required_text(payload.get("description"))
    if description is None:
        errors["description"] = "Description is required."

    category = _normalize_required_text(payload.get("category"))
    if category is None or category not in ALLOWED_CATEGORIES:
        errors["category"] = "Category must be one of the approved HealthCore domains."

    status = _normalize_required_text(payload.get("status"))
    if status is None or status not in ALLOWED_STATUSES:
        errors["status"] = "Status must be one of: open, in_progress, resolved, discarded."

    origin = _normalize_required_text(payload.get("origin"))
    if origin is None or origin not in ALLOWED_ORIGINS:
        errors["origin"] = "Origin must be one of: customer, branch, internal."

    branch = _normalize_required_text(payload.get("branch"))
    if branch is None or branch not in ALLOWED_BRANCHES:
        errors["branch"] = "Branch must be one of the approved HealthCore branches."

    if errors:
        return {}, errors

    return {
        "title": title,
        "description": description,
        "category": category,
        "status": status,
        "origin": origin,
        "branch": branch,
    }, {}


def is_valid_status_transition(current_status: str, next_status: str) -> bool:
    if current_status not in _TRANSITIONS:
        return False
    return next_status in _TRANSITIONS[current_status]


def empty_summary() -> dict[str, dict[str, int]]:
    return {
        "status": {name: 0 for name in ALLOWED_STATUSES},
        "category": {name: 0 for name in ALLOWED_CATEGORIES},
        "origin": {name: 0 for name in ALLOWED_ORIGINS},
        "branch": {name: 0 for name in ALLOWED_BRANCHES},
    }
