"""Compiled, traceable state machine for the HealthCore RAG agent."""

from __future__ import annotations

from typing import Any, Callable, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from data.pipelines.rag import generate_answer, retrieve

HONEST_REFUSAL = "I don't have information about that."


class AgentState(TypedDict):
    question: str
    retrieved_context: list[str]
    answer: str | None
    error: str | None


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
    update: dict[str, Any] = {"question": question, "retrieved_context": [], "answer": None, "error": None}
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


def generation_node(
    state: AgentState,
    *,
    generator: Callable[[str, list[dict[str, Any]]], str] = generate_answer,
    trace_callback: TraceCallback | None = None,
) -> dict[str, Any]:
    chunks = [{"text": text} for text in state["retrieved_context"]]
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
    return "error" if state.get("error") else "retrieve"


def _after_retrieve(state: AgentState) -> str:
    return "generate_answer" if state.get("retrieved_context") else "honest_refusal"


def build_graph(
    *,
    retriever: Callable[..., list[dict[str, Any]]] = retrieve,
    generator: Callable[[str, list[dict[str, Any]]], str] = generate_answer,
    trace_callback: TraceCallback | None = None,
):
    """Build and compile the workflow; compilation happens before invocation."""
    graph = StateGraph(AgentState)
    graph.add_node("receive_input", lambda state: receive_input_node(state, trace_callback=trace_callback))
    graph.add_node("retrieve", lambda state: retrieve_node(state, retriever=retriever, trace_callback=trace_callback))
    graph.add_node("generate_answer", lambda state: generation_node(state, generator=generator, trace_callback=trace_callback))
    graph.add_node("honest_refusal", lambda state: honest_refusal_node(state, trace_callback=trace_callback))
    graph.add_node("error", lambda state: honest_refusal_node(state, trace_callback=trace_callback))
    graph.add_edge(START, "receive_input")
    graph.add_conditional_edges("receive_input", _after_input, {"retrieve": "retrieve", "error": "error"})
    graph.add_conditional_edges(
        "retrieve", _after_retrieve, {"generate_answer": "generate_answer", "honest_refusal": "honest_refusal"}
    )
    graph.add_edge("generate_answer", END)
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
) -> AgentState:
    """Invoke a compiled graph with a stable thread id for checkpointing."""
    graph = agent_graph if retriever is retrieve and generator is generate_answer and trace_callback is None else build_graph(
        retriever=retriever, generator=generator, trace_callback=trace_callback
    )
    run_config = {"configurable": {"thread_id": "healthcore-agent"}, **(config or {})}
    return graph.invoke(
        {"question": question, "retrieved_context": [], "answer": None, "error": None},
        config=run_config,
    )
