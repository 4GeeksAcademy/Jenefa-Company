"""Authorized HealthCore clinic, category, and status values."""

from __future__ import annotations

CLINIC_COUNTRY: dict[str, str] = {
    "US-TX-01": "US",
    "US-TX-02": "US",
    "US-TX-03": "US",
    "US-FL-01": "US",
    "US-FL-02": "US",
    "US-FL-03": "US",
    "US-GA-01": "US",
    "US-GA-02": "US",
    "US-GA-03": "US",
    "UK-LON-01": "UK",
    "UK-LON-02": "UK",
    "UK-MAN-01": "UK",
}

VALID_CLINICS = frozenset(CLINIC_COUNTRY)
VALID_COUNTRIES = frozenset({"US", "UK"})

CATEGORIES = (
    "APPOINTMENT",
    "BILLING",
    "CLINICAL_CARE",
    "ACCESSIBILITY",
    "ADMINISTRATIVE",
)
VALID_CATEGORIES = frozenset(CATEGORIES)

STATUSES = ("OPEN", "CLOSED", "DISCARDED")
VALID_STATUSES = frozenset(STATUSES)

# Rule keys used in invalid breakdown (stable order for reports).
RULE_INVALID_CLINIC = "invalid_clinic_id"
RULE_COUNTRY_MISMATCH = "country_clinic_mismatch"
RULE_INVALID_CATEGORY = "invalid_category"
RULE_EMPTY_DESCRIPTION = "empty_description"
RULE_MISSING_PATIENT_ID = "missing_patient_id"
RULE_CLOSED_NO_SCORE = "closed_no_score"
RULE_SCORE_OUT_OF_RANGE = "score_out_of_range"

RULE_LABELS: dict[str, str] = {
    RULE_INVALID_CLINIC: "Invalid or missing clinic_id",
    RULE_COUNTRY_MISMATCH: "Country/clinic mismatch",
    RULE_INVALID_CATEGORY: "Invalid or missing category",
    RULE_EMPTY_DESCRIPTION: "Empty description",
    RULE_MISSING_PATIENT_ID: "Missing patient_id",
    RULE_CLOSED_NO_SCORE: "Closed case, no score",
    RULE_SCORE_OUT_OF_RANGE: "Satisfaction score out of range",
}

RULE_ORDER = (
    RULE_INVALID_CLINIC,
    RULE_COUNTRY_MISMATCH,
    RULE_INVALID_CATEGORY,
    RULE_EMPTY_DESCRIPTION,
    RULE_MISSING_PATIENT_ID,
    RULE_CLOSED_NO_SCORE,
    RULE_SCORE_OUT_OF_RANGE,
)

PATIENT_ID_PATTERN = r"^PAT-\d{6}$"
INCIDENT_ID_PATTERN = r"^HC-\d{6}$"

REQUIRED_COLUMNS = (
    "incident_id",
    "date",
    "clinic_id",
    "country",
    "category",
    "description",
    "status",
    "patient_id",
    "satisfaction_score",
)

SCORE_LABELS = {
    1: "Very dissatisfied",
    2: "Dissatisfied",
    3: "Neutral",
    4: "Satisfied",
    5: "Very satisfied",
}
