# BIS Procurement Intelligence

AI-assisted procurement specification review with a React two-page interface,
a FastAPI backend, a separate FastAPI AI service, and PostgreSQL metadata.

## Implemented features

- Text procurement input and PDF text extraction with PyMuPDF.
- Deterministic requirement extraction with source evidence.
- BGE embeddings, FAISS semantic retrieval, BM25 lexical retrieval, RRF fusion,
  and CrossEncoder reranking.
- PostgreSQL enrichment of AI-ranked standard identifiers, preserving ranking.
- Data-driven requirement coverage / gap analysis using stored requirement keys.
- Related-standard metadata and structured certification metadata.
- Results tabs, evidence, extracted requirements, and downloadable reports.
- Optional multilingual retrieval; English is the default.

## Architecture and data

React (:5173) calls backend (:8000), which calls AI (:8001) and enriches the
ranked results with PostgreSQL metadata (:5432). FAISS remains the semantic
index. Retrieval, reranking, multilingual behavior, and Docker architecture
are unchanged. There is no LLM, RAG, or replacement vector database in this flow.

`ai/data/sample_standards.json` contains 40 development/prototype standards,
including requirement checklists, 15 typed relationships and five certification
placeholders. These are fictional IS-DEMO identifiers, not official or current
BIS publications. Official BIS ingestion, current revision verification, and
verified QCO applicability are not complete. Certification is not legally
verified. Human review against official BIS sources is required before use.

Requirement Coverage counts mentioned topics divided by stored topics. It is
not a compliance percentage or confidence score, and never uses retrieval or
reranker scores. Each requirement key matches an extractor evidence field.
Negated-only evidence needs review; absent evidence is missing. Standards with
no requirement metadata are not assessed. English topic extraction currently
supports gap checks; multilingual retrieval does not establish topic coverage.

The backend supports `POST /api/analyze` and `POST /api/analyze-pdf`.
Text is limited to 2,000 characters. PDFs may be up to 10 MB; only the first
2,000 extracted characters are analyzed, with an explicit scope notice for
longer documents. Scanned PDFs require OCR, which is not implemented.
AI or database failures return errors without a silent recommendation fallback.

## Local setup (Windows PowerShell)

From the repository root, reuse existing virtual environments if available:

```powershell
py -3.12 -m venv backend/.venv
backend/.venv/Scripts/python -m pip install -r backend/requirements.txt
py -3.12 -m venv ai/.venv
ai/.venv/Scripts/python -m pip install -r ai/requirements-dev.txt
cd frontend
npm ci
cd ..
```

Copy `backend/.env.example` and `frontend/.env.example` to their respective
`.env` files only if those files do not already exist. Configure `DATABASE_URL`,
`AI_SERVICE_URL` and `VITE_API_BASE_URL`. Start Docker Desktop, then:

```powershell
docker compose up -d postgres
cd backend
.venv/Scripts/alembic upgrade head
.venv/Scripts/python -m app.scripts.seed_standards
cd ..
```

The seed is idempotent and synchronizes requirements, relationships and
certifications from JSON for included standards. Rerun it after fixture updates.
No new migration is needed for checklist-key or seed-data changes.

Start each service in its own terminal from the repository root:

```powershell
cd ai
.venv/Scripts/python -m uvicorn app.main:app --reload --port 8001
```

```powershell
cd backend
.venv/Scripts/python -m uvicorn app.main:app --reload --port 8000
```

```powershell
cd frontend
npm run dev -- --port 5173
```

Open http://localhost:5173. Backend API docs: http://127.0.0.1:8000/docs.
Initial AI model loading can take time. Restart AI and backend after updates.
The Python services use separate `app` packages; run them from their own folders.

## Validation and further details

```powershell
cd backend
.venv/Scripts/python -m pytest -v
cd ../ai
.venv/Scripts/python -m pytest -v
cd ../frontend
npm test
npm run build
```

Backend tests use isolated SQLite metadata and a mocked AI service. Topic
contract tests run the real lightweight extractor in a separate process without
loading embedding models. An optional PostgreSQL smoke test is available.
See [backend setup and database compatibility](backend/README.md) and
[AI configuration and optional multilingual setup](ai/README.md).
