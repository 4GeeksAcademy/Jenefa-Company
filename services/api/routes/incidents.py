"""Incident analysis endpoints (existing Phase 2 service)."""

from __future__ import annotations

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse, Response, StreamingResponse

from app import core_path as _core_path  # noqa: F401 — path bootstrap
from app import state
from incident_core import analyze_csv_bytes, results_to_csv_text
from incident_core.constants import RULE_LABELS

router = APIRouter(tags=["incidents"])


@router.post("/api/incidents/analyze")
async def analyze_incidents(file: UploadFile = File(...)) -> JSONResponse:
    filename = file.filename or "upload.csv"
    data = await file.read()

    if not data:
        return JSONResponse(
            status_code=400,
            content={
                "error": "Bad Request",
                "detail": "Uploaded file is empty (zero-byte upload).",
            },
        )

    result = analyze_csv_bytes(data, source_file=filename)
    if result.error:
        return JSONResponse(
            status_code=400,
            content={
                "error": "Bad Request",
                "detail": result.error,
            },
        )

    payload = result.to_dict()
    payload["invalid_breakdown_labels"] = {
        rule: RULE_LABELS[rule] for rule in result.invalid_breakdown
    }
    csv_text = results_to_csv_text(result)
    state.save_analysis(payload, csv_text)
    return JSONResponse(content=payload)


@router.get("/api/incidents/results/export")
def export_results() -> Response:
    csv_text = state.get_latest_csv()
    if csv_text is None:
        return JSONResponse(
            status_code=400,
            content={
                "error": "Bad Request",
                "detail": "No analysis results available. Upload a CSV via POST /api/incidents/analyze first.",
            },
        )

    return StreamingResponse(
        iter([csv_text]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="results.csv"'},
    )
