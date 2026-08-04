"""Validate incident CSV rows and compute aggregate metrics.

PHI guardrail: never include patient_id (or other patient identifiers) in
returned structures, logs, or error strings — only aggregate rule counts.
"""

from __future__ import annotations

import csv
import io
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

from .constants import (
    CATEGORIES,
    CLINIC_COUNTRY,
    PATIENT_ID_PATTERN,
    REQUIRED_COLUMNS,
    RULE_CLOSED_NO_SCORE,
    RULE_COUNTRY_MISMATCH,
    RULE_EMPTY_DESCRIPTION,
    RULE_INVALID_CATEGORY,
    RULE_INVALID_CLINIC,
    RULE_MISSING_PATIENT_ID,
    RULE_ORDER,
    RULE_SCORE_OUT_OF_RANGE,
    STATUSES,
    VALID_CATEGORIES,
    VALID_CLINICS,
    VALID_STATUSES,
)

_PATIENT_ID_RE = re.compile(PATIENT_ID_PATTERN)


@dataclass
class AnalysisResult:
    source_file: str
    total_records: int
    valid_records: int
    invalid_records: int
    invalid_breakdown: dict[str, int]
    by_category: dict[str, int]
    by_status: dict[str, int]
    by_country: dict[str, int]
    satisfaction_counts: dict[int, int]
    satisfaction_scored: int
    satisfaction_closed: int
    satisfaction_average: float | None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_file": self.source_file,
            "total_records": self.total_records,
            "valid_records": self.valid_records,
            "invalid_records": self.invalid_records,
            "invalid_breakdown": dict(self.invalid_breakdown),
            "by_category": dict(self.by_category),
            "by_status": dict(self.by_status),
            "by_country": dict(self.by_country),
            "satisfaction": {
                "scored_cases": self.satisfaction_scored,
                "closed_cases": self.satisfaction_closed,
                "average": self.satisfaction_average,
                "counts": {str(k): v for k, v in sorted(self.satisfaction_counts.items())},
            },
            "error": self.error,
        }


@dataclass
class _Accumulators:
    invalid_breakdown: Counter[str] = field(default_factory=Counter)
    by_category: Counter[str] = field(default_factory=Counter)
    by_status: Counter[str] = field(default_factory=Counter)
    by_country: Counter[str] = field(default_factory=Counter)
    satisfaction_counts: Counter[int] = field(default_factory=Counter)
    satisfaction_scores: list[int] = field(default_factory=list)
    valid_records: int = 0
    invalid_records: int = 0
    closed_valid: int = 0


def _cell(row: Mapping[str, str], key: str) -> str:
    value = row.get(key, "")
    if value is None:
        return ""
    return str(value).strip()


def _parse_score(raw: str) -> tuple[int | None, bool]:
    """Return (score, present). present=False means blank/missing."""
    if raw == "":
        return None, False
    try:
        # Accept "4" or "4.0" but reject non-integers like "3.5".
        as_float = float(raw)
        as_int = int(as_float)
        if as_float != as_int:
            return None, True
        return as_int, True
    except ValueError:
        return None, True


def validate_record(row: Mapping[str, str]) -> list[str]:
    """Return rule keys violated by this row. Never includes PHI values."""
    rules: list[str] = []

    clinic_id = _cell(row, "clinic_id")
    country = _cell(row, "country")
    category = _cell(row, "category")
    description = _cell(row, "description")
    status = _cell(row, "status")
    patient_id = _cell(row, "patient_id")
    score_raw = _cell(row, "satisfaction_score")

    if clinic_id not in VALID_CLINICS:
        rules.append(RULE_INVALID_CLINIC)
    elif country != CLINIC_COUNTRY[clinic_id]:
        rules.append(RULE_COUNTRY_MISMATCH)

    if category not in VALID_CATEGORIES:
        rules.append(RULE_INVALID_CATEGORY)

    if len(description) < 5:
        rules.append(RULE_EMPTY_DESCRIPTION)

    if not _PATIENT_ID_RE.match(patient_id):
        rules.append(RULE_MISSING_PATIENT_ID)

    score, score_present = _parse_score(score_raw)
    if score_present and (score is None or score < 1 or score > 5):
        rules.append(RULE_SCORE_OUT_OF_RANGE)

    if status == "CLOSED" and not score_present:
        rules.append(RULE_CLOSED_NO_SCORE)

    return rules


def _empty_breakdown() -> dict[str, int]:
    return {rule: 0 for rule in RULE_ORDER}


