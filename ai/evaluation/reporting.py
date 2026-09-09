"""Render reproducible diagnostic artifacts alongside the full evaluation JSON."""
import json
from pathlib import Path


def regression_lines(report):
    lines = ["Rank changes: positive means improvement; absent ranks use depth+1 for delta only.",
             "OOD queries are not applicable and excluded from improvement/regression counts."]
    for comparison, result in report["regressions"].items():
        lines.extend(["", comparison, json.dumps(result["counts"], sort_keys=True)])
        for key in ("largest_improvements", "largest_regressions"):
            lines.append(f"{key} (up to 10)")
            if not result[key]:
                lines.append("  None observed.")
            for row in result[key]:
                lines.extend([
                    f"  {row['query_id']} [{row['category']}] {row['query']}",
                    f"  Expected: {row['expected_standards']}",
                    f"  First relevant: {row['baseline_first_relevant_rank']} -> {row['comparison_first_relevant_rank']}; change={row['rank_change']:+d}",
                    f"  Baseline ranking: {row['baseline_ranking']}",
                    f"  Comparison ranking: {row['comparison_ranking']}",
                ])
    return lines


def ambiguous_lines(report):
    lines = ["Ambiguous query diagnostics: grades 3/2 are relevant, 1 is weakly related.",
             "Review NDCG@5 and Recall@5 rather than first-rank metrics alone."]
    for row in report["ambiguous_queries"]:
        lines.extend(["", f"{row['query_id']}: {row['query']}", f"Graded labels: {row['relevance']}"])
        for system, predictions in row["top5_by_system"].items():
            ranking = ", ".join(f"{p['standard_id']} (grade {p['relevance_grade']})" for p in predictions)
            metrics = row["metrics_by_system"][system]
            lines.append(f"  {system}: {ranking}")
            lines.append(f"    NDCG@5={metrics['ndcg@5']:.4f}; Recall@5={metrics['recall@5']:.4f}")
    return lines


def comparison_lines(report):
    summaries = {**report["summary"], **report["experiment_summary"]}
    titles = report["system_titles"]
    fields = ("recall@1", "recall@3", "recall@5", "mrr", "ndcg@5")
    lines = ["Ranking comparison: unfiltered; means exclude out-of-domain queries."]
    for category in next(iter(summaries.values())):
        lines.extend(["", category, f"{'System':38}" + "".join(f"{field:>12}" for field in fields)])
        for system, categories in summaries.items():
            metrics = categories[category]["metrics"]
            lines.append(f"{titles[system]:38}" + "".join(f"{metrics[field]:12.4f}" if metrics else f"{'n/a':>12}" for field in fields))
    return lines


def print_diagnostics(report):
    print(f"\nSelected evaluation-only reranker fusion weight: {report['experiment_configuration']['reranker_fusion_weight']}")
    print("\n".join(regression_lines(report)))
    print("\nHybrid overlap and ordering statistics:")
    print(json.dumps(report["hybrid_statistics"], indent=2))
    print("\nQuery-level score distributions:")
    print(json.dumps(report["query_score_distributions"], indent=2))
    print("\nExploratory threshold candidates (production unchanged):")
    for system, analysis in report["threshold_analysis"].items():
        if isinstance(analysis, dict) and "candidates" in analysis:
            print(system)
            print(json.dumps(analysis["candidates"], indent=2))
    print("\n".join(ambiguous_lines(report)))


def write_diagnostic_reports(report, directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    payloads = {
        "regressions.json": report["regressions"],
        "hybrid_diagnostics.json": {"summary": report["hybrid_statistics"], "queries": report["hybrid_diagnostics"]},
        "query_scores.json": {"distributions": report["query_score_distributions"], "queries": report["query_scores"]},
        "threshold_analysis.json": report["threshold_analysis"],
        "ambiguous_queries.json": report["ambiguous_queries"],
    }
    for name, payload in payloads.items():
        (directory / name).write_text(json.dumps(payload, indent=2, allow_nan=False), encoding="utf-8")
    for name, lines in [("comparison.txt", comparison_lines(report)),
                        ("regressions.txt", regression_lines(report)),
                        ("ambiguous_queries.txt", ambiguous_lines(report))]:
        (directory / name).write_text("\n".join(lines) + "\n", encoding="utf-8")
