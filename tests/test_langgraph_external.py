from __future__ import annotations

from typing import Any

from services.langgraph_agent.graph import build_graph
from services.langgraph_agent.tools import ExternalToolError


def test_live_ticket_query_uses_incident_tool_without_rag() -> None:
    calls: list[str] = []

    def incident_tool(payload: Any) -> dict[str, str]:
        calls.append(f"incident:{payload.ticket_id}")
        return {"id": payload.ticket_id, "status": "open"}

    def rag_retriever(_: str) -> list[dict[str, str]]:
        raise AssertionError("live ticket lookup must not call RAG")

    graph = build_graph(
        retriever=rag_retriever,
        generator=lambda _, chunks: chunks[-1]["text"],
        incident_tool=incident_tool,
    )
    result = graph.invoke({"question": "What's the status of ticket 482?"}, config={"configurable": {"thread_id": "test-live"}})

    assert calls == ["incident:482"]
    assert "'status': 'open'" in result["answer"]
    assert result["contacted_sources"] == ["incident_service"]


def test_offline_ticket_service_uses_transparent_fallback() -> None:
    def incident_tool(_: Any) -> dict[str, str]:
        raise ExternalToolError("incident", "live service request failed")

    graph = build_graph(incident_tool=incident_tool)
    result = graph.invoke({"question": "What's the status of ticket 482?"}, config={"configurable": {"thread_id": "test-fallback"}})

    assert result["answer"] == "I couldn't confirm that ticket's status right now"
    assert result["error"] == "incident: live service request failed"


def test_policy_query_uses_rag_without_external_tools() -> None:
    calls: list[str] = []

    def incident_tool(_: Any) -> dict[str, str]:
        calls.append("incident")
        return {}

    def inventory_tool(_: Any) -> dict[str, str]:
        calls.append("inventory")
        return {}

    graph = build_graph(
        retriever=lambda _: [{"text": "HIPAA policy guidance"}],
        generator=lambda _, chunks: chunks[0]["text"],
        incident_tool=incident_tool,
        inventory_tool=inventory_tool,
    )
    result = graph.invoke({"question": "What is our HIPAA compliance policy?"}, config={"configurable": {"thread_id": "test-rag"}})

    assert result["answer"] == "HIPAA policy guidance"
    assert calls == []
    assert result["contacted_sources"] == []
