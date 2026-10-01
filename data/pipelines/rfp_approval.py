"""Persistent human approval, arbitration, and final synthesis for RFP responses.

Approval branches are independently resumable through ticket- and department-scoped
thread IDs. A branch checkpoint is committed before returning the approval interrupt,
so API process restarts do not lose pending review state.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlmodel import Session, select

from app.rfp.models import (
    DepartmentSectionAspect,
    RFPApprovalBranch,
    RFPFinalProposal,
    RFPLineageEvent,
    RFPTicket,
)
from data.pipelines.rfp_response import RFPResponseSection, generate_department_draft

MAX_APPROVAL_ITERATIONS = 3
APPROVERS = {
    "Revenue Cycle and Billing": "Tom Callahan",
    "Clinical Operations": "Dr. Marcus Reid",
    "Compliance and Data Governance": "Claire Whitfield",
}
DEPARTMENT_ALIASES = {
    "sales & billing": "Revenue Cycle and Billing",
    "sales, revenue cycle & billing": "Revenue Cycle and Billing",
    "revenue cycle and billing": "Revenue Cycle and Billing",
    "billing": "Revenue Cycle and Billing",
    "clinical operations & delivery": "Clinical Operations",
    "clinical operations": "Clinical Operations",
    "compliance & data governance": "Compliance and Data Governance",
    "compliance and data governance": "Compliance and Data Governance",
    "compliance": "Compliance and Data Governance",
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def canonical_department(name: str) -> str:
    return DEPARTMENT_ALIASES.get(name.casefold().strip(), name.strip())


def _branch_id(ticket_id: str, department: str) -> str:
    return f"{ticket_id}:{department}"


def _lineage(
    session: Session,
    ticket_id: str,
    agent_id: str,
    input_payload: dict[str, Any],
    output_payload: dict[str, Any],
    branch_id: str | None = None,
) -> None:
    session.add(
        RFPLineageEvent(
            ticket_id=ticket_id,
            branch_id=branch_id,
            agent_id=agent_id,
            input_payload=input_payload,
            output_payload=output_payload,
            timestamp=_now(),
        )
    )


def _section_text(section: RFPResponseSection) -> str:
    return section.draft


def _require_ticket(session: Session, ticket_id: str) -> RFPTicket:
    ticket = session.get(RFPTicket, ticket_id)
    if ticket is None:
        raise ValueError("RFP ticket not found")
    return ticket


def begin_approval(engine: Any, ticket_id: str) -> dict[str, Any]:
    """Create one independent pending approval checkpoint per generated section."""
    with Session(engine) as session:
        ticket = _require_ticket(session, ticket_id)
        if ticket.status not in {"under_evaluation", "needs_human_review", "waiting_for_approval"}:
            raise ValueError("Response drafts must exist before approval can begin")
        sections = session.exec(
            select(RFPResponseSection).where(RFPResponseSection.ticket_id == ticket_id)
        ).all()
        if not sections:
            raise ValueError("No response sections are available for approval")

        branches: list[RFPApprovalBranch] = []
        for section in sections:
            department = canonical_department(section.department_name)
            branch_id = _branch_id(ticket_id, department)
            existing = session.get(RFPApprovalBranch, branch_id)
            if existing:
                branches.append(existing)
                continue
            source_aspect = session.exec(
                select(DepartmentSectionAspect).where(
                    DepartmentSectionAspect.ticket_id == ticket_id,
                    DepartmentSectionAspect.department == section.department_name,
                )
            ).first()
            requirements = source_aspect.key_aspects if source_aspect else ""
            owner = next(
                (value for key, value in APPROVERS.items() if canonical_department(key) == department),
                "Unassigned approver",
            )
            checkpoint = {
                "department_id": section.department_id,
                "department": department,
                "draft": _section_text(section),
                "requirements": requirements,
                "evaluation_result": section.evaluation_result,
                "warnings": section.evaluation_result.get("compliance", {}).get("violations", []),
                "changelog": [{"iteration": section.iteration_count, "draft": section.draft}],
                "iteration_count": 0,
                "state": "waiting_for_approval",
            }
            branch = RFPApprovalBranch(
                branch_id=branch_id,
                ticket_id=ticket_id,
                department_id=section.department_id,
                department_name=department,
                owner=owner,
                status="waiting_for_approval",
                thread_id=f"rfp-{ticket_id}:{department}",
                checkpoint=checkpoint,
                updated_at=_now(),
            )
            session.add(branch)
            _lineage(
                session,
                ticket_id,
                "approval_interrupt",
                {"department": department, "section_id": section.section_id},
                {"status": "waiting_for_approval", "thread_id": branch.thread_id},
                branch_id,
            )
            branches.append(branch)

        ticket.status = "waiting_for_approval"
        ticket.updated_at = _now()
        session.add(ticket)
        session.commit()
        return {"ticket_id": ticket_id, "status": ticket.status, "branches": [_branch_payload(branch) for branch in branches]}


def _branch_payload(branch: RFPApprovalBranch) -> dict[str, Any]:
    return {
        "branch_id": branch.branch_id,
        "department_id": branch.department_id,
        "department": branch.department_name,
        "owner": branch.owner,
        "status": branch.status,
        "decision": branch.decision,
        "feedback": branch.feedback,
        "thread_id": branch.thread_id,
        "iteration_count": branch.iteration_count,
        "draft": branch.checkpoint.get("draft", ""),
        "requirements": branch.checkpoint.get("requirements", ""),
        "warnings": branch.checkpoint.get("warnings", []),
        "changelog": branch.checkpoint.get("changelog", []),
    }


def get_approval_state(engine: Any, ticket_id: str) -> dict[str, Any]:
    with Session(engine) as session:
        ticket = _require_ticket(session, ticket_id)
        branches = session.exec(
            select(RFPApprovalBranch).where(RFPApprovalBranch.ticket_id == ticket_id)
        ).all()
        final = session.get(RFPFinalProposal, ticket_id)
        lineage = session.exec(
            select(RFPLineageEvent)
            .where(RFPLineageEvent.ticket_id == ticket_id)
            .order_by(RFPLineageEvent.timestamp, RFPLineageEvent.event_id)
        ).all()
        return {
            "ticket_id": ticket_id,
            "status": ticket.status,
            "branches": [_branch_payload(branch) for branch in branches],
            "final_proposal": final.document if final else None,
            "lineage": [
                {
                    "agent_id": event.agent_id,
                    "branch_id": event.branch_id,
                    "input_payload": event.input_payload,
                    "output_payload": event.output_payload,
                    "timestamp": event.timestamp.isoformat(),
                }
                for event in lineage
            ],
        }


def _refresh_ticket_status(session: Session, ticket: RFPTicket) -> None:
    branches = session.exec(
        select(RFPApprovalBranch).where(RFPApprovalBranch.ticket_id == ticket.ticket_id)
    ).all()
    if branches and all(branch.status == "approved" for branch in branches):
        ticket.status = "done"
    elif any(branch.status == "waiting_for_approval" for branch in branches):
        ticket.status = "waiting_for_approval"
    else:
        ticket.status = "needs_human_review"
    ticket.updated_at = _now()
    session.add(ticket)


def _synthesize(session: Session, ticket: RFPTicket, branches: list[RFPApprovalBranch]) -> dict[str, Any]:
    if not branches or any(branch.status != "approved" for branch in branches):
        raise ValueError("Every assigned department must be approved before synthesis")
    sections = [
        {
            "department": branch.department_name,
            "owner": branch.owner,
            "terms": branch.checkpoint["draft"],
            "approved_by": branch.checkpoint.get("approved_by"),
            "approved_at": branch.checkpoint.get("approved_at"),
        }
        for branch in branches
    ]
    document = {
        "title": "HealthCore Digital Proposal",
        "ticket_id": ticket.ticket_id,
        "sections": sections,
        "pricing": {
            "us_commercial": {"status": "Requires authorized pricing input", "terms": None},
            "uk_private_pay": {"status": "Requires authorized pricing input", "terms": None},
            "uk_nhs": {"status": "Requires authorized pricing input", "terms": None},
        },
        "approval_status": "all_departments_approved",
    }
    existing = session.get(RFPFinalProposal, ticket.ticket_id)
    if existing:
        existing.document = document
        existing.created_at = _now()
        session.add(existing)
    else:
        session.add(RFPFinalProposal(ticket_id=ticket.ticket_id, document=document, created_at=_now()))
    _lineage(
        session,
        ticket.ticket_id,
        "ultimate_document_synthesizer",
        {"approved_departments": [branch.department_name for branch in branches]},
        {"title": document["title"], "section_count": len(sections), "approval_status": document["approval_status"]},
    )
    ticket.status = "done"
    ticket.updated_at = _now()
    session.add(ticket)
    return document


def submit_approval(
    engine: Any,
    ticket_id: str,
    department: str,
    decision: str,
    feedback: str = "",
) -> dict[str, Any]:
    """Resume exactly one department branch with a validated reviewer decision."""
    if decision not in {"approve", "reject", "request_changes"}:
        raise ValueError("Decision must be approve, reject, or request_changes")
    if decision in {"reject", "request_changes"} and not feedback.strip():
        raise ValueError("Feedback is required for rejection or requested changes")

    canonical = canonical_department(department)
    branch_id = _branch_id(ticket_id, canonical)
    with Session(engine) as session:
        ticket = _require_ticket(session, ticket_id)
        branch = session.get(RFPApprovalBranch, branch_id)
        if branch is None:
            raise ValueError("Approval branch not found; begin approval first")
        if branch.status != "waiting_for_approval":
            raise ValueError("Approval branch is not waiting for a decision")

        old_state = {"decision": decision, "feedback": feedback, "iteration_count": branch.iteration_count}
        _lineage(session, ticket_id, "human_approval", old_state, {"department": canonical, "reviewer": branch.owner}, branch_id)
        branch.decision = decision
        branch.feedback = feedback.strip() or None
        branch.updated_at = _now()
        if decision == "approve":
            branch.status = "approved"
            branch.checkpoint["state"] = "approved"
            branch.checkpoint["approved_by"] = branch.owner
            branch.checkpoint["approved_at"] = branch.updated_at.isoformat()
            _lineage(session, ticket_id, "approval_resume", old_state, {"status": "approved"}, branch_id)
        else:
            next_iteration = branch.iteration_count + 1
            branch.iteration_count = next_iteration
            if next_iteration >= MAX_APPROVAL_ITERATIONS:
                branch.status = "needs_human_review"
                branch.checkpoint["state"] = "needs_human_review"
                branch.checkpoint["iteration_limit_reached"] = True
                _lineage(session, ticket_id, "iteration_limit_safeguard", old_state, {"status": branch.status, "maximum": MAX_APPROVAL_ITERATIONS}, branch_id)
            else:
                branch.status = "revision_requested"
                branch.checkpoint["state"] = "revision_requested"
                revised = generate_department_draft(
                    branch.department_id,
                    branch.department_name,
                    branch.checkpoint.get("requirements", ""),
                    feedback=feedback.strip(),
                )
                branch.checkpoint.setdefault("changelog", []).append(
                    {"iteration": branch.iteration_count, "decision": decision, "feedback": feedback.strip(), "draft": revised}
                )
                branch.checkpoint["draft"] = revised
                branch.status = "waiting_for_approval"
                branch.checkpoint["state"] = "waiting_for_approval"
                _lineage(
                    session,
                    ticket_id,
                    "department_generator_resume",
                    {"department": canonical, "feedback": feedback.strip(), "iteration": next_iteration},
                    {"draft": revised, "status": "waiting_for_approval"},
                    branch_id,
                )

        session.add(branch)
        _refresh_ticket_status(session, ticket)
        branches = session.exec(
            select(RFPApprovalBranch).where(RFPApprovalBranch.ticket_id == ticket_id)
        ).all()
        document = None
        if branches and all(item.status == "approved" for item in branches):
            document = _synthesize(session, ticket, branches)
        session.commit()
        return {
            "ticket_id": ticket_id,
            "department": canonical,
            "branch_status": branch.status,
            "ticket_status": ticket.status,
            "final_proposal": document,
        }


def arbitrate_conflicts(
    engine: Any,
    ticket_id: str,
    resolution: dict[str, Any],
    actor: str,
) -> dict[str, Any]:
    """Record explicit fixed-arbiter decisions; model/agent voting is not accepted."""
    if actor != "Dr. Sandra Okonkwo":
        raise ValueError("Only fixed human arbiter Dr. Sandra Okonkwo may resolve conflicts")
    if not isinstance(resolution, dict) or not resolution.get("conflicts"):
        raise ValueError("A structured non-empty conflicts list is required")
    conflicts = resolution["conflicts"]
    if not isinstance(conflicts, list) or any(not isinstance(item, dict) or not item.get("type") or not item.get("resolution") for item in conflicts):
        raise ValueError("Each conflict requires type and resolution fields")
    with Session(engine) as session:
        ticket = _require_ticket(session, ticket_id)
        _lineage(session, ticket_id, "fixed_human_arbiter", {"conflicts": conflicts}, {"actor": actor, "resolution": resolution})
        ticket.raw_metadata = {**ticket.raw_metadata, "approval_arbitration": {"actor": actor, **resolution}}
        ticket.updated_at = _now()
        session.add(ticket)
        session.commit()
        return {"ticket_id": ticket_id, "actor": actor, "resolution": resolution}
