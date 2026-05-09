# Agentic_Rag

> **Deterministic, local-first legal RAG with grounded answers, answerability gating, citations, tracing, and offline evaluation.**

<p>
  <img alt="Python" src="https://img.shields.io/badge/Python-3-blue">
  <img alt="Streamlit" src="https://img.shields.io/badge/UI-Streamlit-red">
  <img alt="RAG" src="https://img.shields.io/badge/Architecture-RAG-purple">
  <img alt="Legal AI" src="https://img.shields.io/badge/Domain-Legal%20AI-darkgreen">
  <img alt="Local First" src="https://img.shields.io/badge/Runtime-Local--first-orange">
  <img alt="Evaluation" src="https://img.shields.io/badge/Quality-Offline%20Evals-informational">
</p>

`Agentic_Rag` is a legal retrieval-augmented generation system designed around **explicit graph orchestration**, **parent-child retrieval**, **hybrid search**, **answerability assessment**, and a **strict final answer contract**.

It is intentionally built as a transparent engineering system rather than a black-box chatbot: every answer is routed through retrieval, evidence sufficiency checks, grounded synthesis, citations, warnings, traces, and evaluation tooling.

---

## 🎬 Hero GIFs

> The repository does not currently include these GIF assets. The paths below are placeholders for demo media that can be added later.

### End-to-end demo

![Agentic RAG Demo](assets/demo.gif)

**Suggested demo content:** upload/select documents in the Streamlit inspection UI, submit a legal question, inspect the final answer, expand citations, and download the debug payload.

### Retrieval + answerability flow

![RAG Flow](assets/rag-flow.gif)

**Suggested demo content:** query understanding → hybrid retrieval → reranking → parent expansion → answerability gate → grounded answer or insufficient-context fallback.

### Architecture walkthrough

![Architecture](assets/architecture.gif)

**Suggested demo content:** animate how source documents become parent/child chunks, how child hits map back to parent context, and how final answers preserve citations.

---

## Table of Contents

