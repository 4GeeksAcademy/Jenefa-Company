"""FastAPI producer endpoints for Celery-backed async operations."""

from __future__ import annotations

from typing import Any

from celery.result import AsyncResult
from fastapi import APIRouter, status
from pydantic import BaseModel, ConfigDict

from app.tasks.celery import app as celery_app, generate_reporting_task

router = APIRouter(tags=["async-tasks"])
_ALLOWED_STATES = {"PENDING", "STARTED", "SUCCESS", "FAILURE"}


class ReportTaskRequest(BaseModel):
    """Only a database reference crosses the task boundary."""

    model_config = ConfigDict(extra="forbid")
    database_url: str | None = None


@router.post("/reports/generate", status_code=status.HTTP_202_ACCEPTED)
def generate_report(request: ReportTaskRequest) -> dict[str, str]:
    task = generate_reporting_task.delay(request.database_url)
    return {"task_id": task.id}


@router.get("/tasks/{task_id}")
def task_status(task_id: str) -> dict[str, Any]:
    result = AsyncResult(task_id, app=celery_app)
    state = result.state.lower()
    if result.state not in _ALLOWED_STATES:
        state = "pending"
    return {
        "task_id": task_id,
        "status": state,
        "result": result.result if result.state == "SUCCESS" else None,
    }
