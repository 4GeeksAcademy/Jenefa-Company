"""Retrieval and generation orchestration for the stateless HealthCore RAG service."""
from __future__ import annotations

import os
from typing import Any, Callable

from data.process.rag import COLLECTION_NAME, _client, embed

DEFAULT_MIN_SCORE = float(os.getenv("RAG_MIN_SCORE", "0.35"))
GENERATION_MODEL_ID = os.getenv("RAG_GENERATION_MODEL_ID", "4geeks-healthcore-generation")


def retrieve(query: str, *, k: int = 5, min_score: float = DEFAULT_MIN_SCORE, client: Any = None) -> list[dict[str, Any]]:
    if not query.strip():
        return []
    qdrant = client or _client()
    hits = qdrant.search(collection_name=COLLECTION_NAME, query_vector=embed(query), limit=k)
    records = []
    for hit in hits:
        score = float(getattr(hit, "score", 0.0))
        payload = dict(getattr(hit, "payload", {}) or {})
        if score >= min_score:
            records.append({**payload, "score": score})
    return records


def _default_generator(prompt: str) -> str:
    # Provider integration can be supplied without coupling retrieval to an LLM SDK.
    return "The current HealthCore documentation does not contain enough verified information to answer this question."


def generate_answer(question: str, context: list[dict[str, Any]], *, generator: Callable[[str], str] | None = None) -> str:
    if context:
        evidence = "\n\n".join(item.get("text", "") for item in context)
        prompt = (
            "You are HealthCore Digital's executive chief of staff. Answer directly, professionally, "
            "and exclusively from the supplied internal evidence. Do not invent facts.\n\n"
            f"Question: {question}\n\nEvidence:\n{evidence}"
        )
    else:
        prompt = (
            "State clearly that the requested information is not present in current HealthCore "
            f"documentation. Do not speculate. Question: {question}"
        )
    return (generator or _default_generator)(prompt)


def query(question: str, *, retriever: Callable[..., list[dict[str, Any]]] | None = None, generator: Callable[[str], str] | None = None) -> str:
    context = (retriever or retrieve)(question)
    return generate_answer(question, context, generator=generator)
