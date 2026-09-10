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
.venv/Scripts/python -m uvicorn app.main:app --reload --port 8001
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

Open http://127.0.0.1:8001/docs, expand `POST /recommend`, and select Try it out.
The main backend runs separately on 8000 and calls this service using
`AI_SERVICE_URL`. React calls the main backend only. See the root README for
PostgreSQL migrations, seeding and the complete startup sequence.

```json
{
  "text": "oil used for electrical insulation and cooling in transformers",
  "top_k": 5
}
```

Or in PowerShell:

```powershell
Invoke-RestMethod http://127.0.0.1:8001/recommend -Method Post -ContentType 'application/json' -Body '{"text":"three phase oil immersed distribution transformer","top_k":5}'
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

## Calibration and ranking-fusion experiments

The evaluation now compares the three existing systems, raw hybrid retrieval,
and evaluation-only weighted rank fusion at weights 0.5, 1.0, 1.5 and 2.0.
Production still uses the existing cross-encoder ordering and disabled threshold.
No production configuration, model, API schema or retriever is changed by these
experiments. The same 40 standards and 100 labels are reused without relabelling.

```powershell
.venv/Scripts/python -u -m evaluation.evaluate
# Add/highlight a weight; defaults still evaluate 0.5, 1.0, 1.5, 2.0:
.venv/Scripts/python -u -m evaluation.evaluate --reranker-fusion-weight 0.75
# Override the experiment sweep or the experiment-only RRF constant:
.venv/Scripts/python -u -m evaluation.evaluate --fusion-weights 0.5 1 1.5 2 --fusion-rrf-k 60
# Recalculate threshold candidates from saved query scores; no model loading:
.venv/Scripts/python -m evaluation.calibration evaluation/results/latest.json --score-field top_hybrid_reranker_score
```

`RERANKER_FUSION_WEIGHT` is an optional environment default for the CLI's
`--reranker-fusion-weight`. It is consumed only by evaluation. Every weight in
the sweep gets a separate overall and per-category result. The configured
weight is also included in the sweep and recorded in experiment_configuration.

Semantic fusion combines FAISS ranks with cross-encoder ranks on the same
semantic candidate pool. Hybrid fusion combines the hybrid RRF ranks with
cross-encoder ranks on the same hybrid candidate pool. Both use
`1/(k + base_rank) + weight/(k + reranker_rank)` with one-based ranks. Ties retain
base rank, then reranker rank, then ID. Zero weight preserves the base ranking.
Raw model scores are never added to each other.

The evaluator writes these files under the output report's directory:

- `latest.json`: full metrics, predictions, diagnostics and settings.
- `comparison.txt`: all systems and weights, overall and by category.
- `regressions.json` / `regressions.txt`: first-relevant-rank improvements,
  regressions, unchanged cases, and the ten largest changes in each direction.
- `hybrid_diagnostics.json`: candidate IDs, overlap, RRF and final rankings.
- `query_scores.json`: one maximum per query/system and domain-group percentiles.
- `threshold_analysis.json`: all observed threshold boundaries and candidates.
- `ambiguous_queries.json` / `ambiguous_queries.txt`: graded labels, all top-five
  rankings and NDCG@5/Recall@5 for each ambiguous query.

Regression deltas are baseline rank minus comparison rank: positive is better.
Missing ranks remain null and use one rank below both lists only for the delta.
OOD cases are not included in improvement/regression counts. Ordered top-five
comparisons detect both membership and ordering changes. Overlap@K is the
intersection size divided by configured K, even when BM25 returns fewer entries.

Threshold analysis uses query maxima, not individual candidate pairs. The
positive class is in-domain; acceptance is score >= threshold, matching the API.
The sweep covers every distinct observed decision boundary plus a reject-all
boundary, and reports acceptance/rejection rates, confusion counts, precision,
recall and F1. Separate analyses cover semantic and hybrid candidate pools.
Recommended candidates maximize F1, or satisfy empirical recall/rejection
constraints with explicit tie-breaking. No settings are written automatically.

These are in-sample exploratory findings. Ten OOD examples cannot establish a
99% population rejection rate. Domain detection also does not prove that a
returned standard is correct. Select any threshold manually after independent
validation. See [the calibration report](evaluation/CALIBRATION_REPORT.md).

## Deterministic requirement extraction

This is a deterministic MVP extraction layer, not a trained domain-specific
NER model. Regex and configurable product aliases make the small fictional
catalogue's extraction rules reproducible, inexpensive, and independently
testable. No dependency or model was added.

`RequirementExtractor.extract(text)` returns a Pydantic `ExtractedRequirements`:
product and matched phrase; product types; materials; voltage, frequency, power
and dimensions (explicit diameter); phase; IP rating; technical classes;
installation/environment; testing, safety, performance, installation, material
and certification requirements. Quantities retain their units and raw spelling.
Evidence includes source substrings and character offsets into the supplied
text. Negated attribute matches are recorded as evidence but excluded from
positive fields. A certification requirement is not evidence of certification.

```python
from app.nlp.extractor import RequirementExtractor
from app.nlp.query_builder import QueryBuilder

