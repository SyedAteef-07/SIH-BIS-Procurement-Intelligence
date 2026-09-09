# Local AI recommendation service

Implements AI_PLAN.md milestones 0-7: conservative preprocessing, pretrained BGE
embeddings, normalized FAISS inner-product retrieval, cross-encoder reranking,
and a typed FastAPI endpoint. No API key or model training is required.

## Run (PowerShell, from the repository root)

```powershell
cd ai
py -3.12 -m venv .venv
.venv/Scripts/python -m pip install -r requirements-dev.txt
.venv/Scripts/python -m uvicorn app.main:app --reload
```

Python 3.11 or 3.12 is recommended. On macOS/Linux use `python3 -m venv .venv`
and `.venv/bin/python` instead. First startup downloads both pretrained models
from Hugging Face and builds the small in-memory index. Subsequent starts reuse
the model cache. Startup fails visibly if the dataset or models cannot load;
there is no keyword-only fallback. Model inference runs on CPU by default.

Open http://127.0.0.1:8000/docs. `GET /` reports readiness after model startup.

```powershell
Invoke-RestMethod http://127.0.0.1:8000/recommend -Method Post -ContentType 'application/json' -Body '{"text":"Procurement of three phase oil immersed distribution transformers","top_k":5}'
```

The response contains the cleaned query, ranked `recommendations`, and warnings.
Each recommendation includes its standard metadata, cosine `retrieval_score`,
raw `reranker_score`, verbatim scope evidence, and `validity: unverified`.
Raw scores are not confidence percentages. Every supplied dataset entry is
fictional (`IS-DEMO-*`, `is_mock: true`), never a real or verified current standard.

## Configuration and data

Copy `.env.example` to `.env` to override model names, CPU/device selection,
retrieval count, or dataset path. Relative dataset paths resolve against `ai/`,
not the shell working directory. The index is rebuilt at each startup; no stale
on-disk index can be reused accidentally.

Replace `data/sample_standards.json` with a JSON array containing unique `id`
(or `standard_id`), `title`, and `scope`. Optional fields are `abstract`,
`keywords`, `status`, `revision`, `source`, and `is_mock`. Metadata is returned
as supplied and is never treated as independent verification of validity.

Requests allow 1-50 results and at most 2,000 characters. Inputs exceeding the
embedding model token budget are rejected rather than silently truncated.
The broad retrieval pool is at least as large as the requested result count.
Small datasets return only available entries. This prototype ranks candidates
without a calibrated relevance cutoff and may return unrelated entries for
out-of-domain requests. Review the evidence before using any result.

## Validation

```powershell
.venv/Scripts/python -m pytest
.venv/Scripts/python -m scripts.build_index
.venv/Scripts/python -m scripts.test_retrieval
```

Unit/API tests use deterministic model doubles and real FAISS; they require no
model downloads. The separate smoke script exercises both real models through
FastAPI and checks transformer, head protection, and road-lighting queries.
It is a small demo check, not a measured production-quality benchmark.

The frontend remains a static mockup; use Swagger or an HTTP client for this API.
PDF parsing, requirement extraction, graph relationships, version verification,
RAG and labelled evaluation are later roadmap milestones, not implemented here.
See the root `AI_PLAN.md` and `README_AI.md` for the full roadmap.

Model usage follows the upstream documentation:
- https://huggingface.co/BAAI/bge-small-en-v1.5
- https://www.sbert.net/docs/package_reference/cross_encoder/model.html

## Verified local environment

Validated on Windows with Python 3.12.8: all 9 unit/API tests passed, and all
3 real-model API smoke queries returned the expected mock standard at rank 1.
`pip check` reported no dependency conflicts. `requirements-lock.txt` records
the exact tested environment, including development/test packages. To recreate
it, install with `python -m pip install -r requirements-lock.txt`.
