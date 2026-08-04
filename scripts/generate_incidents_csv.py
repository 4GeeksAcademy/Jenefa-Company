#!/usr/bin/env python3
"""Generate incidents-healthcore.csv matching context-fileIncident.md targets."""

from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

CLINICS_US = [
    "US-TX-01",
    "US-TX-02",
    "US-TX-03",
    "US-FL-01",
    "US-FL-02",
    "US-FL-03",
    "US-GA-01",
    "US-GA-02",
    "US-GA-03",
]
CLINICS_UK = ["UK-LON-01", "UK-LON-02", "UK-MAN-01"]
CLINIC_COUNTRY = {c: "US" for c in CLINICS_US} | {c: "UK" for c in CLINICS_UK}

DESCRIPTIONS = {
    "APPOINTMENT": "Waited over an hour past scheduled appointment time",
    "BILLING": "Unexpected charge appeared on the monthly statement",
    "CLINICAL_CARE": "Concern about follow-up instructions after visit",
    "ACCESSIBILITY": "Language support was unavailable during check-in",
    "ADMINISTRATIVE": "Referral paperwork delayed more than two weeks",
}

# Target valid distribution from context-fileIncident.md
CATEGORY_TARGETS = {
    "APPOINTMENT": 30,
    "BILLING": 20,
    "CLINICAL_CARE": 14,
    "ACCESSIBILITY": 17,
    "ADMINISTRATIVE": 13,
}
STATUS_TARGETS = {"OPEN": 28, "CLOSED": 52, "DISCARDED": 14}
SCORE_TARGETS = {1: 3, 2: 5, 3: 12, 4: 23, 5: 9}
# Valid country split among 94: US 61, UK 33
US_VALID = 61
UK_VALID = 33


def _incident_id(n: int) -> str:
    return f"HC-{n:06d}"


def _patient_id(n: int) -> str:
    return f"PAT-{n:06d}"


def _date_for(index: int) -> str:
    base = date(2026, 1, 1)
    return (base + timedelta(days=index % 28)).isoformat()


def build_rows() -> list[dict[str, str]]:
    rng = random.Random(42)
    rows: list[dict[str, str]] = []
    next_id = 1
    next_patient = 1

    # Build status bag and score bag for CLOSED records.
    status_bag: list[str] = []
    for status, count in STATUS_TARGETS.items():
        status_bag.extend([status] * count)
    rng.shuffle(status_bag)

    score_bag: list[str] = []
    for score, count in SCORE_TARGETS.items():
        score_bag.extend([str(score)] * count)
    rng.shuffle(score_bag)
    score_iter = iter(score_bag)

    # Country assignment bags for valid records.
    country_bag = ["US"] * US_VALID + ["UK"] * UK_VALID
    rng.shuffle(country_bag)
    country_iter = iter(country_bag)

    # Category expansion
    category_bag: list[str] = []
    for category, count in CATEGORY_TARGETS.items():
        category_bag.extend([category] * count)
    rng.shuffle(category_bag)

    if len(category_bag) != len(status_bag):
        raise RuntimeError("Category/status target counts must match.")
    for category, status in zip(category_bag, status_bag):
        country = next(country_iter)
        clinic = rng.choice(CLINICS_US if country == "US" else CLINICS_UK)
        score = ""
        if status == "CLOSED":
            score = next(score_iter)
        rows.append(
            {
                "incident_id": _incident_id(next_id),
                "date": _date_for(next_id),
                "clinic_id": clinic,
                "country": country,
                "category": category,
                "description": DESCRIPTIONS[category],
                "status": status,
                "patient_id": _patient_id(next_patient),
                "satisfaction_score": score,
            }
        )
        next_id += 1
        next_patient += 1

    # Six invalid records — one per required rule in the sample breakdown.
    invalid_specs = [
        {
            # Missing or invalid clinic_id
            "clinic_id": "US-XX-99",
            "country": "US",
            "category": "APPOINTMENT",
            "description": "Invalid clinic code used in this sample row",
            "status": "OPEN",
            "patient_id": _patient_id(next_patient),
            "satisfaction_score": "",
        },
        {
            # Country/clinic mismatch
            "clinic_id": "US-TX-01",
            "country": "UK",
            "category": "BILLING",
            "description": "Country does not match clinic jurisdiction",
            "status": "OPEN",
            "patient_id": _patient_id(next_patient + 1),
            "satisfaction_score": "",
        },
        {
            # Missing or invalid category
            "clinic_id": "UK-LON-01",
            "country": "UK",
            "category": "UNKNOWN",
            "description": "Category value is not in the authorized list",
            "status": "OPEN",
            "patient_id": _patient_id(next_patient + 2),
            "satisfaction_score": "",
        },
        {
            # Empty / too-short description
            "clinic_id": "US-FL-01",
            "country": "US",
            "category": "ACCESSIBILITY",
            "description": "no",
            "status": "OPEN",
            "patient_id": _patient_id(next_patient + 3),
            "satisfaction_score": "",
        },
        {
            # Missing patient_id (empty) — never echoed by analyzer
            "clinic_id": "US-GA-01",
            "country": "US",
            "category": "ADMINISTRATIVE",
            "description": "Patient identifier field left blank on purpose",
            "status": "OPEN",
            "patient_id": "",
            "satisfaction_score": "",
        },
        {
            # CLOSED with no satisfaction_score
            "clinic_id": "UK-MAN-01",
            "country": "UK",
            "category": "CLINICAL_CARE",
            "description": "Closed without recording a satisfaction score",
            "status": "CLOSED",
            "patient_id": _patient_id(next_patient + 4),
            "satisfaction_score": "",
        },
    ]

    for spec in invalid_specs:
        rows.append(
            {
                "incident_id": _incident_id(next_id),
                "date": _date_for(next_id),
                **spec,
            }
        )
        next_id += 1

    rng.shuffle(rows)
    return rows


def main() -> None:
    out = Path(__file__).resolve().parent / "incidents-healthcore.csv"
    rows = build_rows()
    fieldnames = [
        "incident_id",
        "date",
        "clinic_id",
        "country",
        "category",
        "description",
        "status",
        "patient_id",
        "satisfaction_score",
    ]
    with out.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {out}")


if __name__ == "__main__":
    main()
