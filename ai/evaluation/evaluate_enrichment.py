"""Controlled raw versus rule-enriched retrieval, with the same original CE query."""
import argparse
from collections import Counter
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from app.config import ROOT, Settings
from app.recommendation.recommender import build_engine
from app.retrieval.hybrid_search import reciprocal_rank_fusion
from evaluation.evaluate import aggregate, load_queries, query_metrics, print_comparison
from evaluation.diagnostics import compare_rankings

SYSTEMS = {f"{base}_{variant}{suffix}": f"{base} {variant}{' + CE' if suffix else ''}"
           for base in ("semantic", "hybrid") for variant in ("raw", "enriched") for suffix in ("", "_rerank")}


def run_enrichment_evaluation(engine, queries):
    if engine.bm25 is None:
        raise ValueError("Enrichment evaluation requires a hybrid engine")
    records, comparisons, diagnostics = [], [], []
    seen_categories = Counter()
    settings = engine.settings
    for number, row in enumerate(queries, 1):
        original, extracted, enriched = engine.prepare_query(row["query"], use_enrichment=True)
        candidates = {}
        for variant, text in (("raw", original), ("enriched", enriched)):
            semantic = engine.store.search(engine.embedder.encode_query(text), settings.retrieval_k)
            lexical = engine.bm25.search(text, settings.retrieval_k)
            candidates[f"semantic_{variant}"] = semantic
            candidates[f"hybrid_{variant}"] = reciprocal_rank_fusion([semantic, lexical], settings.retrieval_k, settings.rrf_k)
        # The union is scored once, without using relevance labels to select candidates.
        union = {s.id: s for pairs in candidates.values() for s, _ in pairs}
        scores = engine.reranker.score(original, [s.to_retrieval_text() for s in union.values()])
        if len(scores) != len(union):
            raise RuntimeError("Invalid evaluation reranker output")
        score_map = dict(zip(union, scores))
        rankings = {}
        for system, pairs in candidates.items():
            ranked = engine.rank_candidates(pairs, [score_map[s.id] for s, _ in pairs],
                                            "rrf" if system.startswith("hybrid") else "cosine")
            rankings[system] = [s.id for s, _ in pairs]
            rankings[system + "_rerank"] = [r.standard.id for r in ranked]
            for suffix, top_score in (("", pairs[0][1] if pairs else None),
                                      ("_rerank", ranked[0].reranker_score if ranked else None)):
                ids = rankings[system + suffix]
                records.append({"query_id": row["id"], "category": row["category"], "system": system + suffix,
                                "metrics": query_metrics(ids, row), "predictions": ids[:settings.final_k],
                                "accepted_ids": ids[:settings.final_k], "top_score": top_score})
        changes = {}
        for base in ("semantic", "hybrid"):
            for suffix in ("", "_rerank"):
                change = compare_rankings(row, rankings[f"{base}_raw{suffix}"], rankings[f"{base}_enriched{suffix}"])
                # Keep ranks/metrics, but avoid repeating full query and twenty-item lists.
                changes[base + suffix] = {k: v for k, v in change.items()
                                           if k not in {"query", "baseline_ranking", "comparison_ranking"}}
        comparisons.append({"query_id": row["id"], "changes": changes})
        seen_categories[row["category"]] += 1
        regressed = any(c["outcome"] == "worsened" or (
            c["baseline_ndcg@5"] is not None and c["comparison_ndcg@5"] < c["baseline_ndcg@5"])
                        for c in changes.values())
        if seen_categories[row["category"]] <= 2 or (regressed and len(diagnostics) < 20):
            diagnostics.append({"query_id": row["id"], "original_query": row["query"],
                                "extracted": extracted.model_dump(exclude_none=True, exclude_defaults=True),
                                "enriched_query": enriched, "top5": {k: v[:5] for k, v in rankings.items()},
                                "changes": changes})
        if number % 10 == 0:
            print(f"Evaluated {number}/{len(queries)} queries", flush=True)
    return {"summary": aggregate(records, SYSTEMS), "records": records,
            "comparisons": comparisons, "diagnostics": diagnostics}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queries", type=Path, default=ROOT / "evaluation/queries.json")
    parser.add_argument("--output", type=Path, default=ROOT / "evaluation/results/nlp_enrichment.json")
    args = parser.parse_args()
    settings = replace(Settings(), retrieval_mode="hybrid", min_reranker_score=None, query_enrichment=False)
    print("Loading existing BGE and CrossEncoder models...", flush=True)
    engine = build_engine(settings)
    queries = load_queries(args.queries, {s.id for s in engine.store.documents})
    report = run_enrichment_evaluation(engine, queries)
    report["metadata"] = {"created_at": datetime.now(timezone.utc).isoformat(),
                          "embedding_model": settings.embedding_model, "reranker_model": settings.reranker_model,
                          "retrieval_k": settings.retrieval_k, "final_k": settings.final_k, "rrf_k": settings.rrf_k,
                          "min_reranker_score": None, "production_defaults_changed": False,
                          "standards_count": len(engine.store.documents), "query_count": len(queries),
                          "dataset_sha256": hashlib.sha256(settings.dataset_path.read_bytes()).hexdigest(),
                          "queries_sha256": hashlib.sha256(args.queries.read_bytes()).hexdigest(),
                          "policy": "Same indexes, models, depths, original cleaned CE query and unfiltered rankings. MRR uses all retrieved candidates; OOD excluded from ranking averages. Fictional dataset and authored synthetic queries; no held-out generalization claim."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False), encoding="utf-8")
    args.output.with_name(args.output.stem + "_diagnostics.json").write_text(
        json.dumps(report["diagnostics"], indent=2, allow_nan=False), encoding="utf-8")
    print_comparison(report["summary"], SYSTEMS)
    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()
