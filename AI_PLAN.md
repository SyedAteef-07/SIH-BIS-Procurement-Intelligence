# AI Implementation Plan

## 1. Objective

Build the AI layer for an Indian Standards recommendation engine used in procurement workflows.

The system must accept:

- Product descriptions
- Technical specifications
- Tender text
- Eventually PDF / DOCX tender documents

It should return:

- Most relevant Indian Standards
- Ranked relevance
- Explanation of relevance
- Evidence from retrieved standard data
- Allied standards
- Normative references
- Cross-referenced standards
- Standard status / revision information when available

---

## 2. Guiding Architecture

The system should be implemented as a multi-stage retrieval pipeline instead of asking an LLM to guess standards directly.

```text
INPUT
  |
  v
Tender / Product Description
  |
  v
Document Parsing
  |
  v
NLP Preprocessing
  |
  v
Requirement Extraction
  |
  v
Semantic Query Representation
  |
  v
Embedding Retrieval
  |
  v
Top-K Candidate Standards
  |
  v
Cross-Encoder Reranking
  |
  v
Top-N Standards
  |
  +-------------------+
  |                   |
  v                   v
Relationship Graph    Metadata / Version Validation
  |                   |
  +---------+---------+
            |
            v
       RAG / LLM
            |
            v
Evidence-backed Recommendation
```

---

# 3. Implementation Order

Do not implement all components simultaneously.

Use the milestones below.

---

# Milestone 0 — Environment and Project Setup

## Goal

Prepare the `ai` folder for development.

## Tasks

Create:

```text
ai/
├── app/
├── data/
├── indexes/
├── scripts/
├── tests/
├── requirements.txt
├── README.md
└── AI_PLAN.md
```

Recommended Python:

```text
Python 3.11
```

Create environment:

```bash
python -m venv .venv
```

Windows activation:

```bash
.venv\Scripts\activate
```

Install initial dependencies:

```bash
pip install fastapi uvicorn sentence-transformers faiss-cpu numpy pandas pydantic pymupdf python-dotenv
```

Expected `requirements.txt` categories:

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

## Acceptance Criteria

- Python virtual environment activates successfully.
- `python -c "import sentence_transformers"` works.
- `python -c "import faiss"` works.
- `python -c "import fastapi"` works.

---

# Milestone 1 — NLP Preprocessing

## Goal

Create a minimal preprocessing layer for procurement text.

File:

```text
app/nlp/preprocess.py
```

Responsibilities:

- Normalize whitespace
- Normalize line breaks
- Remove obvious extraction noise
- Preserve meaningful punctuation, numbers, units, negations and technical terminology

Avoid traditional aggressive preprocessing such as:

- stemming every word
- removing all stopwords
- deleting numbers
- deleting measurement units

Reason:

Transformer embedding models work better with natural text.

For example:

```text
not suitable for indoor use
```

must never be transformed into:

```text
suitable indoor use
```

## Function

Suggested API:

```python
def clean_text(text: str) -> str:
    ...
```

## Tests

Create examples containing:

- voltage
- dimensions
- quantities
- units
- `not`
- symbols
- multiline tender text

---

# Milestone 2 — Mock Standards Dataset

## Goal

Build the system before the final BIS / Indian Standards dataset is ready.

Create:

```text
data/sample_standards.json
```

Suggested schema:

```json
[
  {
    "id": "IS-DEMO-001",
    "title": "Distribution Transformers",
    "scope": "Requirements for oil immersed three phase distribution transformers.",
    "keywords": [
      "transformer",
      "oil immersed",
      "three phase"
    ]
  }
]
```

Use clearly fake IDs such as `IS-DEMO-001`.

Do not use invented IDs that could be confused with real standards.

## Future Production Schema

The real dataset should eventually support:

```json
{
  "standard_id": "IS XXXX",
  "title": "...",
  "scope": "...",
  "abstract": "...",
  "keywords": [],
  "product_categories": [],
  "technical_requirements": [],
  "normative_references": [],
  "related_standards": [],
  "supersedes": [],
  "superseded_by": [],
  "amendments": [],
  "publication_date": null,
  "revision": null,
  "status": null,
  "source": null
}
```

---

# Milestone 3 — Embedding Model

## Goal

Convert procurement text and standards into semantic vectors.

File:

```text
app/nlp/embeddings.py
```

Initial model:

```text
BAAI/bge-small-en-v1.5
```

Suggested class:

