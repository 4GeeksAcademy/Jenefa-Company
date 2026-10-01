from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TypedDict

from langgraph.checkpoint.base import BaseCheckpointSaver, CheckpointTuple
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from sqlalchemy.orm.attributes import flag_modified
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
class ApprovalState(TypedDict, total=False):
    ticket_id: str
    department: str
    department_id: str
    requirements: str
    draft: str
    feedback: str
    decision: str
    iteration_count: int
    status: str
    reviewer: str


class SQLiteCheckpointSaver(BaseCheckpointSaver):
    """SQLite checkpointer for approval threads; each branch has its own thread ID."""

    def __init__(self, path: str | Path):
        super().__init__()
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS rfp_graph_checkpoints "
                "(thread_id TEXT NOT NULL, checkpoint_ns TEXT NOT NULL, checkpoint_id TEXT NOT NULL, checkpoint BLOB NOT NULL, metadata BLOB NOT NULL, PRIMARY KEY(thread_id, checkpoint_ns, checkpoint_id))"
            )

    def _connect(self):
        return sqlite3.connect(self.path)

    def get_tuple(self, config: dict[str, Any]) -> CheckpointTuple | None:
        values = config.get("configurable", {})
        thread_id, namespace = values.get("thread_id"), values.get("checkpoint_ns", "")
        checkpoint_id = values.get("checkpoint_id")
        if not thread_id:
            return None
        query = "SELECT checkpoint_id, checkpoint, metadata FROM rfp_graph_checkpoints WHERE thread_id=? AND checkpoint_ns=?"
        params: list[Any] = [thread_id, namespace]
        if checkpoint_id:
            query += " AND checkpoint_id=?"
            params.append(checkpoint_id)
        with self._connect() as connection:
            row = connection.execute(query + " ORDER BY checkpoint_id DESC LIMIT 1", params).fetchone()
        if row is None:
            return None
        return CheckpointTuple(
            config={"configurable": {"thread_id": thread_id, "checkpoint_ns": namespace, "checkpoint_id": row[0]}},
            checkpoint=self.serde.loads_typed(("msgpack", row[1])),
            metadata=self.serde.loads_typed(("msgpack", row[2])),
            parent_config=None,
            pending_writes=[],
        )

    def put(self, config: dict[str, Any], checkpoint: dict[str, Any], metadata: dict[str, Any], new_versions: dict[str, Any]) -> dict[str, Any]:
        values = config["configurable"]
        checkpoint_type, checkpoint_blob = self.serde.dumps_typed(checkpoint)
        metadata_type, metadata_blob = self.serde.dumps_typed(metadata)
        if checkpoint_type != metadata_type:
            raise TypeError("RFP checkpoint and metadata serializers differ")
        checkpoint_id = checkpoint["id"]
        with self._connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO rfp_graph_checkpoints (thread_id, checkpoint_ns, checkpoint_id, checkpoint, metadata) VALUES (?, ?, ?, ?, ?)",
                (values["thread_id"], values.get("checkpoint_ns", ""), checkpoint_id, checkpoint_blob, metadata_blob),
            )
        return {"configurable": {"thread_id": values["thread_id"], "checkpoint_ns": values.get("checkpoint_ns", ""), "checkpoint_id": checkpoint_id}}

    def put_writes(self, config: dict[str, Any], writes: list[tuple[str, Any]], task_id: str, task_path: str = "") -> None:
        return None

    def list(self, config: dict[str, Any] | None, *, filter: dict[str, Any] | None = None, before: dict[str, Any] | None = None, limit: int | None = None):
        values = (config or {}).get("configurable", {})
        thread_id = values.get("thread_id")
        if not thread_id:
            return iter(())
        namespace = values.get("checkpoint_ns", "")
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT checkpoint_id, checkpoint, metadata FROM rfp_graph_checkpoints WHERE thread_id=? AND checkpoint_ns=? ORDER BY checkpoint_id DESC",
                (thread_id, namespace),
            ).fetchall()
        if limit is not None:
            rows = rows[:limit]
        return iter(CheckpointTuple(
            config={"configurable": {"thread_id": thread_id, "checkpoint_ns": namespace, "checkpoint_id": row[0]}},
            checkpoint=self.serde.loads_typed(("msgpack", row[1])),
            metadata=self.serde.loads_typed(("msgpack", row[2])), parent_config=None, pending_writes=[]
        ) for row in rows)

    async def aget_tuple(self, config: dict[str, Any]) -> CheckpointTuple | None:
        return self.get_tuple(config)

    async def aput(self, config: dict[str, Any], checkpoint: dict[str, Any], metadata: dict[str, Any], new_versions: dict[str, Any]) -> dict[str, Any]:
        return self.put(config, checkpoint, metadata, new_versions)

    async def aput_writes(self, config: dict[str, Any], writes: list[tuple[str, Any]], task_id: str, task_path: str = "") -> None:
        return None

    async def alist(self, config: dict[str, Any] | None, *, filter: dict[str, Any] | None = None, before: dict[str, Any] | None = None, limit: int | None = None):
        return self.list(config, filter=filter, before=before, limit=limit)


def _saver_for(engine: Any) -> SQLiteCheckpointSaver:
    configured = os.getenv("RFP_APPROVAL_CHECKPOINT_DB")
    database = engine.url.database
    if configured:
        path = Path(configured)
    elif database and database != ":memory:":
        path = Path(database).resolve().parent / "rfp_approval_checkpoints.sqlite"
    else:
        path = Path.home() / ".healthcore" / "rfp_approval_checkpoints.sqlite"
    return SQLiteCheckpointSaver(path)


