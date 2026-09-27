"""HTTP pass-through for the compiled RAG graph."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from .graph import invoke_agent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agent", tags=["agent"])


class AgentQuery(BaseModel):
    question: str


@router.post("/query")
def query_agent(payload: AgentQuery) -> dict[str, Any]:
    try:
        state = invoke_agent(payload.question)
    except Exception:
        logger.exception("LangGraph agent execution failed")
        return {"answer": None, "error": "The agent could not process the request safely."}
    return {"answer": state.get("answer"), "error": state.get("error")}
