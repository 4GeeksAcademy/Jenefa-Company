"""Compiled, traceable state machine for the HealthCore RAG agent."""

from __future__ import annotations

import re
from typing import Any, Callable, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from data.pipelines.rag import generate_answer, retrieve
from .tools import (
    ExternalToolError,
    IncidentLookup,
    InventoryLookup,
    format_tool_context,
    lookup_incident,
    lookup_inventory,
)
from .memory import AgentMemoryStore

HONEST_REFUSAL = "I don't have information about that."


class AgentState(TypedDict):
    question: str
    retrieved_context: list[str]
    answer: str | None
    error: str | None
    route: str
    live_context: list[str]
    contacted_sources: list[str]
    memory_context: list[str]
    memory_proposal: dict[str, Any] | None


TraceCallback = Callable[[dict[str, Any]], None]


def _trace(state: AgentState, node: str, trace_callback: TraceCallback | None) -> None:
    if trace_callback:
        trace_callback(
            {
                "node": node,
                "input": dict(state),
                "output": dict(state),
            }
        )


def receive_input_node(
    state: AgentState, *, trace_callback: TraceCallback | None = None
) -> dict[str, Any]:
    question = (state.get("question") or "").strip()
    update: dict[str, Any] = {
        "question": question, "retrieved_context": [], "live_context": [],
        "contacted_sources": [], "answer": None, "error": None,
        "memory_context": state.get("memory_context", []), "memory_proposal": state.get("memory_proposal"),
        "route": _route_question(question),
    }
    if not question:
        update["error"] = "question is required"
        update["answer"] = HONEST_REFUSAL
    next_state = {**state, **update}
    _trace(next_state, "receive_input", trace_callback)
    return update


def retrieve_node(
    state: AgentState,
    *,
    retriever: Callable[..., list[dict[str, Any]]] = retrieve,
    trace_callback: TraceCallback | None = None,
) -> dict[str, Any]:
    chunks = retriever(state["question"])
    context = [str(chunk.get("text", "")) for chunk in chunks if chunk.get("text")]
    update = {"retrieved_context": context, "error": None}
    _trace({**state, **update}, "retrieve", trace_callback)
    return update


def _route_question(question: str) -> str:
    lowered = question.lower()
    live = any(term in lowered for term in ("ticket", "incident", "stock", "inventory", "product"))
    docs = any(term in lowered for term in ("policy", "hipaa", "gdpr", "compliance", "regulation", "procedure"))
    if live and docs:
        return "live_then_rag"
    if live:
        return "live"
    return "rag"


def live_lookup_node(
    state: AgentState,
    *,
    incident_tool: Callable[[IncidentLookup], Any] = lookup_incident,
    inventory_tool: Callable[[InventoryLookup], Any] = lookup_inventory,
    trace_callback: TraceCallback | None = None,
) -> dict[str, Any]:
    question = state["question"]
    lowered = question.lower()
    contexts: list[str] = []
    sources: list[str] = []
    try:
        ticket_match = re.search(r"(?:ticket|incident)\s*[#:]?\s*([A-Za-z0-9_-]+)", question, re.I)
        if "ticket" in lowered or "incident" in lowered:
            result = incident_tool(IncidentLookup(ticket_id=ticket_match.group(1) if ticket_match else None))
            contexts.append(format_tool_context("incident", result))
            sources.append("incident_service")
        if "stock" in lowered or "inventory" in lowered or "product" in lowered:
            result = inventory_tool(InventoryLookup())
            contexts.append(format_tool_context("inventory", result))
            sources.append("inventory_service")
        update = {"live_context": contexts, "contacted_sources": sources, "error": None}
    except ExternalToolError as exc:
        update = {"live_context": contexts, "contacted_sources": sources, "error": f"{exc.tool}: {exc.reason}"}
    _trace({**state, **update}, "live_tool_lookup", trace_callback)
    return update


def fallback_node(state: AgentState, *, trace_callback: TraceCallback | None = None) -> dict[str, Any]:
    question = state["question"].lower()
    subject = "inventory" if any(term in question for term in ("stock", "inventory", "product")) else "ticket"
    update = {"answer": f"I couldn't confirm that {subject}'s status right now", "error": state.get("error")}
    _trace({**state, **update}, "external_tool_fallback", trace_callback)
    return update


