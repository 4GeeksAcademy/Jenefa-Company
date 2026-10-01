"""Deterministic, source-grounded RFP intake workflow.

The graph boundaries are intentionally model-provider agnostic: normalization,
classification and routing use explicit rules, making the default path safe and
reproducible. A future LLM adapter can implement these functions without changing
persistence, routing, or the API contract.
"""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from markitdown import MarkItDown
from sqlmodel import Session, select

from .models import DepartmentSectionAspect, RFPTicket

# In this repository no CONTEXT-company.md exists yet. Keep the supported map in
# one place and make that fact explicit rather than silently consulting unrelated context.
DEPARTMENTS: dict[str, tuple[str, ...]] = {
    "Engineering": ("engineering", "software", "platform", "integration", "technical", "system"),
    "Legal": ("legal", "contract", "agreement", "liability", "jurisdiction", "terms"),
    "Information Security": ("security", "cybersecurity", "encryption", "incident", "access control", "compliance"),
    "Finance": ("finance", "pricing", "cost", "budget", "payment", "invoice"),
}

RFP_SIGNALS = (
    "request for proposal", "rfp", "proposal submission", "evaluation criteria",
    "submission deadline", "scope of work", "statement of work", "vendor response",
)


def convert_pdf(file_path: str | Path) -> str:
    """Convert a PDF to Markdown using MarkItDown."""
    result = MarkItDown().convert(str(file_path))
    text = result.text_content.strip()
    if not text:
        raise ValueError("The PDF did not contain extractable text")
    return text


def readability_metrics(markdown: str) -> dict[str, Any]:
    """Return reproducible, dependency-free document size and readability estimates."""
    words = re.findall(r"\b[\w'-]+\b", markdown)
    sentences = max(1, len(re.findall(r"[.!?](?:\s|$)", markdown)))
    syllables = sum(_syllable_count(word) for word in words)
    word_count = len(words)
    if not word_count:
        grade = 0.0
        fog = 0.0
    else:
        grade = round(0.39 * (word_count / sentences) + 11.8 * (syllables / word_count) - 15.59, 2)
        complex_words = sum(_syllable_count(word) >= 3 for word in words)
        fog = round(0.4 * ((word_count / sentences) + 100 * complex_words / word_count), 2)
    return {
        "word_count": word_count,
        "estimated_tokens": max(1, round(len(markdown) / 4)) if markdown else 0,
        "flesch_kincaid_grade_level": grade,
        "gunning_fog_index": fog,
    }


def _syllable_count(word: str) -> int:
    word = re.sub(r"[^a-z]", "", word.lower())
    if not word:
        return 1
    groups = re.findall(r"[aeiouy]+", word)
    count = len(groups)
    if word.endswith("e") and count > 1 and not word.endswith(("le", "ye")):
        count -= 1
    return max(1, count)


def classify_rfp(markdown: str, *, force: bool = False) -> tuple[bool, list[str]]:
    """Require multiple recognizable RFP signals to limit false-positive intake."""
    lowered = markdown.lower()
    signals = [signal for signal in RFP_SIGNALS if signal in lowered]
    return (force or len(signals) >= 2), signals


def _section_blocks(markdown: str) -> list[tuple[str, str]]:
    """Split content by headings; if no headings exist, treat each paragraph as a block."""
    lines = markdown.splitlines()
    blocks: list[tuple[str, str]] = []
    heading = "Document"
    content: list[str] = []
    for line in lines:
        if re.match(r"^#{1,6}\s+", line):
            if content:
                blocks.append((heading, "\n".join(content).strip()))
            heading = re.sub(r"^#{1,6}\s+", "", line).strip()
            content = []
        else:
            content.append(line)
    if content:
        blocks.append((heading, "\n".join(content).strip()))
    if len(blocks) == 1 and blocks[0][0] == "Document":
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", markdown) if p.strip()]
        blocks = [("Document", paragraph) for paragraph in paragraphs]
    return [(heading, body) for heading, body in blocks if body]


def orchestrate(markdown: str) -> list[dict[str, str]]:
    """Route only relevant sections to departments; unmatched material is preserved."""
    grouped: dict[str, list[str]] = defaultdict(list)
    for heading, body in _section_blocks(markdown):
        text = f"{heading}\n{body}".strip()
        lowered = text.lower()
        matches = [
            department for department, terms in DEPARTMENTS.items()
            if any(term in lowered for term in terms)
        ]
        if not matches:
            grouped["Unassigned / General Review"].append(text)
        else:
            for department in matches:
                grouped[department].append(text)
    return [
        {"department_name": name, "relevant_markdown_extract": "\n\n".join(extracts)}
        for name, extracts in grouped.items()
    ]


