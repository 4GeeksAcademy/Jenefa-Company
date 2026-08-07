"""HealthCore incident analysis API (Phase 2).

Run from this directory:
    uvicorn app:app --reload --port 8000
"""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse

import state

# Shared validator lives in /scripts — keep PHI out of API responses.
_SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from incident_core import analyze_csv_bytes, results_to_csv_text  # noqa: E402
from incident_core.constants import RULE_LABELS  # noqa: E402

app = FastAPI(
    title="HealthCore Incident Analysis API",
    description="Validate patient incident CSVs without exposing PHI in responses.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/incidents/analyze")
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


@app.get("/api/incidents/results/export")
def export_results() -> Response:
    csv_text = state.get_latest_csv()
    if csv_text is None:
        return JSONResponse(
            status_code=400,
            content={
                "error": "Bad Request",
                "detail": (
                    "No analysis results available. "
                    "Upload a CSV via POST /api/incidents/analyze first."
                ),
            },
        )

    return StreamingResponse(
        iter([csv_text]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="results.csv"'},
    )
