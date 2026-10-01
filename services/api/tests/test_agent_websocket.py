"""Contract and interruption coverage for the agent WebSocket transport."""

from __future__ import annotations

import asyncio

from starlette.websockets import WebSocketDisconnect
from fastapi.testclient import TestClient


def test_agent_websocket_rejects_missing_auth(auth_db, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DB_URL", f"sqlite:///{tmp_path / 'ws.db'}")
    from app.main import app

    with TestClient(app) as client:
        try:
            with client.websocket_connect("/agent/ws?session_id=session-1"):
                raise AssertionError("unauthenticated connection should be rejected")
        except WebSocketDisconnect as exc:
            assert exc.code == 1008


def test_agent_websocket_streams_contract_frames(sample_user, auth_db, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DB_URL", f"sqlite:///{tmp_path / 'ws.db'}")
    from app.auth.security import create_access_token
    from app.main import app
    from services.langgraph_agent import websocket as agent_ws

    monkeypatch.setattr(
        agent_ws,
        "guarded_invoke_agent",
        lambda question, **kwargs: {"answer": "first\nsecond"},
    )
    token = create_access_token(sample_user["user"].id)

    with TestClient(app) as client:
        with client.websocket_connect(
            f"/agent/ws?token={token}&session_id=session-1&thread_id=thread-1"
        ) as socket:
            socket.send_json({"type": "message", "message_id": "turn-1", "text": "Hello"})
            frames = [socket.receive_json() for _ in range(3)]

    assert [frame["type"] for frame in frames] == [
        "token_chunk",
        "token_chunk",
        "generation_completed",
    ]
    assert [frame.get("text") for frame in frames[:2]] == ["first\n", "second"]
    assert all(frame["session_id"] == "session-1" for frame in frames)
    assert all(frame["thread_id"] == "thread-1" for frame in frames)


def test_agent_websocket_interrupt_cancels_active_turn(sample_user, auth_db, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DB_URL", f"sqlite:///{tmp_path / 'ws.db'}")
    from app.auth.security import create_access_token
    from app.main import app
    from services.langgraph_agent import websocket as agent_ws

    async def blocked_answer(*args, **kwargs):
        await asyncio.Future()

    monkeypatch.setattr(agent_ws, "_stream_answer", blocked_answer)
    token = create_access_token(sample_user["user"].id)

    with TestClient(app) as client:
        with client.websocket_connect(f"/agent/ws?token={token}&session_id=session-1") as socket:
            socket.send_json({"type": "message", "message_id": "turn-1", "text": "Hello"})
            socket.send_json({"type": "interrupt", "message_id": "turn-1"})
            frame = socket.receive_json()

    assert frame["type"] == "generation_interrupted"
    assert frame["message_id"] == "turn-1"


def test_local_qdrant_placeholder_uses_safe_retriever(monkeypatch) -> None:
    from services.langgraph_agent import websocket as agent_ws

    monkeypatch.setenv("QDRANT_URL", "sqlite:///:memory:")
    assert agent_ws._local_retriever()("question")[0]["text"].startswith("HealthCore operates")


def test_local_chat_answers_known_topics_instead_of_refusing(monkeypatch) -> None:
    from services.langgraph_agent import websocket as agent_ws

    monkeypatch.setenv("QDRANT_URL", "sqlite:///:memory:")
    frames: list[str] = []

    async def send(frame: str) -> None:
        frames.append(frame)

    asyncio.run(
        agent_ws._stream_answer(
            "What framework protects HIPAA records?",
            session_id="session-1",
            thread_id="thread-1",
            message_id="turn-1",
            send=send,
        )
    )

    assert "HIPAA" in "".join(frames)
    assert "I don't have information about that" not in "".join(frames)