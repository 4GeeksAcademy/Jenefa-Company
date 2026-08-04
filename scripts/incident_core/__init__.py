"""Shared HealthCore patient-incident analysis core (CLI + API)."""

from .analyzer import AnalysisResult, analyze_csv_bytes, analyze_csv_path, analyze_rows
from .export import results_to_csv_rows, results_to_csv_text
from .report import format_console_report

__all__ = [
    "AnalysisResult",
    "analyze_csv_bytes",
    "analyze_csv_path",
    "analyze_rows",
    "format_console_report",
    "results_to_csv_rows",
    "results_to_csv_text",
]
