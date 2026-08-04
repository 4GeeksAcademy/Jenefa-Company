"""In-memory store for the latest analysis export (single-process demo)."""

from __future__ import annotations

from typing import Any

_latest_result: dict[str, Any] | None = None
_latest_csv: str | None = None


def save_analysis(result: dict[str, Any], csv_text: str) -> None:
    global _latest_result, _latest_csv
    _latest_result = result
    _latest_csv = csv_text


def get_latest_csv() -> str | None:
    return _latest_csv


def get_latest_result() -> dict[str, Any] | None:
    return _latest_result


def clear() -> None:
    global _latest_result, _latest_csv
    _latest_result = None
    _latest_csv = None
