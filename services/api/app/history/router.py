"""Authenticated history listing and recording for incident analysis runs."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import Engine
from sqlmodel import Session, select

from ..auth.deps import get_current_user
from ..inventory.database import get_inventory_engine
from .models import RETENTION_DAYS, IncidentAnalysisRun, purge_expired

router = APIRouter(prefix="/history", tags=["history"])


class IncidentRunRead(BaseModel):
    id: str
    source_file: str
    total_records: int
    valid_records: int
    invalid_records: int
    created_at: str


class IncidentHistoryResponse(BaseModel):
    retention_days: int
    items: list[IncidentRunRead]


def record_incident_run(engine: Engine, payload: dict[str, Any]) -> None:
    with Session(engine) as session:
        purge_expired(session)
        session.add(
            IncidentAnalysisRun(
                source_file=str(payload.get("source_file") or "upload.csv")[:255],
                total_records=int(payload.get("total_records") or 0),
                valid_records=int(payload.get("valid_records") or 0),
                invalid_records=int(payload.get("invalid_records") or 0),
            )
        )
        session.commit()


@router.get("/incidents", response_model=IncidentHistoryResponse)
def list_incident_runs(
    request: Request,
    _current_user: dict[str, Any] = Depends(get_current_user),
) -> IncidentHistoryResponse:
    engine = get_inventory_engine(request)
    with Session(engine) as session:
        purge_expired(session)
        session.commit()
        rows = session.exec(
            select(IncidentAnalysisRun).order_by(IncidentAnalysisRun.created_at.desc()).limit(50)
        ).all()
    return IncidentHistoryResponse(
        retention_days=RETENTION_DAYS,
        items=[
            IncidentRunRead(
                id=row.id,
                source_file=row.source_file,
                total_records=row.total_records,
                valid_records=row.valid_records,
                invalid_records=row.invalid_records,
                created_at=row.created_at.isoformat(),
            )
            for row in rows
        ],
    )