```python
from sentence_transformers import SentenceTransformer


class EmbeddingModel:
    def __init__(self, model_name="BAAI/bge-small-en-v1.5"):
        self.model = SentenceTransformer(model_name)

    def encode(self, texts):
        return self.model.encode(
            texts,
            normalize_embeddings=True
        )
```

## Document Representation

Each standard should be embedded using meaningful text.

Example:

```text
Standard: IS-DEMO-001
Title: Distribution Transformers
Scope: Requirements for oil immersed three phase distribution transformers.
Keywords: transformer, electrical distribution, oil immersed
```

Do not embed only the standard title.

## Acceptance Criteria

Given:

```text
three phase oil immersed distribution transformer
```

the transformer mock standard should score higher than unrelated cement or lighting standards.

---

# Milestone 4 — FAISS Vector Retrieval

## Goal

Retrieve a broad candidate set using semantic similarity.

File:

```text
app/retrieval/vector_store.py
```

Initial FAISS index:

```python
faiss.IndexFlatIP(dimension)
```

Because embeddings are normalized, inner-product similarity behaves like cosine similarity.

Suggested API:

```python
class VectorStore:
    def add(self, embeddings, documents):
        ...

    def search(self, query_embedding, top_k=20):
        ...
```

## Retrieval Philosophy

The retriever optimizes for **recall**, not perfect ranking.

Example:

```text
5,000 standards
      |
      v
FAISS
      |
      v
Top 20-50 candidates
```

Do not expect FAISS alone to determine the final ordering.

## Persistence

During the first prototype, in-memory indexing is acceptable.

Later:

- Save FAISS index under `indexes/`
- Save document metadata alongside it
- Rebuild only when dataset changes

---

# Milestone 5 — Cross-Encoder Reranking

## Goal

Improve ranking accuracy on the candidates returned by vector search.

File:

```text
app/nlp/reranker.py
```

Initial model:

```text
cross-encoder/ms-marco-MiniLM-L-6-v2
```

The reranker receives pairs:

```text
(procurement query, candidate standard)
```

Example:

```python
pairs = [
    (query, candidate_1_text),
    (query, candidate_2_text),
]
```

Then:

```python
scores = model.predict(pairs)
```

## Pipeline

```text
Query
 |
 v
Embedding Search
 |
 v
Top 20
 |
 v
Cross Encoder
 |
 v
Top 5
```

## Why Reranking Matters

Embedding retrieval compares vectors independently.

A cross encoder reads the query and candidate together, allowing deeper relevance scoring.

## Acceptance Criteria

Relevant standards should move upward even if lexical overlap is weak.

---

# Milestone 6 — Recommendation Engine

## Goal

Combine preprocessing, embeddings, retrieval and reranking.

File:

```text
app/recommendation/recommender.py
```

Suggested API:

```python
class RecommendationEngine:
    def recommend(
        self,
        query: str,
        retrieval_k: int = 20,
        final_k: int = 5
    ):
        ...
```

Process:

```text
clean query
   |
embed query
   |
FAISS search
   |
candidate standards
   |
cross-encoder reranking
   |
ranked standards
```

Expected internal result:

```json
{
  "standard": {
    "id": "IS-DEMO-001",
    "title": "Distribution Transformers"
  },
  "retrieval_score": 0.82,
  "reranker_score": 7.91
}
```

Do not convert reranker raw scores directly into percentages unless they have been calibrated.

---

# Milestone 7 — FastAPI Integration

## Goal

Expose the recommendation engine through an API.

File:

```text
app/main.py
```

Recommended endpoints:

```text
GET /
POST /recommend
```

Prefer a Pydantic request body instead of a query-string-only production endpoint.

Example request:

```json
{
  "text": "Procurement of three phase oil immersed distribution transformers",
  "top_k": 5
}
```

Example response:

```json
{
  "query": "...",
  "recommendations": [...]
}
```

Use:

