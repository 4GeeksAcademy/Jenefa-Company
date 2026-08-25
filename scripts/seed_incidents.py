#!/usr/bin/env python3
"""Seed historical incidents into the central HealthCore incident store."""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SHARED_DIR = ROOT / "packages" / "shared"
API_DIR = ROOT / "services" / "api"
for candidate in (SHARED_DIR, API_DIR):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from incidents import sanitize_incident_payload  # noqa: E402
import state  # noqa: E402

CATEGORY_MAP = {
    "APPOINTMENT": "patient_experience",
    "BILLING": "revenue_cycle",
    "CLINICAL_CARE": "clinical_operations",
    "ACCESSIBILITY": "patient_experience",
    "ADMINISTRATIVE": "people_workforce",
}

STATUS_MAP = {
    "OPEN": "open",
    "CLOSED": "resolved",
    "DISCARDED": "discarded",
}

BRANCH_MAP = {
    "US-TX-01": "texas_clinic_1",
    "US-TX-02": "texas_clinic_2",
    "US-TX-03": "texas_clinic_3",
    "US-FL-01": "florida_clinic_1",
    "US-FL-02": "florida_clinic_2",
    "US-FL-03": "florida_clinic_3",
    "US-GA-01": "georgia_clinic_1",
    "US-GA-02": "georgia_clinic_2",
    "US-GA-03": "georgia_clinic_3",
    "UK-LON-01": "london_clinic_1",
    "UK-LON-02": "london_clinic_2",
    "UK-MAN-01": "manchester_clinic",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Seed historical incidents from CSV into services/api/incidents.db."
        )
    )
    parser.add_argument(
        "--source",
        default=str(ROOT / "scripts" / "incidents-healthcore.csv"),
        help="Path to historical source CSV.",
    )
    return parser.parse_args()


def iso_from_date(text: str) -> str:
    value = text.strip()
    date_obj = datetime.strptime(value, "%Y-%m-%d")
    return date_obj.replace(tzinfo=timezone.utc).isoformat()


def to_payload(row: dict[str, str]) -> tuple[dict[str, str], str | None]:
    legacy_id = row.get("incident_id", "").strip()
    clinic_code = row.get("clinic_id", "").strip()
    status_code = row.get("status", "").strip().upper()
    category_code = row.get("category", "").strip().upper()

    branch = BRANCH_MAP.get(clinic_code)
    status = STATUS_MAP.get(status_code)
    category = CATEGORY_MAP.get(category_code)

    if branch is None or status is None or category is None:
        return {}, None

    description = row.get("description", "").strip()
    if not description:
        return {}, None

    payload = {
        "title": description[:255],
        "description": description,
        "category": category,
        "status": status,
        "origin": "customer",
        "branch": branch,
    }

    source_key = f"legacy:{legacy_id}" if legacy_id else None
    return payload, source_key


def main() -> int:
    args = parse_args()
    source = Path(args.source)
    if not source.exists():
        print(f"Source file not found: {source}")
        return 1

    state.init_db()

    inserted = 0
    skipped = 0
    expected_status = Counter()
    expected_category = Counter()

    with source.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            payload, source_key = to_payload(row)
            if not payload or source_key is None:
                skipped += 1
                continue

            sanitized, errors = sanitize_incident_payload(payload)
            if errors:
                skipped += 1
                continue

            created_at = None
            date_value = (row.get("date") or "").strip()
            if date_value:
                try:
                    created_at = iso_from_date(date_value)
                except ValueError:
                    skipped += 1
                    continue

            was_inserted = state.create_incident_if_missing(
                sanitized,
                source_key=source_key,
                created_at=created_at,
            )
            if was_inserted:
                inserted += 1
                expected_status[sanitized["status"]] += 1
                expected_category[sanitized["category"]] += 1

    summary = state.summary()

    # Validation target from specs: in a clean DB, summary should match transformed baseline.
    status_matches = all(
        summary["status"].get(name, 0) >= count
        for name, count in expected_status.items()
    )
    category_matches = all(
        summary["category"].get(name, 0) >= count
        for name, count in expected_category.items()
    )

    print(f"Inserted: {inserted}")
    print(f"Skipped: {skipped}")
    print("Summary snapshot (status):", summary["status"])
    print("Summary snapshot (category):", summary["category"])

    if not status_matches or not category_matches:
        print("Summary validation failed.")
        return 1

    print("Summary validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
