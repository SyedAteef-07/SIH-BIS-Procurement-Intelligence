"""python -m evaluation.evaluate --output evaluation/results/latest.json"""
import argparse
from collections import Counter
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from statistics import mean

import numpy as np

from app.config import ROOT, Settings
from app.nlp.preprocess import clean_text
from app.recommendation.recommender import build_engine
from app.retrieval.hybrid_search import reciprocal_rank_fusion
from evaluation.metrics import recall_at_k, precision_at_k, reciprocal_rank, ndcg_at_k
from evaluation.calibration import calibrate_query_scores
from evaluation.diagnostics import (compare_rankings, regression_report, hybrid_query_stats,
                                    summarize_hybrid, query_score_distributions)
from evaluation.rank_fusion import fuse_rankings

CATEGORIES = {"exact", "semantic_paraphrase", "near_confuser", "technical", "ambiguous", "out_of_domain"}
SYSTEMS = {"semantic": "BGE + FAISS", "semantic_rerank": "BGE + FAISS + Reranker", "hybrid_rerank": "Hybrid + Reranker"}
DEFAULT_FUSION_WEIGHTS = (0.5, 1.0, 1.5, 2.0)


def experiment_systems(weights):
    systems = {"hybrid": "Hybrid RRF (before reranking)"}
    for weight in weights:
        for base, title in [("semantic", "BGE"), ("hybrid", "Hybrid")]:
            systems[f"{base}_fusion_{weight:g}"] = f"{title} + CE rank fusion w={weight:g}"
    return systems


def load_queries(path, standard_ids):
    queries = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(queries, list) or not queries:
        raise ValueError("Evaluation queries must be a nonempty list")
    seen = set()
    for row in queries:
        if not isinstance(row.get("id"), str) or not row["id"] or row["id"] in seen:
            raise ValueError("Evaluation query IDs must be unique nonempty strings")
        seen.add(row["id"])
        if not isinstance(row.get("query"), str) or not clean_text(row["query"]):
            raise ValueError("Evaluation query text must not be empty")
        if row.get("category") not in CATEGORIES:
            raise ValueError("Unknown evaluation category")
        relevant, grades = row.get("relevant"), row.get("relevance")
        if not isinstance(relevant, list) or not isinstance(grades, dict):
            raise ValueError("Expected relevant list and relevance map")
        if any(type(grade) is not int or not 0 <= grade <= 3 for grade in grades.values()):
            raise ValueError("Relevance grades must be integers from 0 to 3")
        if len(set(relevant)) != len(relevant) or set(relevant) != {key for key, grade in grades.items() if grade >= 2}:
            raise ValueError("Relevant IDs must correspond exactly to grades 2 and 3")
        if not (set(relevant) | set(grades)).issubset(standard_ids):
            raise ValueError("Evaluation references unknown standards")
        if row["category"] == "out_of_domain":
            if relevant or any(grades.values()):
                raise ValueError("Out-of-domain queries cannot have relevant standards")
        elif not relevant:
            raise ValueError("In-domain queries need a relevant standard")
    return queries


def query_metrics(predicted, row):
    if not row["relevant"]:
        return None
    return {"recall@1": recall_at_k(predicted, row["relevant"], 1),
            "recall@3": recall_at_k(predicted, row["relevant"], 3),
            "recall@5": recall_at_k(predicted, row["relevant"], 5),
            "precision@5": precision_at_k(predicted, row["relevant"], 5),
            "mrr": reciprocal_rank(predicted, row["relevant"]),
            "ndcg@5": ndcg_at_k(predicted, row["relevance"], 5)}


def score_summary(values):
    if not values:
        return {"count": 0}
    return {"count": len(values), "min": min(values), "p10": float(np.percentile(values, 10)),
            "median": float(np.median(values)), "p90": float(np.percentile(values, 90)), "max": max(values)}


