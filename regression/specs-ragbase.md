# Technical Specification: Modular RAG Architecture

## 1. Stack, Toolchain & Validation Rules
All code implemented within the monorepo must strictly align with the following dependency, technology, and naming parameters:

### Mandatory Environment Configurations
* **Package Manager:** **`uv` must be used exclusively** for environment initialization and dependency onboarding (`uv add ...`). The use of `pip install` or `pipenv` is strictly prohibited.
* **Vector Store Architecture:** **Qdrant** (orchestrated via local `docker-compose.yml` or hooked into Qdrant Cloud), confirming secure connectivity from the Python runtime environment.
* **Model Configuration Isolation:** The 4Geeks-provided embedding engine and generation LLM must be configured under **distinct, separate model IDs** within your `.env` layout. Never use the generation model to run token embedding transformations.
* **Context Synchronization:** Collection naming schemas, data dictionary fields, paths, and internal entity IDs must mirror the rules defined in `CONTEXT-company.md` exactly.

---

## 2. Monorepo File Layout & Architecture

The system's modular dependencies must map strictly to the following directory layout:

| Responsibility / Asset | Repository Location | Technical Mandate |
| :--- | :--- | :--- |
| **Source Knowledge Corpus** | `docs/company-knowledge-base/` | Ingests copied company source documents (policies, catalogs, procedures) from `00-general-contexts/healthcore/`. |
| **Chunking + Indexing** | `data/process/rag.py` | Handles filesystem reading, text parsing, token chunking, and Qdrant population. |
| **Retrieval + Generation** | `data/pipelines/rag.py` | Contains vector lookups, similarity scoring, and LLM orchestration. |
| **HTTP Endpoints** | `services/` | Exposes the pipeline via FastAPI routing blocks. |
| **Query User Interface** | `uis/` | Front-end panel built for leadership, with active state trackers. |
| **Unit Test Suite** | `tests/pipelines/test_rag.py` | Contains deterministic pipeline tests executing entirely on mocked infrastructure. |
| **Retrieval Evaluation** | `data/eval/` | Execution hub for calculating system performance and information recall. |
| **RAG Design Document** | `docs/rag/rag-design.md` | Core engineering document summarizing layout, chunking choice, and model IDs. |

---

## 3. Implementation Sequence & Functional Specifications
The application must be developed in this exact linear progression: 
`setup` ➔ `embed` ➔ `retrieve` ➔ `query` ➔ `API` ➔ `UI` ➔ `tests` ➔ `eval`.

### Phase 1 — Data Preparation and Indexing (`data/process/rag.py`)

#### `setup()`
* **Responsibility:** Targets `docs/company-knowledge-base/`, parsing the HealthCore multi-jurisdictional compliance, procedure, and internal policy documents.
* **Chunking Constraints:** Splits files into clear, self-contained semantic units. No chunk boundary may bisect a specific sentence, an explicit healthcare protocol, or a cross-border regulatory rule.
* **Idempotency Guard:** Repeatedly firing `setup()` must not pollute Qdrant with duplicate items. Developers must build a clear-and-reload collection routine or utilize deterministic, content-hashed point IDs.

#### `embed(text: str) -> list[float]`
* **Responsibility:** Evaluates a single string block and outputs a dense vector array using HealthCore's dedicated embedding model ID. This identical function must handle processing both at index-time and query-time.

#### Qdrant Payload Schema
All records pushed to the target company collection must store vectors alongside a structured dictionary:
* `vector`: Dense float array output from `embed(chunk_text)`
* `payload`: Must contain `source_document`, `section`, `company`, `language`, `chunk_index`, and `text` (the clean string fragment utilized during final downstream prompt building).

---

### Phase 2 — Retrieval and Generation Pipeline (`data/pipelines/rag.py`)

#### `retrieve(query: str, *, k: int = 5, min_score: float) -> list[dict]`
* **Responsibility:** Vectors the user's string query, triggers a nearest-neighbor query inside Qdrant for top-k vectors, drops any matches that fail the `min_score` threshold, and maps the passing elements into standard Python dictionaries (never expose raw SDK database object types to downstream services).

#### `query(question: str) -> str`
* **Responsibility:** The centralized, public entry point. It sequences operations: `retrieve()` ➔ prompt construction ➔ LLM generation call. It returns the final text block.
* **Safety Fallback:** If `retrieve()` yields no passing records, it enforces a fallback prompt requiring the model to declare the information missing rather than hallucinating details.

#### `generate_answer(question: str, context: list[dict]) -> str`
* **Responsibility:** Isolate the generation prompt construction and LLM endpoint call out of `query()`. This structural separation ensures that future workflows (like an autonomous LangGraph agent) can safely call `retrieve()` and `generate_answer()` independently without looping or repeating lookups.
* **Prompt Instructions:** Contextualizes the LLM to reply exactly in HealthCore's executive corporate voice, using *exclusively* the provided document text chunks.

---

### Phase 3 — Query Endpoint (`services/`)
* **Framework Engine:** FastAPI.
* **Endpoint Route:** `POST /knowledge/query`
* **Payload Interface:**
  * Request Body: `{ "question": "..." }`
  * Response Body: `{ "answer": "..." }` (Returns the model-generated text string exclusively).
* **Isolation Rule:** The route router must import and invoke `query()` from `data/pipelines/rag.py`. It is forbidden from housing independent retrieval or generation logic. It must never leak internal scores, raw vector arrays, or fragment arrays to the consumer.

---

### Phase 4 — Query Interface (`uis/`)
* **Design:** Provides a clean interface within the `uis/` space matching our internal system styles.
* **Operational States:** The frontend must natively process, trace, and render loading spinners, dynamic query timeouts, and explicit error screens. Broken or timed-out API events must never present as empty white windows. Supports both dark and light display modes.

---

### Phase 5 — Validation, Testing & Evaluation

#### Unit Testing Framework (`tests/pipelines/test_rag.py`)
* Must execute successfully when running `python -m pytest tests/pipelines/test_rag.py`.
* **Retrieval Assertions:** Uses an in-memory database stub or mocked client wrapper (no live Docker network dependencies during automated CI workflows). Verifies that elements dropping below `min_score` are thrown out and that the engine responds when zero records pass.
* **Query Assertions:** Mocks both the retrieval function and the LLM SDK. Asserts that the system successfully outputs a clean text payload and completely blocks raw data leaks.

#### Retrieval Evaluation Strategy (`data/eval/`)
* **Evaluation Set:** Build a `data/eval/test-queries.json` file consisting of a minimum of **8 custom validation questions** comprehensively testing the documents mirrored inside `docs/company-knowledge-base/`.
* **System Benchmark:** Calculate **Recall@3** using the evaluation script against that file. The pipeline must hit or exceed an **80% Recall@3 score**, ensuring that for at least 80% of our test inquiries, the necessary source chunk lands within the top 3 items returned by Qdrant.

---

### Phase 6 — RAG Design Document (`docs/rag/rag-design.md`)
A standalone markdown document that provides an incoming engineer with total system visibility without reviewing the code files. It must thoroughly detail:
1. **End-to-End Pipeline Map:** A numbered step-by-step description or workflow map detailing the lifecycle of data from initial ingestion up to final generation.
2. **Chunking Strategy & Justification:** Technical breakdown of the chunking mechanism used (e.g., token limits, markdown section splitters) and why it guarantees that interconnected policies are not cut in half.
3. **Embedding Specifics:** Documenting precise model IDs, vector dimensionality, selected distance formulas within Qdrant, and the calibration steps used to set our `min_score` threshold.
