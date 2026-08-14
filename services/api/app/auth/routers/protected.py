"""Cross-functional business routes hardened with get_current_user."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ..deps import get_current_user

router = APIRouter(tags=["protected-operations"])


class BookingRequest(BaseModel):
    clinic_id: str
    patient_ref: str = Field(
        description="Opaque non-PHI booking reference (never a patient_id / MRN)."
    )
    slot_iso: str


class ClaimUpdateRequest(BaseModel):
    coding_notes: str = ""
    status: str = "under_review"


class ClinicalDocRequest(BaseModel):
    encounter_ref: str = Field(
        description="Opaque encounter reference; do not include PHI free-text."
    )
    draft_sections: list[str]


@router.get("/clinics/telemetry")
async def clinics_telemetry(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    return {
        "requested_by": current_user["id"],
        "locations_online": 12,
        "alerts": [],
        "status": "ok",
    }


@router.post("/appointments/booking")
async def create_booking(
    payload: BookingRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    return {
        "booking_id": str(uuid4()),
        "clinic_id": payload.clinic_id,
        "patient_ref": payload.patient_ref,
        "slot_iso": payload.slot_iso,
        "created_by": current_user["id"],
        "status": "reserved",
    }


@router.put("/billing/claims/{claim_id}")
async def update_claim(
    claim_id: str,
    payload: ClaimUpdateRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    return {
        "claim_id": claim_id,
        "status": payload.status,
        "coding_notes": payload.coding_notes,
        "reviewed_by": current_user["id"],
    }


@router.get("/compliance/audit-logs")
async def compliance_audit_logs(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    return {
        "requested_by": current_user["id"],
        "entries": [],
        "note": "Audit log query layer placeholder — no PHI returned.",
    }


@router.post("/ai/clinical-documentation")
async def ai_clinical_documentation(
    payload: ClinicalDocRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    return {
        "request_id": str(uuid4()),
        "encounter_ref": payload.encounter_ref,
        "suggested_sections": payload.draft_sections or ["subjective", "assessment"],
        "generated_by_user": current_user["id"],
        "requires_clinician_verification": True,
    }