def aggregate(records, systems=None):
    summary = {}
    for system in (SYSTEMS if systems is None else systems):
        summary[system] = {}
        for category in ["overall"] + sorted(CATEGORIES):
            group = [r for r in records if r["system"] == system and (category == "overall" or r["category"] == category)]
            ranked = [r["metrics"] for r in group if r["metrics"] is not None]
            ood = [r for r in group if r["category"] == "out_of_domain"]
            summary[system][category] = {
                "query_count": len(group), "ranking_query_count": len(ranked),
                "metrics": {key: mean(r[key] for r in ranked) for key in ranked[0]} if ranked else None,
                "out_of_domain_count": len(ood),
                "ood_return_rate": mean(bool(r["accepted_ids"]) for r in ood) if ood else None,
                "ood_top_score_distribution": score_summary([r["top_score"] for r in ood if r["top_score"] is not None]),
            }
    return summary


def run_evaluation(engine, queries, fusion_weights=(), reranker_fusion_weight=1.0, fusion_rrf_k=None):
    """Share models/index; rerank the candidate union once per query for fairness."""
    if engine.bm25 is None:
        raise ValueError("Evaluation needs a hybrid-configured engine to compare all systems")
    records = []
    experiment_records, diagnostics, query_scores, ambiguous = [], [], [], []
    comparisons = {key: [] for key in ("semantic_vs_reranked", "semantic_vs_hybrid", "reranked_semantic_vs_reranked_hybrid")}
    distributions = {key: [] for key in ("relevant", "weakly_related", "irrelevant", "out_of_domain")}
    settings = engine.settings
    weights = sorted(set(fusion_weights))
    fusion_rrf_k = settings.rrf_k if fusion_rrf_k is None else fusion_rrf_k
    for weight in weights + [reranker_fusion_weight]:
        fuse_rankings([], [], weight, fusion_rrf_k)  # Reject invalid experiment configuration early.
    extra_systems = experiment_systems(weights)
    for number, row in enumerate(queries, 1):
        query = clean_text(row["query"])
        semantic = engine.store.search(engine.embedder.encode_query(query), settings.retrieval_k)
        lexical = engine.bm25.search(query, settings.retrieval_k)
        hybrid = reciprocal_rank_fusion([semantic, lexical], settings.retrieval_k, settings.rrf_k)
        union = {standard.id: standard for standard, _ in semantic + hybrid}
        documents = list(union.values())
        scores = engine.reranker.score(query, [s.to_retrieval_text() for s in documents])
        if len(scores) != len(documents) or not np.isfinite(scores).all():
            raise RuntimeError("Invalid evaluation reranker output")
        score_map = dict(zip(union, scores))
        for identifier, score in score_map.items():
            grade = row["relevance"].get(identifier, 0)
            label = "out_of_domain" if not row["relevant"] else "relevant" if grade >= 2 else "weakly_related" if grade == 1 else "irrelevant"
            distributions[label].append(float(score))
        query_predictions = {}
        for system in SYSTEMS:
            if system == "semantic":
                predictions = [{"standard_id": s.id, "retrieval_score": value, "reranker_score": None} for s, value in semantic]
            else:
                candidates = semantic if system == "semantic_rerank" else hybrid
                ranked = engine.rank_candidates(candidates, [score_map[s.id] for s, _ in candidates], "cosine" if system == "semantic_rerank" else "rrf")
                predictions = [{"standard_id": r.standard.id, "retrieval_score": r.retrieval_score, "reranker_score": r.reranker_score} for r in ranked]
            query_predictions[system] = predictions
            ids = [p["standard_id"] for p in predictions]
            accepted = [p["standard_id"] for p in predictions if system == "semantic" or settings.min_reranker_score is None or p["reranker_score"] >= settings.min_reranker_score][:settings.final_k]
            records.append({"query_id": row["id"], "category": row["category"], "system": system,
                            "metrics": query_metrics(ids, row), "predictions": predictions, "accepted_ids": accepted,
                            "top_score": (predictions[0]["retrieval_score"] if system == "semantic" else predictions[0]["reranker_score"]) if predictions else None})
        semantic_ids = [s.id for s, _ in semantic]
        lexical_ids = [s.id for s, _ in lexical]
        hybrid_ids = [s.id for s, _ in hybrid]
        semantic_reranked = [p["standard_id"] for p in query_predictions["semantic_rerank"]]
        hybrid_reranked = [p["standard_id"] for p in query_predictions["hybrid_rerank"]]
        query_predictions["hybrid"] = [{"standard_id": s.id, "retrieval_score": value,
                                         "reranker_score": None} for s, value in hybrid]
        # These experiments use the same candidate sets as their corresponding
        # base/CE systems; labels are only used afterwards to calculate metrics.
        for weight in weights:
            for base, base_candidates, base_ids, reranked_ids in [
                ("semantic", semantic, semantic_ids, semantic_reranked),
                ("hybrid", hybrid, hybrid_ids, hybrid_reranked),
            ]:
                base_scores = {s.id: value for s, value in base_candidates}
                fused = fuse_rankings(base_ids, reranked_ids, weight, fusion_rrf_k)
                query_predictions[f"{base}_fusion_{weight:g}"] = [
                    {"standard_id": identifier, "retrieval_score": base_scores[identifier],
                     "reranker_score": score_map[identifier], "rank_fusion_score": value}
                    for identifier, value in fused]
        for system in extra_systems:
            predictions = query_predictions[system]
            ids = [p["standard_id"] for p in predictions]
            accepted = [p["standard_id"] for p in predictions if system == "hybrid" or settings.min_reranker_score is None or p["reranker_score"] >= settings.min_reranker_score][:settings.final_k]
            experiment_records.append({"query_id": row["id"], "category": row["category"], "system": system,
                                       "metrics": query_metrics(ids, row), "predictions": predictions, "accepted_ids": accepted,
                                       "top_score": (predictions[0]["retrieval_score"] if system == "hybrid" else predictions[0]["reranker_score"]) if predictions else None})
        for name, before, after in [
            ("semantic_vs_reranked", semantic_ids, semantic_reranked),
            ("semantic_vs_hybrid", semantic_ids, hybrid_ids),
            ("reranked_semantic_vs_reranked_hybrid", semantic_reranked, hybrid_reranked),
        ]:
            comparisons[name].append(compare_rankings(row, before, after))
        diagnostics.append({"query_id": row["id"], "query": row["query"], "category": row["category"],
                            "faiss_ranking": semantic_ids, "bm25_ranking": lexical_ids,
                            "rrf_ranking": hybrid_ids, "semantic_cross_encoder_ranking": semantic_reranked,
                            "final_cross_encoder_ranking": hybrid_reranked,
                            **hybrid_query_stats(semantic_ids, lexical_ids, hybrid_ids,
                                                 semantic_reranked, hybrid_reranked, settings.retrieval_k)})
        query_scores.append({"query_id": row["id"], "query": row["query"], "category": row["category"],
                             "in_domain": bool(row["relevant"]),
                             "top_semantic_score": max((value for _, value in semantic), default=None),
                             "top_reranker_score": max((score_map[i] for i in semantic_ids), default=None),
                             "top_hybrid_reranker_score": max((score_map[i] for i in hybrid_ids), default=None)})
        if row["category"] == "ambiguous":
            ambiguous.append({"query_id": row["id"], "query": row["query"], "relevance": row["relevance"],
                              "top5_by_system": {system: [{**p, "relevance_grade": row["relevance"].get(p["standard_id"], 0)}
                                                          for p in predictions[:5]] for system, predictions in query_predictions.items()},
                              "metrics_by_system": {system: query_metrics([p["standard_id"] for p in predictions], row)
                                                    for system, predictions in query_predictions.items()}})
        if number % 10 == 0:
            print(f"Evaluated {number}/{len(queries)} queries", flush=True)
    calibration = ({"semantic_rerank": calibrate_query_scores(query_scores),
                    "hybrid_rerank": calibrate_query_scores(query_scores, "top_hybrid_reranker_score")}
                   if {row["in_domain"] for row in query_scores} == {True, False}
                   and all(row["top_reranker_score"] is not None and row["top_hybrid_reranker_score"] is not None for row in query_scores)
                   else {"status": "unavailable", "reason": "Both domain classes and finite top scores are required"})
    return {"summary": aggregate(records), "score_distributions": {key: score_summary(values) for key, values in distributions.items()}, "records": records,
            "system_titles": {**SYSTEMS, **extra_systems},
            "experiment_systems": extra_systems, "experiment_summary": aggregate(experiment_records, extra_systems),
            "experiment_records": experiment_records, "regressions": {key: regression_report(rows) for key, rows in comparisons.items()},
            "hybrid_diagnostics": diagnostics, "hybrid_statistics": summarize_hybrid(diagnostics, settings.retrieval_k),
            "query_scores": query_scores, "query_score_distributions": query_score_distributions(query_scores),
            "threshold_analysis": calibration, "ambiguous_queries": ambiguous,
            "experiment_configuration": {"fusion_weights": weights, "reranker_fusion_weight": reranker_fusion_weight,
                                         "fusion_rrf_k": fusion_rrf_k, "production_configuration_changed": False}}


