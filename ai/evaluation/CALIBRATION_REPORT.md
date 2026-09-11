# Retrieval calibration and ranking-fusion report

Real-model evaluation completed on 2026-09-09 at 16:21:52 UTC. The corpus and
labels are unchanged: 40 fictional standards, 90 in-domain queries and 10 OOD
queries. BGE and the existing MiniLM cross encoder were retained. No production
configuration was changed. All numbers below are evaluation metrics, not
confidence percentages or independent validation of standards.

## Ranking comparison

The full requested Recall@1/3/5, MRR and NDCG@5 results for every weight, overall
and by category, are in [results/comparison.txt](results/comparison.txt). Detailed
predictions and metadata are in [results/latest.json](results/latest.json).

- BGE + FAISS: Recall@1 0.9204; Recall@3 0.9593; Recall@5 0.9778;
  MRR 0.9944; NDCG@5 0.9720.
- BGE + FAISS + cross encoder: Recall@1 0.9148; Recall@3 0.9583;
  Recall@5 0.9741; MRR 0.9889; NDCG@5 0.9690.
- Hybrid + cross encoder: Recall@1 0.9148; Recall@3 0.9583;
  Recall@5 0.9741; MRR 0.9889; NDCG@5 0.9690.
- Best overall NDCG semantic-fusion weight, 1.0: Recall@1 0.9204;
  Recall@3 0.9583; Recall@5 0.9769; MRR 0.9944; NDCG@5 0.9728.
- Best overall NDCG hybrid-fusion weight, 1.0: Recall@1 0.9231;
  Recall@3 0.9556; Recall@5 0.9741; MRR 0.9870; NDCG@5 0.9697.

Weights 0.5, 1.0, 1.5 and 2.0 were evaluated for both fusion experiments.
Semantic fusion at 1.0 has a small NDCG gain over BGE alone (about 0.00087),
with a small Recall@5 decrease (about 0.00093). This is a tradeoff on synthetic
fixtures, not sufficient evidence to replace production ranking automatically.
Hybrid fusion did not beat semantic-only overall NDCG or Recall@5.

## Per-query changes

First relevant rank, over 90 in-domain queries:

- Semantic vs semantic + cross encoder: 1 improved, 87 preserved, 2 worsened.
- Semantic vs raw hybrid RRF: 1 improved, 86 preserved, 3 worsened.
- Semantic + cross encoder vs hybrid + cross encoder: 0 improved,
  90 preserved, 0 worsened.

The ten OOD queries are not applicable to first-relevant-rank comparisons.
The reports contain all queries, expected IDs, both complete candidate rankings,
first relevant ranks, signed changes, and NDCG@5 values. See
[regressions.txt](results/regressions.txt) for the largest changes and
[regressions.json](results/regressions.json) for every case. Rank preservation
does not mean the entire ranking is identical.

## Why hybrid metrics were identical after reranking

- Mean overlap@20: 0.5405, or 10.81 shared candidates per query.
- BM25-only candidates/query: 5.78; FAISS-only candidates/query: 9.19.
- FAISS/BM25 candidate sets are identical on 0 of 100 queries.
- RRF changes the candidate set on 85 of 100 queries.
- RRF changes the ordered top five on 88 of 100 queries.
- Hybrid changes the final cross-encoder top five on only 7 of 100 queries.
- 81 of the 88 initial top-five differences disappear after reranking (92.05%).

BM25 does contribute distinct candidates and RRF has a substantial effect.
The cross encoder overrides most initial ordering differences; remaining
differences produce the same aggregate relevance metrics on these labels.
This does not establish that BM25 is redundant. Inspect each candidate pool in
[hybrid_diagnostics.json](results/hybrid_diagnostics.json).

## Query-level score distributions

These count each query once, using its highest candidate score. Full min,
p05, p10, median, p90, p95 and max values are in
[query_scores.json](results/query_scores.json).

- In-domain (90 queries): top reranker scores range from -5.271080017089844
  to 9.870622634887695; median 2.7685. Semantic scores range from 0.6592
  to 0.8898; median 0.7751.
- Out-of-domain (10 queries): top reranker scores range from -11.1864
  to -9.99397087097168; median -11.0958. Semantic scores range from 0.4491
  to 0.5666; median 0.5187.

Semantic and hybrid query-level top reranker distributions are identical here.
Unlike the earlier candidate-level distributions, query maxima separate the
two classes on this fixture set. A low-scoring related candidate does not mean
the query's best candidate also has a low score.

## Threshold candidates for manual review

For both candidate pools, the observed-boundary sweep selects
**-5.271080017089844** for all three requested objectives:

- Maximum F1.
- At least 95% in-domain recall, prioritizing OOD rejection.
- At least 99% empirical OOD rejection, prioritizing in-domain recall.

At that exact inclusive boundary, TP=90, TN=10, FP=0, FN=0. In-domain acceptance
and OOD rejection are both 1.0; false rejection and false acceptance are 0.0;
precision, recall and F1 are 1.0. The full sweep and tie-breaking policy are in
[threshold_analysis.json](results/threshold_analysis.json).

On these observations, every threshold in
(-9.99397087097168, -5.271080017089844] yields the same binary classification.
The reported candidate is an observed decision boundary, not a uniquely optimal
or validated production threshold. It has no margin below the weakest positive
query. Avoid rounding a threshold upward when checking boundary equality.

These findings are in-sample and include only ten OOD examples. An observed
10/10 rejection rate cannot demonstrate 99% population rejection. New datasets,
models or candidate depths can shift the boundary. Correct domain classification
does not guarantee correct standards or retention of every relevant candidate.
Production MIN_RERANKER_SCORE remains disabled, so the actual API still returns
unassessed candidates for OOD queries until a threshold is manually approved.

## Ambiguous queries

There are ten queries with multiple plausible standards. Semantic-only gives
NDCG@5 0.8074 and Recall@5 0.8000. Cross-encoder-only ordering gives 0.7770 and
0.7667. Semantic fusion at weight 0.5 gives 0.8162 and 0.7917; weight 1.0 gives
0.8152 and 0.7917. Fusion improves graded ordering on these ambiguous examples,
while slightly reducing Recall@5 relative to semantic-only retrieval.

[ambiguous_queries.txt](results/ambiguous_queries.txt) prints every query,
graded labels and the top five for all baselines and fusion weights.
[ambiguous_queries.json](results/ambiguous_queries.json) contains structured
predictions and per-query metrics. These tradeoffs should be reviewed on an
independent set rather than optimizing only first-rank accuracy.

## Validation and scope

83 unit/API tests passed, including all original tests. The complete real-model
evaluation covered all 100 queries and 12 configurations (three existing
systems, raw hybrid, and eight fusion experiments). No new large dependencies,
model training, model switches, PDF processing, RAG or graph features were added.

The experiments did not change production defaults or the labelled fixtures.
Threshold activation and any production ranking change remain manual decisions.
