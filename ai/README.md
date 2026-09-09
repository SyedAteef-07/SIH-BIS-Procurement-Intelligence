# Local AI recommendation service

This phase implements BGE sentence embeddings, FAISS semantic retrieval, BM25
lexical retrieval, reciprocal rank fusion (RRF), cross-encoder reranking and a
FastAPI API. It uses 40 explicitly fictional standards and 100 authored queries.
The latest root `Codex Next Implementation Instructions.md` explicitly retains
`BAAI/bge-small-en-v1.5`, superseding the older MiniLM preference in
`CHAT_CONTEXT.md`. Models remain configurable.

## Run locally

From the repository root in PowerShell:

```powershell
cd ai
py -3.12 -m venv .venv
.venv/Scripts/python -m pip install -r requirements-dev.txt
.venv/Scripts/python -m uvicorn app.main:app --reload
```

If the virtual environment already exists, only install the updated dependencies.
Python 3.11 or 3.12 is recommended. On macOS/Linux use `python3 -m venv .venv`
and `.venv/bin/python`. The exact tested dependencies, including test tools,
are recorded in `requirements-lock.txt` for reproducible installation.

First startup downloads the public pretrained models from Hugging Face; later
starts reuse the model cache. Inference and both indexes run locally without
external LLM APIs. Startup initializes the models and rebuilds the in-memory
indexes before serving requests. Model/dataset failures fail startup visibly.
Strict offline model provisioning is not implemented in this phase.

Open http://127.0.0.1:8000/docs, expand `POST /recommend`, and select Try it out.

```json
{
  "text": "oil used for electrical insulation and cooling in transformers",
  "top_k": 5
}
```

