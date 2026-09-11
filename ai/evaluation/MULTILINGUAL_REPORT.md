# Optional multilingual retrieval demo

Implemented and manually exercised on 2026-09-10. English remains the default
with BGE-small, FAISS, BM25/RRF and the existing CrossEncoder. BGE-M3 is an
explicitly enabled second mode. It is an experimental hackathon demo and has
not been production-calibrated.

## Configuration and model loading

- `EMBEDDING_MODE=english` remains the default; `multilingual` selects
  `BAAI/bge-m3`.
- `MULTILINGUAL_ENABLED=false` remains the default. Set it to `true` to preload
  M3 alongside the English engine. Models load during startup, not on requests.
- Existing English `EMBEDDING_MODEL` overrides remain supported. Multilingual
  mode always chooses M3, including when an old `.env` names BGE-small.
- A direct AI request may specify `embedding_mode`. Omission uses the configured
  AI service default. Backend requests default to English and pass that choice
  explicitly; the frontend selector also defaults to English.
- An unavailable mode returns 503 rather than silently using another model.

Separate persisted indexes are `ai/indexes/bge-small/index.faiss` (384 dimensions)
and `ai/indexes/bge-m3/index.faiss` (1024 dimensions). Each has a manifest with
model name, dimension, corpus hash and ordered standard IDs. Startup validates
these plus the actual FAISS type/dimension/count before loading. Custom English
models use a model-name hash directory. Missing indexes are built; incompatible
ones fail with an explicit rebuild command. Generated indexes remain ignored
by Git. The real English and M3 indexes both contain 40 fictional standards.

M3 uses dense embeddings through the existing SentenceTransformer dependency,
without the BGE-small query instruction. This follows the
[BGE-M3 model documentation](https://huggingface.co/BAAI/bge-m3). No translation
service, new language model, embedding training or new vector database was added.
The official model snapshot used for this run provided `pytorch_model.bin`;
the initial safetensors-only artifact fetch was insufficient, so the actual
checkpoint was fetched before the successful run. Unit tests do not fetch it.

## Language and reranking policy

The deterministic script detector counts Devanagari/Kannada letters; dominant
Kannada maps to Kannada, otherwise Devanagari maps to Hindi, and remaining text
defaults to English. Ties favor Hindi. This is a demo routing hint and does not
distinguish every language sharing those scripts. Mixed-script input follows
the non-English policy when either supported Indic script is present.

English M3 queries retain configured semantic/hybrid retrieval and the existing
English CrossEncoder. Hindi/Kannada M3 queries use FAISS dense retrieval only:
BM25, English enrichment and CrossEncoder are skipped. No translation or unit
rewriting is performed. Conservative existing preprocessing still applies.
The English reranker threshold is not misapplied to cosine scores. Such results
remain unassessed with explicit warnings and `reranker_score=null`.

The English model, reranker, threshold, enrichment and evaluation defaults were
not changed. Response metadata reports `embedding_mode`, `detected_language`
and `reranking_applied`, and survives backend database enrichment. API clients
must allow a null reranker score when reranking is skipped.

## Real-model manual results

Executed `python -m scripts.test_multilingual_demo` against real BGE-M3, its
separate FAISS index and the unchanged 40-standard fixture:

- English transformer: **IS-DEMO-001 at rank 1**, CrossEncoder applied.
- Hindi transformer: **IS-DEMO-001 at rank 1**, CrossEncoder skipped.
- Kannada transformer: **IS-DEMO-001 at rank 1**, CrossEncoder skipped.
- English 33 kV XLPE cable: **IS-DEMO-024 at rank 1**, CrossEncoder applied.
- Hindi 33 kV XLPE cable: **IS-DEMO-024 at rank 1**, CrossEncoder skipped.
- Kannada 33 kV XLPE cable: **IS-DEMO-024 at rank 1**, CrossEncoder skipped.

All six requested examples met the expected retrieval result. Exact texts,
top-five IDs, raw scores, detected language and reranking flags are stored in
`evaluation/results/multilingual_demo.json`. The reproducible script contains
the original supplied examples. These six authored queries are not a held-out
multilingual benchmark or evidence of calibrated confidence. No ranking rules
were tuned to force a particular ID to the top.

## Automated validation

- **155 AI tests passed**, including all 142 pre-existing tests.
- **31 backend tests passed**; the optional live PostgreSQL test was skipped
  because no test database was configured for this phase. PostgreSQL code and
  migrations are unchanged.
- **4 frontend tests passed**, and the production build passed.
- Real BGE-small index creation passed: 40 standards, 384 dimensions.
- Real BGE-M3 loading/index creation and the six-query demo passed.

Tests cover mode defaults, model selection, script detection, separate paths,
cached index loading, incompatible model/corpus/dimension rejection, old API
requests, unloaded/invalid modes, skipped-reranker responses, unchanged English
reranking, startup opt-in, backend mode/evidence metadata pass-through and UI
mode selection. Backend validation was adjusted to retain Devanagari/Kannada
combining marks rather than splitting words into fragments. Existing English
meaningful-input checks remain covered. Dependency deprecation warnings do not
affect the passing results.

## Startup

With PostgreSQL, migrations and seeding already configured as described in the
root README, start the AI service from a root PowerShell terminal:

```powershell
cd ai
$env:EMBEDDING_MODE='english'
$env:MULTILINGUAL_ENABLED='true'
.venv/Scripts/python -m uvicorn app.main:app --reload --port 8001
```

Start backend :8000 and frontend :5173 normally, then choose **Multilingual**
in the input page. M3's checkpoint requires additional download space and RAM.
To run the six-query check directly from `ai/`:

```powershell
.venv/Scripts/python -m scripts.test_multilingual_demo
```

To make omitted-mode direct AI requests multilingual, set
`$env:EMBEDDING_MODE='multilingual'` before startup. Explicit English requests
still use the English engine. The backend's default remains English.

## Changed files

Created: `ai/app/nlp/language.py`, `ai/app/retrieval/index_cache.py`,
`ai/tests/test_multilingual.py`, `ai/scripts/test_multilingual_demo.py`,
`backend/tests/test_multilingual.py`, and this report. The manual run also
writes the ignored JSON results and isolated index artifacts.

Modified: root `README.md`; `ai/.env.example`, `ai/README.md`, `ai/app/config.py`,
`ai/app/main.py`, `ai/app/nlp/embeddings.py`,
`ai/app/recommendation/recommender.py`, `ai/app/schemas/recommendation.py`,
`ai/scripts/build_index.py`; `backend/README.md`, `backend/app/main.py`,
`backend/app/schemas.py`, `backend/app/services/ai_client.py`,
`backend/app/services/response_adapter.py`, `backend/tests/conftest.py`;
`frontend/src/api.js`, `frontend/src/InputPage.jsx`, `frontend/src/ResultsPage.jsx`,
`frontend/tests/integration.test.js`.

No PostgreSQL schema, RAG, PDF, Neo4j, model training or other feature work was added.
