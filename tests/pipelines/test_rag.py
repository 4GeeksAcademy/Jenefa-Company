from types import SimpleNamespace

from data.pipelines.rag import generate_answer, retrieve


def test_retrieve_filters_low_scores():
    client = SimpleNamespace(search=lambda **kwargs: [
        SimpleNamespace(score=0.9, payload={"text": "accepted"}),
        SimpleNamespace(score=0.2, payload={"text": "rejected"}),
    ])
    result = retrieve("policy", min_score=0.5, client=client)
    assert [item["text"] for item in result] == ["accepted"]


def test_empty_context_is_honest():
    answer = generate_answer("unknown", [])
    assert "does not contain enough verified information" in answer
    assert "score" not in answer


def test_generation_returns_text_only():
    answer = generate_answer("where?", [{"text": "US records stay in the US."}], generator=lambda prompt: "US records stay in the US.")
    assert answer == "US records stay in the US."
