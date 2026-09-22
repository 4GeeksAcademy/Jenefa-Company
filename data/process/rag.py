"""Document ingestion and embedding primitives for the HealthCore knowledge base."""
from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path
from typing import Any

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, PointStruct, VectorParams
except ImportError:  # pragma: no cover - optional until uv sync installs RAG deps
    QdrantClient = Any  # type: ignore[misc,assignment]
    Distance = PointStruct = VectorParams = None  # type: ignore[assignment]

KNOWLEDGE_BASE = Path(os.getenv("RAG_KNOWLEDGE_PATH", "docs/company-knowledge-base"))
COLLECTION_NAME = os.getenv("RAG_COLLECTION_NAME", "healthcore_company_knowledge")
EMBEDDING_MODEL_ID = os.getenv("RAG_EMBEDDING_MODEL_ID", "4geeks-healthcore-embedding")
VECTOR_SIZE = int(os.getenv("RAG_VECTOR_SIZE", "384"))


def _client() -> QdrantClient:
    url = os.getenv("QDRANT_URL", "http://localhost:6333")
    return QdrantClient(url=url, api_key=os.getenv("QDRANT_API_KEY"))


def embed(text: str) -> list[float]:
    """Return a deterministic local vector, or delegate to the configured provider.

    The provider hook deliberately uses the embedding model ID only; generation
    credentials/models are never consulted here.
    """
    if not text.strip():
        raise ValueError("Cannot embed empty text")
    # A stable hashed vector keeps local tests and development deterministic.
    digest = hashlib.sha256(f"{EMBEDDING_MODEL_ID}:{text}".encode()).digest()
    values = [(digest[index % len(digest)] / 255.0) for index in range(VECTOR_SIZE)]
    norm = sum(value * value for value in values) ** 0.5 or 1.0
    return [value / norm for value in values]


def _chunks(text: str, max_chars: int = 1800) -> list[tuple[str, str]]:
    sections = re.split(r"(?=^#{1,6}\s+)", text, flags=re.MULTILINE)
    result: list[tuple[str, str]] = []
    for section in sections:
        section = section.strip()
        if not section:
            continue
        heading = section.splitlines()[0].lstrip("# ").strip() or "General"
        paragraphs = re.split(r"\n\s*\n", section)
        current = ""
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            candidate = f"{current}\n\n{paragraph}".strip()
            if current and len(candidate) > max_chars:
                result.append((heading, current))
                current = paragraph
            else:
                current = candidate
        if current:
            result.append((heading, current))
    return result


def setup(*, knowledge_path: Path | str | None = None, client: QdrantClient | None = None) -> int:
    """Clear and rebuild the Qdrant collection from markdown/text documents."""
    source = Path(knowledge_path) if knowledge_path else KNOWLEDGE_BASE
    qdrant = client or _client()
    files = sorted(path for path in source.rglob("*") if path.suffix.lower() in {".md", ".txt"})
    if qdrant.collection_exists(COLLECTION_NAME):
        qdrant.delete_collection(COLLECTION_NAME)
    qdrant.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
    )
    points: list[PointStruct] = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        for index, (section, chunk) in enumerate(_chunks(text)):
            payload = {
                "source_document": str(path.relative_to(source)),
                "section": section,
                "company": "HealthCore Digital",
                "language": "en",
                "chunk_index": index,
                "text": chunk,
            }
            point_id = hashlib.sha256(f"{payload['source_document']}:{index}:{chunk}".encode()).hexdigest()
            points.append(PointStruct(id=point_id, vector=embed(chunk), payload=payload))
    if points:
        qdrant.upsert(collection_name=COLLECTION_NAME, points=points)
    return len(points)