```bash
uvicorn app.main:app --reload
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

---

# Milestone 8 — Tender Document Parsing

## Goal

Support procurement documents instead of only plain text.

Files:

```text
app/documents/pdf_parser.py
app/documents/chunker.py
```

Use:

```text
PyMuPDF
```

Responsibilities:

- Extract text
- Identify pages
- Remove repeated headers / footers where possible
- Preserve table-like text when possible
- Chunk long documents

Do not send an entire large tender directly to the retrieval model.

Suggested chunking strategy:

- Use sections / paragraphs when identifiable
- Otherwise use token-aware overlapping chunks
- Preserve page or section metadata

Possible chunk object:

```json
{
  "page": 4,
  "section": "Technical Specifications",
  "text": "...",
  "source": "tender.pdf"
}
```

---

# Milestone 9 — NLP Requirement Extraction

## Goal

Identify important procurement attributes before retrieval.

File:

```text
app/nlp/extractor.py
```

Target entities / fields:

```text
product
product type
material
application
voltage
power rating
dimensions
environment
installation type
testing requirements
performance requirements
safety requirements
industry / domain
```

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

## Initial Approach

Do not train NER from scratch initially.

Use a combination of:

- regex for obvious technical quantities
- lightweight rules
- optional pretrained NLP models
- later an LLM with structured output if needed

The extractor should **improve retrieval**, not replace semantic search.

---

# Milestone 10 — Query Construction

## Goal

Create a better retrieval query from raw tender text.

Possible query:

```text
Product: distribution transformer
Type: oil immersed
Phase: three phase
Voltage: 11 kV / 433 V
Installation: outdoor
Requirements: electrical safety, performance testing
```

Use both:

1. Raw procurement text
2. Structured extracted requirements

Possible retrieval strategy:

```text
embedding(raw text)
+
embedding(structured query)
```

Experiment later with fusion.

---

# Milestone 11 — Standards Relationship Layer

## Goal

Discover:

- normative references
- cross-referenced standards
- allied standards
- superseding / superseded standards
- amendments

File:

```text
app/graph/standards_graph.py
```

Initial representation can be a dictionary or PostgreSQL relation table.

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

Do not introduce Neo4j until the relationship data becomes large or graph traversal becomes sufficiently complex.

The graph should augment retrieved standards rather than replace semantic retrieval.

---

# Milestone 12 — Metadata and Version Validation

## Goal

Prevent recommendations of outdated standards.

Validation should check, when data is available:

```text
status
revision
publication year
amendments
superseded_by
withdrawal
latest version
```

Semantic relevance and validity are separate concepts.

Example:

```text
High semantic relevance
        +
Superseded standard
        =
