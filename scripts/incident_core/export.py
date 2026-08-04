"""Flatten analysis results to CSV rows (metric, value, percentage)."""

from __future__ import annotations

import csv
import io
from typing import Any

from .analyzer import AnalysisResult, pct
from .constants import CATEGORIES, RULE_ORDER, STATUSES


def results_to_csv_rows(result: AnalysisResult) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = [
        {"metric": "total_records", "value": result.total_records, "percentage": ""},
        {"metric": "valid_records", "value": result.valid_records, "percentage": ""},
        {"metric": "invalid_records", "value": result.invalid_records, "percentage": ""},
    ]

    for rule in RULE_ORDER:
        rows.append(
            {
                "metric": f"invalid.{rule}",
                "value": result.invalid_breakdown.get(rule, 0),
                "percentage": "",
            }
        )

    valid = result.valid_records
    for category in CATEGORIES:
        count = result.by_category.get(category, 0)
        rows.append(
            {
                "metric": f"category.{category}",
                "value": count,
                "percentage": f"{pct(count, valid):.1f}" if valid else "0.0",
            }
        )

    for status in STATUSES:
        count = result.by_status.get(status, 0)
        rows.append(
            {
                "metric": f"status.{status}",
                "value": count,
                "percentage": f"{pct(count, valid):.1f}" if valid else "0.0",
            }
        )

    for country in ("US", "UK"):
        count = result.by_country.get(country, 0)
        rows.append(
            {
                "metric": f"country.{country}",
                "value": count,
                "percentage": f"{pct(count, valid):.1f}" if valid else "0.0",
            }
        )

    rows.append(
        {
            "metric": "satisfaction.scored_cases",
            "value": result.satisfaction_scored,
            "percentage": "",
        }
    )
    rows.append(
        {
            "metric": "satisfaction.closed_cases",
            "value": result.satisfaction_closed,
            "percentage": "",
        }
    )
    rows.append(
        {
            "metric": "satisfaction.average",
            "value": result.satisfaction_average if result.satisfaction_average is not None else "",
            "percentage": "",
        }
    )
    for score in range(1, 6):
        rows.append(
            {
                "metric": f"satisfaction.score_{score}",
                "value": result.satisfaction_counts.get(score, 0),
                "percentage": "",
            }
        )
    return rows


def results_to_csv_text(result: AnalysisResult) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=["metric", "value", "percentage"])
    writer.writeheader()
    for row in results_to_csv_rows(result):
        writer.writerow(row)
    return buffer.getvalue()
