"""Authenticated endpoints for asynchronous RFP intake tickets."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlmodel import Session, select

from ..auth.deps import get_current_user
from ..inventory.database import get_inventory_engine
from .models import DepartmentSectionAspect, RFPTicket
from data.pipelines.rfp_intake.graph import process_ticket

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/rfp", tags=["RFP intake"])
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="rfp-intake")
# Keep uploads outside the protected data/raw tree until that directory is explicitly approved.
UPLOAD_DIR = Path(__file__).resolve().parents[2] / "data" / "rfp_raw"
MAX_UPLOAD_BYTES = 25 * 1024 * 1024
FAILED_AFTER_SECONDS = 30 * 60


def _authorized_user(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    return user


def _ticket_response(ticket: RFPTicket) -> dict[str, Any]:
    age = (datetime.now(timezone.utc) - ticket.updated_at.replace(tzinfo=timezone.utc)).total_seconds()
    failed = ticket.status == "analyzing" and age > FAILED_AFTER_SECONDS
    return {
        "ticket_id": ticket.ticket_id,
        "status": "failed" if failed else ticket.status,
        "created_at": ticket.created_at.isoformat(),
        "updated_at": ticket.updated_at.isoformat(),
        "metrics": ticket.metrics,
        "raw_metadata": ticket.raw_metadata,
        "synthesizer_payload": ticket.synthesizer_payload if ticket.status == "intake_complete" else None,
        "error": "Processing heartbeat expired; retry or contact an administrator." if failed else ticket.raw_metadata.get("processing_error"),
    }


@router.post("/tickets", status_code=status.HTTP_202_ACCEPTED)
async def upload_rfp(
    file: UploadFile = File(...),
    engine: Any = Depends(get_inventory_engine),
    _user: dict[str, Any] = Depends(_authorized_user),
) -> dict[str, str]:
    if Path(file.filename or "").suffix.lower() != ".pdf":
        raise HTTPException(status_code=415, detail="Only PDF uploads are supported")
    prefix = await file.read(5)
    if prefix != b"%PDF-":
        raise HTTPException(status_code=415, detail="Uploaded file is not a valid PDF")
    body = prefix + await file.read(MAX_UPLOAD_BYTES + 1)
    if len(body) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="PDF exceeds the 25 MB upload limit")

    ticket_id = str(uuid4())
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    file_path = UPLOAD_DIR / f"{ticket_id}.pdf"
    try:
        file_path.write_bytes(body)
        with Session(engine) as session:
            ticket = RFPTicket(ticket_id=ticket_id, file_path=str(file_path))
            session.add(ticket)
            session.commit()
    except Exception:
        file_path.unlink(missing_ok=True)
        logger.exception("Failed to create RFP ticket")
        raise HTTPException(status_code=500, detail="Could not create RFP ticket")

    _executor.submit(process_ticket, engine, ticket_id)
    return {"ticket_id": ticket_id, "status": "analyzing"}


@router.get("/tickets")
def list_tickets(
    engine: Any = Depends(get_inventory_engine),
    _user: dict[str, Any] = Depends(_authorized_user),
) -> list[dict[str, Any]]:
    with Session(engine) as session:
        tickets = session.exec(select(RFPTicket).order_by(RFPTicket.created_at.desc()).limit(100)).all()
        return [_ticket_response(ticket) for ticket in tickets]


@router.get("/tickets/{ticket_id}")
def get_ticket(
    ticket_id: UUID,
    engine: Any = Depends(get_inventory_engine),
    _user: dict[str, Any] = Depends(_authorized_user),
) -> dict[str, Any]:
    with Session(engine) as session:
        ticket = session.get(RFPTicket, str(ticket_id))
        if ticket is None:
            raise HTTPException(status_code=404, detail="RFP ticket not found")
        result = _ticket_response(ticket)
        result["workstreams"] = [
            {"department": row.department, "key_aspects": row.key_aspects, "contacts": row.contacts}
            for row in session.exec(select(DepartmentSectionAspect).where(DepartmentSectionAspect.ticket_id == str(ticket_id))).all()
        ]
        return result


@router.post("/tickets/{ticket_id}/reprocess", status_code=status.HTTP_202_ACCEPTED)
def force_reprocess(
    ticket_id: UUID,
    engine: Any = Depends(get_inventory_engine),
    user: dict[str, Any] = Depends(_authorized_user),
) -> dict[str, str]:
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Administrator role required")
    with Session(engine) as session:
        ticket = session.get(RFPTicket, str(ticket_id))
        if ticket is None:
            raise HTTPException(status_code=404, detail="RFP ticket not found")
        if not Path(ticket.file_path).is_file():
            raise HTTPException(status_code=410, detail="Source PDF is no longer available")
        ticket.status = "analyzing"
        ticket.raw_metadata = {"forced": True}
        ticket.updated_at = datetime.now(timezone.utc)
        session.add(ticket)
        session.commit()
    _executor.submit(process_ticket, engine, str(ticket_id), force=True)
    return {"ticket_id": str(ticket_id), "status": "analyzing"}