def generation_node(
    state: AgentState,
    *,
    generator: Callable[[str, list[dict[str, Any]]], str] = generate_answer,
    trace_callback: TraceCallback | None = None,
) -> dict[str, Any]:
    chunks = [{"text": text} for text in [
        *state.get("retrieved_context", []),
        *state.get("live_context", []),
        *state.get("memory_context", []),
    ]]
    update = {"answer": generator(state["question"], chunks), "error": None}
    _trace({**state, **update}, "generate_answer", trace_callback)
    return update


def honest_refusal_node(
    state: AgentState, *, trace_callback: TraceCallback | None = None
) -> dict[str, Any]:
    update = {"answer": HONEST_REFUSAL}
    _trace({**state, **update}, "honest_refusal", trace_callback)
    return update


def _after_input(state: AgentState) -> str:
    return "error" if state.get("error") else state.get("route", "rag")


def _after_retrieve(state: AgentState) -> str:
    return "generate_answer" if state.get("retrieved_context") or state.get("memory_context") else "honest_refusal"


def build_graph(
    *,
    retriever: Callable[..., list[dict[str, Any]]] = retrieve,
    generator: Callable[[str, list[dict[str, Any]]], str] = generate_answer,
    trace_callback: TraceCallback | None = None,
    incident_tool: Callable[[IncidentLookup], Any] = lookup_incident,
    inventory_tool: Callable[[InventoryLookup], Any] = lookup_inventory,
):
    """Build and compile the workflow; compilation happens before invocation."""
    graph = StateGraph(AgentState)
    graph.add_node("receive_input", lambda state: receive_input_node(state, trace_callback=trace_callback))
    graph.add_node("retrieve", lambda state: retrieve_node(state, retriever=retriever, trace_callback=trace_callback))
    graph.add_node("generate_answer", lambda state: generation_node(state, generator=generator, trace_callback=trace_callback))
    graph.add_node("honest_refusal", lambda state: honest_refusal_node(state, trace_callback=trace_callback))
    graph.add_node("error", lambda state: honest_refusal_node(state, trace_callback=trace_callback))
    graph.add_node("live_lookup", lambda state: live_lookup_node(state, incident_tool=incident_tool, inventory_tool=inventory_tool, trace_callback=trace_callback))
    graph.add_node("fallback", lambda state: fallback_node(state, trace_callback=trace_callback))
    graph.add_edge(START, "receive_input")
    graph.add_conditional_edges("receive_input", _after_input, {"rag": "retrieve", "live": "live_lookup", "live_then_rag": "live_lookup", "error": "error"})
    graph.add_conditional_edges("live_lookup", lambda state: "fallback" if state.get("error") else ("retrieve" if state.get("route") == "live_then_rag" else "generate_answer"), {"fallback": "fallback", "retrieve": "retrieve", "generate_answer": "generate_answer"})
    graph.add_conditional_edges(
        "retrieve", _after_retrieve, {"generate_answer": "generate_answer", "honest_refusal": "honest_refusal"}
    )
    graph.add_edge("generate_answer", END)
    graph.add_edge("fallback", END)
    graph.add_edge("honest_refusal", END)
    graph.add_edge("error", END)
    return graph.compile(checkpointer=MemorySaver())


agent_graph = build_graph()


def invoke_agent(
    question: str,
    *,
    config: dict[str, Any] | None = None,
    retriever: Callable[..., list[dict[str, Any]]] = retrieve,
    generator: Callable[[str, list[dict[str, Any]]], str] = generate_answer,
    trace_callback: TraceCallback | None = None,
    memory_store: AgentMemoryStore | None = None,
) -> AgentState:
    """Invoke a compiled graph with a stable thread id for checkpointing."""
    graph = agent_graph if retriever is retrieve and generator is generate_answer and trace_callback is None else build_graph(
        retriever=retriever, generator=generator, trace_callback=trace_callback
    )
    run_config = {"configurable": {"thread_id": "healthcore-agent"}, **(config or {})}
    return graph.invoke(
        {
            "question": question,
            "retrieved_context": [],
            "live_context": [],
            "contacted_sources": [],
            "memory_context": [],
            "memory_proposal": None,
            "route": "rag",
            "answer": None,
            "error": None,
            "memory_context": memory_store.search(question) if memory_store else [],
            "memory_proposal": None,
        },
        config=run_config,
    )
