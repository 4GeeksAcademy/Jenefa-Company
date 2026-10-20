"""Authenticated bidirectional WebSocket transport for agent conversations."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from jose import JWTError
from sqlmodel import Session, select

from app import state as incident_state
from app.auth import database as auth_db
from app.auth.security import decode_access_token
from app.inventory.service import list_supplies
from app.rfp.models import RFPTicket

from .guardrails import guarded_invoke_agent
from .memory import AgentMemoryStore
from .tools import IncidentLookup, InventoryLookup

logger = logging.getLogger(__name__)
router = APIRouter(tags=["agent"])
memory_store = AgentMemoryStore()
_LOCAL_KNOWLEDGE_CONTEXT = [
    {
        "text": (
            "HealthCore operates 12 clinics across the United States and the United Kingdom. "
            "US records follow HIPAA requirements and UK records follow UK GDPR. "
            "Dr. Sandra Okonkwo leads HealthCore. Clinical roles take an average of 47 days to fill. "
            "The organization tracks appointments, no-shows, revenue, and insurance claims."
        )
    }
]


def _local_retriever() -> Any:
    if os.getenv("QDRANT_URL", "").startswith("sqlite://"):
        return lambda _question: list(_LOCAL_KNOWLEDGE_CONTEXT)
    return None


def _authenticate(token: str | None) -> dict[str, Any] | None:
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if not isinstance(user_id, str):
            return None
    except JWTError:
        return None
    user = auth_db.get_user_by_id(user_id)
    if not user or not user.get("is_active", True):
        return None
    return user


def _local_incident_lookup(payload: IncidentLookup, engine: Any) -> Any:
    """Read aggregate incident results and RFP ticket status from this API."""
    with Session(engine) as session:
        if payload.ticket_id:
            ticket = session.get(RFPTicket, payload.ticket_id)
            return {
                "ticket_id": payload.ticket_id,
                "status": ticket.status if ticket else "not found",
                "updated_at": ticket.updated_at.isoformat() if ticket else None,
            }
        tickets = session.exec(select(RFPTicket).order_by(RFPTicket.updated_at.desc()).limit(10)).all()
        return {
            "latest_incident_analysis": incident_state.get_latest_result(),
            "rfp_tickets": [
                {"ticket_id": ticket.ticket_id, "status": ticket.status, "updated_at": ticket.updated_at.isoformat()}
                for ticket in tickets
            ],
        }


def _local_inventory_lookup(_payload: InventoryLookup, engine: Any) -> Any:
    """Read the same stock catalog exposed by the authenticated inventory page."""
    with Session(engine) as session:
        return [item.model_dump(mode="json") for item in list_supplies(session)]


def _frame(frame_type: str, *, session_id: str, thread_id: str, **payload: Any) -> str:
    return json.dumps(
        {"type": frame_type, "session_id": session_id, "thread_id": thread_id, **payload},
        separators=(",", ":"),
    )


def _concise_answer(answer: Any) -> str:
    text = " ".join(str(answer or "").split())
    if not text:
        return "I don't have information about that."
    end = min((index + 1 for index, character in enumerate(text) if character in ".!?"), default=len(text))
    return text[:end]


async def _stream_answer(
    question: str,
    *,
    session_id: str,
    thread_id: str,
    message_id: str,
    send: Callable[[str], Awaitable[None]],
    engine: Any | None = None,
    concise: bool = False,
) -> None:
    config = {"configurable": {"thread_id": thread_id}}
    retriever = _local_retriever()
    invoke_kwargs: dict[str, Any] = {
        "config": config,
        "memory_store": memory_store,
        "incident_tool": lambda payload: _local_incident_lookup(payload, engine),
        "inventory_tool": lambda payload: _local_inventory_lookup(payload, engine),
    }
    if retriever is not None:
        invoke_kwargs["retriever"] = retriever
    state = await asyncio.to_thread(
        guarded_invoke_agent,
        question,
        **invoke_kwargs,
    )
    answer = _concise_answer(state.get("answer")) if concise else state.get("answer") or ""
    for chunk in answer.splitlines(keepends=True) or [answer]:
        await send(
            _frame(
                "token_chunk",
                session_id=session_id,
                thread_id=thread_id,
                message_id=message_id,
                text=chunk,
            )
        )
        await asyncio.sleep(0)
    await send(
        _frame(
            "generation_completed",
            session_id=session_id,
            thread_id=thread_id,
            message_id=message_id,
        )
    )


@router.websocket("/agent/ws")
async def agent_websocket(websocket: WebSocket) -> None:
    """Stream one or more authenticated agent turns on a stable conversation thread."""
    token = websocket.query_params.get("token")
    session_id = websocket.query_params.get("session_id")
    thread_id = websocket.query_params.get("thread_id") or session_id
    user = _authenticate(token)
    if not user or not session_id or not thread_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    active: dict[str, asyncio.Task[None]] = {}
    try:
        while True:
            try:
                raw_message = await websocket.receive_text()
                message = json.loads(raw_message)
            except (json.JSONDecodeError, TypeError):
                await websocket.send_text(
                    _frame(
                        "error",
                        session_id=session_id,
                        thread_id=thread_id,
                        error="invalid JSON frame",
                    )
                )
                continue

            message_type = message.get("type")
            message_id = message.get("message_id")
            if message_type == "interrupt":
                task = active.pop(message_id, None)
                if task is not None:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                await websocket.send_text(
                    _frame(
                        "generation_interrupted",
                        session_id=session_id,
                        thread_id=thread_id,
                        message_id=message_id,
                    )
                )
                continue

            if message_type not in {"message", "user_message"}:
                await websocket.send_text(
                    _frame(
                        "error",
                        session_id=session_id,
                        thread_id=thread_id,
                        error="unsupported frame type",
                    )
                )
                continue
            question = message.get("text")
            if not isinstance(message_id, str) or not message_id or not isinstance(question, str):
                await websocket.send_text(
                    _frame(
                        "error",
                        session_id=session_id,
                        thread_id=thread_id,
                        error="message_id and text are required",
                    )
                )
                continue

            task = asyncio.create_task(
                _stream_answer(
                    question,
                    session_id=session_id,
                    thread_id=thread_id,
                    message_id=message_id,
                    engine=getattr(websocket.app.state, "inventory_engine", None),
                    send=websocket.send_text,
                    concise=True,
                )
            )
            active[message_id] = task

            def _discard(completed: asyncio.Task[None], key: str = message_id) -> None:
                active.pop(key, None)
                if not completed.cancelled() and completed.exception():
                    logger.error("WebSocket agent generation failed", exc_info=completed.exception())

            task.add_done_callback(_discard)
    except WebSocketDisconnect:
        pass
    finally:
        for task in active.values():
            task.cancel()
        if active:
            await asyncio.gather(*active.values(), return_exceptions=True)