- [Short Project Introduction](#short-project-introduction)
- [Architecture Overview](#architecture-overview)
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
- [Current Limitations](#current-limitations)
- [Future Improvements](#future-improvements)
- [Why This Project Matters](#why-this-project-matters)

---

## Short Project Introduction

Legal RAG systems need more than a retriever and a generator. They need to know when **not** to answer.

This repository implements a local-first legal RAG architecture that emphasizes:

- **Deterministic orchestration** over open-ended agent loops.
- **Grounded answers** produced only from retrieved context.
- **Citation-bearing responses** with parent-chunk traceability.
- **Answerability gating** before synthesis.
- **Offline evaluation and traceability** as first-class system features.
- **Streamlit inspection dashboards** for debugging retrieval, grounding, traces, and failures.

The system is currently best understood as a **portfolio-quality local legal RAG platform and evaluation harness**, not as a deployed production service.

---

## Architecture Overview

### High-level system diagram

```text
┌─────────────────────────────────────────────────────────────────────┐
│                          Streamlit UI                               │
│  Inspection · Quality · Trace Debug · Failure Triage · Review Queue  │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                v
┌─────────────────────────────────────────────────────────────────────┐
│                       Backend Adapter                               │
│  validates final contract · switches mock/local/real runner boundary │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                  ┌─────────────┴─────────────┐
                  │                           │
                  v                           v
        ┌──────────────────┐       ┌──────────────────────────┐
        │ Mock Backend      │       │ Local Legal RAG Backend  │
        │ deterministic UI  │       │ in-memory document scope │
        │ demo responses    │       │ + LegalRagDependencies   │
        └──────────────────┘       └─────────────┬────────────┘
                                                  │
                                                  v
                                  ┌──────────────────────────┐
                                  │ Retrieval Graph          │
                                  │ query understanding      │
                                  │ decomposition/rewrite    │
                                  │ hybrid search/rerank     │
                                  │ parent expansion         │
                                  └─────────────┬────────────┘
                                                │
                                                v
                                  ┌──────────────────────────┐
                                  │ Answer Graph             │
                                  │ answer context selection │
                                  │ answerability gate       │
                                  │ grounded synthesis       │
                                  │ safe fallback            │
                                  └─────────────┬────────────┘
                                                │
                                                v
                                  ┌──────────────────────────┐
                                  │ FinalAnswerModel         │
                                  │ answer_text              │
                                  │ grounded                 │
                                  │ sufficient_context       │
                                  │ citations                │
                                  │ warnings                 │
                                  └──────────────────────────┘
```

### Component relationship diagram

```text
app.py
  ├── ui/backend_adapter.py
  │     ├── ui/mock_backend.py
  │     └── real/local backend runner boundary
  │
  ├── ui/local_backend.py
  │     ├── ingestion/document_ingestors.py
  │     ├── chunking/markdown.py
  │     ├── retrieval/parent_child.py
  │     ├── tools/query_intelligence.py
  │     ├── tools/answer_generation.py
  │     └── orchestration/legal_rag_graph.py
  │
  └── dashboards
        ├── ui/quality_dashboard.py
        ├── ui/trace_dashboard.py
        ├── ui/triage_dashboard.py
        └── ui/review_queue_dashboard.py
```

### Retrieval + answer flow visualization

```text
User Query
   │
   v
Query Understanding
   │  question type · family notes · rewrite flags · retrieval flags
   v
Context Resolution
   │  follow-up/session scope handling
   v
Decomposition Gate
   │  optional subquery plan
   v
Hybrid Retrieval
   │  dense path + sparse path
   v
RRF Fusion
   │  rank-based merge of child hits
   v
Deterministic Rerank
   │  lexical/legal-term scoring
   v
Parent Expansion
   │  child_chunk_id → parent_chunk_id → parent context
   v
Answerability Gate
   │  sufficient evidence? partial? weak? none?
   ├─────────────── no ────────────────┐
   │                                   v
   │                      Insufficient-context response
   │                                   │
   v yes                               │
Grounded Synthesis                     │
   │                                   │
   v                                   v
Citations + Warnings + Final Contract
```

### Layer summary

| Layer | Responsibility | Representative modules |
|---|---|---|
| UI | Local inspection, dashboards, document selection, debug payload display | `app.py`, `ui/components.py`, `ui/backend_adapter.py` |
| Local backend | Build in-memory legal RAG dependencies from selected local documents | `ui/local_backend.py` |
| Ingestion | Markdown/PDF normalization into `Document` | `src/agentic_rag/ingestion/` |
| Chunking | Markdown-aware parent-child chunking | `src/agentic_rag/chunking/` |
| Retrieval | Dense/sparse facades, RRF, rerank, parent expansion | `src/agentic_rag/retrieval/` |
| Orchestration | Explicit retrieval and answer graphs | `src/agentic_rag/orchestration/` |
| Safety/tools | Answerability, grounded synthesis, query intelligence, context processing | `src/agentic_rag/tools/` |
| Evaluation | Offline runner, graders, reports, dashboards, CI gates | `evals/`, `.github/workflows/` |

---

## Key Architectural Design Decisions

### 1. Deterministic orchestration instead of free-form agent loops

**Why it exists**

Legal answering needs traceability. The retrieval and answer stages are implemented as explicit graphs with named nodes and bounded transitions.

**Tradeoff**

- ✅ Easier to test, inspect, and reason about.
- ✅ Safer routing and clearer failure modes.
- ❌ Less flexible than autonomous agent loops for open-ended tool use.

**Production reasoning**

For legal workflows, predictable control flow is usually more valuable than autonomous creativity. The system favors explicit state transitions and typed contracts.

---

### 2. Parent-child chunking

**Why it exists**

Small chunks improve retrieval precision, but legal answers often need larger clause/section context. This repo splits documents into:

- **Child chunks**: retrieval units.
- **Parent chunks**: context units for answer generation.

**Tradeoff**

- ✅ Better precision during search.
- ✅ Better context during synthesis.
- ❌ Requires maintaining parent/child traceability.

**Production reasoning**

This makes citations and context expansion auditable: child hits can be mapped back to parent chunks before synthesis.

---

### 3. Hybrid retrieval with RRF

**Why it exists**

Legal queries often mix semantic paraphrase with exact terms, dates, roles, section labels, and legal phrases. Dense-only or sparse-only retrieval can miss important evidence.

**Tradeoff**

- ✅ Sparse retrieval helps exact legal terminology.
- ✅ Dense-compatible retrieval architecture supports semantic retrieval.
- ✅ RRF avoids comparing incompatible score scales.
- ❌ More moving parts than a single retriever.

**Production reasoning**

Rank fusion is robust and deterministic. It lets retrieval sources contribute without pretending their raw scores mean the same thing.

---

### 4. Answerability gate before synthesis

**Why it exists**

A retrieved chunk can be related to a query without actually answering it. The system evaluates evidence coverage and evidence strength before generating a final answer.

**Tradeoff**

- ✅ Reduces unsupported answers.
- ✅ Makes insufficient evidence a first-class outcome.
- ❌ May be conservative and decline some borderline answerable cases.

**Production reasoning**

In legal contexts, safe refusal or qualification is better than confident unsupported synthesis.

---

### 5. Grounded synthesis with structured citations

**Why it exists**

The answer generator is designed to synthesize only from supplied context and return structured citations separately from prose.

**Tradeoff**

- ✅ Auditability and downstream validation.
- ✅ UI can render citations independently.
- ❌ Responses depend heavily on retrieval quality.

**Production reasoning**

Separating answer text from citations and warnings gives callers a stable contract and makes quality checks easier.

---

### 6. Local-first design

**Why it exists**

The system can run with local documents, in-memory repositories, a mock backend, and optional local `llama.cpp` model support.

**Tradeoff**

- ✅ Easy inspection and iteration.
- ✅ No hosted service required for the local path.
- ❌ Not a production deployment architecture by itself.

**Production reasoning**

Local-first debugging is valuable before introducing persistent stores, hosted services, or deployment complexity.

---

### 7. Evaluation-first architecture

**Why it exists**

The repository includes offline datasets, deterministic graders, LLM judge helpers, quality reports, trace dashboards, triage workflows, and CI/nightly eval workflows.

**Tradeoff**

- ✅ Quality behavior can be inspected and regression-tested.
- ✅ Failures can be triaged into review queues and regression drafts.
- ❌ Evaluation infrastructure adds code and maintenance overhead.

**Production reasoning**

RAG quality is system behavior, not just model behavior. Evaluation must be part of the architecture, not an afterthought.

---

## End-to-End Pipeline

```text
1. Document ingestion
   └── Markdown/PDF → Document

2. Markdown-aware chunking
   └── Document → ParentChunk[] + ChildChunk[]

3. Indexing / local repositories
   └── ChildChunk[] → dense-compatible payloads + sparse/in-memory records

4. Retrieval
   └── query → dense hits + sparse hits → RRF fused child hits

5. Reranking
   └── fused child hits → reranked child hits

6. Parent expansion
   └── parent_chunk_id[] → ParentChunkResult[]

7. Optional context compression
   └── parent context → compressed context when thresholds trigger

8. Answerability
   └── coverage + evidence strength → answer / partial / insufficient route

9. Synthesis
   └── grounded answer or insufficient-context fallback

10. Final contract
   └── answer_text · grounded · sufficient_context · citations · warnings
```

| Stage | Implementation | Important classes/functions |
|---|---|---|
| Ingestion | `src/agentic_rag/ingestion/` | `MarkdownDocumentIngestor`, `PDFDocumentIngestor`, `PyMuPDF4LLMConverter` |
| Chunking | `src/agentic_rag/chunking/` | `MarkdownParentChildChunker`, `ParentChunker`, `RecursiveChildChunker`, `ParentChunk`, `ChildChunk` |
| Dense-compatible indexing | `src/agentic_rag/indexing/dense_child_chunks.py` | `DenseEmbeddingService`, `ChildChunkDenseIndexer`, `QdrantChildChunkStore`, `ChildChunkQdrantPayload` |
| Sparse indexing | `src/agentic_rag/indexing/sparse_child_chunks.py` | `BM25Index`, `LegalSparseTokenizer`, `SparseIndexedChildChunk` |
| Retrieval | `src/agentic_rag/retrieval/parent_child.py` | `HybridSearchService`, `RRFFuser`, `ChunkReranker`, `ParentChunkStore` |
| Retrieval graph | `src/agentic_rag/orchestration/retrieval_graph.py` | `RetrievalStageState`, `RetrievalDependencies`, `build_retrieval_graph`, `run_retrieval_stage` |
| Answer graph | `src/agentic_rag/orchestration/legal_rag_graph.py` | `LegalRagState`, `FinalAnswerModel`, `build_answer_graph`, `run_legal_rag_turn_with_state` |
| Answerability | `src/agentic_rag/tools/answerability.py` | `AnswerabilityAssessment`, `evaluate_coverage`, `evaluate_evidence_strength`, `assess_answerability` |
| Synthesis | `src/agentic_rag/tools/answer_generation.py` | `LegalAnswerSynthesizer`, `GenerateAnswerResult`, `AnswerCitation`, `generate_answer` |
| UI | `app.py`, `ui/` | `run_backend_query`, `build_local_backend_dependencies`, dashboard renderers |
| Evaluation | `evals/` | `run_offline_eval`, deterministic graders, report builders |

---

## Repository Structure

```text
.
├── app.py                                # Streamlit entrypoint and dashboard router
├── requirements.txt                      # Runtime/test dependencies
├── README.md                             # Project documentation
│
├── src/agentic_rag/
│   ├── __init__.py                       # Package exports
│   ├── types.py                          # Shared Document/Chunk/RetrievedItem/Generation dataclasses
│   ├── versioning.py                     # Stable version attribution for traces/evals
│   │
│   ├── ingestion/                        # Markdown/PDF ingestion into Document objects
│   │   ├── converters.py                 # PDF → Markdown converter protocol + PyMuPDF4LLM implementation
│   │   └── document_ingestors.py         # MarkdownDocumentIngestor, PDFDocumentIngestor
│   │
│   ├── chunking/                         # Markdown-aware parent-child chunking
│   │   ├── markdown.py                   # ParentChunker, RecursiveChildChunker, MarkdownParentChildChunker
│   │   └── models.py                     # ParentChunk, ChildChunk, ChunkingResult
│   │
│   ├── indexing/                         # Dense-compatible and sparse indexing components
│   │   ├── dense_child_chunks.py         # Embedding service + Qdrant-compatible child payload/upsert pipeline
│   │   └── sparse_child_chunks.py        # In-memory BM25 sparse index
│   │
│   ├── retrieval/                        # Parent-child retrieval services
│   │   ├── parent_child.py               # Hybrid search, RRF fusion, reranking, parent expansion
│   │   └── sparse.py                     # Sparse search service facade
│   │
│   ├── orchestration/                    # Deterministic graph orchestration
│   │   ├── query_understanding.py        # Query classification and routing hints
│   │   ├── retrieval_graph.py            # Retrieval-stage graph
│   │   ├── legal_rag_graph.py            # Full retrieval + answer graph
│   │   ├── tracing.py                    # Trace helpers
│   │   ├── metrics.py                    # Request metric emission
│   │   ├── traffic_sampling.py           # Production traffic sampling helpers
│   │   └── online_shadow_grading.py      # Shadow grading support
│   │
│   ├── tools/                            # Deterministic RAG tools
│   │   ├── answerability.py              # Evidence coverage/strength assessment
│   │   ├── answer_generation.py          # Grounded synthesis + citations
│   │   ├── context_processing.py         # Context compression
│   │   ├── evidence_units.py             # Normalized evidence extraction
│   │   ├── party_role_resolution.py      # Party-role-specific parsing helpers
│   │   └── query_intelligence.py         # Rewrite/entity/decomposition helpers
│   │
│   ├── llm/                              # Local LLM provider abstraction
│   │   └── local_provider.py             # llama.cpp-backed prompt client and env config
│   │
│   ├── config/                           # Configuration interfaces
│   ├── evaluation/                       # Evaluation interfaces
│   └── prompts/                          # Prompt template interfaces
│
├── ui/
│   ├── backend_adapter.py                # Strict UI/backend boundary and final result validation
│   ├── local_backend.py                  # Local in-memory LegalRagDependencies builder
│   ├── mock_backend.py                   # Mock backend for immediate UI testing
│   ├── components.py                     # Streamlit widgets and result rendering
│   ├── upload_manager.py                 # Local upload persistence and validation
│   ├── session_memory.py                 # Conversation history/context helpers
│   ├── quality_dashboard.py              # Quality dashboard UI
│   ├── trace_dashboard.py                # Trace debug dashboard UI
│   ├── triage_dashboard.py               # Failure triage dashboard UI
│   └── review_queue_dashboard.py         # Human review queue dashboard UI
│
├── evals/
│   ├── datasets/                         # JSONL legal eval datasets
│   ├── fixtures/offline_documents/       # Local Markdown fixture documents
│   ├── schema/legal_eval_case.json       # Eval case JSON schema
│   ├── runners/run_offline_eval.py       # Offline eval runner
│   ├── ci/offline_eval_ci.py             # CI wrapper/gates for eval runs
│   ├── graders/                          # Deterministic graders + LLM judge parsers
│   └── reports/                          # Report/dashboard/triage data builders
│
├── docs/                                 # Quality contracts, release gates, taxonomy, ramp/checklist docs
├── observability/schema/trace_schema.md  # Trace schema and required spans
├── tests/                                # Unit/integration tests for core architecture and eval tooling
└── .github/workflows/                    # Offline eval PR and nightly workflows
```

<details>
<summary><strong>Why the structure matters</strong></summary>

The repository separates concerns deliberately:

- `src/agentic_rag/` contains reusable system logic.
- `ui/` contains Streamlit-specific inspection and dashboard code.
- `evals/` contains offline quality infrastructure.
- `.github/workflows/` operationalizes eval gates.
- `docs/` and `observability/` define quality and trace contracts.

This keeps the core RAG architecture usable independently from the local UI and evaluation dashboards.

</details>

---

## Retrieval Architecture Deep Dive

Legal retrieval has two competing needs:

1. **Semantic recall** for paraphrased questions.
2. **Exact lexical precision** for clauses, dates, parties, legal terms, and document-specific language.

This repository models retrieval as a parent-child pipeline.

```text
                      ┌─────────────────────────────┐
                      │          User Query          │
                      └──────────────┬──────────────┘
                                     │
                                     v
                  ┌─────────────────────────────────────┐
                  │       Query Understanding            │
                  │ flags · family notes · expectations  │
                  └──────────────┬──────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                    v                         v
        ┌──────────────────────┐   ┌──────────────────────┐
        │ Dense-compatible path │   │ Sparse keyword path   │
        │ child chunk search    │   │ BM25/in-memory search │
        └──────────┬───────────┘   └──────────┬───────────┘
                   │                          │
                   └────────────┬─────────────┘
                                v
                    ┌──────────────────────┐
                    │ RRF Fusion            │
                    │ rank-based merge      │
                    └──────────┬───────────┘
                               v
                    ┌──────────────────────┐
                    │ Deterministic Rerank  │
                    │ lexical + legal bonus │
                    └──────────┬───────────┘
                               v
                    ┌──────────────────────┐
                    │ Parent Expansion      │
                    │ child → parent        │
                    └──────────────────────┘
```

### Dense-compatible retrieval

The dense indexing path defines:

- `DenseEmbeddingConfig`
- `DenseEmbeddingService`
- `ChildChunkDenseIndexer`
- `QdrantChildChunkStore`
- `ChildChunkQdrantPayload`

It is designed around child chunks and Qdrant-compatible payloads. The code includes a Qdrant-like client protocol and deterministic point IDs for idempotent upserts.

> Current status: the dense indexing code is implemented, but concrete persistent vector database setup is not included in the repository.

### Sparse retrieval

Sparse retrieval uses a deterministic in-memory BM25 index:

- `LegalSparseTokenizer`
- `BM25Index`
- `SparseSearchService`

The tokenizer intentionally preserves legal notation better than aggressive punctuation stripping.

### RRF fusion

`RRFFuser` combines dense and sparse ranked lists using Reciprocal Rank Fusion:

```text
score += 1 / (rrf_k + rank)
```

Why RRF?

- Dense scores and sparse scores are not directly comparable.
- Rank-based fusion is deterministic.
- A chunk found by both retrievers gets stronger evidence through matched-source count and rank position.

### Reranking

`ChunkReranker` is currently deterministic and lexical. It scores query overlap and adds small bonuses for legal terms such as:

```text
means · shall · must · defined · rule · clause
```

> Future work: replace or augment this with a learned cross-encoder reranker while preserving the same rerank contract.

### Parent expansion

The retriever does not send isolated child chunks directly to answer generation. Instead:

```text
child_chunk_id → parent_chunk_id → ParentChunkResult
```

This preserves context for legal reasoning and gives citations a clear path back to source document sections.

---

## Answer Generation & Safety

The answer stage is built around a simple principle:

> **If the retrieved evidence is not sufficient, the system should say so.**

### Answer graph

```text
Retrieved parent context
        │
        v
prepare_answer_context
        │
        v
assess_answerability
        │
        v
 generate_subquery_subanswers
        │
        ├── sufficient evidence ──► generate_grounded_answer
        │                              │
        │                              v
        │                         finalize_response
        │
        └── insufficient evidence ─► build_insufficient_response
                                       │
                                       v
                                  finalize_response
```

### Final answer contract

Every final answer conforms to:

```python
{
    "answer_text": str,
    "grounded": bool,
    "sufficient_context": bool,
    "citations": list,
    "warnings": list,
}
```

This contract is enforced in both the graph output model and the UI backend adapter.

### Answerability gate

The answerability layer evaluates:

- whether context is relevant,
- whether evidence is strong enough,
- whether a definition/summary/fact/comparison expectation is satisfied,
- whether a partial or insufficient response is safer.

It produces an `AnswerabilityAssessment` consumed by the answer graph.

### Grounded synthesis

`LegalAnswerSynthesizer`:

- uses supplied context only,
- extracts support points,
- builds citations,
- identifies caveats and warnings,
- returns safe insufficient/failure responses when needed,
- optionally uses a configured local LLM for drafting while preserving fallback behavior.

### Citation model

Each `AnswerCitation` includes:

| Field | Purpose |
|---|---|
| `parent_chunk_id` | Trace answer support back to parent context |
| `document_id` | Identify source document |
| `source_name` | Human-readable source label |
| `heading` | Section/heading context |
| `supporting_excerpt` | Short evidence excerpt supporting the claim |

---

## Evaluation & Observability

This repository treats evaluation as part of the system architecture.

### Offline evals

```text
JSONL eval case
   │
   v
run_offline_eval.py
   │
   ├── execute legal RAG case
   ├── capture final result
   ├── capture debug payload/state
   ├── run deterministic graders
   ├── optionally run LLM judge parsers/callables
   └── write machine-readable JSON artifact
```

Key files:

| Area | Files |
|---|---|
| Eval runner | `evals/runners/run_offline_eval.py` |
| CI eval wrapper | `evals/ci/offline_eval_ci.py` |
| Eval schema | `evals/schema/legal_eval_case.json` |
| Datasets | `evals/datasets/*.jsonl` |
| Fixture docs | `evals/fixtures/offline_documents/*.md` |

### Deterministic graders

The repository includes deterministic graders for:

- answerability checks,
- citation checks,
- final contract checks,
- family routing,
- retrieval checks.

These live under `evals/graders/`.

### LLM judge helpers

The repo includes prompt/result parsing helpers for:

- answer correctness,
- groundedness,
- safe failure.

These live under `evals/graders/llm_judges/`.

> The repository provides judge prompt/parsing infrastructure. Actual external model execution depends on callables supplied to the eval runner.

### CI gates

Pull request workflow:

```text
Offline Eval PR Gates
├── Smoke offline eval
│   ├── install requirements
│   ├── run smoke eval
│   └── enforce pass-rate gate
│
└── Family offline eval for touched areas
    ├── collect changed files
    ├── resolve impacted families
    ├── run family evals
    └── enforce pass-rate gate
```

Nightly workflow:

```text
Offline Eval Nightly Regression
└── full offline regression
    ├── run full eval
    ├── build markdown report
    └── upload artifacts
```

### Observability

The trace schema defines seven required core spans:

1. `query_understanding`
2. `decomposition`
3. `retrieval`
4. `rerank`
5. `parent_expansion`
6. `answerability`
7. `final_synthesis`

Trace and dashboard support is implemented through:

- `src/agentic_rag/orchestration/tracing.py`
- `observability/schema/trace_schema.md`
- `ui/trace_dashboard.py`
- `evals/reports/trace_dashboard_data.py`

### Review and triage workflow

The repository includes dashboard/report support for:

- quality dashboard data,
- trace drilldowns,
- failure triage,
- human review queues,
- run comparison reports.

Representative modules:

```text
evals/reports/quality_dashboard_data.py
evals/reports/trace_dashboard_data.py
evals/reports/triage_workflow.py
evals/reports/human_review_queue.py
evals/reports/compare_runs.py
```

---

## Streamlit Inspection UI

Run locally:

```bash
streamlit run app.py
```

The Streamlit app provides a local-first inspection surface for the legal RAG pipeline.

### Dashboard pages

| Page | Purpose |
|---|---|
| Inspection | Submit queries, select documents, inspect answer/citations/debug payload |
| Quality | Explore offline quality/eval results |
| Trace Debug | Inspect trace-stage behavior and failure points |
| Failure Triage | Review failing eval cases and draft regression follow-ups |
| Human Review Queue | Review queued cases and human feedback workflows |

### Backend modes

| Mode | Description |
|---|---|
| Mock backend | Immediate UI testing without running the full local RAG pipeline |
| Local backend | Builds in-memory retrieval dependencies from selected `.md`, `.txt`, or `.pdf` documents |
| Real runner boundary | `app.py` can call a configured `LegalRagDependencies` runner through the adapter boundary |

### Local debugging features

- final answer rendering,
- citation rendering,
- expandable debug payloads,
- runtime mode status,
- uploaded document selection,
- conversation context handling,
- quality/trace/failure dashboards.

---

## Example Query Flow

> Example is illustrative of the implemented pipeline shape, not a benchmark result.

```text
User query:
"Who is the employer in this agreement?"
```

### 1. Query understanding

```text
question_type: extractive/legal fact style
routing_notes: may include party-role family notes
should_rewrite: possibly true for party-role style queries
should_extract_entities: true for party-role style queries
```

### 2. Retrieval

```text
Hybrid search over child chunks
├── dense-compatible path
├── sparse keyword path
└── RRF fused child candidates
```

### 3. Rerank + parent expansion

```text
reranked_child_results
   │
   v
parent_chunk_ids
   │
   v
parent_chunks containing agreement introduction / party language
```

### 4. Answerability

```text
Does the retrieved parent context actually identify the employer?
├── yes → generate grounded answer
└── no  → insufficient-context response
```

### 5. Final answer contract

```json
{
  "answer_text": "Direct answer: ...",
  "grounded": true,
  "sufficient_context": true,
  "citations": [
    {
      "parent_chunk_id": "...",
      "document_id": "...",
      "source_name": "...",
      "heading": "...",
      "supporting_excerpt": "..."
    }
  ],
  "warnings": []
}
```

---

## Tech Stack

| Category | Technology / Pattern | Where used |
|---|---|---|
| Language | Python | Entire repository |
| UI | Streamlit | `app.py`, `ui/` |
| PDF parsing | PyMuPDF / `fitz` | `src/agentic_rag/ingestion/converters.py` |
| PDF → Markdown | `pymupdf4llm` | `src/agentic_rag/ingestion/converters.py` |
| Local LLM | `llama-cpp-python` | `src/agentic_rag/llm/local_provider.py` |
| Optional graph runtime | LangGraph if installed, deterministic fallback otherwise | `src/agentic_rag/orchestration/retrieval_graph.py`, `legal_rag_graph.py` |
| Optional data models | Pydantic if installed, local compatibility shim otherwise | `_compat_pydantic.py`, graph/tool models |
| Sparse retrieval | In-memory BM25-style index | `src/agentic_rag/indexing/sparse_child_chunks.py` |
| Hybrid retrieval | Reciprocal Rank Fusion | `src/agentic_rag/retrieval/parent_child.py` |
| Dense-compatible indexing | Qdrant-like client protocol and payload schema | `src/agentic_rag/indexing/dense_child_chunks.py` |
| Testing | pytest | `tests/` |
| CI quality | GitHub Actions offline eval workflows | `.github/workflows/` |
| Eval artifacts | JSONL datasets + JSON reports | `evals/` |

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

On Windows PowerShell:

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

### 5. Run tests

```bash
pytest -q
```

> Note: tests that import the Streamlit app require `streamlit` to be installed. It is listed in `requirements.txt`.

### 6. Run offline evals

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

Full offline eval runner:

```bash
python evals/runners/run_offline_eval.py \
  --output artifacts/offline_eval/manual_run.json \
  --all-families
```

Build report from a candidate run:

```bash
python evals/reports/build_report.py \
  --candidate artifacts/offline_eval/manual_run.json \
  --output artifacts/offline_eval/manual_report.md
```

### 7. Optional local LLM configuration

The local LLM provider reads environment variables such as:

```bash
export AGENTIC_RAG_LOCAL_LLM_ENABLED=true
export AGENTIC_RAG_LOCAL_LLM_PROVIDER=llama_cpp
export AGENTIC_RAG_LOCAL_LLM_MODEL_PATH=/path/to/model.gguf
export AGENTIC_RAG_LOCAL_LLM_TEMPERATURE=0.0
export AGENTIC_RAG_LOCAL_LLM_N_CTX=4096
export AGENTIC_RAG_LOCAL_LLM_MAX_TOKENS=512
```

If local LLM support is disabled or unavailable, the system uses deterministic fallback paths where implemented.

---

## Current Limitations

This section is intentionally explicit. The repository is engineered, but it does not claim more than it implements.

| Limitation | Current state |
|---|---|
| Production deployment | No Dockerfile, API service, deployment manifests, or cloud infrastructure are included. |
| Persistent vector DB runtime | Dense indexing is Qdrant-compatible by interface/payload, but concrete persistent Qdrant setup is not included. |
| Local backend storage | The local backend builds in-memory repositories from selected documents. |
| Sparse index persistence | BM25 index is in-memory and process-local. |
| Reranker | Reranking is deterministic lexical scoring, not a learned cross-encoder. |
| Optional dependencies | LangGraph, Pydantic, and tiktoken are supported opportunistically/fallback-style, but not all are listed as required runtime dependencies. |
| Hosted LLM providers | Not implemented. Local `llama.cpp` support is implemented. |
| Upload ingestion hook | `register_uploaded_documents` is currently a no-op hook; local backend reads selected documents directly. |
| README media | GIF paths are placeholders unless assets are added. |

---

## Future Improvements

These are realistic next steps, not claims about current functionality.

### Retrieval and indexing

- Add concrete persistent Qdrant wiring and setup documentation.
- Add caching for local document chunking/index construction.
- Add an optional learned reranker behind the existing rerank contract.
- Add larger-corpus retrieval performance tests.

### Serving and deployment

- Add an API layer if non-Streamlit consumption is needed.
- Add Docker/deployment configuration once runtime requirements are finalized.
- Add environment/config templates for production-like settings.

### Evaluation and quality

- Add coverage reporting.
- Add static typing and lint/format configuration.
- Add benchmark summaries generated from actual eval artifacts.
- Add regression dashboards backed by committed or generated sample artifacts.

### UX and inspection

- Add demo GIFs under `assets/`.
- Add richer retrieval trace visualization in the UI.
- Add side-by-side comparison for baseline vs candidate eval runs.

---

## Why This Project Matters

RAG systems fail in ways that are easy to miss:

- retrieving related but non-answering context,
- synthesizing beyond the evidence,
- hiding uncertainty,
- losing citation traceability,
- improving a demo while regressing evaluation behavior.

Those failures are especially serious in legal AI systems, where **groundedness, sufficiency, auditability, and repeatability** matter more than conversational fluency.

`Agentic_Rag` is built around that premise. It treats retrieval, answerability, synthesis, citations, traces, and evaluation as one connected system. The architecture is intentionally conservative: explicit graphs, typed contracts, deterministic fallbacks, offline quality gates, and human-review tooling.

The goal is not to make the system look magical.

The goal is to make it inspectable.

