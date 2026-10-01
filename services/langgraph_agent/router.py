"""HTTP pass-through for the compiled RAG graph."""

from __future__ import annotations

import logging
import os
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .guardrails import guardrail_summary, guarded_invoke_agent
from .memory import AgentMemoryStore

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agent", tags=["agent"])
memory_store = AgentMemoryStore(os.getenv("AGENT_MEMORY_DB_PATH", "data/agent_memory.db"))


class AgentQuery(BaseModel):
    question: str


class MemoryProposalRequest(BaseModel):
    fact_to_remember: str = Field(min_length=1)
    justification: str = Field(min_length=1)
    originating_message: str = Field(min_length=1)


class MemoryResolutionRequest(BaseModel):
    response: str = Field(min_length=1)
    authorizing_user_metadata: dict[str, Any] = Field(default_factory=dict)


@router.post("/query")
def query_agent(payload: AgentQuery) -> dict[str, Any]:
    try:
        state = guarded_invoke_agent(payload.question)
    except Exception:
        logger.exception("LangGraph agent execution failed")
        return {"answer": None, "error": "The agent could not process the request safely."}
    return {
        "answer": state.get("answer"),
        "error": state.get("error"),
        "route": state.get("route"),
        "contacted_sources": state.get("contacted_sources", []),
        "memory_context": state.get("memory_context", []),
        "memory_proposal": state.get("memory_proposal"),
    }


@router.post("/memory/proposals")
def create_memory_proposal(payload: MemoryProposalRequest) -> dict[str, Any]:
    try:
        proposal = memory_store.propose(
            payload.fact_to_remember, payload.justification, payload.originating_message
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"proposal": proposal.__dict__, "confirmation_required": True}


@router.get("/memory/pending")
def get_pending_memory_proposal() -> dict[str, Any]:
    proposal = memory_store.pending()
    return {"proposal": proposal.__dict__ if proposal else None}


@router.post("/memory/resolve")
def resolve_memory_proposal(payload: MemoryResolutionRequest) -> dict[str, Any]:
    try:
        resolution = memory_store.resolve(
            payload.response,
            authorizing_user_metadata=payload.authorizing_user_metadata,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"resolution": resolution.__dict__}


@router.get("/memory/audit")
def get_memory_audit() -> dict[str, Any]:
    return {"entries": memory_store.audit_entries()}


@router.get("/guardrails/summary")
def get_guardrail_summary() -> dict[str, Any]:
    return guardrail_summary()
