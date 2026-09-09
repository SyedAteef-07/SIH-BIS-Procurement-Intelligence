"""Pure diagnostic helpers operating on saved rankings, never on model labels."""
from statistics import mean
import numpy as np
from evaluation.metrics import ndcg_at_k


def distribution(values):
    values = list(values)
    if not values:
        return {"count": 0, **{key: None for key in ("min", "p05", "p10", "median", "p90", "p95", "max")}}
    if not np.isfinite(values).all():
        raise ValueError("Score distributions require finite values")
    return {"count": len(values), "min": float(min(values)),
            "p05": float(np.percentile(values, 5)), "p10": float(np.percentile(values, 10)),
            "median": float(np.median(values)), "p90": float(np.percentile(values, 90)),
            "p95": float(np.percentile(values, 95)), "max": float(max(values))}


def first_relevant_rank(ranking, relevant):
    relevant = set(relevant)
    return next((rank for rank, identifier in enumerate(ranking, 1) if identifier in relevant), None)


def compare_rankings(query, baseline, comparison):
    expected = query["relevant"]
    before, after = first_relevant_rank(baseline, expected), first_relevant_rank(comparison, expected)
    # For the delta only, absence is assigned the same rank just below both lists.
    missing_rank = max(len(baseline), len(comparison)) + 1
    change = ((before or missing_rank) - (after or missing_rank)) if expected else None
    outcome = "not_applicable" if not expected else "improved" if change > 0 else "worsened" if change < 0 else "preserved"
    return {"query_id": query["id"], "query": query["query"], "category": query["category"],
            "expected_standards": expected, "baseline_ranking": baseline, "comparison_ranking": comparison,
            "baseline_first_relevant_rank": before, "comparison_first_relevant_rank": after,
            "missing_rank_for_delta": missing_rank, "rank_change": change, "outcome": outcome,
            "baseline_ndcg@5": ndcg_at_k(baseline, query["relevance"], 5) if expected else None,
            "comparison_ndcg@5": ndcg_at_k(comparison, query["relevance"], 5) if expected else None}


def regression_report(rows, limit=10):
    return {
        "counts": {outcome: sum(row["outcome"] == outcome for row in rows)
                   for outcome in ("improved", "preserved", "worsened", "not_applicable")},
        "largest_improvements": sorted([row for row in rows if row["outcome"] == "improved"],
                                       key=lambda row: (-row["rank_change"], row["query_id"]))[:limit],
        "largest_regressions": sorted([row for row in rows if row["outcome"] == "worsened"],
                                      key=lambda row: (row["rank_change"], row["query_id"]))[:limit],
        "queries": rows,
    }


def hybrid_query_stats(semantic, lexical, rrf, semantic_reranked, hybrid_reranked, k):
    if k < 1:
        raise ValueError("Candidate depth must be positive")
    semantic_set, lexical_set = set(semantic), set(lexical)
    overlap = semantic_set & lexical_set
    union = semantic_set | lexical_set
    return {
        "faiss_only_candidate_ids": [i for i in semantic if i not in lexical_set],
        "bm25_only_candidate_ids": [i for i in lexical if i not in semantic_set],
        "overlapping_candidate_ids": [i for i in semantic if i in overlap],
        "overlap_at_k": len(overlap) / k,
        "jaccard": len(overlap) / len(union) if union else 0.0,
        "candidate_sets_identical": semantic_set == lexical_set,
        "rrf_candidate_set_changed": set(rrf) != semantic_set,
        "hybrid_changes_top5": semantic[:5] != rrf[:5],
        "hybrid_changes_final_top5": semantic_reranked[:5] != hybrid_reranked[:5],
    }


def summarize_hybrid(rows, k):
    if not rows:
        return {"query_count": 0}
    changed = [r for r in rows if r["hybrid_changes_top5"]]
    erased = [r for r in changed if not r["hybrid_changes_final_top5"]]
    return {
        "query_count": len(rows), "candidate_depth": k,
        "overlap_definition": "Intersection of FAISS/BM25 IDs divided by configured candidate depth, even for short lists.",
        "mean_overlap_at_k": mean(r["overlap_at_k"] for r in rows),
        "mean_jaccard": mean(r["jaccard"] for r in rows),
        "mean_bm25_unique_candidates_per_query": mean(len(r["bm25_only_candidate_ids"]) for r in rows),
        "mean_faiss_unique_candidates_per_query": mean(len(r["faiss_only_candidate_ids"]) for r in rows),
        "identical_candidate_sets_percent": 100 * mean(r["candidate_sets_identical"] for r in rows),
        "rrf_candidate_set_changed_percent": 100 * mean(r["rrf_candidate_set_changed"] for r in rows),
        "hybrid_changes_top5_percent": 100 * len(changed) / len(rows),
        "hybrid_changes_final_top5_percent": 100 * mean(r["hybrid_changes_final_top5"] for r in rows),
        "rrf_top5_changes_erased_by_reranking_count": len(erased),
        "rrf_top5_changed_query_count": len(changed),
        "erased_percent_of_rrf_changed_queries": 100 * len(erased) / len(changed) if changed else None,
    }


def query_score_distributions(rows):
    fields = ("top_semantic_score", "top_reranker_score", "top_hybrid_reranker_score")
    return {group: {field: distribution(row[field] for row in rows
                    if row["in_domain"] == in_domain and row[field] is not None)
                    for field in fields}
            for group, in_domain in (("in_domain", True), ("out_of_domain", False))}
