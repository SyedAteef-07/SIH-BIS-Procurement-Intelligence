# NLP requirement-understanding evaluation

The deterministic extraction layer is implemented. Keep query enrichment
disabled by default: this synthetic benchmark shows no final-ranking gain and
one small semantic first-stage regression. Extraction is useful structured
evidence, but this run does not establish improved recommendation quality.

## Validation and controlled experiment

- Complete suite: **142 passed, 0 failed**, including the original 83 tests.
  Two existing dependency deprecation warnings concern Starlette/httpx and
  AnyIO; no test failure or additional dependency was introduced.
- Real-model experiment: 100 existing queries, 40 fictional standards;
  90 in-domain queries contribute to ranking means and 10 are out of domain.
- BGE remains `BAAI/bge-small-en-v1.5`; CrossEncoder remains
  `cross-encoder/ms-marco-MiniLM-L-6-v2`. FAISS, BM25, RRF constant 60,
  candidate depth 20 and final depth 5 are unchanged.
- Both variants share models/indexes and score the candidate union against the
  original cleaned query once per query. Only first-stage query enrichment
  differs. Relevance labels are used only for measurement, not retrieval.
- Thresholding is disabled for this experiment. MRR uses all retrieved
  candidates, binary relevance uses grades >= 2, and NDCG includes grade 1.
- Reproduce from `ai/`: `python -m pytest -v`, then
  `python -m evaluation.evaluate_enrichment`. The latter supports `--queries`
  and `--output`; existing calibration outputs are preserved.

## Overall results

Metrics below are ordered Recall@1 / Recall@3 / Recall@5 / MRR / NDCG@5.

- **Hybrid + CrossEncoder, raw:** 0.914815 / 0.958333 / 0.974074 /
  0.988889 / 0.968993.
- **Hybrid + CrossEncoder, enriched:** 0.914815 / 0.958333 / 0.974074 /
  0.988889 / 0.968993. All metric deltas are zero.
- Semantic + CrossEncoder has the same above metrics for raw and enriched.
- Hybrid before reranking, raw and enriched: 0.919444 / 0.947222 /
  0.968519 / 0.981481 / 0.962318.
- Semantic before reranking, raw: 0.920370 / 0.959259 / 0.977778 /
  0.994444 / 0.971951. Enriched: identical recall and MRR, NDCG@5
  **0.971388** (delta -0.000563).

## Category results and regressions

For final hybrid + CrossEncoder rankings, raw and enriched category metrics
are identical. Using the same metric order as above:

- Exact (40): 0.975000 / 1 / 1 / 0.987500 / 0.990773.
- Semantic paraphrase (15): 1 / 1 / 1 / 1 / 1.
- Near confuser (15): 1 / 1 / 1 / 1 / 0.987226.
- Technical (10): 1 / 1 / 1 / 1 / 1.
- Ambiguous (10): 0.333333 / 0.625000 / 0.766667 / 0.950000 / 0.777003.
- Out of domain (10): ranking metrics are undefined; both return candidates
  for all ten because no rejection threshold is enabled. This is not evidence
  that these candidates are relevant or that extraction provides OOD rejection.

The sole measured enrichment regression is semantic first-stage query Q067:
"assembled switchboard busbars and metal enclosure interlocks". The alias
adds `Product: switchgear.`. The correct standard IS-DEMO-027 stays first,
but grade-1 IS-DEMO-026 moves out of the top five. Query NDCG@5 changes from
0.968015 to 0.917319; near-confuser semantic NDCG@5 changes from 0.984711
to 0.981332. Recall and first-relevant rank are unchanged. Hybrid and final
reranked metrics do not regress. All other category metrics are unchanged.
No first-relevant-rank improvements or regressions were observed.

## Extraction examples

- `11KV/433V three phase oil immersed distribution transformer for outdoor
  installation` yields product `distribution transformer`, type `oil immersed`,
  phase `three_phase`, voltages 11 kV and 433 V, and installation `outdoor`.
- `IP65 LED road lighting fixture suitable for outdoor installation` yields
  `street luminaire`, IP65, LED type and outdoor installation.
- `33 kV XLPE insulated high voltage power cable` yields `power cable`,
  33 kV and XLPE material.
- `centrifugal water pump rated 15 kW at 50 Hz` yields `pump`, centrifugal
  type, 15 kW and 50 Hz.
- `PVC pressure pipe of 110 mm diameter for potable water` yields
  `PVC water pipe`, PVC and an explicit diameter of 110 mm.
- `protective headgear for construction workers against falling objects`
  yields `safety helmet` and falling-object safety evidence.
- `ergonomic office chair with adjustable armrests` leaves product unset
  and contributes no fabricated transformer or electrical attributes.

The original cleaned query remains the prefix of enriched retrieval text.
Source spelling and character offsets are preserved separately from normalized
values. Coordinated "insulation and efficiency testing" produces both testing
requirements with the shared original phrase as evidence.

## Assumptions and limitations

Rules and aliases are an English deterministic MVP, not trained domain-specific
NER. A singular product is set only when explicit aliases identify one canonical
product; longer overlapping aliases win and distinct multiple products leave
it unset. Generic "transformer" does not imply distribution transformer.
Materials are matched only when named. Certification text is a requirement,
not a validity check. Local negation is conservative and cannot resolve all
grammatical scopes. Multi-product attribute linking, ranges, tolerances,
unit conversion and document/page metadata are outside this phase.

The benchmark is authored and synthetic, not held-out procurement data. No
aliases or labels were tuned to erase Q067's regression. Do not enable
enrichment on the basis of unchanged aggregate scores from this small corpus;
validate on representative independent queries first.

## Files

Created:

- `app/nlp/technical_patterns.py`, `normalization.py`, `product_matcher.py`,
  `extractor.py`, `query_builder.py`.
- `app/schemas/requirements.py`.
- `evaluation/evaluate_enrichment.py` and this report.
- `tests/test_extractor.py`, `test_normalization.py`, `test_product_matcher.py`,
  `test_query_builder.py` (also covers engine integration and controlled evaluation).
- `evaluation/results/nlp_enrichment.json` and
  `evaluation/results/nlp_enrichment_diagnostics.json`.

Modified: `app/config.py`, `app/recommendation/recommender.py`, `.env.example`,
`README.md`, and `evaluation/README.md`.

The machine-readable results include all eight systems, category metrics,
top-five predictions and per-query rank/NDCG comparisons. The compact
[diagnostics JSON](results/nlp_enrichment_diagnostics.json) includes two examples
per category plus the observed regression, with original text, extraction
evidence, enriched text, top-five rankings and expected-standard rank changes.
See [full results](results/nlp_enrichment.json) for model/configuration metadata
and dataset/query hashes. No production defaults or API contracts changed.
No PostgreSQL, PDF/OCR, RAG, LLM, graph integration or training was added.
