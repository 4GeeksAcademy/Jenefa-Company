"""Source-grounded RFP response drafting and evaluation pipeline.

This module deliberately uses deterministic templates and rule checks rather
than making unsupported model-provider calls. It consumes only the structured
Part 1 ticket handoff; it never opens or reparses the source PDF.
"""

from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import Column, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON
from sqlmodel import Field, Session, SQLModel, select

from app.rfp.models import DepartmentSectionAspect, RFPTicket

COMPANY_RULES_PATH = Path(__file__).resolve().parents[2] / "docs" / "company-knowledge-base" / "healthcore-operating-principles.md"
MAX_ITERATIONS = 3

# These stable identifiers map directly to the approved operating-principles
# source. Do not infer legal advice beyond these documented company controls.
RULES: tuple[dict[str, str], ...] = (
    {
        "rule_id": "HC-GOV-001",
        "source": "Executive governance",
        "description": "Executive decisions must be evidence-based, compliance-aware, and traceable to current internal documentation.",
    },
    {
        "rule_id": "HC-DATA-RESIDENCY-001",
        "source": "Data residency",
        "description": "US patient records remain in approved US environments and UK patient records remain in approved UK environments.",
    },
    {
        "rule_id": "HC-CROSS-BORDER-MINIMUM-001",
        "source": "Data residency",
        "description": "Cross-border views are temporary, authorized, and limited to the minimum necessary information.",
    },
    {
        "rule_id": "HC-EVIDENCE-001",
        "source": "Assistant safety",
        "description": "Use verified document evidence; state limitations rather than speculate when documentation is insufficient.",
    },
)


class RFPResponseSection(SQLModel, table=True):
    """One immutable coordinator write per evaluated department section."""

    __tablename__ = "rfp_response_sections"
    __table_args__ = (
        UniqueConstraint("ticket_id", "department_id", name="uq_rfp_response_ticket_department"),
        {"extend_existing": True},
    )

    id: int | None = Field(default=None, primary_key=True)
    ticket_id: str = Field(foreign_key="rfp_tickets.ticket_id", index=True, ondelete="CASCADE")
    section_id: str
    department_id: str
    department_name: str
    draft: str = Field(sa_type=Text)
    iteration_count: int = Field(default=1)
    evaluation_result: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON().with_variant(JSONB, "postgresql"), nullable=False),
    )


def _load_company_rules() -> list[dict[str, str]]:
    """Verify that the static evaluator rules remain grounded in current docs."""
    try:
        text = COMPANY_RULES_PATH.read_text(encoding="utf-8")
    except OSError:
        return []
    return [rule for rule in RULES if rule["description"] in text]


def map_department(department: str, key_aspects: str) -> str:
    """Map Part 1 labels into the three HealthCore response domains."""
    text = f"{department} {key_aspects}".lower()
    if re.search(r"sales|revenue|billing|finance|pricing|payer|commercial|payment|collection", text):
        return "Sales, Revenue Cycle & Billing"
    if re.search(r"compliance|legal|privacy|security|governance|hipaa|gdpr|jurisdiction|data protection", text):
        return "Compliance & Data Governance"
    if re.search(r"clinical|operation|delivery|clinic|ehr|staffing|care|medical|resource", text):
        return "Clinical Operations & Delivery"
    return "Unassigned / General Review"


def _sentences(aspects: str) -> list[str]:
    return [part.strip(" \t\r\n-*•") for part in re.split(r"(?<=[.!?])\s+|\n+", aspects) if part.strip(" \t\r\n-*•")]


def generate_department_draft(
    department_id: str,
    department_name: str,
    key_aspects: str,
    feedback: str = "",
) -> str:
    """Draft from exact Part 1 evidence while avoiding invented commitments."""
    requirements = _sentences(key_aspects)
    if not requirements:
        requirements = ["No structured requirement text was supplied; human clarification is required."]
    lines = [f"## {department_name}", "", "### Requirements captured from the RFP"]
    lines.extend(f"- {requirement}" for requirement in requirements)
    lines.extend(
        [
            "",
            "### HealthCore response position",
            "These requirements are captured for departmental review. Capabilities, pricing, delivery dates, service levels, and contractual commitments are not confirmed by the available intake evidence and require authorized subject-matter review before submission.",
        ]
    )
    if department_id == "Unassigned / General Review":
        lines.extend(["", "### Review status", "This workstream has no confirmed departmental owner and must be assigned before submission."])
    if feedback:
        lines.extend(["", "### Evaluator feedback addressed", feedback])
    return "\n".join(lines)


