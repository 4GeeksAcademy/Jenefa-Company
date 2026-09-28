# Architecture Design Document: HealthCore Knowledge Layer (RAG)

## 1. End-to-End System Process Flow
The implementation separates data ingestion from inference logic into two distinct, decoupled pipelines running over a centralized **Qdrant Vector Database**:

1. **Ingestion Setup (`data/process/rag.py`):** Reads structural data from `docs/company-knowledge-base/`, cleanses text boundaries, fragments documents into semantic sections via paragraphs, transforms textual windows into dense float vectors using a separate embedding ID, and upserts payloads safely with content-hashed UUID tokens to preserve idempotency.
2. **Retrieval & Inference Flow (`data/pipelines/rag.py`):** Ingests an executive user question, translates it using the identical embedding function, maps lookups inside Qdrant via vector similarity calculations, prunes poor matches falling below the strict similarity threshold score, aggregates passing text pieces into an isolated context format, and passes text elements down to a generation LLM matching Dr. Okonkwo's executive persona.

## 2. Chunking & Ingestion Strategy
* **Splitting Strategy:** Section and paragraph-based cutting mapping heading blocks (`#` through `######`) combined with double-newline boundaries (`\n\n`).
* **Chunk Length Constraints:** Fixed to a maximum threshold length of 1,800 characters with fallback safety rules preventing the code from cutting down the middle of a specific clinical sentence or regulatory policy boundary.
* **Idempotency Safeguard:** Point IDs are established cleanly by wrapping content seeds (`source_document:chunk_index:text`) directly inside a deterministic `uuid.uuid5` namespace mapping structure. This guarantees that duplicate points are overwritten instead of stacking inside the storage system if the setup pipeline triggers multiple times.

## 3. Embedding and Retrieval Settings
* **Embedding Model Configuration:** Dedicated embedding model (`4geeks-healthcore-embedding`) generating a fixed vector size footprint of **384 dimensions**.
* **Distance Metric Logic:** Calculated utilizing **Cosine Similarity** formulas configured directly inside Qdrant collection params during runtime execution cycles.
* **Strict Scoring Guardrail:** A mandatory cutoff threshold of **0.35** (`RAG_MIN_SCORE`) is actively enforced inside `retrieve()`. Any retrieved text chunk matching underneath this scalar value is purged from the context buffer to protect the system from text pollution.
* **Honest Fallback Protocol:** If the filtered array yields zero passing elements, generation context drops into a safe text statement declaring lack of clear evidence, eliminating hallucinations.
