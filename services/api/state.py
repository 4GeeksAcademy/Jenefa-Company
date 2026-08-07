"""In-memory store for the latest analysis export (single-process demo)."""

from __future__ import annotations

from typing import Any, Dict, Optional

_latest_result: Optional[Dict[str, Any]] = None
_latest_csv: Optional[str] = None


def save_analysis(result: Dict[str, Any], csv_text: str) -> None:
    global _latest_result, _latest_csv
    _latest_result = result
    _latest_csv = csv_text


def get_latest_csv() -> Optional[str]:
    return _latest_csv


def get_latest_result() -> Optional[Dict[str, Any]]:
    return _latest_result


def clear() -> None:
    global _latest_result, _latest_csv
    _latest_result = None
    _latest_csv = None
