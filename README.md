# BIS Procurement Intelligence

AI-powered procurement intelligence system for government tender specification analysis.

## Problem

Government procurement officers need to identify the correct Indian Standards
for products and services mentioned in procurement tenders. This process can
require manually searching standards, related references, revisions,
amendments, certification requirements, and checking whether tender
specifications contain important missing requirements.

## Solution

The current implementation uses local semantic/lexical retrieval and
CrossEncoder reranking to recommend fictional development standards.
PostgreSQL stores structured metadata. RAG, official BIS ingestion, version
verification, document parsing and gap analysis remain future work.

## Roadmap (not all implemented)

- Tender/Product requirement understanding
- Relevant BIS Standard identification
- Semantic search
- Related and normative standard discovery
- Standard version checking
- Amendment detection
- Certification/compliance information
- Tender requirement vs standard comparison
- Tender gap analysis
- Explainable procurement report

## Architecture

React :5173 → Backend :8000 → AI service :8001 → ranked standard IDs
→ PostgreSQL metadata :5432 → backend response adapter → React.

PostgreSQL stores standards metadata, keywords and relationships. FAISS stores
the semantic index; BM25 supplies lexical candidates; RRF fuses retrieval ranks;
CrossEncoder orders final results. The backend orchestrates these services.
The AI service retains deterministic NLP, BGE and the existing retrieval code.
No pgvector or replacement vector database is used.

## Project Status

The frontend now calls the backend only. `/api/analyze` calls AI `/recommend`,
fetches metadata for returned codes in one SQL query and preserves AI order.
All 40 shared `IS-DEMO-*` records remain fictional, `is_mock=true` and
`status=unverified`. Scores are uncalibrated relevance values, never confidence
percentages. Enrichment remains off by default; the AI rejection threshold
behavior is unchanged. Missing database records are explicitly reported as
incomplete results. AI/database outages return errors with no silent fallback.

## Local setup (Windows PowerShell)

Run these setup commands from the repository root. If an environment already
exists, reuse it. Start Docker Desktop first.

```powershell
py -3.12 -m venv backend/.venv
backend/.venv/Scripts/python -m pip install -r backend/requirements.txt
py -3.12 -m venv ai/.venv
ai/.venv/Scripts/python -m pip install -r ai/requirements-dev.txt
Copy-Item backend/.env.example backend/.env
Copy-Item frontend/.env.example frontend/.env
cd frontend
npm ci
cd ..
```

Copy examples only when the destination `.env` does not already exist; otherwise
merge settings. The sample database password is for local development only.
Backend environment variables: `DATABASE_URL`, `AI_SERVICE_URL`, and finite
`AI_TIMEOUT_SECONDS` (default 30). Frontend: `VITE_API_BASE_URL`. Backend loads
root/backend `.env` files; process environment takes precedence. Vite reads its
own `frontend/.env`. Restart services after configuration changes.

Start in this order:

1. PostgreSQL, from the root:

   ```powershell
   docker compose up -d postgres
   docker compose ps postgres
   ```

2. Apply migrations:

   ```powershell
   cd backend
   .venv/Scripts/alembic upgrade head
   ```

3. Seed the shared fictional AI fixture (safe to repeat):

   ```powershell
   .venv/Scripts/python -m app.scripts.seed_standards
   cd ..
   ```

4. Start AI in a new root terminal; initial model loading may take time:

   ```powershell
   cd ai
   .venv/Scripts/python -m uvicorn app.main:app --reload --port 8001
   ```

5. Start the backend in another root terminal:

   ```powershell
   cd backend
   .venv/Scripts/python -m uvicorn app.main:app --reload --port 8000
   ```

6. Start the frontend in another root terminal:

   ```powershell
   cd frontend
   npm run dev -- --port 5173
   ```

Open http://localhost:5173 or backend docs at http://127.0.0.1:8000/docs.
AI docs are at http://127.0.0.1:8001/docs. The two Python services both use an
`app` package, so run them from separate directories/environments.

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/ready
Invoke-RestMethod http://127.0.0.1:8000/api/analyze -Method Post -ContentType 'application/json' -Body '{"description":"three phase oil immersed distribution transformer","limit":5}'
```

The request limit is 2,000 characters, aligned with the AI contract. Long
documents must not be silently truncated; PDF upload/parsing is not implemented.

## Existing database compatibility

The old `database/schema.sql` defines a different, unmigrated catalog and is
retained only as a legacy reference. Compose now uses a separate
`bis_metadata_data` volume and database `bis_procurement`; it no longer runs
that SQL file. Existing `postgres_data` is not deleted. Use a fresh database
for revision `0001_standards_metadata`; do not stamp the legacy schema as this
revision. Migrating legacy catalog contents is outside this demo phase.

If another database already occupies port 5432, set `$env:POSTGRES_PORT='5433'`
before `docker compose up -d postgres`, then change `DATABASE_URL` to port 5433.
Do not stop or delete another database just to run this project.

## Tests and details

```powershell
cd backend
.venv/Scripts/python -m pytest -v
cd ../ai
.venv/Scripts/python -m pytest -v
cd ../frontend
npm test
npm run build
```

Backend unit tests mock the AI HTTP boundary and use isolated SQLite databases;
they never import/download AI models. An optional PostgreSQL smoke test is
documented in [backend/README.md](backend/README.md). See also
[AI documentation](ai/README.md) and the
[integration report](docs/POSTGRES_INTEGRATION_REPORT.md) for files, contracts,
validation results and compatibility changes.