def _approval_node(state: ApprovalState) -> dict[str, Any]:
    response = interrupt({
        "kind": "department_approval",
        "ticket_id": state["ticket_id"],
        "department": state["department"],
        "draft": state["draft"],
        "requirements": state.get("requirements", ""),
    })
    if not isinstance(response, dict) or response.get("decision") not in {"approve", "reject", "request_changes"}:
        raise ValueError("Decision must be approve, reject, or request_changes")
    if response["decision"] in {"reject", "request_changes"} and not str(response.get("feedback", "")).strip():
        raise ValueError("Feedback is required for rejection or requested changes")
    return {"decision": response["decision"], "feedback": str(response.get("feedback", "")), "reviewer": str(response.get("reviewer", ""))}


def _decision_node(state: ApprovalState) -> dict[str, Any]:
    if state["decision"] == "approve":
        return {"status": "approved"}
    count = state.get("iteration_count", 0) + 1
    if count >= MAX_APPROVAL_ITERATIONS:
        return {"iteration_count": count, "status": "needs_human_review"}
    draft = generate_department_draft(
        state.get("department_id", state["department"]), state["department"],
        state.get("requirements", ""), feedback=state.get("feedback", "")
    )
    return {"iteration_count": count, "draft": draft, "status": "waiting_for_approval"}


def _route_after_decision(state: ApprovalState) -> str:
    return "approval" if state.get("status") == "waiting_for_approval" else END


def build_approval_graph(checkpointer: BaseCheckpointSaver):
    graph = StateGraph(ApprovalState)
    graph.add_node("approval", _approval_node)
    graph.add_node("decision", _decision_node)
    graph.add_edge(START, "approval")
    graph.add_edge("approval", "decision")
    graph.add_conditional_edges("decision", _route_after_decision, {"approval": "approval", END: END})
    return graph.compile(checkpointer=checkpointer)


def run_scoped_approval_interrupt(checkpointer: BaseCheckpointSaver, state: ApprovalState, resume: dict[str, Any] | None = None) -> dict[str, Any]:
    graph = build_approval_graph(checkpointer)
    config = {"configurable": {"thread_id": f"rfp-{state['ticket_id']}:{state['department']}"}}
    return graph.invoke(Command(resume=resume), config) if resume is not None else graph.invoke(state, config)


def _run_until_interrupt(checkpointer: BaseCheckpointSaver, state: ApprovalState) -> None:
    try:
        run_scoped_approval_interrupt(checkpointer, state)
    except Exception as exc:
        if exc.__class__.__name__ != "GraphInterrupt":
            raise


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
                if existing.status == "revision_requested":
                    existing.status = "waiting_for_approval"
                    existing.checkpoint["state"] = "waiting_for_approval"
                    existing.updated_at = _now()
                    session.add(existing)
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
        payloads = [_branch_payload(branch) for branch in branches]
    saver = _saver_for(engine)
    for branch in branches:
        _run_until_interrupt(
            saver,
            ApprovalState(
                ticket_id=ticket_id,
                department=branch.department_name,
                department_id=branch.department_id,
                requirements=branch.checkpoint.get("requirements", ""),
                draft=branch.checkpoint.get("draft", ""),
                iteration_count=branch.iteration_count,
                status=branch.status,
            ),
        )
    return {"ticket_id": ticket_id, "status": "waiting_for_approval", "branches": payloads}


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
    elif any(branch.status in {"waiting_for_approval", "revision_requested"} for branch in branches):
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
    reviewer: str | None = None,
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
        if reviewer and reviewer.casefold() != branch.owner.casefold():
            raise ValueError("Reviewer is not the assigned departmental approver")

        saver = _saver_for(engine)
        resumed = run_scoped_approval_interrupt(
            saver,
            ApprovalState(
                ticket_id=ticket_id,
                department=branch.department_name,
                department_id=branch.department_id,
                requirements=branch.checkpoint.get("requirements", ""),
                draft=branch.checkpoint.get("draft", ""),
                iteration_count=branch.iteration_count,
                status=branch.status,
            ),
            resume={"decision": decision, "feedback": feedback.strip(), "reviewer": reviewer or branch.owner},
        )
        resumed_status = resumed.get("status")
        if resumed_status == "needs_human_review":
            branch.iteration_count = resumed.get("iteration_count", branch.iteration_count)

        old_state = {"decision": decision, "feedback": feedback, "iteration_count": branch.iteration_count}
        reviewer_name = reviewer or branch.owner
        _lineage(session, ticket_id, "human_approval", old_state, {"department": canonical, "reviewer": reviewer_name}, branch_id)
        branch.decision = decision
        branch.feedback = feedback.strip() or None
        branch.updated_at = _now()
        if decision == "approve":
            branch.status = "approved"
            branch.checkpoint["state"] = "approved"
            branch.checkpoint["approved_by"] = reviewer_name
            branch.checkpoint["approved_at"] = branch.updated_at.isoformat()
            _lineage(session, ticket_id, "approval_resume", old_state, {"status": "approved"}, branch_id)
        else:
            next_iteration = resumed.get("iteration_count", branch.iteration_count + 1)
            branch.iteration_count = next_iteration
            if next_iteration >= MAX_APPROVAL_ITERATIONS:
                branch.status = "needs_human_review"
                branch.checkpoint["state"] = "needs_human_review"
                branch.checkpoint["iteration_limit_reached"] = True
                _lineage(session, ticket_id, "iteration_limit_safeguard", old_state, {"status": branch.status, "maximum": MAX_APPROVAL_ITERATIONS}, branch_id)
            else:
                branch.status = "revision_requested"
                branch.checkpoint["state"] = "revision_requested"
                branch.checkpoint["requested_decision"] = decision
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

        flag_modified(branch, "checkpoint")
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