def print_comparison(summary, systems=None):
    keys = ["recall@1", "recall@3", "recall@5", "precision@5", "mrr", "ndcg@5"]
    for category in ["overall"] + sorted(CATEGORIES):
        print(f"\n{category} (ranking means exclude out-of-domain queries)")
        print(f"{'System':30}" + "".join(f"{key:>13}" for key in keys))
        for system, title in (SYSTEMS if systems is None else systems).items():
            result = summary[system][category]
            metrics = result["metrics"]
            print(f"{title:30}" + "".join(f"{metrics[key]:13.4f}" if metrics else f"{'n/a':>13}" for key in keys))
            if result["out_of_domain_count"]:
                print(f"  OOD return rate: {result['ood_return_rate']:.4f} ({result['out_of_domain_count']} queries)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queries", type=Path, default=ROOT / "evaluation/queries.json")
    parser.add_argument("--output", type=Path, default=ROOT / "evaluation/results/latest.json")
    parser.add_argument("--fusion-weights", type=float, nargs="+", default=DEFAULT_FUSION_WEIGHTS)
    parser.add_argument("--reranker-fusion-weight", type=float, default=float(os.getenv("RERANKER_FUSION_WEIGHT", "1.0")),
                        help="Evaluation-only highlighted weight, also included in the sweep")
    parser.add_argument("--fusion-rrf-k", type=float, default=None)
    args = parser.parse_args()
    settings = replace(Settings(), retrieval_mode="hybrid")
    weights = sorted(set(args.fusion_weights) | {args.reranker_fusion_weight})
    try:
        for weight in weights:
            fuse_rankings([], [], weight, settings.rrf_k if args.fusion_rrf_k is None else args.fusion_rrf_k)
    except ValueError as exc:
        parser.error(str(exc))
    print("Loading models and building indexes...", flush=True)
    engine = build_engine(settings)
    queries = load_queries(args.queries, {s.id for s in engine.store.documents})
    report = run_evaluation(engine, queries, weights, args.reranker_fusion_weight, args.fusion_rrf_k)
    report["metadata"] = {
        "created_at": datetime.now(timezone.utc).isoformat(), "embedding_model": settings.embedding_model,
        "reranker_model": settings.reranker_model, "retrieval_k": settings.retrieval_k, "final_k": settings.final_k,
        "rrf_k": settings.rrf_k, "min_reranker_score": settings.min_reranker_score,
        "standards_count": len(engine.store.documents), "query_count": len(queries),
        "categories": dict(Counter(row["category"] for row in queries)),
        "dataset_sha256": hashlib.sha256(settings.dataset_path.read_bytes()).hexdigest(),
        "queries_sha256": hashlib.sha256(args.queries.read_bytes()).hexdigest(),
        "ranking_policy": "Unfiltered rankings; MRR over retrieval_k candidates; binary relevance is grade >= 2; NDCG includes grade 1.",
        "limitations": "Authored synthetic queries and fictional standards, not a held-out production benchmark. Thresholds are exploratory in-sample candidates only; production settings remain unchanged. Candidate score samples cover retrieved pairs; query_scores contain one maximum per query and system.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False), encoding="utf-8")
    print_comparison({**report["summary"], **report["experiment_summary"]}, {**SYSTEMS, **report["experiment_systems"]})
    print("\nReranker score distributions:")
    print(json.dumps(report["score_distributions"], indent=2))
    from evaluation.reporting import print_diagnostics, write_diagnostic_reports
    print_diagnostics(report)
    write_diagnostic_reports(report, args.output.parent)
    print(f"\nSaved report: {args.output}")


if __name__ == "__main__":
    main()
