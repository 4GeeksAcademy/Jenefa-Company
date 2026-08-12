"""HealthCore API — incident analysis plus JWT authentication layer (AUTH-01)."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse

from . import core_path as _core_path  # noqa: F401 — side effect: path bootstrap
from . import state
from .auth.database import close_db
from .auth.routers import auth as auth_router
from .auth.routers import profiles as profiles_router
from .auth.routers import protected as protected_router
from .auth.routers import users as users_router

# Import shared core after path bootstrap.
from incident_core import analyze_csv_bytes, results_to_csv_text  # noqa: E402
from incident_core.constants import RULE_LABELS  # noqa: E402


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Fail fast if SECRET_KEY / token config is missing.
    from .auth.config import get_settings

    get_settings()
    yield
    close_db()


app = FastAPI(
    title="HealthCore Unified API",
    description=(
        "Incident analysis plus zero-trust JWT authentication for user, profile, "
        "and protected operational routes."
    ),
    version="1.1.0",
    lifespan=lifespan,
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

app.include_router(auth_router.router)
app.include_router(users_router.router)
app.include_router(profiles_router.router)
app.include_router(protected_router.router)


@app.get("/health")
def health() -> dict[str, str]:
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
    # Human-readable labels for the diagnostic banner (no PHI).
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
                "detail": "No analysis results available. Upload a CSV via POST /api/incidents/analyze first.",
            },
        )

    return StreamingResponse(
        iter([csv_text]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="results.csv"'},
    )
