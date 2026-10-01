from __future__ import annotations

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.rfp.models import DepartmentSectionAspect, RFPTicket
from data.pipelines.rfp_response import (
    COMPANY_RULES_PATH,
    RFPResponseSection,
    evaluate_department_draft,
    generate_department_draft,
    generate_ticket_response,
)


def test_department_generator_uses_only_handoff_requirements():
    aspects = "Provide a clinic staffing plan by location."
    draft = generate_department_draft("Clinical Operations & Delivery", "Clinical Operations & Delivery", aspects)
    assert aspects in draft
    assert "staffing plan by location" in draft
    assert "not confirmed" in draft


def test_evaluator_rejects_omitted_rfp_requirement_with_actionable_feedback():
    aspects = "Provide a clinic staffing plan by location."
    draft = "## Clinical Operations\n\n### HealthCore response position\nThis section needs review."
    result = evaluate_department_draft("Clinical Operations", draft, aspects)
    assert result["overall_pass"] is False
    assert result["relevance"]["pass"] is False
    assert "clinic staffing plan by location" in result["feedback_for_generator"]


def test_residency_violation_maps_to_explicit_company_rule():
    company_rules = COMPANY_RULES_PATH.read_text(encoding="utf-8")
    assert "US patient records remain in approved US environments" in company_rules
    draft = (
        "## Compliance & Data Governance\n\n"
        "### HealthCore response position\n"
        "All patient records will be stored only in the US."
    )
    result = evaluate_department_draft("Compliance & Data Governance", draft, "Review data residency.")
    assert result["compliance"]["pass"] is False
    assert "HC-DATA-RESIDENCY-001" in result["compliance"]["rule_ids"]
    assert "preserve US and UK residency separately" in result["compliance"]["violations"][0]


def test_ticket_response_persists_evaluations_and_keeps_provisional_sections():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        ticket = RFPTicket(
            ticket_id="response-test-ticket",
            status="intake_complete",
            file_path="unused.pdf",
            synthesizer_payload={
                "workstream_structure": [
                    {
                        "department": "Clinical Operations",
                        "key_aspects": "Provide a clinic staffing plan by location.",
                        "contacts": [],
                    }
                ]
            },
        )
        session.add(ticket)
        session.add(
            DepartmentSectionAspect(
                ticket_id=ticket.ticket_id,
                department="Clinical Operations",
                key_aspects="Provide a clinic staffing plan by location.",
                contacts=[],
            )
        )
        session.commit()

    result = generate_ticket_response(engine, "response-test-ticket")
    with Session(engine) as session:
        ticket = session.get(RFPTicket, "response-test-ticket")
        persisted = session.exec(
            select(RFPResponseSection).where(RFPResponseSection.ticket_id == "response-test-ticket")
        ).all()

    assert result["ticket_id"] == "response-test-ticket"
    assert ticket is not None and ticket.status in {"under_evaluation", "needs_human_review"}
    assert len(persisted) == 1
    assert persisted[0].draft
    assert persisted[0].evaluation_result["overall_pass"] in {True, False}
    assert persisted[0].iteration_count <= 3