def _finalize(source_file: str, total: int, acc: _Accumulators, error: str | None = None) -> AnalysisResult:
    breakdown = _empty_breakdown()
    breakdown.update(acc.invalid_breakdown)

    by_category = {c: acc.by_category.get(c, 0) for c in CATEGORIES}
    by_status = {s: acc.by_status.get(s, 0) for s in STATUSES}
    by_country = {
        "US": acc.by_country.get("US", 0),
        "UK": acc.by_country.get("UK", 0),
    }
    satisfaction_counts = {score: acc.satisfaction_counts.get(score, 0) for score in range(1, 6)}

    average: float | None = None
    if acc.satisfaction_scores:
        average = round(sum(acc.satisfaction_scores) / len(acc.satisfaction_scores), 2)

    return AnalysisResult(
        source_file=source_file,
        total_records=total,
        valid_records=acc.valid_records,
        invalid_records=acc.invalid_records,
        invalid_breakdown=breakdown,
        by_category=by_category,
        by_status=by_status,
        by_country=by_country,
        satisfaction_counts=satisfaction_counts,
        satisfaction_scored=len(acc.satisfaction_scores),
        satisfaction_closed=acc.closed_valid,
        satisfaction_average=average,
        error=error,
    )


def analyze_rows(
    rows: Iterable[Mapping[str, str]],
    *,
    source_file: str = "upload.csv",
) -> AnalysisResult:
    acc = _Accumulators()
    total = 0

    for row in rows:
        total += 1
        violations = validate_record(row)
        if violations:
            acc.invalid_records += 1
            for rule in violations:
                acc.invalid_breakdown[rule] += 1
            continue

        acc.valid_records += 1
        category = _cell(row, "category")
        status = _cell(row, "status")
        country = _cell(row, "country")
        acc.by_category[category] += 1
        # Status outside the authorized set still counts as structurally odd;
        # valid records from this dataset always use OPEN/CLOSED/DISCARDED.
        if status in VALID_STATUSES:
            acc.by_status[status] += 1
        acc.by_country[country] += 1

        if status == "CLOSED":
            acc.closed_valid += 1
            score, present = _parse_score(_cell(row, "satisfaction_score"))
            if present and score is not None:
                acc.satisfaction_scores.append(score)
                acc.satisfaction_counts[score] += 1

    return _finalize(source_file, total, acc)


def _read_dict_rows(text: str) -> tuple[list[dict[str, str]], str | None]:
    if not text.strip():
        return [], "Uploaded file is empty (zero-byte or whitespace only)."

    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        return [], "Unable to read CSV headers."

    headers = [h.strip() if h else "" for h in reader.fieldnames]
    missing = [col for col in REQUIRED_COLUMNS if col not in headers]
    if missing:
        return [], f"Mismatched CSV layout. Missing columns: {', '.join(missing)}."

    rows: list[dict[str, str]] = []
    for raw in reader:
        # Normalize keys; drop None key that csv may add for ragged rows.
        row = {str(k).strip(): ("" if v is None else str(v)) for k, v in raw.items() if k is not None}
        rows.append(row)
    return rows, None


def analyze_csv_text(text: str, *, source_file: str) -> AnalysisResult:
    rows, error = _read_dict_rows(text)
    if error:
        return AnalysisResult(
            source_file=source_file,
            total_records=0,
            valid_records=0,
            invalid_records=0,
            invalid_breakdown=_empty_breakdown(),
            by_category={c: 0 for c in CATEGORIES},
            by_status={s: 0 for s in STATUSES},
            by_country={"US": 0, "UK": 0},
            satisfaction_counts={score: 0 for score in range(1, 6)},
            satisfaction_scored=0,
            satisfaction_closed=0,
            satisfaction_average=None,
            error=error,
        )
    return analyze_rows(rows, source_file=source_file)


def analyze_csv_bytes(data: bytes, *, source_file: str = "upload.csv") -> AnalysisResult:
    if not data:
        return analyze_csv_text("", source_file=source_file)
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return AnalysisResult(
            source_file=source_file,
            total_records=0,
            valid_records=0,
            invalid_records=0,
            invalid_breakdown=_empty_breakdown(),
            by_category={c: 0 for c in CATEGORIES},
            by_status={s: 0 for s in STATUSES},
            by_country={"US": 0, "UK": 0},
            satisfaction_counts={score: 0 for score in range(1, 6)},
            satisfaction_scored=0,
            satisfaction_closed=0,
            satisfaction_average=None,
            error="Unreadable data: file is not valid UTF-8.",
        )
    return analyze_csv_text(text, source_file=source_file)


def analyze_csv_path(path: str | Path) -> AnalysisResult:
    file_path = Path(path)
    source_name = file_path.name
    if not file_path.is_file():
        return AnalysisResult(
            source_file=source_name,
            total_records=0,
            valid_records=0,
            invalid_records=0,
            invalid_breakdown=_empty_breakdown(),
            by_category={c: 0 for c in CATEGORIES},
            by_status={s: 0 for s in STATUSES},
            by_country={"US": 0, "UK": 0},
            satisfaction_counts={score: 0 for score in range(1, 6)},
            satisfaction_scored=0,
            satisfaction_closed=0,
            satisfaction_average=None,
            error=f"File not found: {file_path}",
        )

    data = file_path.read_bytes()
    return analyze_csv_bytes(data, source_file=source_name)


def pct(part: int, whole: int) -> float:
    if whole <= 0:
        return 0.0
    return round((part / whole) * 100, 1)
