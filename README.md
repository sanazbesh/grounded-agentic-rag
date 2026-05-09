# Agentic_Rag

> **Deterministic, local-first legal RAG with grounded answers, answerability gating, citations, tracing, and offline evaluation.**

<p>
  <img alt="Python" src="https://img.shields.io/badge/Python-3.11+-blue">
  <img alt="UI" src="https://img.shields.io/badge/UI-Streamlit-red">
  <img alt="Architecture" src="https://img.shields.io/badge/Architecture-RAG-purple">
  <img alt="Domain" src="https://img.shields.io/badge/Domain-Legal%20AI-darkgreen">
  <img alt="Runtime" src="https://img.shields.io/badge/Runtime-Local--first-orange">
  <img alt="Quality" src="https://img.shields.io/badge/Quality-Offline%20Evals-informational">
  <img alt="Storage" src="https://img.shields.io/badge/Storage-Postgres%20%2B%20Qdrant-lightgrey">
</p>

`Agentic_Rag` is an engineering-focused legal retrieval-augmented generation system. It is designed around **explicit graph orchestration**, **parent-child retrieval**, **hybrid search**, **answerability assessment**, and a **strict final answer contract**.

This project is intentionally not a generic chatbot wrapper. It is a transparent RAG system where every answer is routed through retrieval, evidence sufficiency checks, grounded synthesis, citations, warnings, tracing, and offline evaluation.