def worker(task: dict[str, str], metadata: dict[str, Any]) -> dict[str, Any]:
    """Extract verbatim evidence and flag missing response parameters; invent nothing."""
    excerpt = task["relevant_markdown_extract"]
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", excerpt) if s.strip()]
    relevant = [s for s in sentences if re.search(r"\d|must|shall|required|deadline|submit|provide|include|respond", s, re.I)]
    if not relevant:
        relevant = sentences[:5]
    aspects = "\n".join(f"- {sentence}" for sentence in relevant) or "No explicit requirements found in the source section."
    contacts = sorted(set(re.findall(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", excerpt)))
    warnings = []
    if not re.search(r"\b(?:\$\s?\d|\d+(?:\.\d+)?\s?(?:%|days?|weeks?|months?|hours?))\b", excerpt, re.I):
        warnings.append("Required parameter [quantified target / amount / timeline] missing from source document.")
    return {"department": task["department_name"], "key_aspects": aspects, "contacts": contacts, "warnings": warnings, "source_excerpt": excerpt, "metadata": metadata}


def synthesize(outputs: list[dict[str, Any]]) -> dict[str, Any]:
    """Build sales handoff while preserving possible conflicts as explicit warnings."""
    all_text = [(item["department"], item["key_aspects"]) for item in outputs]
    warnings: list[str] = []
    for i, (dept_a, text_a) in enumerate(all_text):
        for dept_b, text_b in all_text[i + 1 :]:
            nums_a = set(re.findall(r"\b\d+(?:\.\d+)?%?\b", text_a))
            nums_b = set(re.findall(r"\b\d+(?:\.\d+)?%?\b", text_b))
            if nums_a and nums_b and nums_a.isdisjoint(nums_b):
                warnings.append(f"[CONTRADICTION DETECTED] Review differing figures in {dept_a} and {dept_b} sections.")
    if any(item["department"] == "Unassigned / General Review" for item in outputs):
        warnings.append("Manual assignment required for Unassigned / General Review workstream.")
    workstreams = [
        {"department": item["department"], "key_aspects": item["key_aspects"], "contacts": item["contacts"], "warnings": item["warnings"]}
        for item in outputs
    ]
    lines = [f"{item['department']}: {item['key_aspects']}" for item in workstreams]
    lines.extend(warnings)
    return {"sales_summary": "\n\n".join(lines), "workstream_structure": workstreams, "warnings": warnings}


def process_ticket(engine: Any, ticket_id: str, *, force: bool = False, markdown_override: str | None = None) -> None:
    """Execute pipeline and persist each transition in the shared SQL database."""
    with Session(engine) as session:
        ticket = session.get(RFPTicket, ticket_id)
        if ticket is None:
            return
        ticket.updated_at = datetime.now(timezone.utc)
        session.add(ticket)
        session.commit()
        try:
            markdown = markdown_override if markdown_override is not None else convert_pdf(ticket.file_path)
            metrics = readability_metrics(markdown)
            ticket.metrics = metrics
            valid, signals = classify_rfp(markdown, force=force)
            ticket.raw_metadata = {"classifier_signals": signals, "converter": "MarkItDown", "forced": force}
            ticket.updated_at = datetime.now(timezone.utc)
            if not valid:
                ticket.status = "discarded"
                session.add(ticket)
                session.commit()
                return
            tasks = orchestrate(markdown)
            session.exec(select(DepartmentSectionAspect).where(DepartmentSectionAspect.ticket_id == ticket_id)).all()
            existing = session.exec(select(DepartmentSectionAspect).where(DepartmentSectionAspect.ticket_id == ticket_id)).all()
            for row in existing:
                session.delete(row)
            outputs = [worker(task, ticket.raw_metadata) for task in tasks]
            for result in outputs:
                session.add(DepartmentSectionAspect(ticket_id=ticket_id, department=result["department"], key_aspects=result["key_aspects"], contacts=result["contacts"]))
            handoff = synthesize(outputs)
            ticket.synthesizer_payload = handoff
            ticket.status = "intake_complete"
            ticket.updated_at = datetime.now(timezone.utc)
            session.add(ticket)
            session.commit()
        except Exception:
            session.rollback()
            ticket = session.get(RFPTicket, ticket_id)
            if ticket:
                ticket.raw_metadata = {**ticket.raw_metadata, "processing_error": "Document processing failed; retry or contact an administrator."}
                ticket.updated_at = datetime.now(timezone.utc)
                session.add(ticket)
                session.commit()
            raise
