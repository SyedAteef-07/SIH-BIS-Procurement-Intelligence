# CHAT_CONTEXT.md

## Purpose

This file summarizes the important design decisions and implementation context discussed for the AI portion of the SIH project. Codex should read this file together with `README.md` and `AI_PLAN.md` and treat those files as the project source of truth.

## Project Context

The project is an **AI-powered Indian Standards recommendation engine for procurement workflows**.

It should help procurement officials identify:
- relevant Indian Standards
- allied / related standards
- normative references
- cross-referenced standards
- superseded / revised standards
- evidence explaining why a standard is relevant

The system assists the procurement official; the final decision remains with a human.

## Inputs

The system should eventually accept:
- product descriptions
- procurement requirements
- technical specifications
- tender text
- tender PDFs

Example:

```text
Procurement of three-phase oil immersed distribution transformers
suitable for outdoor installation at 11 kV / 433 V.
```

## Expected Output

The final system should return structured recommendations such as:

```json
{
  "standard_id": "IS XXXX",
  "title": "Example standard title",
  "relevance_score": 0.92,
  "reason": "Relevant because ...",
  "supporting_evidence": ["..."],
  "related_standards": ["IS YYYY"],
  "status": "active",
  "revision": "latest verified revision"
}
```

Do not display raw model scores as probabilities unless scores have been calibrated.

---

## Core AI Architecture

```text
Product Description / Tender
            |
            v
    Document Parsing
            |
            v
    NLP Preprocessing
            |
            v
Requirement / Entity Extraction
            |
            v
    Semantic Embeddings
            |
            v
      Vector Search
         FAISS
            |
            v
   Candidate Standards
            |
            v
 Cross-Encoder Reranking
            |
            v
   Top Ranked Standards
            |
      +-----+------+
      |            |
      v            v
Relationship     Metadata /
Layer            Version Check
      |            |
      +-----+------+
            |
            v
        RAG / LLM
            |
            v
Evidence-backed Recommendation
```

The project should be described as:

```text
NLP
+
Semantic Search
+
Information Retrieval
+
Reranking
+
Knowledge / Relationship Graph
+
RAG
```

---

## NLP Preprocessing

Keep preprocessing conservative.

Do:
- normalize whitespace
- normalize line breaks
- remove obvious extraction noise
- preserve technical terminology
- preserve numbers
- preserve units
- preserve negation

Do not aggressively:
- remove stopwords
- stem every word
- remove numbers
- remove measurement units

For example, `not suitable for indoor use` must never become `suitable indoor use`.

---

## Embeddings

The system should use sentence embeddings for semantic retrieval so that:

```text
oil immersed distribution transformer
```

can semantically match:

```text
requirements for distribution transformers
```

even without exact keyword overlap.

Current preferred prototype embedding model:

```text
sentence-transformers/all-MiniLM-L6-v2
```

The embedding model must be configurable so it can later be replaced after evaluation or security review.

---

## Government / Security Design

This project is intended for SIH and potentially a government organization.

The **core recommendation pipeline should be capable of running fully on-premises / locally**.

Preferred architecture:

```text
Tender
  |
Local NLP
  |
Local Embedding Model
  |
Local FAISS Index
  |
Local Reranker
  |
Local Standards Database
  |
Recommendation
```

Tender data should not need to leave the organization's infrastructure.

### Model supply-chain guidance

For serious deployment:
1. Select an approved model.
2. Download model weights once.
3. Verify checksums and provenance.
4. Prefer safe formats such as `safetensors`.
5. Store approved model artifacts internally.
6. Disable runtime model downloads.
7. Run inference locally.
8. Review licenses.
9. Review dependencies.
10. Keep external APIs optional.

An earlier embedding choice was `BAAI/bge-small-en-v1.5`, but it was reconsidered because a government-facing project may need easier model provenance and approval. Country of origin alone does not prove insecurity, but provenance and supply-chain review matter. Therefore the current prototype preference is `sentence-transformers/all-MiniLM-L6-v2`.

---

## Reranking

Vector retrieval should optimize for recall:

```text
5000 standards
      |
      v
Vector Retrieval
      |
      v
Top 20
```

Then rerank:

```text
Top 20
  |
  v
Cross Encoder
  |
  v
Top 5
```

Initial reranker candidate:

```text
cross-encoder/ms-marco-MiniLM-L6-v2
```

The reranker should also be configurable and locally hosted.

### Bi-encoder vs Cross-encoder

Bi-encoder / embedding model:

