# AI-Powered Indian Standards Recommendation Engine

## Project Overview

This project builds an AI-powered recommendation engine for procurement portals. Its goal is to help procurement officials identify the most relevant Indian Standards (IS) for a product description, technical specification, or tender document.

The system should not rely only on keyword matching. It should understand the meaning of procurement requirements, retrieve the most relevant standards, rerank them, identify allied / normative / cross-referenced standards, validate metadata and versions, and generate evidence-backed explanations.

## Core Problem

Government departments, PSEs, procurement agencies, and private organizations frequently prepare technical specifications that must reference appropriate Indian Standards.

The main challenges are:

- Large number of Indian Standards
- Overlapping scopes
- Different terminology between tenders and standards
- Frequent revisions and superseded standards
- Related / normative / cross-referenced standards
- Risk of incomplete or outdated specifications

## Proposed AI Pipeline

```text
Product Description / Tender Document
                |
                v
        Document Parsing
                |
                v
        NLP Preprocessing
                |
                v
 Information / Requirement Extraction
                |
                v
      Query Representation
                |
                v
      Sentence Embeddings
                |
                v
       Vector Retrieval
              FAISS
                |
          Top-K Candidates
                |
                v
        Cross-Encoder Reranker
                |
           Top-N Standards
                |
                v
    Standards Relationship Layer
                |
                v
        RAG / LLM Explanation
                |
                v
 Evidence-backed Recommendations
```

## AI Techniques Used

The system combines:

- Natural Language Processing
- Semantic embeddings
- Vector similarity search
- Information retrieval
- Cross-encoder reranking
- Information extraction
- Knowledge graph / relationship traversal
- Retrieval-Augmented Generation (RAG)
- Metadata and version validation
- Evaluation using ranking metrics

## Initial Technology Stack

| Component | Technology |
|---|---|
| Language | Python |
| API | FastAPI |
| Embeddings | Sentence Transformers |
| Initial embedding model | `BAAI/bge-small-en-v1.5` |
| Vector search | FAISS |
| Reranking | Sentence Transformers CrossEncoder |
| Initial reranker | `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| PDF parsing | PyMuPDF |
| Data handling | pandas, NumPy |
| API schemas | Pydantic |
| Database later | PostgreSQL |
| Knowledge graph later | PostgreSQL relations initially, Neo4j if needed |
| LLM later | OpenAI / Gemini / suitable local model |
| Deployment later | Docker + Cloud Run / AWS |

## Important Design Decision

Do **not** train a large model from scratch for the first version.

The initial system should use pretrained embedding and reranking models. Fine-tuning should only be considered after a labelled dataset of procurement queries and correct standards is available.

## Repository AI Folder

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
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
└── AI_PLAN.md
```

## First Working Milestone

The first milestone should work without the final Indian Standards dataset.

Use a small mock dataset and implement:

```text
User Query
    |
    v
NLP Preprocessing
    |
    v
Embedding Model
    |
    v
FAISS Retrieval
    |
    v
Cross-Encoder Reranking
    |
    v
Ranked Standards
```

Once this works reliably, replace the mock standards with real structured data.

## Environment Setup

Recommended Python version:

```text
Python 3.11
```

Create and activate a virtual environment.

### Windows

```bash
cd ai
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
```

Install the initial dependencies:

```bash
pip install fastapi uvicorn sentence-transformers faiss-cpu numpy pandas pydantic pymupdf python-dotenv
```

Then save:

```bash
pip freeze > requirements.txt
```

## Running the API

After `app/main.py` is implemented:

```bash
uvicorn app.main:app --reload --port 8001
```

Open:

```text
http://127.0.0.1:8001/docs
```

## Development Principles

- Keep NLP preprocessing conservative.
- Do not aggressively remove stopwords when using transformer embeddings.
- Do not let an LLM invent IS numbers or titles.
- Retrieval should happen before generation.
- Reranking should happen after broad semantic retrieval.
- Recommendations should include evidence.
- Version / status validation should be handled separately from semantic relevance.
- Keep components modular so models and databases can be replaced later.
- Build the retrieval engine before adding RAG.

## Planned Output

A recommendation should eventually contain:

```json
{
  "standard_id": "IS XXXX",
  "title": "Example standard",
  "relevance_score": 0.94,
  "reason": "Relevant because ...",
  "supporting_evidence": ["..."],
  "related_standards": ["IS YYYY"],
  "status": "active",
  "revision": "latest known version"
}
```

## Current Status

The AI architecture has been defined.

The immediate implementation target is:

1. Project setup
2. NLP preprocessing
3. Sentence embeddings
4. FAISS indexing
5. Semantic retrieval
6. Cross-encoder reranking
7. FastAPI endpoint

See `AI_PLAN.md` for the full implementation roadmap.
