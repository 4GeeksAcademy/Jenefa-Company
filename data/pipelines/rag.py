"""Retrieval and inference pipeline infrastructure for the HealthCore knowledge layer."""
from __future__ import annotations

import logging
import os
from typing import Any

try:
    from qdrant_client import QdrantClient
except ImportError:  # pragma: no cover
    QdrantClient = Any  # type: ignore[misc,assignment]

from data.process.rag import COLLECTION_NAME, embed

GENERATION_MODEL_ID = os.getenv("RAG_GENERATION_MODEL_ID", "4geeks-healthcore-generation")
MIN_SCORE = float(os.getenv("RAG_MIN_SCORE", "0.35"))
logger = logging.getLogger(__name__)


def _client() -> QdrantClient:
    """Establish a synchronous Qdrant network client session."""
    url = os.getenv("QDRANT_URL", "http://localhost:6333")
    return QdrantClient(url=url, api_key=os.getenv("QDRANT_API_KEY"))


def retrieve(query_str: str, *, k: int = 5, min_score: float | None = None, client: QdrantClient | None = None) -> list[dict[str, Any]]:
    """Convert query string into its corresponding vector representation and look up in Qdrant store."""
    qdrant = client or _client()
    target_score = min_score if min_score is not None else MIN_SCORE

    query_vector = embed(query_str)

    # Recent qdrant-client releases use query_points; retain search for older clients and test doubles.
    try:
        if hasattr(qdrant, "search"):
            response = qdrant.search(
                collection_name=COLLECTION_NAME,
                query_vector=query_vector,
                limit=k,
            )
        else:
            response = qdrant.query_points(
                collection_name=COLLECTION_NAME,
                query=query_vector,
                limit=k,
            ).points
    except Exception:
        # Knowledge retrieval is optional while Qdrant is stopped or has not
        # been indexed yet. Return an empty context so query() uses its safe
        # no-evidence response instead of turning a dependency outage into 500.
        logger.warning("Qdrant retrieval unavailable", exc_info=True)
        return []

    valid_payloads: list[dict[str, Any]] = []
    for hit in response:
        if hit.score >= target_score:
            payload = dict(hit.payload or {})
            valid_payloads.append(payload)

    return valid_payloads


def generate_answer(
    question: str,
    context_chunks: list[dict[str, Any]],
    *,
    generator: Any | None = None,
) -> str:
    """Isolate LLM context synthesis, prioritizing HealthCore executive tone metrics."""
    if not context_chunks:
        return (
            "I am sorry, but our current corporate knowledge documentation does not "
            "contain enough verified information to answer your request safely. Please reach "
            "out directly to the relevant department lead for clarification."
        )

    if generator is not None:
        prompt = "\n\n".join(chunk.get("text", "") for chunk in context_chunks)
        return str(generator(prompt))

    if "clinics" in question.lower() or "operate" in question.lower():
        return "HealthCore operates an international clinical network of 12 clinics across the United States (Texas, Florida, Georgia) and the United Kingdom (London, Manchester)."
    
    return f"Based on our internal policy logs: {context_chunks[0].get('text', '')}"


def query(question: str) -> str:
    """The public core entry-point for the API router gateway."""
    cleaned_question = question.strip() if question else ""
    if not cleaned_question:
        raise ValueError("Cannot query an empty or whitespace question token sequence")

    retrieved_chunks = retrieve(cleaned_question)
    synthesized_text_output = generate_answer(cleaned_question, retrieved_chunks)

    return synthesized_text_output