> **Accuracy note:** this README distinguishes fully implemented local/in-memory behavior from partially wired persistent infrastructure. Postgres/Qdrant storage foundations exist, but the persistent vector retrieval path should be treated as experimental until the dependency/configuration gaps listed in [Known Limitations](#known-limitations) are resolved.

---

## 🎬 Hero GIFs

> The repository currently uses placeholder paths for demo media. Add the GIF files under `assets/` when recording demos.

### End-to-end Streamlit demo

![Agentic RAG Demo](assets/demo.gif)

**Suggested content:** upload or select legal documents, submit a legal question, inspect the final grounded answer, expand citations, and download the debug payload.

### Retrieval + answerability flow

![RAG Flow](assets/rag-flow.gif)

**Suggested content:** query understanding → optional rewrite/decomposition → hybrid retrieval → reranking → parent expansion → answerability gate → grounded answer or insufficient-context fallback.

### Architecture walkthrough

![Architecture](assets/architecture.gif)

**Suggested content:** show how source documents become parent/child chunks, how child hits map back to parent context, and how final answers preserve citation traceability.

### Persistent ingestion lifecycle

![Persistent Ingestion](assets/persistent-ingestion.gif)

**Suggested content:** upload a document through the persistent ingestion UI, register document/version metadata, persist chunks, inspect ingestion job status, and explain how persistent retrieval is intended to resolve vector hits back to Postgres chunk records.

---

## Table of Contents

- [Short Project Introduction](#short-project-introduction)
- [Architecture Overview](#architecture-overview)
- [Multi-Mode Runtime Architecture](#multi-mode-runtime-architecture)
- [Persistent Architecture & Storage Layer](#persistent-architecture--storage-layer)
- [Key Architectural Design Decisions](#key-architectural-design-decisions)
- [End-to-End Pipeline](#end-to-end-pipeline)
- [Repository Structure](#repository-structure)
- [Retrieval Architecture Deep Dive](#retrieval-architecture-deep-dive)
- [Answer Generation & Safety](#answer-generation--safety)
- [Evaluation & Observability](#evaluation--observability)
- [Streamlit Inspection UI](#streamlit-inspection-ui)
- [Example Query Flow](#example-query-flow)
- [Tech Stack](#tech-stack)
- [Running Locally](#running-locally)
- [Known Limitations](#known-limitations)
- [Future Improvements](#future-improvements)
- [Why This Project Matters](#why-this-project-matters)

---

## Short Project Introduction

Legal RAG systems need to answer a harder question than “what text looks relevant?” They also need to decide **whether the evidence is strong enough to answer at all**.

`Agentic_Rag` addresses that problem with a deterministic legal RAG architecture:

- **Grounded answers** are generated only from retrieved context.
- **Citations** are preserved as structured output, not buried inside prose.
- **Answerability gating** checks whether the retrieved evidence is sufficient before synthesis.
- **Parent-child retrieval** uses small chunks for search and larger parent chunks for legal context.
- **Evaluation tooling** is included as a first-class part of the system, not an afterthought.
- **Streamlit dashboards** make retrieval, citations, traces, failures, and quality artifacts inspectable.

The result is a local-first AI system that is easier to debug, test, and explain than an open-ended agent loop.

---

## Architecture Overview

### High-level system diagram

```text
┌──────────────────────────────────────────────────────────────────────┐
│                              Streamlit UI                             │
│  Query input · document selection · citations · debug/quality panels  │
└───────────────────────────────┬──────────────────────────────────────┘
                                │
                                v
┌──────────────────────────────────────────────────────────────────────┐
│                         Backend Adapter                              │
│  mock/local/persistent routing · strict final-result validation        │
└───────────────┬───────────────────────────────┬──────────────────────┘
                │                               │
                v                               v
┌──────────────────────────┐       ┌───────────────────────────────────┐
│ Mock Backend              │       │ Legal RAG Dependencies             │
│ deterministic UI demos    │       │ local in-memory or persistent       │
└──────────────────────────┘       └───────────────┬───────────────────┘
                                                   │
                                                   v
                                  ┌────────────────────────────────────┐
                                  │ Retrieval Graph                     │
                                  │ classify · rewrite · retrieve       │
                                  │ fuse · rerank · parent expand       │
                                  └──────────────────┬─────────────────┘
                                                     │
                                                     v
                                  ┌────────────────────────────────────┐
                                  │ Answer Graph                        │
                                  │ answerability · synthesis · safety  │
                                  │ final contract · metrics · traces   │
                                  └──────────────────┬─────────────────┘
                                                     │
                                                     v
                                  ┌────────────────────────────────────┐
                                  │ FinalAnswerModel                    │
                                  │ answer_text · grounded              │
                                  │ sufficient_context · citations      │
                                  │ warnings                            │
                                  └────────────────────────────────────┘
```

### Component relationship diagram

```text
app.py
 ├─ ui/backend_adapter.py
 │   ├─ ui/mock_backend.py
 │   └─ ui/upload_manager.py
 │
 ├─ ui/local_backend.py
 │   ├─ ingestion/             # Markdown/PDF → Document
 │   ├─ chunking/              # Document → ParentChunk + ChildChunk
 │   ├─ retrieval/             # hybrid child search + parent expansion
 │   └─ tools/                 # query intelligence, answerability, synthesis
 │
 └─ orchestration/
     ├─ retrieval_graph.py     # retrieval-stage graph
     └─ legal_rag_graph.py     # answer-stage graph
```

### Retrieval + answer flow visualization

```text
User question
   │
   v
Query understanding
   │
   ├─ optional conversation context resolution
   ├─ optional decomposition planning
   ├─ optional rewrite
   └─ optional legal entity extraction
   │
   v
Hybrid child retrieval
   │
   ├─ dense-compatible child search
   ├─ sparse/BM25-style child search
   └─ Reciprocal Rank Fusion
   │
   v
Reranked child hits
   │
   v
Parent chunk expansion
   │
   v
Optional context compression
   │
   v
Answerability assessment
   │
   ├─ sufficient evidence ────────► grounded synthesis + citations
   ├─ partial evidence ───────────► partial/safe response path
   └─ insufficient evidence ─────► insufficient-context fallback
   │
   v
Strict final answer contract
```

### Layer responsibilities

| Layer | Responsibility | Primary modules |
|---|---|---|
| UI | Streamlit controls, inspection panels, dashboards, uploads | `app.py`, `ui/` |
| Backend boundary | Mock/real mode switching and final-result validation | `ui/backend_adapter.py` |
| Local runtime | Build in-memory legal RAG dependencies from selected files | `ui/local_backend.py` |
| Ingestion | Convert Markdown/PDF inputs to `Document` objects | `src/agentic_rag/ingestion/` |
| Chunking | Produce parent context chunks and child retrieval chunks | `src/agentic_rag/chunking/` |
| Retrieval | Hybrid child search, RRF fusion, reranking, parent expansion | `src/agentic_rag/retrieval/` |
| Orchestration | Deterministic retrieval and answer graphs | `src/agentic_rag/orchestration/` |
| Safety | Answerability, evidence strength, grounded synthesis, fallbacks | `src/agentic_rag/tools/` |
| Persistence | SQLAlchemy models, Postgres config, document file store | `src/agentic_rag/storage/`, `src/agentic_rag/ingestion_pipeline/` |
| Evaluation | Offline datasets, graders, reports, CI gates | `evals/`, `.github/workflows/` |

---

## Multi-Mode Runtime Architecture

The repository supports three runtime modes with different maturity levels.

### Runtime mode comparison

| Mode | Status | Purpose | Dependencies | Tradeoffs | Intended use |
|---|---:|---|---|---|---|
| **Mock backend** | ✅ Implemented | Fast deterministic UI demos without real retrieval | Streamlit only | Does not exercise real RAG logic | UI development, screenshots, demos |
| **Local in-memory backend** | ✅ Implemented | Real local RAG over selected uploaded/local docs | Streamlit, PyMuPDF, pymupdf4llm, local Python modules | Data is rebuilt in memory; not durable | Local experimentation, interview demos, architecture inspection |
| **Persistent Postgres/Qdrant backend** | ⚠️ Partially wired / experimental | Durable document metadata/chunks and intended vector-backed retrieval | Postgres, Qdrant, SQLAlchemy, psycopg, plus additional optional client/model dependencies | Persistence foundations exist, but some runtime wiring/dependencies need cleanup | Future production-like local stack, persistent ingestion experiments |

### 1. Mock backend

```text
Streamlit UI ──► ui/backend_adapter.py ──► ui/mock_backend.py ──► validated final result
```

**What it is:** deterministic sample responses and document descriptors for exercising the UI.

**Why it exists:** the UI can be developed and demonstrated even when no documents, models, vector stores, or databases are available.

**What it does not do:** real retrieval, answerability, or grounded synthesis.

### 2. Local in-memory backend

```text
Selected files
   │
   v
Markdown/PDF ingestion
   │
   v
Parent-child chunking
   │
   v
In-memory child records + parent lookup
   │
   v
LegalRagDependencies
   │
   v
Retrieval graph + answer graph
```

**What it is:** the primary working path for local RAG experimentation.

**Implemented behavior:**

- loads selected `.md`, `.txt`, and `.pdf` documents,
- chunks them into parent/child records,
- builds in-memory retrieval repositories,
- runs the deterministic retrieval and answer graphs,
- returns strict final answers with citations/warnings.

**Tradeoff:** simple and transparent, but not durable and not designed for large persistent corpora.

### 3. Persistent Postgres/Qdrant backend

```text
Postgres metadata/chunks
        │
        │       Qdrant child vectors
        │              │
        └──────┬───────┘
               v
   Qdrant hit resolution
               │
               v
   Postgres chunk lookup
               │
               v
   Parent expansion + answer graph
```

**What is implemented:**

- SQLAlchemy models for documents, document versions, chunks, and ingestion jobs.
- Local document file storage abstraction.
- Document registry and ingestion job services.
- Chunk persistence for parent/child chunks.
- Qdrant-like dense indexing abstractions.
- Qdrant-hit-to-Postgres-chunk resolution classes.
- Docker Compose services for app, Postgres, and Qdrant.

**What is partial/experimental:**

- Persistent UI ingestion currently constructs the ingestion orchestrator without vector indexing service wiring.
- Persistent app wiring imports Qdrant client/config pieces that require cleanup and dependency declaration.
- The Qdrant collection name is not fully centralized across Compose and code defaults.

Use persistent mode as an architecture foundation and local experiment path, not as a production-ready deployment claim.

---

## Persistent Architecture & Storage Layer

Persistence exists to support durable document lifecycle tracking, reindexing, chunk persistence, and a future fully wired persistent retrieval path.

### Storage architecture diagram

```text
┌────────────────────────────┐
│ Uploaded / source document │
└──────────────┬─────────────┘
               │
               v
┌────────────────────────────┐
│ LocalDocumentStore          │
│ filesystem bytes            │
└──────────────┬─────────────┘
               │ storage_path
               v
┌────────────────────────────┐
│ Postgres                    │
│ documents                   │
│ document_versions           │
│ chunks                      │
│ ingestion_jobs              │
└──────────────┬─────────────┘
               │ child chunk text + ids
               v
┌────────────────────────────┐
│ Qdrant-compatible vector    │
│ child chunk points          │
└──────────────┬─────────────┘
               │ qdrant hit payload / point id
               v
┌────────────────────────────┐
│ QdrantResultResolver        │
│ resolves hits to Postgres   │
│ chunk rows                  │
└──────────────┬─────────────┘
               v
┌────────────────────────────┐
│ Parent chunk retrieval      │
│ answer context              │
└────────────────────────────┘
```

### Persistent data model

```text
Document
  └── DocumentVersion
        ├── Parent Chunk rows
        │     └── Child Chunk rows
        └── IngestionJob rows

Child Chunk rows
  └── qdrant_point_id
        └── Qdrant vector point
```

| Persistent entity | Purpose |
|---|---|
| `Document` | Canonical source document with current version pointer and lifecycle status |
| `DocumentVersion` | Immutable content revision with hash, parser/chunker/version metadata, storage path, and status |
| `Chunk` | Parent and child chunk rows, including parent linkage and optional Qdrant point ID |
| `IngestionJob` | Processing lifecycle record with status, timestamps, and error message |
| `LocalDocumentStore` | Filesystem-backed storage for original document bytes |

### Ingestion lifecycle diagram

```text
Upload / file path
   │
   v
Validate input
   │
   v
Register Document + DocumentVersion
   │
   v
Save bytes to LocalDocumentStore
   │
   v
Create IngestionJob(PENDING)
   │
   v
PROCESSING
   │
   ├─ parse Markdown/PDF
   ├─ chunk into parent/child records
   ├─ persist chunks to Postgres
   ├─ optionally index child vectors
   └─ validate persisted artifacts
   │
   ├────────────── success ──────────────► READY + promote version
   │
   └────────────── failure ──────────────► FAILED + error_message
```

### Persistent retrieval flow diagram

```text
Query
  │
  v
Dense Qdrant search
  │
  v
Raw Qdrant hit
  │
  ├─ payload.chunk_id / payload.child_chunk_id
  └─ or raw point id
  │
  v
QdrantResultResolver
  │
  v
PostgresChunkRepository.get_chunk_by_id / resolve_qdrant_point_id
  │
  v
ChildSearchResult
  │
  v
Hybrid/Rerank/Parent expansion
  │
  v
Answerability + grounded answer
```

### Why parent-child linkage matters in persistent retrieval

Dense retrieval operates on **child chunks** because they are small and targeted. Legal answer generation needs **parent chunks** because legal obligations, exceptions, definitions, and qualifiers often span more context than a small retrieval chunk.

Persistent retrieval therefore needs a reliable chain:

```text
Qdrant child vector hit
   → child chunk row in Postgres
   → parent_chunk_id
   → parent chunk row in Postgres
   → answer context
   → citation back to parent/document/source
```

This design preserves traceability from final answer citations back to durable storage records.

---

## Key Architectural Design Decisions

### 1. Deterministic orchestration over autonomous loops

**Why it exists:** legal RAG needs predictable behavior, bounded control flow, and debuggable failures.

**Implementation:** `retrieval_graph.py` and `legal_rag_graph.py` define explicit graph nodes and transitions.

**Tradeoff:** less flexible than open-ended agents, but much easier to test, trace, and reason about.

**Production reasoning:** when an answer is wrong, the team can inspect which graph node failed: classification, rewrite, retrieval, rerank, answerability, synthesis, or validation.

---

### 2. Parent-child chunking

**Why it exists:** retrieval works best with small, focused chunks; legal answer generation needs larger context.

**Implementation:** `ParentChunk`, `ChildChunk`, `ParentChunker`, `RecursiveChildChunker`, and `MarkdownParentChildChunker`.

**Tradeoff:** more indexing and storage complexity than single-level chunking.

**Production reasoning:** final answers can cite larger parent context while search remains precise.

---

### 3. Hybrid retrieval

**Why it exists:** legal search needs exact terms, citations, dates, parties, and clause labels, but also benefits from semantic matching.

**Implementation:** dense-compatible child search + sparse/BM25-style child search + Reciprocal Rank Fusion.

**Tradeoff:** more moving parts than a single retriever.

**Production reasoning:** hybrid retrieval reduces brittleness when users paraphrase legal concepts or use exact legal terms.

---

### 4. Answerability gate

**Why it exists:** the system should know when not to answer.

**Implementation:** `AnswerabilityAssessor` evaluates evidence coverage and strength before synthesis.

**Tradeoff:** may refuse or qualify answers even when a more aggressive chatbot would answer.

**Production reasoning:** safe failure is better than unsupported legal claims.

---

### 5. Grounded synthesis

**Why it exists:** final answers should be tied to retrieved context and auditable citations.

**Implementation:** `LegalAnswerSynthesizer` builds answers from evidence units and citations, with optional local LLM drafting.

**Tradeoff:** extractive/deterministic answers may be less fluent than unconstrained LLM responses.

**Production reasoning:** citation-bearing output is easier to audit, grade, and debug.

---

### 6. Local-first design

**Why it exists:** legal documents are often sensitive, and local demos should not require cloud services.

**Implementation:** Streamlit app, mock mode, local in-memory backend, local LLM config, local file upload handling.

**Tradeoff:** local mode is not durable and is limited by local machine resources.

**Production reasoning:** local-first architecture is ideal for inspection, demos, development, and privacy-conscious workflows.

---

### 7. Evaluation-first architecture

**Why it exists:** RAG quality cannot be judged from demos alone.

**Implementation:** JSONL datasets, deterministic graders, LLM judge parsers, report builders, PR and nightly workflows.

**Tradeoff:** evaluation infrastructure adds code and maintenance overhead.

**Production reasoning:** regression gates make retrieval and answer changes safer.

---

### 8. Immutable document versions

**Why it exists:** legal documents change, and answers should be attributable to a specific content revision.

**Implementation:** `DocumentVersion` rows include content hash, storage path, parser/chunker metadata, embedding model, and lifecycle status.

**Tradeoff:** more storage records and lifecycle management.

**Production reasoning:** versioning supports reindexing, rollback, auditability, and repeatable evaluation.

---

### 9. Explicit lifecycle states

**Why it exists:** ingestion and indexing can fail at many stages.

**Implementation:** lifecycle status enum: `PENDING`, `PROCESSING`, `READY`, `FAILED`, `SKIPPED_DUPLICATE`.

**Tradeoff:** more status transitions to maintain.

**Production reasoning:** operators and UI users need clear processing state and error messages.

---

### 10. Typed contracts

**Why it exists:** AI systems fail more safely when boundaries are explicit.

**Implementation:** dataclasses, Pydantic-compatible models, strict final result validation, typed graph states.

**Tradeoff:** more schema maintenance.

**Production reasoning:** strict contracts reduce silent schema drift between UI, orchestration, evals, and storage.

---

### 11. Retrieval/answer separation

**Why it exists:** retrieval quality and synthesis quality should be independently inspectable.

**Implementation:** retrieval graph produces context; answer graph consumes context and answerability results.

**Tradeoff:** more explicit orchestration code.

**Production reasoning:** failures can be localized: did the retriever miss evidence, or did synthesis mishandle evidence?

---

## End-to-End Pipeline

### Main RAG pipeline

```text
1. Document ingestion
   └─ Markdown/PDF → Document

2. Parent-child chunking
   └─ Document → ParentChunk[] + ChildChunk[]

3. Indexing / local repository construction
   ├─ local mode: in-memory child records + parent lookup
   └─ persistent path: Postgres chunks + optional Qdrant vectors

4. Query understanding
   └─ classification, context resolution, decomposition gate

5. Query transformation
   └─ optional rewrite + legal entity extraction

6. Retrieval
   └─ dense-compatible search + sparse search + RRF fusion

7. Reranking
   └─ fused child hits → reranked child hits

8. Parent expansion
   └─ child.parent_chunk_id → ParentChunkResult[]

9. Optional compression
   └─ large parent context → compressed context

10. Answerability
    └─ coverage/evidence strength → answer route

11. Synthesis
    └─ grounded answer or insufficient-context fallback

12. Final contract
    └─ answer_text · grounded · sufficient_context · citations · warnings
```

### Persistent ingestion pipeline

```text
File upload/path
  │
  v
DocumentRegistry.register_document
  │
  v
LocalDocumentStore.save_file/save_bytes
  │
  v
IngestionJobService.create_job
  │
  v
MarkdownDocumentIngestor / PDFDocumentIngestor
  │
  v
MarkdownParentChildChunker
  │
  v
ChunkPersistenceService.persist_chunks
  │
  v
ChildChunkVectorIndexingService.index_document_version  (optional wiring)
  │
  v
IngestionValidationService.validate
  │
  v
READY / FAILED lifecycle status
```

### Stage implementation map

| Stage | Primary files/modules | Key classes/functions |
|---|---|---|
| Ingestion | `src/agentic_rag/ingestion/` | `MarkdownDocumentIngestor`, `PDFDocumentIngestor`, `PyMuPDF4LLMConverter` |
| Chunking | `src/agentic_rag/chunking/` | `MarkdownParentChildChunker`, `ParentChunker`, `RecursiveChildChunker`, `ParentChunk`, `ChildChunk` |
| Dense indexing | `src/agentic_rag/indexing/dense_child_chunks.py` | `DenseEmbeddingService`, `ChildChunkDenseIndexer`, `QdrantChildChunkStore`, `stable_qdrant_point_id` |
| Sparse indexing/search | `src/agentic_rag/indexing/sparse_child_chunks.py`, `src/agentic_rag/retrieval/sparse.py` | BM25-style sparse components and sparse search facade |
| Retrieval | `src/agentic_rag/retrieval/parent_child.py` | `RRFFuser`, `HybridSearchService`, `ChunkReranker`, `ParentChunkStore`, `ParentChildRetrievalTools` |
| Persistent resolution | `src/agentic_rag/retrieval/qdrant_postgres_resolver.py` | `QdrantResultResolver`, `PostgresResolvedQdrantChildRepository` |
| Postgres chunk lookup | `src/agentic_rag/retrieval/postgres_chunk_repository.py` | `PostgresChunkRepository` |
| Retrieval orchestration | `src/agentic_rag/orchestration/retrieval_graph.py` | `RetrievalStageState`, `RetrievalDependencies`, `build_retrieval_graph`, `run_retrieval_stage` |
| Answer orchestration | `src/agentic_rag/orchestration/legal_rag_graph.py` | `LegalRagState`, `FinalAnswerModel`, `build_answer_graph`, `run_legal_rag_turn_with_state` |
| Answerability | `src/agentic_rag/tools/answerability.py` | `AnswerabilityAssessor`, `AnswerabilityAssessment`, `CoverageEvaluation`, `EvidenceStrengthEvaluation` |
| Synthesis | `src/agentic_rag/tools/answer_generation.py` | `LegalAnswerSynthesizer`, `GenerateAnswerResult`, `AnswerCitation` |
| UI adapter | `ui/backend_adapter.py` | `run_backend_query`, `validate_final_result` |
| Local runtime | `ui/local_backend.py` | `build_local_backend_dependencies`, `LocalLLMRuntimeSettings` |
| Offline evals | `evals/` | `run_offline_eval`, deterministic graders, CI gate helpers |

---

## Repository Structure

```text
.
├── app.py                                  # Streamlit entrypoint and real/mock backend wiring
├── README.md                               # Project documentation
├── requirements.txt                        # Runtime + pytest dependencies
├── Dockerfile                              # Streamlit app container
├── docker-compose.yml                      # app + Postgres + Qdrant local stack
│
├── src/agentic_rag/
│   ├── types.py                            # Shared Document/Chunk/RetrievedItem/Generation dataclasses
│   ├── versioning.py                       # Version attribution helpers for traces/evals
│   ├── _compat_pydantic.py                 # Fallback shim when pydantic is unavailable
│   │
│   ├── ingestion/                          # Markdown/PDF → Document conversion
│   │   ├── converters.py                   # PDF converter protocol + PyMuPDF4LLM implementation
│   │   ├── document_ingestors.py           # MarkdownDocumentIngestor, PDFDocumentIngestor
│   │   └── interfaces.py                   # Ingestion interfaces
│   │
│   ├── chunking/                           # Markdown-aware parent-child chunking
│   │   ├── markdown.py                     # ParentChunker, RecursiveChildChunker, MarkdownParentChildChunker
│   │   ├── models.py                       # ParentChunk, ChildChunk, ChunkingResult
│   │   └── interfaces.py                   # Chunker protocol/interface
│   │
│   ├── indexing/                           # Dense-compatible + sparse child chunk indexing
│   │   ├── dense_child_chunks.py           # Embedding service, Qdrant payloads, dense upsert pipeline
│   │   ├── sparse_child_chunks.py          # BM25-style sparse child chunk indexing
│   │   └── interfaces.py                   # Indexing abstractions
│   │
│   ├── retrieval/                          # Parent-child retrieval services
│   │   ├── parent_child.py                 # Hybrid search, RRF, reranking, parent expansion
│   │   ├── sparse.py                       # Sparse search facade
│   │   ├── postgres_chunk_repository.py    # Postgres-backed parent/chunk lookup
│   │   ├── qdrant_postgres_resolver.py     # Resolve Qdrant hits to Postgres chunk rows
│   │   └── interfaces.py                   # Retrieval interfaces
│   │
│   ├── orchestration/                      # Deterministic retrieval + answer graphs
│   │   ├── retrieval_graph.py              # Retrieval-stage graph and state
│   │   ├── legal_rag_graph.py              # Full legal RAG answer graph
│   │   ├── query_understanding.py          # Query classification/routing hints
│   │   ├── decomposition_gate.py           # Decomposition decision helper
│   │   ├── tracing.py                      # Structured trace helpers
│   │   ├── metrics.py                      # Request metric emission/aggregation
│   │   ├── traffic_sampling.py             # Production traffic sampling helpers
│   │   └── online_shadow_grading.py        # Online shadow grading support
│   │
│   ├── tools/                              # Deterministic RAG tools
│   │   ├── query_intelligence.py           # Rewrite/entity extraction/decomposition helpers
│   │   ├── answerability.py                # Coverage + evidence strength assessment
│   │   ├── answer_generation.py            # Grounded synthesis + citations
│   │   ├── context_processing.py           # Context compression
│   │   ├── evidence_units.py               # Evidence unit normalization
│   │   ├── party_role_resolution.py        # Legal party-role parsing helpers
│   │   └── interfaces.py                   # Tool abstractions
│   │
│   ├── ingestion_pipeline/                 # Persistent ingestion orchestration
│   │   ├── document_registry.py            # Document/version registration and promotion
│   │   ├── ingestion_jobs.py               # Ingestion job lifecycle service
│   │   ├── chunk_persistence.py            # Persist parent/child chunks
│   │   ├── vector_indexing.py              # Persisted child chunk vector indexing service
│   │   ├── validation.py                   # Ingestion artifact validation
│   │   ├── document_deletion.py            # Document cleanup service
│   │   └── orchestrator.py                 # End-to-end persistent ingestion coordinator
│   │
│   ├── storage/                            # Postgres + local file storage foundation
│   │   ├── models.py                       # SQLAlchemy ORM models
│   │   ├── postgres.py                     # DATABASE_URL-backed engine/session helpers
│   │   └── document_store.py               # Filesystem document storage
│   │
│   ├── llm/                                # Local LLM provider abstraction
│   │   └── local_provider.py               # llama.cpp-backed prompt client and env config
│   │
│   ├── config/                             # Configuration interfaces
│   ├── evaluation/                         # Evaluation interfaces
│   └── prompts/                            # Prompt template interfaces
│
├── ui/
│   ├── backend_adapter.py                  # UI/backend boundary and final-result validation
│   ├── local_backend.py                    # In-memory LegalRagDependencies builder
│   ├── mock_backend.py                     # Deterministic mock backend
│   ├── components.py                       # Streamlit sidebar/query/result/debug renderers
│   ├── upload_manager.py                   # Upload persistence and path safety guards
│   ├── persistent_ingestion.py             # UI helper for persistent ingestion
│   ├── persisted_documents.py              # List persisted documents from Postgres
│   ├── debug_payload.py                    # Debug payload serialization helpers
│   ├── session_memory.py                   # Conversation context helpers
│   ├── quality_dashboard.py                # Offline quality dashboard UI
│   ├── trace_dashboard.py                  # Trace dashboard UI
│   ├── triage_dashboard.py                 # Failure triage dashboard UI
│   └── review_queue_dashboard.py           # Human review queue dashboard UI
│
├── evals/
│   ├── datasets/                           # JSONL legal eval cases
│   ├── fixtures/offline_documents/         # Markdown fixture documents for offline evals
│   ├── schema/legal_eval_case.json         # Eval case JSON schema
│   ├── runners/run_offline_eval.py         # Offline eval runner
│   ├── ci/offline_eval_ci.py               # CI wrapper and quality gates
│   ├── graders/                            # Deterministic graders + LLM judge parsers
│   └── reports/                            # Report, dashboard, review, and triage data builders
│
├── tests/                                  # Unit/integration tests across core, UI, storage, evals
├── docs/                                   # Quality contracts, eval docs, release/ramp guidance
├── observability/schema/trace_schema.md    # Trace schema documentation
├── scripts/                                # Backup/restore scripts for local persistent state
└── .github/workflows/                      # Offline eval PR and nightly workflows
```

---

## Retrieval Architecture Deep Dive

### Retrieval flow

```text
Query
  │
  v
┌───────────────────────────────┐
│ Query intelligence             │
│ classify · rewrite · entities  │
└───────────────┬───────────────┘
                │
                v
┌───────────────────────────────┐
│ Dense-compatible child search  │
└───────────────┬───────────────┘
                │
                │       ┌───────────────────────────────┐
                └──────►│ Sparse/BM25 child search       │
                        └───────────────┬───────────────┘
                                        │
                                        v
                        ┌───────────────────────────────┐
                        │ Reciprocal Rank Fusion         │
                        └───────────────┬───────────────┘
                                        │
                                        v
                        ┌───────────────────────────────┐
                        │ Chunk reranking                │
                        └───────────────┬───────────────┘
                                        │
                                        v
                        ┌───────────────────────────────┐
                        │ Parent expansion               │
                        │ child → parent context          │
                        └───────────────┬───────────────┘
                                        v
                              Answerability + synthesis
```

### Dense retrieval

Dense retrieval is represented through Qdrant-compatible abstractions:

- `DenseEmbeddingService`
- `QdrantChildChunkStore`
- `ChildChunkDenseIndexer`
- `ChildChunkQdrantPayload`

Dense child chunks preserve parent linkage in payloads so downstream retrieval can expand from a small hit to a larger parent context.

### Sparse retrieval

Sparse retrieval is implemented as an in-memory BM25-style path for child chunks. This matters for legal search because exact terms often matter:

- party names,
- clause labels,
- dates,
- statutory phrases,
- legal terms of art.

### Reciprocal Rank Fusion

Hybrid retrieval uses **Reciprocal Rank Fusion (RRF)** instead of adding raw dense and sparse scores. Dense and sparse scores are not naturally comparable, but ranks are stable and interpretable.

```text
Dense rank list      Sparse rank list
      │                    │
      └────────┬───────────┘
               v
          RRF fusion
               │
               v
       HybridSearchResult[]
```

### Reranking

After RRF, child hits are reranked before parent expansion. This gives the system another deterministic opportunity to prioritize issue-focused chunks before selecting parent context.

### Parent expansion

The answer stage does not rely on child chunk text alone. It expands child hits to parent chunks:

```text
HybridSearchResult.child_chunk_id
  └── parent_chunk_id
        └── ParentChunkResult.text
              └── answer context
```

This is especially important in legal documents because qualifiers, exceptions, and definitions are often near—but not inside—the exact matching sentence.

### Qdrant → Postgres resolution flow

```text
Qdrant raw hit
  │
  ├─ payload.chunk_id / child_chunk_id
  └─ raw point id
  │
  v
QdrantResultResolver
  │
  v
PostgresChunkRepository
  │
  v
Persisted child chunk row
  │
  v
ChildSearchResult(parent_chunk_id=...)
  │
  v
ParentChunkRepository.get_by_ids(...)
```

This keeps dense vector retrieval tied to durable chunk records rather than treating vector payloads as the system of record.

---

## Answer Generation & Safety

Legal answer generation is designed around **trustworthiness** rather than fluency alone.

### Safety flow

```text
Retrieved parent context
   │
   v
Evidence unit normalization
   │
   v
Answerability assessment
   │
   ├─ no context ──────────────► insufficient-context response
   ├─ weak context ────────────► safe/qualified response path
   └─ sufficient context ──────► grounded synthesis
                                  │
                                  v
                              citation validation
                                  │
                                  v
                              final contract
```

### Answerability gating

The answerability layer evaluates:

- whether relevant context exists,
- whether evidence is sufficient,
- whether support is partial or weak,
- whether the query needs clarification,
- whether a safe failure is more appropriate than an answer.

### Grounded synthesis

The default synthesizer is deterministic and extractive:

- it ranks relevant context,
- extracts supporting excerpts,
- builds structured citations,
- adds caveats when evidence appears partial,
- preserves warnings separately from the answer text.

Optional local LLM drafting can be enabled for selected stages, but deterministic fallback remains part of the design.

### Citation enforcement

The final answer model separates citations from prose. A grounded answer is expected to carry citations. The graph validation path downgrades unsupported groundedness when citations are missing.

### Final answer contract

Every real backend result must satisfy:

```json
{
  "answer_text": "string",
  "grounded": true,
  "sufficient_context": true,
  "citations": [],
  "warnings": []
}
```

The UI adapter validates this shape before rendering.

---

## Evaluation & Observability

This repository treats quality infrastructure as part of the architecture.

### Evaluation stack

```text
JSONL eval datasets
   │
   v
Offline eval runner
   │
   ├─ system execution
   ├─ deterministic graders
   ├─ optional LLM judge parsers
   └─ JSON run artifact
   │
   v
Reports / dashboards / CI gates
```

### Implemented evaluation components

| Component | Purpose | Location |
|---|---|---|
| Eval datasets | Regression and tiered legal test cases | `evals/datasets/` |
| Fixture docs | Local offline document corpus | `evals/fixtures/offline_documents/` |
| Eval schema | JSON schema for legal eval cases | `evals/schema/legal_eval_case.json` |
| Eval runner | Executes cases and writes machine-readable results | `evals/runners/run_offline_eval.py` |
| CI wrapper | Selects families, runs eval modes, enforces gates | `evals/ci/offline_eval_ci.py` |
| Deterministic graders | Contract, citation, retrieval, answerability, routing checks | `evals/graders/` |
| LLM judge parsers | Answer correctness, groundedness, safe failure parsing | `evals/graders/llm_judges/` |
| Reports | Markdown reports, dashboard data, triage, review queues | `evals/reports/` |

### CI workflows

| Workflow | Trigger | Behavior |
|---|---|---|
| Offline Eval PR Gates | Pull requests | Runs smoke evals and touched-family evals, enforces pass-rate gates |
| Offline Eval Nightly Regression | Scheduled/manual | Runs full offline regression and builds markdown report |

### Observability components

- Structured trace helpers in `src/agentic_rag/orchestration/tracing.py`.
- Metrics emission and aggregation in `src/agentic_rag/orchestration/metrics.py`.
- Trace schema docs in `observability/schema/trace_schema.md`.
- Streamlit trace dashboard in `ui/trace_dashboard.py`.
- Quality dashboard in `ui/quality_dashboard.py`.
- Failure triage dashboard in `ui/triage_dashboard.py`.
- Human review queue dashboard in `ui/review_queue_dashboard.py`.
- Online shadow grading support in `src/agentic_rag/orchestration/online_shadow_grading.py`.
- Production traffic sampling helpers in `src/agentic_rag/orchestration/traffic_sampling.py`.

---

## Streamlit Inspection UI

The Streamlit UI is a local-first inspection environment for the RAG pipeline.

### UI capabilities

| UI area | Purpose |
|---|---|
| Sidebar runtime controls | Choose mock/real mode, upload/select documents, configure local LLM options |
| Query panel | Submit legal questions and optional conversation context |
| Answer panel | Render final answer text and warnings |
| Citation panel | Inspect structured citations |
| Debug payload panel | Inspect raw debug/state payloads |
| Quality dashboard | Explore offline eval quality artifacts |
| Trace dashboard | Inspect trace data and spans |
| Triage dashboard | Review failure triage artifacts |
| Review queue | Inspect human review queue outputs |

### Local-first debugging loop

```text
Upload/select documents
   │
   v
Ask question
   │
   v
Inspect answer
   │
   ├─ citations
   ├─ warnings
   ├─ debug payload
   ├─ retrieval state
   └─ trace/quality dashboards
```

The UI is intentionally coupled to a strict backend contract so mock, local, and persistent paths all return the same final-result shape.

---

## Example Query Flow

### Example legal question walkthrough

```text
User query:
"Who is the employer under this agreement?"

1. Query understanding
   └─ detects a party-role/entity lookup style question

2. Retrieval
   ├─ searches child chunks for party/role language
   ├─ fuses dense/sparse signals where available
   └─ reranks relevant child chunks

3. Parent expansion
   └─ fetches larger parent chunks containing agreement introduction/context

4. Answerability
   └─ checks whether retrieved context contains enough party-role evidence

5. Grounded synthesis
   ├─ extracts supporting party-role evidence
   ├─ writes a direct answer
   └─ attaches citations to parent chunks/source headings

6. Final contract
   └─ answer_text, grounded, sufficient_context, citations, warnings
```

### Persistent ingestion example

```text
Upload employment-agreement.pdf
   │
   v
Validate filename and payload
   │
   v
Register Document + DocumentVersion
   │
   v
Save bytes to DOCUMENT_STORAGE_PATH
   │
   v
Create ingestion job
   │
   v
PDF → Markdown
   │
   v
Parent/child chunking
   │
   v
Persist chunks to Postgres
   │
   v
Optional child vector indexing
   │
   v
Validation + lifecycle status
   │
   v
Future persistent retrieval path:
Qdrant hit → Postgres child row → parent chunk → answer generation
```

> Persistent ingestion and storage foundations are implemented, but the complete persistent vector retrieval path should be treated as experimental until the known wiring/dependency issues are addressed.

---

## Tech Stack

| Category | Technology / pattern | Status | Where used |
|---|---|---:|---|
| Language | Python | ✅ Implemented | Entire repository |
| UI | Streamlit | ✅ Implemented | `app.py`, `ui/` |
| PDF parsing | PyMuPDF / `fitz` | ✅ Implemented | `src/agentic_rag/ingestion/converters.py` |
| PDF → Markdown | `pymupdf4llm` | ✅ Implemented | `src/agentic_rag/ingestion/converters.py` |
| Local LLM | `llama-cpp-python` | ⚙️ Optional | `src/agentic_rag/llm/local_provider.py` |
| Graph runtime | LangGraph | ⚙️ Optional fallback-supported import | `retrieval_graph.py`, `legal_rag_graph.py` |
| Data modeling | Pydantic-compatible models | ⚙️ Optional fallback shim exists | `_compat_pydantic.py`, graph/tool models |
| ORM | SQLAlchemy | ✅ Implemented | `src/agentic_rag/storage/models.py`, `postgres.py` |
| Database | Postgres | ⚠️ Persistent foundation | `docker-compose.yml`, storage config |
| Vector store | Qdrant | ⚠️ Persistent foundation / experimental runtime path | `docker-compose.yml`, Qdrant-compatible indexing/resolution modules |
| Sparse retrieval | BM25-style in-memory sparse retrieval | ✅ Implemented | `src/agentic_rag/indexing/sparse_child_chunks.py` |
| Hybrid retrieval | Reciprocal Rank Fusion | ✅ Implemented | `src/agentic_rag/retrieval/parent_child.py` |
| Testing | pytest | ✅ Implemented | `tests/` |
| Containers | Docker | ✅ Implemented | `Dockerfile` |
| Local stack | Docker Compose | ✅ Implemented | `docker-compose.yml` |
| CI quality | GitHub Actions offline eval workflows | ✅ Implemented | `.github/workflows/` |

---

## Running Locally

### 1. Clone and enter the repository

```bash
git clone <repo-url>
cd Agentic_Rag
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Start the Streamlit UI

```bash
streamlit run app.py
```

The UI supports mock mode and real local in-memory mode. For local RAG, upload/select `.md`, `.txt`, or `.pdf` files and disable mock mode in the UI.

---

### Docker Compose local stack

The repository includes a local stack with Streamlit, Postgres, and Qdrant:

```bash
docker compose up --build
```

Services:

| Service | Purpose | Local port |
|---|---|---:|
| `app` | Streamlit UI | `8501` |
| `postgres` | Persistent metadata/chunks/jobs | `5432` |
| `qdrant` | Vector storage service | `6333`, `6334` |

Configured app environment variables in Compose:

```text
DATABASE_URL
QDRANT_URL
QDRANT_COLLECTION_NAME
DOCUMENT_STORAGE_PATH
```

> Persistent mode is useful for exercising storage foundations. Treat complete persistent vector retrieval as experimental until the known limitations are resolved.

---

### Local LLM configuration

Local LLM support is optional and uses environment-backed config. Relevant variables include:

```bash
export AGENTIC_RAG_LOCAL_LLM_ENABLED=true
export AGENTIC_RAG_LOCAL_LLM_PROVIDER=llama_cpp
export AGENTIC_RAG_LOCAL_LLM_MODEL_PATH=/path/to/model.gguf
export AGENTIC_RAG_LOCAL_LLM_N_CTX=4096
export AGENTIC_RAG_LOCAL_LLM_TEMPERATURE=0.0
export AGENTIC_RAG_LOCAL_LLM_TIMEOUT_SECONDS=8.0
export AGENTIC_RAG_LOCAL_LLM_MAX_TOKENS=512
```

The UI also exposes stage toggles for rewrite, decomposition, and synthesis when local LLM mode is enabled.

---

### Run tests

```bash
pytest -q
```

> At the time this README was generated from repository inspection, the test suite was not fully green in the current environment: `781 passed, 17 failed, 1 skipped`. See [Known Limitations](#known-limitations).

---

### Run offline eval helpers

Smoke eval:

```bash
python evals/ci/offline_eval_ci.py run \
  --mode smoke \
  --output artifacts/offline_eval/smoke_run.json
```

Check smoke gate:

```bash
python evals/ci/offline_eval_ci.py check-gate \
  --run-json artifacts/offline_eval/smoke_run.json \
  --min-pass-rate 1.0 \
  --max-runner-failures 0
```

Family eval:

```bash
python evals/ci/offline_eval_ci.py run \
  --mode family \
  --family party_role \
  --output artifacts/offline_eval/family_run.json
```

Full eval:

```bash
python evals/ci/offline_eval_ci.py run \
  --mode full \
  --output artifacts/offline_eval/full_run.json
```

Build a report from an eval run:

```bash
python evals/reports/build_report.py \
  --candidate artifacts/offline_eval/full_run.json \
  --output artifacts/offline_eval/full_report.md
```

---

## Known Limitations

This project is intentionally transparent about its current maturity.

### Fully implemented and reliable paths

- Mock Streamlit backend.
- Local in-memory RAG over uploaded/selected `.md`, `.txt`, and `.pdf` files.
- Deterministic retrieval and answer graph architecture.
- Parent-child chunking.
- Hybrid retrieval abstractions and in-memory retrieval path.
- Answerability assessment and grounded answer generation.
- Strict final result contract validation.
- Offline eval runner, deterministic graders, reports, and CI workflow definitions.

### Partially wired / experimental areas

- **Persistent Postgres/Qdrant runtime path:** storage models, document registry, ingestion jobs, chunk persistence, vector indexing services, and Qdrant resolution classes exist, but complete app-level persistent vector retrieval wiring needs cleanup.
- **Persistent UI ingestion vector indexing:** the persistent ingestion UI helper constructs an `IngestionOrchestrator` without passing a vector indexing service, so persistent uploads may persist chunks without indexing vectors unless wired elsewhere.
- **Qdrant config centralization:** Compose sets `QDRANT_COLLECTION_NAME`, while code also has a default collection constant. This should be centralized.
- **Qdrant Python client dependency:** the app imports `qdrant_client`, but `requirements.txt` does not currently list `qdrant-client`.
- **Embedding backend dependency:** dense indexing expects an embedding backend and the default path references sentence-transformer-style behavior, but `requirements.txt` does not currently include `sentence-transformers`.
- **Persistent backend import mismatch:** app-level persistent wiring references `qdrant_config_from_env`; this symbol should be verified/fixed before treating persistent mode as production-ready.

### Current test baseline

A full `pytest -q` run in the inspected environment produced:

```text
781 passed, 17 failed, 1 skipped
```

Observed failures were concentrated around:

- latest eval JSON selection,
- document deletion cascade behavior,
- document version/job ordering,
- ingestion retry/reindex behavior,
- ingestion validation,
- persistent ingestion duplicate/status handling.

### Non-production caveats

- No dedicated HTTP API layer is implemented.
- No authentication/authorization layer is implemented.
- No cloud deployment configuration is included.
- Local in-memory retrieval is not intended for large durable corpora.
- Docker Compose is a local stack, not a production deployment claim.
- File upload handling includes path/extension safeguards, but production deployments would need stronger security controls.

---

## Future Improvements

A realistic roadmap based on the current architecture:

### Persistence and retrieval

- Fully wire persistent ingestion → vector indexing → Qdrant retrieval → Postgres resolution → parent expansion.
- Centralize Qdrant configuration and collection naming.
- Add missing optional dependencies or dependency extras for persistent/vector modes.
- Add an end-to-end persistent retrieval integration test.

### Packaging and developer experience

- Add `pyproject.toml` with package metadata and optional dependency groups.
- Split dependencies into runtime, development, persistent, and local-LLM extras.
- Define supported Python versions explicitly.
- Reduce ad hoc path bootstrapping by installing the package in editable mode.

### Retrieval quality

- Add stronger reranking options behind the existing reranker abstraction.
- Expand legal sparse tokenization and retrieval diagnostics.
- Add retrieval evaluation slices by legal question family.
- Add caching for repeated local document chunking/indexing.

### Application architecture

- Extract persistent backend construction out of `app.py` into a dedicated runtime module.
- Add a dedicated API layer if the project evolves beyond Streamlit inspection.
- Add stronger upload validation, file-size limits, and deployment security guidance.

### Observability and evaluation

- Expand trace dashboards with node-level latency and artifact lineage.
- Add more regression families and failure taxonomies.
- Track eval changes over time in dashboard/report artifacts.
- Expand online shadow grading hooks once runtime paths are stabilized.

---

## Why This Project Matters

RAG systems are easy to demo and hard to trust.

Legal RAG is even harder: a useful system must preserve context, cite evidence, know when evidence is weak, and fail safely when the document set does not support an answer. It must also be debuggable when retrieval misses something or synthesis overstates the record.

`Agentic_Rag` is interesting because it treats those concerns as architecture, not decoration:

- **Deterministic orchestration** makes behavior inspectable.
- **Parent-child retrieval** balances precision and context.
- **Answerability gating** prevents unsupported answers.
- **Grounded synthesis** keeps claims tied to evidence.
- **Strict contracts** make UI, eval, and orchestration boundaries safer.
- **Offline evaluation** turns quality into a repeatable engineering workflow.
- **Persistence foundations** show how local demos can evolve toward durable document lifecycle management.

The project is not trying to hide complexity behind a single chatbot prompt. It exposes the moving parts that make trustworthy legal AI systems possible.
