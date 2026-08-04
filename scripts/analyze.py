#!/usr/bin/env python3
"""HealthCore patient incident report analyzer (Phase 1 terminal engine).

Usage:
    python analyze.py <path_to_csv>

Never prints patient_id or other PHI — only aggregate metrics.
"""

from __future__ import annotations

import sys
from pathlib import Path

from incident_core import (
    analyze_csv_path,
    format_console_report,
    results_to_csv_text,
)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1:
        print("Usage: python analyze.py <path_to_csv>", file=sys.stderr)
        return 2

    csv_path = Path(args[0])
    result = analyze_csv_path(csv_path)
    print(format_console_report(result))

    if result.error:
        return 1

    try:
        answer = input("Export results to CSV? [y / n]: ").strip().lower()
    except EOFError:
        answer = "n"
        print()

    if answer in {"y", "yes"}:
        out_path = Path.cwd() / "results.csv"
        out_path.write_text(results_to_csv_text(result), encoding="utf-8")
        print(f"Saved: {out_path}")
    else:
        print("Export skipped.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
