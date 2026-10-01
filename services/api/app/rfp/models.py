"""Relational records for asynchronous RFP intake and its handoff contract."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Text
from sqlalchemy.types import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


def _now() -> datetime:
    return datetime.now(timezone.utc)


class RFPTicket(SQLModel, table=True):
    __tablename__ = "rfp_tickets"
    __table_args__ = (
        CheckConstraint(
            "status IN ('analyzing', 'discarded', 'intake_complete', 'drafting', "
            "'under_evaluation', 'needs_human_review', 'waiting_for_approval', 'done')",
            name="ck_rfp_ticket_status",
        ),
        {"extend_existing": True},
    )

    ticket_id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    status: str = Field(default="analyzing", index=True)
    file_path: str
    raw_metadata: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON().with_variant(JSONB, "postgresql"), nullable=False),
    )
    metrics: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON().with_variant(JSONB, "postgresql"), nullable=False),
    )
    synthesizer_payload: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON().with_variant(JSONB, "postgresql"), nullable=False),
    )
    created_at: datetime = Field(default_factory=_now, sa_column=Column(DateTime(timezone=True), nullable=False))
    updated_at: datetime = Field(default_factory=_now, sa_column=Column(DateTime(timezone=True), nullable=False))


class DepartmentSectionAspect(SQLModel, table=True):
    __tablename__ = "department_section_aspects"
    __table_args__ = {"extend_existing": True}

    id: int | None = Field(default=None, primary_key=True)
    ticket_id: str = Field(foreign_key="rfp_tickets.ticket_id", index=True, ondelete="CASCADE")
    department: str
    key_aspects: str = Field(sa_type=Text)
    contacts: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSON().with_variant(JSONB, "postgresql"), nullable=False),
    )


class RFPApprovalBranch(SQLModel, table=True):
    """Durable, department-scoped approval/checkpoint state for one ticket."""

    __tablename__ = "rfp_approval_branches"
    __table_args__ = ({"extend_existing": True},)

    branch_id: str = Field(primary_key=True)
    ticket_id: str = Field(foreign_key="rfp_tickets.ticket_id", index=True, ondelete="CASCADE")
    department_id: str
    department_name: str
    owner: str
    status: str = Field(default="waiting_for_approval", index=True)
    thread_id: str = Field(index=True, unique=True)
    checkpoint: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON().with_variant(JSONB, "postgresql"), nullable=False),
    )
    decision: str | None = None
    feedback: str | None = Field(default=None, sa_type=Text)
    iteration_count: int = Field(default=0)
    updated_at: datetime = Field(default_factory=_now, sa_column=Column(DateTime(timezone=True), nullable=False))


class RFPLineageEvent(SQLModel, table=True):
    """Append-only node lineage for approval and proposal synthesis."""

    __tablename__ = "rfp_lineage_events"
    __table_args__ = ({"extend_existing": True},)

    event_id: int | None = Field(default=None, primary_key=True)
    ticket_id: str = Field(foreign_key="rfp_tickets.ticket_id", index=True, ondelete="CASCADE")
    branch_id: str | None = Field(default=None, foreign_key="rfp_approval_branches.branch_id", index=True)
    agent_id: str
    input_payload: dict[str, Any] = Field(sa_column=Column(JSON().with_variant(JSONB, "postgresql"), nullable=False))
    output_payload: dict[str, Any] = Field(sa_column=Column(JSON().with_variant(JSONB, "postgresql"), nullable=False))
    timestamp: datetime = Field(default_factory=_now, sa_column=Column(DateTime(timezone=True), nullable=False))


class RFPFinalProposal(SQLModel, table=True):
    """Synthesized sales deliverable after every departmental sign-off."""

    __tablename__ = "rfp_final_proposals"
    __table_args__ = ({"extend_existing": True},)

    ticket_id: str = Field(foreign_key="rfp_tickets.ticket_id", primary_key=True, ondelete="CASCADE")
    document: dict[str, Any] = Field(sa_column=Column(JSON().with_variant(JSONB, "postgresql"), nullable=False))
    created_at: datetime = Field(default_factory=_now, sa_column=Column(DateTime(timezone=True), nullable=False))
