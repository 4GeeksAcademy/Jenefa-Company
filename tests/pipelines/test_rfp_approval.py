from __future__ import annotations

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.rfp.models import (
    DepartmentSectionAspect,
    RFPApprovalBranch,
    RFPFinalProposal,
    RFPLineageEvent,
    RFPTicket,
)
from data.pipelines.rfp_approval import (
    MAX_APPROVAL_ITERATIONS,
    arbitrate_conflicts,
    begin_approval,
    get_approval_state,
    submit_approval,
)
from data.pipelines.rfp_response import RFPResponseSection


def _engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


def _ticket(engine, ticket_id="approval-test"):
    with Session(engine) as session:
        session.add(
            RFPTicket(
                ticket_id=ticket_id,
                status="under_evaluation",
                file_path="unused.pdf",
                synthesizer_payload={},
            )
        )
        for index, (department, domain) in enumerate(
            [
                ("Clinical Operations", "Clinical Operations & Delivery"),
                ("Compliance & Data Governance", "Compliance & Data Governance"),
            ]
        ):
            section_id = f"section-{index}"
            session.add(
                DepartmentSectionAspect(
                    ticket_id=ticket_id,
                    department=department,
                    key_aspects=f"Review {department} requirements for this proposal.",
                    contacts=[],
                )
            )
            session.add(
                RFPResponseSection(
                    ticket_id=ticket_id,
                    section_id=section_id,
                    department_id=domain,
                    department_name=department,
                    draft=f"## {department}\n\n### HealthCore response position\nDraft for {department} review.",
                    iteration_count=2,
                    evaluation_result={
                        "overall_pass": True,
                        "readability": {"pass": True, "score": 8.0, "details": "Clear."},
                        "relevance": {"pass": True, "missing_aspects": []},
                        "compliance": {"pass": True, "rule_ids": [], "violations": []},
                        "feedback_for_generator": "",
                    },
                )
            )
        session.commit()


def test_scoped_interrupts_allow_department_b_to_approve_while_a_waits():
    engine = _engine()
    _ticket(engine)
    started = begin_approval(engine, "approval-test")
    assert started["status"] == "waiting_for_approval"
    assert {b["thread_id"] for b in started["branches"]} == {
        "rfp-approval-test:Clinical Operations",
        "rfp-approval-test:Compliance and Data Governance",
    }

    decision = submit_approval(engine, "approval-test", "Clinical Operations", "approve")
    state = get_approval_state(engine, "approval-test")
    branches = {branch["department"]: branch for branch in state["branches"]}
    assert decision["ticket_status"] == "waiting_for_approval"
    assert branches["Clinical Operations"]["status"] == "approved"
    assert branches["Compliance and Data Governance"]["status"] == "waiting_for_approval"
    assert state["final_proposal"] is None


def test_request_changes_resumes_one_branch_and_records_changelog():
    engine = _engine()
    _ticket(engine)
    begin_approval(engine, "approval-test")
    result = submit_approval(
        engine,
        "approval-test",
        "Clinical Operations",
        "request_changes",
        "Clarify that staffing availability requires confirmation.",
    )
    state = get_approval_state(engine, "approval-test")
    branch = next(item for item in state["branches"] if item["department"] == "Clinical Operations")
    assert result["branch_status"] == "waiting_for_approval"
    assert branch["iteration_count"] == 1
    assert len(branch["changelog"]) == 2
    assert "Clarify that staffing availability" in branch["draft"]


def test_invalid_decisions_and_feedback_are_rejected():
    engine = _engine()
    _ticket(engine)
    begin_approval(engine, "approval-test")
    for decision, feedback in [("yes", ""), ("reject", " ")]:
        try:
            submit_approval(engine, "approval-test", "Clinical Operations", decision, feedback)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid approval payload was accepted")


def test_iteration_ceiling_and_fixed_human_arbitration():
    engine = _engine()
    _ticket(engine)
    begin_approval(engine, "approval-test")
    for _ in range(MAX_APPROVAL_ITERATIONS):
        try:
            submit_approval(
                engine,
                "approval-test",
                "Clinical Operations",
                "request_changes",
                "Request a further review.",
            )
        except ValueError:
            # A branch at the ceiling is no longer waiting; only reach it once.
            break
    state = get_approval_state(engine, "approval-test")
    branch = next(item for item in state["branches"] if item["department"] == "Clinical Operations")
    assert branch["status"] == "needs_human_review"
    with Session(engine) as session:
        assert session.get(RFPApprovalBranch, branch["branch_id"]).iteration_count == MAX_APPROVAL_ITERATIONS

    try:
        arbitrate_conflicts(engine, "approval-test", {"conflicts": [{"type": "cross_border", "resolution": "keep data regional"}]}, "someone else")
    except ValueError as exc:
        assert "Dr. Sandra Okonkwo" in str(exc)
    else:
        raise AssertionError("Unauthorized arbiter was accepted")
    result = arbitrate_conflicts(
        engine,
        "approval-test",
        {"conflicts": [{"type": "cross_border_data_scope", "resolution": "keep US and UK records in their own regions"}]},
        "Dr. Sandra Okonkwo",
    )
    assert result["actor"] == "Dr. Sandra Okonkwo"


def test_all_human_signoffs_synthesize_final_proposal_and_lineage():
    engine = _engine()
    _ticket(engine)
    begin_approval(engine, "approval-test")
    submit_approval(engine, "approval-test", "Clinical Operations", "approve")
    result = submit_approval(engine, "approval-test", "Compliance and Data Governance", "approve")
    assert result["ticket_status"] == "done"
    assert result["final_proposal"]["approval_status"] == "all_departments_approved"
    assert {"us_commercial", "uk_private_pay", "uk_nhs"} == set(result["final_proposal"]["pricing"])
    with Session(engine) as session:
        assert session.get(RFPFinalProposal, "approval-test") is not None
        assert session.exec(select(RFPLineageEvent).where(RFPLineageEvent.ticket_id == "approval-test")).all()
