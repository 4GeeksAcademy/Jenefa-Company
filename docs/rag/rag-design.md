# HealthCore RAG design

## Pipeline
1. Markdown and text documents are placed in `docs/company-knowledge-base/`.
2. `data.process.rag.setup()` splits documents at headings and paragraph boundaries, embeds each chunk, and rebuilds the Qdrant collection.
3. Deterministic SHA-256 point IDs make rebuilds reproducible and prevent duplicate points.
4. `data.pipelines.rag.retrieve()` embeds the query with the embedding model and filters nearest-neighbor results by `RAG_MIN_SCORE`.
5. `generate_answer()` constructs an evidence-only executive prompt and calls the generation provider boundary.
6. FastAPI exposes only `{answer}` at `POST /knowledge/query`; vectors, scores, and chunks never leave the service.

## Chunking
Sections are detected from Markdown headings, then accumulated by paragraph up to 1,800 characters. A paragraph is never split, so a sentence or policy rule remains intact. Heading text is retained as the payload section for traceability.

## Embeddings and Qdrant
The embedding ID is `RAG_EMBEDDING_MODEL_ID` (default `4geeks-healthcore-embedding`) and is separate from `RAG_GENERATION_MODEL_ID` (default `4geeks-healthcore-generation`). Local development uses deterministic 384-dimensional vectors; production should replace `embed()` with the approved embedding provider while preserving the same interface. Qdrant uses cosine distance. The initial `min_score` is 0.35 and should be calibrated against labeled queries in `data/eval/test-queries.json`, selecting the lowest threshold that preserves precision and reaches Recall@3 >= 80%.
