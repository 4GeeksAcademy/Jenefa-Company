from services.langgraph_agent.graph import HONEST_REFUSAL, invoke_agent


def test_valid_query_traces_retrieve_before_generation():
    trace = []
    state = invoke_agent(
        "What framework protects US records?",
        retriever=lambda question: [{"text": "US records are protected by HIPAA."}],
        generator=lambda question, context: context[0]["text"],
        trace_callback=trace.append,
    )
    assert state["answer"] == "US records are protected by HIPAA."
    assert [entry["node"] for entry in trace] == ["receive_input", "retrieve", "generate_answer"]


def test_empty_query_follows_error_without_retrieval_or_generation():
    calls = []
    state = invoke_agent(
        "   ",
        retriever=lambda question: calls.append("retrieve") or [{"text": "bad"}],
        generator=lambda question, context: calls.append("generate") or "bad",
    )
    assert state["answer"] == HONEST_REFUSAL
    assert state["error"] == "question is required"
    assert calls == []


def test_out_of_scope_query_uses_honest_refusal():
    state = invoke_agent(
        "What is the weather?",
        retriever=lambda question: [],
        generator=lambda question, context: "must not run",
    )
    assert state["answer"] == HONEST_REFUSAL


def test_known_policy_answer_is_grounded_in_context():
    state = invoke_agent(
        "What framework protects US records?",
        retriever=lambda question: [{"text": "HIPAA applies to US protected health information."}],
        generator=lambda question, context: f"Based on policy: {context[0]['text']}",
    )
    assert "HIPAA applies to US protected health information" in state["answer"]
