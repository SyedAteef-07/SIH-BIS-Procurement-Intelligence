# Retrieval evaluation results

The subsequent calibration and rank-fusion experiments are documented in
[CALIBRATION_REPORT.md](CALIBRATION_REPORT.md). The latest JSON now includes
those experiments alongside the three baseline systems described below.

Measured on 2026-09-09 with 40 fictional standards and 100 authored queries.
The full rankings, scores, category metrics, settings and dataset hashes are in
[results/latest.json](results/latest.json). Run instructions and metric
definitions are in [../README.md](../README.md).

## Overall results

Ranking means cover 90 in-domain queries; 10 out-of-domain queries are reported
separately. These values are ranking metrics, not model confidence.

- BGE + FAISS: Recall@1 0.9204, Recall@3 0.9593, Recall@5 0.9778,
  Precision@5 0.2267, MRR 0.9944, NDCG@5 0.9720.
- BGE + FAISS + reranker: Recall@1 0.9148, Recall@3 0.9583, Recall@5 0.9741,
  Precision@5 0.2244, MRR 0.9889, NDCG@5 0.9690.
- Hybrid + reranker: Recall@1 0.9148, Recall@3 0.9583, Recall@5 0.9741,
  Precision@5 0.2244, MRR 0.9889, NDCG@5 0.9690.

Hybrid provides no measured overall improvement over semantic + reranker in
this run. Semantic-only retrieval has slightly better overall metrics.
Reranking improves semantic-paraphrase MRR from 0.9667 to 1.0000 but decreases
ambiguous-query NDCG@5 from 0.8074 to 0.7770. Many queries have just one relevant
standard, so returning five results yields Precision@5 of 0.2 even with a
correct first result. Ambiguous queries have multiple relevant standards,
making Recall@1 different from top-1 accuracy.

## Observed ranking failures

- Q018, indoor LED luminaires: reranking places outdoor luminaire safety
  (IS-DEMO-021) above the labelled indoor luminaires (IS-DEMO-018).
- Q087, lighting for a public building: reranking places road luminaires
  (IS-DEMO-003) above labelled indoor/emergency lighting (IS-DEMO-018/019).

These are recorded evaluation failures, not hidden or relabelled to improve
the scores. The focused real-model smoke checks all pass; they do not cover
every evaluation query and are not proof of production accuracy.

## Abstention evidence

All configurations return candidates for all 10 out-of-domain queries with the
threshold disabled. The API explicitly reports reliability as unassessed.
Retrieved relevant candidate scores range from -10.3086 to 9.8706; irrelevant
in-domain candidate scores range from -11.4538 to 3.4162. Out-of-domain scores
range from -11.3878 to -9.9940. The overlap means a simple cutoff can reject
some labelled relevant candidates while still accepting some irrelevant ones.

No threshold is selected. The fixtures are synthetic development data, with
40 deliberately exact queries, not a representative held-out procurement
benchmark. Use a separate labelled calibration set and independent validation
set before enabling MIN_RERANKER_SCORE. Score distributions include only
retrieved candidate pairs, not every possible corpus pair.

## Validation

- 52 unit/API tests passed, including all original tests.
- 16 real-model ranking assertions passed across semantic/hybrid modes.
- Real-model health/readiness and out-of-domain response checks passed.
- The evaluation completed for all 100 queries and three systems.
- pip check found no broken dependencies. Two upstream test-client
  deprecation warnings remain; they did not fail tests.

This report belongs to the code's evaluation fixtures. No model training,
threshold fitting, PDF processing or RAG was performed.
# NLP enrichment comparison

Run `python -m evaluation.evaluate_enrichment` from `ai/` to compare raw queries
with appended deterministic requirements. Models, indexes, candidate depths,
RRF and original CrossEncoder queries are held fixed. This separate experiment
does not overwrite calibration reports or change production defaults.
See [NLP_ENRICHMENT_REPORT.md](NLP_ENRICHMENT_REPORT.md) and the extraction
documentation in [../README.md](../README.md).