Or in PowerShell:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/recommend -Method Post -ContentType 'application/json' -Body '{"text":"three phase oil immersed distribution transformer","top_k":5}'
```

## Retrieval and response contract

1. Conservative cleaning preserves units, numbers, technical wording and negation.
2. BGE generates normalized embeddings; FAISS uses inner-product/cosine search.
3. In hybrid mode BM25 retrieves lexical matches with technical tokenization
   (`11kV` and `11 kV` align; IP65, PVC, LED and 50 Hz are retained).
4. RRF combines one-based ranks with `sum(1 / (RRF_K + rank))`, deduplicated by
   standard ID. Raw cosine and BM25 scores are never averaged. Each source
   retrieves RETRIEVAL_K candidates; fusion retains RETRIEVAL_K candidates.
5. The cross encoder reranks the candidates. An optional raw-score filter runs
   before taking the final results. Reranking determines the final order.

One `Standard.to_retrieval_text()` method supplies title, scope, abstract and
keywords consistently to all stages; IDs and field labels are metadata only.
`document_text` remains available as a compatibility alias.

Existing `query`, `recommendations` and `warnings` response fields are preserved.
Each recommendation contains standard metadata, verbatim scope evidence,
`retrieval_score`, raw `reranker_score`, `retrieval_score_type` and
`validity: unverified`. Retrieval score type is `cosine` in semantic mode and
`rrf` in hybrid mode. Neither score is a probability or confidence percentage.
These scores are development/debugging values, not a procurement decision.

All supplied standards use `IS-DEMO-*`, `is_mock: true` and a fictional source.
Status/revision metadata is never treated as proof of current validity.

## No-match behavior

`MIN_RERANKER_SCORE` is **disabled by default** (blank or `null`). With filtering
disabled, nonempty responses have `has_reliable_match: null` and
`match_status: NOT_ASSESSED`, with a warning that candidates may be unrelated.
The service does not claim to detect out-of-domain requests in that mode.

When a threshold is configured, only candidates at or above it are returned.
An empty result has `has_reliable_match: false`,
`match_status: NO_RELIABLE_MATCH` and a readable warning. A nonempty result has
`has_reliable_match: true` and `match_status: MATCH`; this only means it passes
the configured cutoff, not that confidence or standards validity is verified.
No production threshold has been selected or calibrated.

## Configuration

Copy `.env.example` to `.env`; do not commit secrets. Supported settings:

- EMBEDDING_MODEL: `BAAI/bge-small-en-v1.5`
- RERANKER_MODEL: `cross-encoder/ms-marco-MiniLM-L-6-v2`
- RETRIEVAL_MODE: `hybrid` (or `semantic`)
- RETRIEVAL_K: `20`
- FINAL_K: `5`, used when a request omits top_k
- RRF_K: `60`
- MIN_RERANKER_SCORE: blank/disabled
- DATASET_PATH: `data/sample_standards.json`, relative to `ai/`
- MODEL_DEVICE: `cpu`

Require 1 <= FINAL_K <= 50, RETRIEVAL_K >= FINAL_K, RRF_K > 0, and a finite
threshold when enabled. Explicit request top_k (1-50) overrides FINAL_K and
expands the candidate pool when necessary. Small corpora return only available
entries. Inputs allow at most 2,000 characters and must fit the embedding model's
token limit; long tender chunking is a later phase.

A replacement dataset is a JSON array with unique `id` (or `standard_id`),
`title` and `scope`. Optional fields include `abstract`, `keywords`, `status`,
`revision`, `source` and `is_mock`. Evaluation labels must also be updated when
replacing the dataset. Indices rebuild on startup to avoid stale metadata.

## Health and logs

- GET / preserves the existing readiness response.
- GET /health returns `{"status":"ok"}` for process liveness.
- GET /ready checks the embedding/reranker objects, nonempty matching FAISS
  index and dataset, and BM25 index in hybrid mode. Returns status,
  standards_count and retrieval_mode; failures return HTTP 503.

These endpoints become available after FastAPI startup initialization completes.
Logs report query length, retrieval mode, candidate/reranking counts, final
counts, no-match conditions and error types. Full tender text is not logged.

## Tests and real-model smoke checks

```powershell
.venv/Scripts/python -m pytest
.venv/Scripts/python -m scripts.build_index
.venv/Scripts/python -u -m scripts.test_retrieval
```

Unit tests use model doubles and real BM25/FAISS without downloading models.
The separate smoke script loads the real models once and checks technical
paraphrases and near-confusers through both semantic and hybrid APIs, plus
out-of-domain response handling and readiness. It does not calibrate a threshold.

## Run the evaluation

```powershell
.venv/Scripts/python -u -m evaluation.evaluate
# Optional paths:
.venv/Scripts/python -u -m evaluation.evaluate --queries evaluation/queries.json --output evaluation/results/latest.json
```

The runner evaluates these separately on the same corpus and candidate depth:
BGE + FAISS, BGE + FAISS + reranker, and hybrid + reranker. It shares the models,
encodes each query once and scores each query/candidate pair once across the
candidate union. No labels influence retrieval, fusion or reranking.

It prints overall and per-category Recall@1/3/5, Precision@5, MRR and NDCG@5,
and writes detailed rankings and scores to JSON. Binary relevance for recall,
precision and MRR is grade >= 2. Grade 1 is weakly related and contributes only
to graded NDCG. Precision@5 always divides by 5, including short result lists.
MRR is computed over the returned candidate ranking (20 by default), not the
entire corpus. Ranking metrics are computed before optional score filtering.

The fixtures contain 40 exact, 15 semantic_paraphrase, 15 near_confuser,
10 technical, 10 ambiguous and 10 out_of_domain queries. Empty-relevance OOD
queries are excluded from ranking averages and reported separately with their
return rate and top-score distributions. `accepted_ids` records the configured
filter's effect (the semantic-only baseline has no reranker filter). Reports
also include candidate score distributions, model names, dataset/query hashes,
settings and timestamp.

These are hand-authored synthetic development fixtures, not a held-out
production benchmark. Exact queries deliberately name products. Do not claim
improvement without comparing actual metrics, or choose a production threshold
from these small fixtures alone. Compare relevant/irrelevant/OOD score overlap,
then collect a representative labelled calibration set and a separate held-out
validation set before enabling a cutoff. No automatic threshold tuning occurs.

Measured results and known ranking failures are documented in
[evaluation/README.md](evaluation/README.md); the complete report is
[evaluation/results/latest.json](evaluation/results/latest.json).

## Scope

The frontend remains a static mockup; use Swagger or an HTTP client. This phase
does not add RAG, external LLM APIs, PDF/OCR processing, entity extraction,
Neo4j, cloud deployment, custom training or standards-version verification.
The roadmap files are at the repository root, not duplicated under `ai/`.

Upstream model/library references:
- https://huggingface.co/BAAI/bge-small-en-v1.5
- https://www.sbert.net/docs/package_reference/cross_encoder/model.html
- https://github.com/dorianbrown/rank_bm25