def _readability_evaluator(draft: str) -> dict[str, Any]:
    words = re.findall(r"\b[\w'-]+\b", draft)
    sentences = [part for part in re.split(r"(?<=[.!?])\s+", draft) if part.strip()]
    average_sentence_words = len(words) / max(len(sentences), 1)
    score = max(0.0, min(1.0, round(1.0 - max(0, average_sentence_words - 28) / 50, 2)))
    passed = score >= 0.55 and bool(words)
    return {
        "pass": passed,
        "score": score,
        "details": f"{len(words)} words across {len(sentences)} sentences; average sentence length {average_sentence_words:.1f} words.",
    }


def _relevance_evaluator(draft: str, key_aspects: str) -> dict[str, Any]:
    normalized_draft = re.sub(r"\s+", " ", draft).casefold()
    aspects = _sentences(key_aspects)
    missing = [aspect for aspect in aspects if re.sub(r"\s+", " ", aspect).casefold() not in normalized_draft]
    return {"pass": not missing, "missing_aspects": missing}


def _compliance_evaluator(draft: str, rules: list[dict[str, str]]) -> dict[str, Any]:
    # Only inspect HealthCore-authored response text, not quoted RFP demands.
    response_position = draft.split("### HealthCore response position", 1)[-1]
    lowered = response_position.casefold()
    violations: list[str] = []
    rule_ids: list[str] = []

    # Deterministic contradiction checks against HC-DATA-RESIDENCY-001.
    us_only = re.search(r"(?:all|both|us and uk|uk and us)\s+(?:patient\s+)?records?\s+(?:will be|are|must be)?\s*(?:stored|hosted|kept)\s+(?:only\s+)?in\s+the\s+us", lowered)
    uk_only = re.search(r"(?:all|both|us and uk|uk and us)\s+(?:patient\s+)?records?\s+(?:will be|are|must be)?\s*(?:stored|hosted|kept)\s+(?:only\s+)?in\s+the\s+uk", lowered)
    generic_cross_border = re.search(r"(?:all|entire|complete)\s+(?:patient\s+)?records?\s+(?:will be|are|must be)?\s*(?:freely\s+)?(?:shared|accessible|transferred)\s+(?:across borders|between countries|globally)", lowered)
    if us_only or uk_only:
        rule_ids.append("HC-DATA-RESIDENCY-001")
        violations.append("The draft proposes a single-country storage location for records across both jurisdictions; preserve US and UK residency separately.")
    if generic_cross_border:
        rule_ids.append("HC-CROSS-BORDER-MINIMUM-001")
        violations.append("The draft proposes unrestricted cross-border access; require temporary, authorized, minimum-necessary views.")

    if "source document" not in lowered and any(term in lowered for term in ("guarantee", "guaranteed", "will deliver", "will provide", "commits to")):
        rule_ids.append("HC-EVIDENCE-001")
        violations.append("The draft makes an unverified operational commitment; identify the source evidence or state that authorized review is required.")

    known_ids = {rule["rule_id"] for rule in rules}
    rule_ids = list(dict.fromkeys(rule_id for rule_id in rule_ids if rule_id in known_ids))
    return {"pass": not violations, "rule_ids": rule_ids, "violations": violations}