text = "11KV/433V three phase oil immersed distribution transformer for outdoor installation"
requirements = RequirementExtractor().extract(text)
print(requirements.model_dump(exclude_none=True))
print(QueryBuilder().build(text, requirements))
```

The example identifies `distribution transformer`, `oil immersed`,
`three_phase`, `11 kV`, `433 V`, and `outdoor`. Product aliases are configurable
through `ProductMatcher(aliases=...)`, injected into `RequirementExtractor`.
Unknown products return `None`; multiple distinct product matches also leave
the singular product unset. Longer overlapping aliases take precedence.

Extraction runs before retrieval. **Query enrichment is off by default**
(`QUERY_ENRICHMENT=false`). For an explicit experiment, set it to `true` in
the environment or pass `Settings(query_enrichment=True)`. Enrichment appends
nonempty, positive fields to the entire cleaned original query for BGE and
BM25. The CrossEncoder always receives the original cleaned query. The engine
checks the BGE tokenizer budget, including its query prefix, and omits trailing
enrichment fields that would exceed it; original text is never shortened.
An original query exceeding the budget retains the existing validation error.
The API request/response schemas and ranking defaults remain unchanged.
Logging records only product presence, attribute count and enrichment use.

Limitations: the alias vocabulary is finite and English-focused. The extractor
does not infer an unspecified transformer subtype, resolve coreferences, attach
attributes to individual products, convert units, or interpret measurement
ranges/tolerances. Local negation rules are conservative, not a grammatical
parser. Unit spelling is case-insensitive for the supported procurement units;
ambiguous SI spellings require review. Ordinary unitless numbers are ignored.
Evidence offsets refer to input characters, not document pages.

From `ai/`, run:

```powershell
.venv/Scripts/python -m pytest tests/test_extractor.py tests/test_normalization.py tests/test_product_matcher.py tests/test_query_builder.py -v
.venv/Scripts/python -m pytest -v
.venv/Scripts/python -m evaluation.evaluate_enrichment
```

The enrichment evaluation holds models, indexes, candidate depths and reranker
query fixed. It compares raw/enriched semantic and hybrid retrieval both before
and after reranking, using existing metrics and query labels. Results go to
`evaluation/results/nlp_enrichment.json`; two extraction/ranking examples per
category plus selected regressions go to `nlp_enrichment_diagnostics.json`.
MRR uses the full candidate
ranking; stored predictions are limited to final K. OOD has no ranking labels
and is excluded from ranking means. Thresholding is disabled in this comparison.
See [the NLP evaluation report](evaluation/NLP_ENRICHMENT_REPORT.md) for findings.

## Scope

The frontend calls the main backend, which enriches AI IDs with PostgreSQL
metadata. The AI service itself continues to index the shared JSON fixture.
This phase
does not add RAG, external LLM APIs, PDF/OCR processing, trained NER,
Neo4j, cloud deployment, custom training or standards-version verification.
The roadmap files are at the repository root, not duplicated under `ai/`.

Upstream model/library references:
- https://huggingface.co/BAAI/bge-small-en-v1.5
- https://www.sbert.net/docs/package_reference/cross_encoder/model.html
- https://github.com/dorianbrown/rank_bm25
