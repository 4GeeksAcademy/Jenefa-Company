"""HealthCore incident analysis API (Phase 2)."""

from __future__ import annotations

import csv
import logging

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse

from . import core_path as _core_path  # noqa: F401 — side effect: path bootstrap
from . import state
from .auth.routers.auth import router as auth_router
from .auth.routers.profiles import router as profiles_router
from .auth.routers.protected import router as protected_router
from .auth.routers.users import router as users_router
from .errors import GENERIC_INTERNAL, json_error, register_exception_handlers

# Import shared core after path bootstrap.
from incident_core import analyze_csv_bytes, results_to_csv_text  # noqa: E402
from incident_core.constants import RULE_LABELS  # noqa: E402

logger = logging.getLogger(__name__)

app = FastAPI(
    title="HealthCore Incident Analysis API",
    description="Validate patient incident CSVs without exposing PHI in responses.",
    version="1.0.0",
)

register_exception_handlers(app)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(profiles_router)
app.include_router(protected_router)

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
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/incidents/analyze")
async def analyze_incidents(file: UploadFile = File(...)) -> JSONResponse:
    filename = file.filename or "upload.csv"

    try:
        data = await file.read()
    except OSError:
        logger.exception("Failed to read uploaded incident file")
        return json_error(400, "The uploaded file could not be read.")

    if not data:
        return json_error(400, "Uploaded file is empty (zero-byte upload).")

    try:
        result = analyze_csv_bytes(data, source_file=filename)
    except UnicodeDecodeError:
        return json_error(400, "Unreadable data: file is not valid UTF-8.")
    except csv.Error:
        logger.exception("CSV parser rejected incident upload")
        return json_error(400, "The file could not be parsed as CSV.")
    except ValueError:
        logger.exception("Incident CSV layout was invalid")
        return json_error(400, "The file layout is invalid.")

    if result.error:
        return json_error(400, result.error)

    payload = result.to_dict()
    # Human-readable labels for the diagnostic banner (no PHI).
    payload["invalid_breakdown_labels"] = {
        rule: RULE_LABELS[rule] for rule in result.invalid_breakdown
    }

    try:
        csv_text = results_to_csv_text(result)
    except csv.Error:
        logger.exception("Failed to serialize incident results")
        return json_error(500, GENERIC_INTERNAL)

    try:
        state.save_analysis(payload, csv_text)
    except (TypeError, ValueError):
        logger.exception("Failed to store incident analysis")
        return json_error(500, GENERIC_INTERNAL)

    return JSONResponse(content=payload)


@app.get("/api/incidents/results/export")
def export_results() -> Response:
    csv_text = state.get_latest_csv()
    if csv_text is None:
        return json_error(
            400,
            "No analysis results available. Upload a CSV via POST /api/incidents/analyze first.",
        )

    return StreamingResponse(
        iter([csv_text]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="results.csv"'},
    )