def evaluate_department_draft(
    department_id: str,
    draft: str,
    key_aspects: str,
    *,
    compliance_rules: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Run isolated readability, relevance and compliance evaluators."""
    rules = compliance_rules if compliance_rules is not None else _load_company_rules()
    with ThreadPoolExecutor(max_workers=3) as pool:
        readability_future = pool.submit(_readability_evaluator, draft)
        relevance_future = pool.submit(_relevance_evaluator, draft, key_aspects)
        compliance_future = pool.submit(_compliance_evaluator, draft, rules)
        readability = readability_future.result()
        relevance = relevance_future.result()
        compliance = compliance_future.result()

    feedback: list[str] = []
    if not rules:
        compliance = {
            "pass": False,
            "rule_ids": [],
            "violations": ["Approved company compliance rules are unavailable; human review is required."],
        }
    if relevance["missing_aspects"]:
        feedback.append("Include these omitted RFP requirements verbatim: " + "; ".join(relevance["missing_aspects"]))
    if compliance["violations"]:
        feedback.extend(compliance["violations"])
    if not readability["pass"]:
        feedback.append("Shorten long sentences and use clear, direct language.")
    return {
        "section_id": department_id,
        "department_id": department_id,
        "readability": readability,
        "relevance": relevance,
        "compliance": compliance,
        "overall_pass": readability["pass"] and relevance["pass"] and compliance["pass"],
        "feedback_for_generator": " ".join(feedback),
    }


def _prepare_sections(rows: list[DepartmentSectionAspect]) -> list[dict[str, str]]:
    grouped: dict[str, list[str]] = {}
    for row in rows:
        department = map_department(row.department, row.key_aspects)
        grouped.setdefault(department, []).append(row.key_aspects.strip())
    return [
        {
            "department_id": department,
            "department_name": department,
            "key_aspects": "\n".join(aspects),
        }
        for department, aspects in grouped.items()
    ]


def execute_generator_evaluator_loop(
    department_id: str,
    department_name: str,
    key_aspects: str,
    *,
    max_iterations: int = MAX_ITERATIONS,
) -> dict[str, Any]:
    """Run one bounded section loop and always return its last provisional draft."""
    feedback = ""
    draft = ""
    evaluation: dict[str, Any] = {}
    iteration = 0
    for iteration in range(1, max(1, max_iterations) + 1):
        draft = generate_department_draft(department_id, department_name, key_aspects, feedback)
        evaluation = evaluate_department_draft(department_id, draft, key_aspects)
        if evaluation["overall_pass"]:
            break
        feedback = evaluation["feedback_for_generator"]
    return {
        "section_id": department_id,
        "department_id": department_id,
        "department_name": department_name,
        "key_aspects": key_aspects,
        "draft": draft,
        "iteration_count": iteration,
        "evaluation_result": evaluation,
    }


def generate_ticket_response(engine: Any, ticket_id: str) -> dict[str, Any]:
    """Generate and persist response sections for a completed Part 1 ticket."""
    with Session(engine) as session:
        ticket = session.get(RFPTicket, ticket_id)
        if ticket is None:
            raise ValueError("RFP ticket not found")
        if ticket.status != "intake_complete":
            raise ValueError("RFP intake must be complete before response generation")
        handoff = ticket.synthesizer_payload or {}
        rows = session.exec(select(DepartmentSectionAspect).where(DepartmentSectionAspect.ticket_id == ticket_id)).all()
        sections = _prepare_sections(rows)
        if not sections:
            # Keep any structured handoff sections that do not have companion rows.
            for workstream in handoff.get("workstream_structure", []):
                aspects = str(workstream.get("key_aspects", "")).strip()
                if aspects:
                    department = map_department(str(workstream.get("department", "")), aspects)
                    existing = next((item for item in sections if item["department_id"] == department), None)
                    if existing:
                        existing["key_aspects"] += "\n" + aspects
                    else:
                        sections.append({"department_id": department, "department_name": department, "key_aspects": aspects})
        if not sections:
            raise ValueError("The structured Part 1 handoff contains no response requirements")

        if ticket.status not in {"intake_complete", "drafting"}:
            raise ValueError("RFP intake must be complete before response generation")
        ticket.status = "drafting"
        ticket.updated_at = datetime.now(timezone.utc)
        session.add(ticket)
        session.commit()

    try:
        with Session(engine) as session:
            ticket = session.get(RFPTicket, ticket_id)
            ticket.status = "under_evaluation"
            ticket.updated_at = datetime.now(timezone.utc)
            session.add(ticket)
            session.commit()

        with ThreadPoolExecutor(max_workers=min(8, len(sections))) as pool:
            results = list(pool.map(lambda section: execute_generator_evaluator_loop(**section), sections))

        needs_review = any(not section["evaluation_result"]["overall_pass"] for section in results)
        with Session(engine) as session:
            ticket = session.get(RFPTicket, ticket_id)
            existing = session.exec(select(RFPResponseSection).where(RFPResponseSection.ticket_id == ticket_id)).all()
            for row in existing:
                session.delete(row)
            for section in results:
                session.add(
                    RFPResponseSection(
                        ticket_id=ticket_id,
                        section_id=section["section_id"],
                        department_id=section["department_id"],
                        department_name=section["department_name"],
                        draft=section["draft"],
                        iteration_count=section["iteration_count"],
                        evaluation_result=section["evaluation_result"],
                    )
                )
            ticket.status = "needs_human_review" if needs_review else "under_evaluation"
            ticket.updated_at = datetime.now(timezone.utc)
            ticket.raw_metadata = {**ticket.raw_metadata, "response_generation": {"iterations": MAX_ITERATIONS, "section_count": len(results)}}
            session.add(ticket)
            session.commit()

        return {
            "ticket_id": ticket_id,
            "status": "needs_human_review" if needs_review else "under_evaluation",
            "sections": results,
        }
    except Exception:
        with Session(engine) as session:
            ticket = session.get(RFPTicket, ticket_id)
            if ticket:
                ticket.status = "needs_human_review"
                ticket.raw_metadata = {**ticket.raw_metadata, "response_generation_error": "Response generation failed; preserved Part 1 handoff for human review."}
                session.add(ticket)
                session.commit()
        raise
