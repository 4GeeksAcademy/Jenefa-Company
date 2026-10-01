"""Relational records for asynchronous RFP intake and its handoff contract."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Text
from sqlalchemy.types import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


def _now() -> datetime:
    return datetime.now(timezone.utc)


class RFPTicket(SQLModel, table=True):
    __tablename__ = "rfp_tickets"
    __table_args__ = {"extend_existing": True}

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
