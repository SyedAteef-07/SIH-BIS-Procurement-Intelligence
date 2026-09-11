# PostgreSQL and backend/AI integration

Implemented and validated on 2026-09-10. The backend now calls the existing
AI service and resolves its ranked codes against PostgreSQL metadata. The AI
models, retrieval/reranking code, enrichment default and rejection threshold
configuration were not changed.

## Database and API

Alembic revision **0001_standards_metadata** creates `standards`,
`standard_keywords`, and `standard_relationships`. Alembic also creates its
version table. The standard code is unique/indexed; relationships have foreign
keys and uniqueness constraints. Mock records are constrained to remain
unverified. SQLAlchemy 2.x sessions use `pool_pre_ping=True`.

`POST /api/analyze` validates input, calls configurable AI `/recommend`, fetches
all returned standard codes and keywords in one query, then adapts database
metadata in AI order. The adapter preserves evidence, source score types,
raw scores, warnings and match state without treating scores as probabilities.
Missing codes produce an explicit incomplete response; no invented metadata is
used to fill them. The original upstream match state is retained separately
when incomplete metadata makes the overall result unassessed.

The seed reads the existing shared AI JSON fixture directly and updates by
`standard_code`; repeated runs retain 40 unique demo records and their internal
IDs. Source text describing a fictional fixture is not treated as an official
source URL. No BIS IDs, certifications or relationships are fabricated.

Environment configuration added/updated:

- `DATABASE_URL`: PostgreSQL/psycopg connection URL, no application credential default.
- `AI_SERVICE_URL`: defaults to `http://127.0.0.1:8001`.
- `AI_TIMEOUT_SECONDS`: finite positive timeout, default 30 seconds.
- `VITE_API_BASE_URL`: frontend backend URL, typically `http://localhost:8000`.
  The previous `VITE_API_URL` remains a compatibility fallback in the frontend.
- `POSTGRES_PORT`: optional Compose host port override, default 5432.

AI failures return 503/504, unexpected or malformed AI responses return 502,
and input rejection returns 422. Database failures return 503. There is no
automatic heuristic fallback. `/health` remains liveness; `/ready` checks the
migrated database table and AI readiness.

## Validation

- **29 backend tests passed**, including a real PostgreSQL 16 smoke test.
  The existing catalog API tests were adapted for the explicitly requested new
  fictional metadata/service contract; all backend tests pass.
- **142 existing AI tests passed**, unchanged.
- **3 frontend tests passed**: backend-only HTTP contract, visible service
  failures, and categorical relevance labels independent of raw scores.
- **Frontend production build passed** using the existing lockfile.
- `git diff --check` and `docker compose config --quiet` passed.

Isolated SQLite tests cover repository search/pagination, a one-query bulk
lookup including keywords, mock constraints, relationship foreign keys,
idempotency, Alembic upgrade/repeated upgrade/schema drift/downgrade, HTTP
boundary validation, rank preservation, absent IDs, no-match and outage states.
Backend tests never load/download AI models.

The PostgreSQL smoke test used a separate container on localhost:15432, applied
the actual migration, checked schema/ORM agreement, seeded twice and exercised
the HTTP adapter and `/api/analyze` with real PostgreSQL metadata and a mocked
AI HTTP response. The existing database on 5432 was left untouched. The
temporary test container was removed afterward. This is not a live-model
browser-to-database end-to-end test; AI behavior is covered by its existing suite.
Two existing Starlette/httpx and AnyIO deprecation warnings remain in Python
test output.

Commands used, from each component directory:

```powershell
# backend/; TEST_DATABASE_URL pointed at the isolated PostgreSQL test DB
.venv/Scripts/python -m pytest -q
# ai/
.venv/Scripts/python -m pytest -q
# frontend/
npm test
npm run build
```

Exact installation and local startup commands, in order PostgreSQL → migration
→ seed → AI :8001 → backend :8000 → frontend :5173, are in
[the root README](../README.md#local-setup-windows-powershell). The repeatable
isolated PostgreSQL test commands are in [backend/README.md](../backend/README.md#tests).

## Compatibility decisions

- The old SQL bootstrap uses a different schema. Compose now uses a new
  `bis_metadata_data` volume and `bis_procurement` database, without mounting
  the old SQL file. Existing volumes are preserved. Use a fresh database for
  the initial revision; migrating existing legacy catalog contents is separate work.
- The request maximum is now 2,000 characters to match AI's existing contract;
  oversized text is rejected rather than silently truncated.
- `edition` is nullable and aliases `revision`. The old normalized `score`
  was removed in favor of named uncalibrated scores and a categorical label.
  Consumers relying on the old percentage/score field must update.
- Demo IDs replace the legacy catalog's real-looking identifiers in API results.
  Legacy catalog/service/graph modules are retained but are not called by routes.
- Related standards, gap analysis and certification output lists remain empty;
  these checks are explicitly described as not performed by this integration.
- Frontend warnings and demo/unverified state are visible. The layout is retained.
  PDF processing is still unsupported; enter requirement text.
- Both services have an `app` package; use their separate directories and
  virtual environments to avoid importing the wrong application.

## File inventory

Created:

- `backend/.env.example`, `backend/pytest.ini`, `backend/alembic.ini`.
- `backend/alembic/env.py`, `script.py.mako`,
  `versions/0001_standards_metadata.py`.
- `backend/app/database/__init__.py`, `models.py`, `session.py`,
  `repositories/__init__.py`, `repositories/standards.py`.
- `backend/app/scripts/seed_standards.py`.
- `backend/app/services/ai_client.py`, `response_adapter.py`.
- `backend/tests/conftest.py`, `test_ai_client.py`, `test_database.py`,
  `test_integration.py`, `test_postgres.py`.
- `frontend/.env.example`, `frontend/src/api.js`, `frontend/src/relevance.js`,
  `frontend/tests/integration.test.js`, and this report.

Modified:

- Root `.env.example`, `README.md`, `README_AI.md`, `docker-compose.yml`.
- `ai/README.md` (ports/integration documentation only).
- `backend/README.md`, `requirements.txt`, `app/config.py`, `app/main.py`,
  `app/schemas.py`, `tests/test_api.py`.
- `database/schema.sql` (legacy-only notice).
- `frontend/package.json`, `src/InputPage.jsx`, `src/ResultsPage.jsx`.

No RAG, LLM APIs, PDF/OCR, Neo4j integration changes, scraping, real BIS
ingestion, pgvector, model training or calibration changes were implemented.