```text
Query -> vector
Standard -> vector
Compare vectors
```

Cross-encoder:

```text
Query + Candidate Standard
            |
            v
        Transformer
            |
            v
      Relevance Score
```

Use both.

---

## Vector Search

Use FAISS for the first working prototype.

Indexing:

```text
Standards Dataset
      |
      v
Generate Embeddings
      |
      v
Create FAISS Index
      |
      v
Store Index
```

Query time:

```text
User Query
    |
    v
Embedding
    |
    v
FAISS Search
    |
    v
Top-K Candidates
```

FAISS retrieval order is not the final ranking.

---

## Dataset Status

The real Indian Standards dataset is **not ready yet**.

Do not block implementation while waiting for it.

Use a small mock dataset with clearly fake IDs such as:

```text
IS-DEMO-001
IS-DEMO-002
```

Do not invent realistic-looking IS numbers.

Future real dataset fields should include:

```text
standard_id
title
scope
abstract
keywords
status
revision
publication_date
normative_references
related_standards
supersedes
superseded_by
amendments
source
```

---

## No Model Training Initially

Do not train a model from scratch for the MVP.

Use:

```text
Pretrained Embedding Model
+
FAISS
+
Pretrained Cross Encoder
+
Optional LLM later
```

Fine-tuning should only be considered after labelled examples exist, such as:

```text
procurement query
positive standard
hard negative standard
```

---

## Requirement Extraction

Later the system should extract technical requirements.

Example input:

```text
Transformer shall be oil immersed, three phase,
11 kV/433 V and suitable for outdoor installation.
```

Desired structure:

```json
{
  "product": "transformer",
  "type": "oil immersed",
  "phase": "three phase",
  "input_voltage": "11 kV",
  "output_voltage": "433 V",
  "installation": "outdoor"
}
```

Initial approach:

```text
Regex + Rules
```

Later, optionally use pretrained NER or structured LLM extraction.

Do not train custom NER in the MVP.

---

## Tender Document Processing

Later milestones should support PDFs with PyMuPDF.

Pipeline:

```text
Tender PDF
    |
    v
Extract Text
    |
    v
Clean Text
    |
    v
Chunk Document
    |
    v
Extract Requirements
    |
    v
Semantic Retrieval
```

Preserve:
- page number
- section
- source document

Use OCR only if required for scanned documents.

---

## Chunking

Do not treat an entire long tender as one embedding input.

Later implement:
- section-based chunking
- paragraph-based chunks
- overlapping chunks where necessary
- metadata preservation

Example:

```json
{
  "page": 6,
  "section": "Technical Specifications",
  "text": "...",
  "source": "tender.pdf"
}
```

---

## Standards Relationship Layer

The system should later identify:
- allied standards
- normative references
- cross references
- superseded standards
- replacement standards
- amendments

Initial representation can be JSON or relational tables.

Example:

```json
{
  "IS XXXX": {
    "normative_references": ["IS YYYY"],
    "related": ["IS ZZZZ"],
    "supersedes": ["IS AAAA"]
  }
}
```

Neo4j is not required initially. Prefer PostgreSQL / structured relations unless graph complexity justifies a graph database.

---

## Metadata / Version Validation

Semantic relevance and validity are separate.

A standard can be highly relevant but outdated.

Later check:
- active / withdrawn status
- revision
- publication year
- amendments
- superseded_by
- latest version

Example:

```text
Highly Relevant
+
Superseded
=
Do not recommend as current primary standard
```

---

## RAG / LLM Role

The LLM must not guess which Indian Standards exist.

Correct:

```text
User Query
   |
Retriever
   |
Reranker
   |
Verified Candidate Standards
   |
LLM
   |
Explanation
```

Wrong:

```text
User Query
   |
LLM Memory
   |
Guess IS Number
```

The LLM should generate explanations and structured summaries from retrieved evidence.

Hallucination rules should include:

```text
Use only provided context.

Do not invent:
- IS numbers
- titles
- clauses
- relationships
- amendments
- test requirements

If evidence is insufficient, state:
"Insufficient evidence."
```

External LLM APIs are optional and are not required for the core recommendation engine.

---

## Evaluation

The system must eventually be evaluated using:
- Precision@K
- Recall@K
- MRR
- NDCG@K

Recommended demo metrics:

```text
Recall@5
MRR@5
NDCG@5
```

Useful experiment:

```text
Keyword Search
vs
Embedding Search
vs
Embedding Search + Reranking
```

---

## Current Implementation Priority