Do not recommend as current primary standard
```

Instead show:

```text
This standard appears relevant but has been superseded by ...
```

---

# Milestone 13 — RAG / LLM Explanations

## Goal

Generate grounded, readable recommendations.

Files:

```text
app/rag/prompt.py
app/rag/generator.py
```

Important rule:

The LLM must **not search its memory for Indian Standard numbers**.

It receives only:

- user requirement
- retrieved standards
- metadata
- supporting text
- relationship data

Prompt rules should include:

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

Desired output:

```json
{
  "standard_id": "IS XXXX",
  "title": "...",
  "reason": "...",
  "supporting_evidence": ["..."],
  "related_standards": []
}
```

---

# Milestone 14 — Evaluation

## Goal

Measure whether recommendations are genuinely useful.

Create:

```text
scripts/evaluate.py
```

Later build a labelled evaluation dataset:

```text
procurement query
correct primary standards
acceptable related standards
irrelevant standards
```

Metrics:

### Recall@K

Was a correct standard present in the first K results?

### Precision@K

How many returned standards were relevant?

### MRR

How high was the first correct result?

### NDCG@K

Useful when standards have graded relevance.

Recommended demo metrics:

```text
Recall@5
MRR@5
NDCG@5
```

Also compare:

```text
Keyword search baseline
vs
Embedding retrieval
vs
Embedding + reranking
```

This gives strong evidence that the AI pipeline improves search quality.

---

# 4. Dataset Strategy

The final dataset will be added later.

Do not block implementation while waiting for it.

## Required fields eventually

At minimum:

```text
standard_id
title
scope
description / abstract
keywords
status
revision
```

Highly valuable:

```text
normative references
related standards
cross references
amendments
supersedes
superseded_by
product categories
technical requirements
source metadata
```

## Important

Do not scrape or redistribute standards content without checking licensing / access conditions.

Store only data the project is legally allowed to use.

---

# 5. Model Training Strategy

## Version 1

No custom model training.

Use pretrained:

```text
Embedding model
+
FAISS
+
Cross Encoder
+
Optional LLM
```

## Later Fine-Tuning

Fine-tune only after collecting labelled pairs such as:

```text
Query
Positive Standard
Hard Negative Standard
```

Possible future work:

- embedding fine-tuning
- reranker fine-tuning
- domain-specific NER
- score calibration

Fine-tuning is an optimization phase, not a prerequisite.

---

# 6. Recommended Code Organization

```text
ai/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   │
│   ├── nlp/
│   │   ├── __init__.py
│   │   ├── preprocess.py
│   │   ├── extractor.py
│   │   ├── embeddings.py
│   │   └── reranker.py
│   │
│   ├── retrieval/
│   │   ├── __init__.py
│   │   ├── vector_store.py
│   │   └── search.py
│   │
│   ├── recommendation/
│   │   ├── __init__.py
│   │   └── recommender.py
│   │
│   ├── documents/
│   │   ├── __init__.py
│   │   ├── pdf_parser.py
│   │   └── chunker.py
│   │
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── prompt.py
│   │   └── generator.py
│   │
│   ├── graph/
│   │   ├── __init__.py
│   │   └── standards_graph.py
│   │
│   └── schemas/
│       ├── __init__.py
│       └── recommendation.py
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── sample_standards.json
│
├── models/
├── indexes/
├── scripts/
│   ├── build_index.py
│   ├── test_retrieval.py
│   └── evaluate.py
│
├── tests/
│   ├── test_preprocess.py
│   ├── test_retrieval.py
│   └── test_recommender.py
│
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
└── AI_PLAN.md
```

---

# 7. Suggested `.gitignore`

```text
.venv/
__pycache__/
*.pyc
.env
indexes/*
!indexes/.gitkeep
models/*
!models/README.md
.pytest_cache/
.vscode/
.idea/
```

Do not commit API keys.

---

# 8. Configuration

Use:

```text
app/config.py
```

for central settings such as:

```text
embedding model name
reranker model name
retrieval_k
final_k
dataset path
index path
LLM provider
```

Load secrets from `.env`.

Example `.env.example`:

```text
LLM_API_KEY=
LLM_MODEL=
```

Do not hardcode secrets in source code.

---

# 9. Codex Implementation Instructions

When implementing with Codex, proceed milestone by milestone.

Do not ask Codex to generate the entire project in one shot.

Recommended sequence:

```text
1. Create folder structure
2. Add requirements.txt
3. Implement preprocess.py + tests
4. Add mock dataset
5. Implement embeddings.py
6. Implement vector_store.py
7. Implement build_index.py
8. Add retrieval test
9. Implement reranker.py
10. Implement recommender.py
11. Add FastAPI schemas
12. Implement /recommend
13. Add integration tests
14. Implement PDF parsing
15. Add requirement extractor
16. Add graph relationships
17. Add RAG
18. Add evaluation
```

After each milestone:

```bash
pytest
```

and manually test the relevant script or endpoint.

---

# 10. Definition of the MVP

The AI MVP is complete when:

1. User submits a natural-language procurement requirement.
2. The system preprocesses it.
3. A pretrained embedding model encodes the query.
4. FAISS retrieves candidate standards.
5. A cross encoder reranks candidates.
6. The API returns the top recommendations.
7. Retrieval is demonstrably semantic rather than keyword-only.
8. The architecture can later accept the real standards dataset without rewriting the core pipeline.

The MVP does **not** require:

- model training
- knowledge graph database
- RAG
- OCR
- real BIS dataset
- production cloud deployment

Those are later milestones.

---

# 11. Definition of the Final AI Prototype

The full prototype should support:

```text
Tender PDF / Text
       |
       v
NLP Requirement Understanding
       |
       v
Semantic Retrieval
       |
       v
Cross-Encoder Reranking
       |
       v
Relationship Discovery
       |
       v
Version / Metadata Validation
       |
       v
RAG Explanation
       |
       v
Human-readable evidence-backed recommendations
```

Expected recommendation fields:

```text
standard number
title
relevance
reason
evidence
related / normative standards
status
revision
source
```

The final decision must remain with the procurement official.

---

# 12. Non-Negotiable Reliability Rules

1. Never let the LLM invent a standard number.
2. Never present an unverified standard as current.
3. Keep semantic relevance separate from standard validity.
4. Preserve evidence used for every recommendation.
5. Keep retrieval deterministic enough to evaluate.
6. Store source metadata where possible.
7. Use human review as the final decision point.
8. Clearly distinguish primary recommendations from allied standards.
9. Clearly distinguish real dataset entries from mock development data.
10. Do not label raw model scores as probabilities without calibration.

---

# 13. Immediate Next Task for Codex

Start only with **Milestones 0–7**.

The first deliverable should be a working local API:

```text
POST /recommend
```

Input:

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
response
```

Use the mock standards dataset until the real dataset is available.

Once this first vertical slice is stable, continue with document parsing and requirement extraction.
