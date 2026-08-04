"""Console dashboard formatting for incident analysis results."""

from __future__ import annotations

from .analyzer import AnalysisResult, pct
from .constants import CATEGORIES, RULE_LABELS, RULE_ORDER, SCORE_LABELS, STATUSES


def _line(label: str, value: str, width: int = 34, fill: str = ".") -> str:
    dots = fill * max(2, width - len(label))
    return f"  {label} {dots} {value}"


def _tree(label: str, value: str, last: bool = False, width: int = 32) -> str:
    branch = "└─" if last else "├─"
    pad = width - len(label)
    dots = "." * max(2, pad)
    return f"  {branch} {label} {dots} {value}"


def format_console_report(result: AnalysisResult) -> str:
    lines: list[str] = []
    lines.append("=" * 60)
    lines.append("  HEALTHCORE — PATIENT INCIDENT REPORT ANALYSIS")
    lines.append(f"  Source file: {result.source_file}")
    lines.append("=" * 60)
    lines.append("")

    if result.error:
        lines.append(f"ERROR: {result.error}")
        lines.append("")
        lines.append("=" * 60)
        return "\n".join(lines)

    lines.append(_line("TOTAL RECORDS IN FILE", str(result.total_records), width=30, fill="."))
    lines.append(_tree("Valid records", f"{result.valid_records:>6}", last=False, width=28))
    lines.append(_tree("Invalid / incomplete", f"{result.invalid_records:>4}", last=True, width=28))
    lines.append("")

    lines.append("INVALID RECORDS BREAKDOWN")
    visible_rules = [r for r in RULE_ORDER if r in RULE_LABELS]
    for i, rule in enumerate(visible_rules):
        # Hide out-of-range line when zero to match the sample console closely,
        # but still show it when the dataset triggers that rule.
        if rule == "score_out_of_range" and result.invalid_breakdown.get(rule, 0) == 0:
            continue
        label = RULE_LABELS[rule]
        count = result.invalid_breakdown.get(rule, 0)
        # Determine last visible branch among remaining shown rules.
        remaining = [
            r
            for r in visible_rules[i:]
            if not (r == "score_out_of_range" and result.invalid_breakdown.get(r, 0) == 0)
        ]
        last = len(remaining) == 1
        lines.append(_tree(label, str(count), last=last, width=34))
    lines.append("")

    valid = result.valid_records
    lines.append("BREAKDOWN BY CATEGORY (valid records)")
    for i, category in enumerate(CATEGORIES):
        count = result.by_category.get(category, 0)
        share = pct(count, valid)
        last = i == len(CATEGORIES) - 1
        lines.append(_tree(category, f"{count}  ({share:.1f}%)", last=last, width=28))
    lines.append("")

    lines.append("BREAKDOWN BY STATUS (valid records)")
    for i, status in enumerate(STATUSES):
        count = result.by_status.get(status, 0)
        share = pct(count, valid)
        last = i == len(STATUSES) - 1
        lines.append(_tree(status, f"{count}  ({share:.1f}%)", last=last, width=28))
    lines.append("")

    lines.append("BREAKDOWN BY COUNTRY (valid records)")
    countries = ("US", "UK")
    for i, country in enumerate(countries):
        count = result.by_country.get(country, 0)
        share = pct(count, valid)
        last = i == len(countries) - 1
        lines.append(_tree(country, f"{count}  ({share:.1f}%)", last=last, width=28))
    lines.append("")

    avg = result.satisfaction_average
    avg_text = f"{avg:.2f}" if avg is not None else "n/a"
    lines.append("SATISFACTION INDEX (closed cases)")
    lines.append(
        f"  Scored cases: {result.satisfaction_scored} of {result.satisfaction_closed}"
    )
    lines.append(f"  Average score: {avg_text} / 5.00")
    for score in range(1, 6):
        label = f"Score {score} ({SCORE_LABELS[score]})"
        count = result.satisfaction_counts.get(score, 0)
        last = score == 5
        lines.append(_tree(label, str(count), last=last, width=34))
    lines.append("")
    lines.append("=" * 60)
    return "\n".join(lines)