Do not implement the complete system immediately.

Current target:

```text
Natural-Language Procurement Query
            |
            v
      NLP Preprocessing
            |
            v
      Sentence Embedding
            |
            v
        FAISS Search
            |
            v
      Candidate Standards
            |
            v
    Cross-Encoder Reranking
            |
            v
       Top Recommendations
            |
            v
        FastAPI Response
```

This must first work using the mock dataset.

---

## Current Milestones

Codex should initially implement only:

### Milestone 0
Environment and folder setup

### Milestone 1
NLP preprocessing

### Milestone 2
Mock standards dataset

### Milestone 3
Embedding model

### Milestone 4
FAISS vector retrieval

### Milestone 5
Cross-encoder reranking

### Milestone 6
Recommendation engine

### Milestone 7
FastAPI endpoint

Do not jump directly to RAG, Neo4j, custom training, or cloud deployment.

---

## Initial API

Endpoint:

```text
POST /recommend
```

Example request:

```json
{
  "text": "Procurement of three phase oil immersed distribution transformers",
  "top_k": 5
}
```

Pipeline:

```text
clean_text
   |
embedding
   |
FAISS
   |
top candidates
   |
reranker
   |
JSON response
```

---

## Expected Folder Structure

```text
ai/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── nlp/
│   │   ├── __init__.py
│   │   ├── preprocess.py
│   │   ├── extractor.py
│   │   ├── embeddings.py
│   │   └── reranker.py
│   ├── retrieval/
│   │   ├── __init__.py
│   │   ├── vector_store.py
│   │   └── search.py
│   ├── recommendation/
│   │   ├── __init__.py
│   │   └── recommender.py
│   ├── documents/
│   │   ├── __init__.py
│   │   ├── pdf_parser.py
│   │   └── chunker.py
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── prompt.py
│   │   └── generator.py
│   ├── graph/
│   │   ├── __init__.py
│   │   └── standards_graph.py
│   └── schemas/
│       ├── __init__.py
│       └── recommendation.py
├── data/
│   ├── raw/
│   ├── processed/
│   └── sample_standards.json
├── models/
├── indexes/
├── scripts/
│   ├── build_index.py
│   ├── test_retrieval.py
│   └── evaluate.py
├── tests/
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
├── AI_PLAN.md
└── CHAT_CONTEXT.md
```

---

## Initial Dependencies

Recommended Python:

```text
Python 3.11
```

Core libraries:

```text
fastapi
uvicorn
sentence-transformers
faiss-cpu
numpy
pandas
pydantic
pymupdf
python-dotenv
```

Do not add LangChain just because RAG may be added later. A custom small pipeline is easier to understand, debug, evaluate, and secure.

---

## Development Principles

Codex should:
1. Keep modules small and testable.
2. Avoid unnecessary abstractions.
3. Keep model names configurable.
4. Keep paths configurable.
5. Never hardcode API keys.
6. Never commit `.env`.
7. Add tests after each component.
8. Keep mock data clearly labelled.
9. Prefer a working vertical slice over implementing every planned feature.
10. Produce readable code that is easy to explain during SIH judging.

Do not initially:
- train an LLM
- train a custom transformer
- train custom NER
- implement Neo4j
- implement Kubernetes
- build agent workflows
- create complex LangChain chains
- rely on external APIs for core search
- create fake realistic IS numbers
- expose raw reranker scores as percentages
- let an LLM invent standard information

---

## Recommended Codex Sequence

When asked to begin implementation:

```text
1. Read README.md
2. Read AI_PLAN.md
3. Read CHAT_CONTEXT.md
4. Inspect the existing ai/ folder
5. Preserve useful existing files
6. Implement Milestone 0
7. Implement Milestone 1
8. Add tests
9. Implement Milestones 2-4
10. Test semantic retrieval
11. Implement reranker
12. Implement RecommendationEngine
13. Implement FastAPI schemas and endpoint
14. Run tests
15. Document how to run locally
```

Do not rewrite the entire repository unless necessary.

---

## Definition of First Success

The first implementation is successful when:

```text
Procurement of three phase oil immersed distribution transformers
```

is sent to:

```text
POST /recommend
```

and the system:

1. cleans the text
2. generates a sentence embedding
3. searches the mock FAISS index
4. retrieves semantically relevant candidates
5. reranks them with a cross encoder
6. returns ranked JSON results

The MVP should work without:
- the real BIS dataset
- RAG
- external LLM APIs
- custom training
- Neo4j

That is the current implementation target.
