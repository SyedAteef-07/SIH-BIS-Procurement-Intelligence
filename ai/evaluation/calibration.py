"""Analyze query-level abstention thresholds; never write production settings."""
import argparse
import json
import math
from pathlib import Path


def threshold_metrics(scores, in_domain, threshold):
    if not scores or len(scores) != len(in_domain):
        raise ValueError("Require equally sized, nonempty scores and labels")
    if not math.isfinite(threshold) or not all(math.isfinite(s) for s in scores):
        raise ValueError("Scores and threshold must be finite")
    if any(type(label) is not bool for label in in_domain) or len(set(in_domain)) != 2:
        raise ValueError("Both boolean in-domain and out-of-domain labels are required")
    # This matches the API's >= cutoff. Positive class means in-domain.
    tp = sum(score >= threshold and label for score, label in zip(scores, in_domain))
    fp = sum(score >= threshold and not label for score, label in zip(scores, in_domain))
    fn = sum(score < threshold and label for score, label in zip(scores, in_domain))
    tn = sum(score < threshold and not label for score, label in zip(scores, in_domain))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn)
    return {"threshold": threshold, "true_positive": tp, "false_positive": fp,
            "false_negative": fn, "true_negative": tn,
            "in_domain_acceptance_rate": recall, "in_domain_false_rejection_rate": fn / (tp + fn),
            "ood_rejection_rate": tn / (tn + fp), "ood_false_acceptance_rate": fp / (tn + fp),
            "precision": precision, "recall": recall,
            "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0}


def analyze_thresholds(scores, in_domain):
    # Observed unique scores cover every >= decision boundary except reject-all.
    # Include the next finite float above the maximum for that endpoint.
    threshold_metrics(scores, in_domain, 0.0)  # Validate before constructing boundaries.
    thresholds = sorted(set(scores))
    upper = math.nextafter(thresholds[-1], math.inf)
    if math.isfinite(upper):
        thresholds.append(upper)
    rows = [threshold_metrics(scores, in_domain, value) for value in thresholds]
    best_f1 = max(rows, key=lambda r: (r["f1"], r["ood_rejection_rate"], r["recall"], -r["threshold"]))
    recall_candidates = [r for r in rows if r["recall"] >= 0.95]
    rejection_candidates = [r for r in rows if r["ood_rejection_rate"] >= 0.99]
    return {
        "sample_count": len(scores), "in_domain_count": sum(in_domain),
        "out_of_domain_count": len(in_domain) - sum(in_domain),
        "positive_class": "in_domain", "acceptance_rule": "top reranker score >= threshold",
        "selection_policy": "Max-F1 ties prefer OOD rejection then recall; recall-constrained selection maximizes OOD rejection; OOD-constrained selection maximizes recall. Remaining ties prefer the smallest threshold.",
        "candidates": {
            "maximum_f1": best_f1,
            "in_domain_recall_at_least_95_percent": max(recall_candidates, key=lambda r: (r["ood_rejection_rate"], r["f1"], -r["threshold"])) if recall_candidates else None,
            "ood_rejection_at_least_99_percent": max(rejection_candidates, key=lambda r: (r["recall"], r["f1"], -r["threshold"])) if rejection_candidates else None,
        },
        "thresholds": rows,
        "limitations": "Exploratory fit on the reported synthetic queries, not held-out calibration. Binary domain detection does not guarantee correct top-ranked standards. Production settings are not modified.",
    }


def calibrate_query_scores(rows, field="top_reranker_score"):
    if not rows or any(row.get(field) is None for row in rows):
        raise ValueError("Every query needs a top score for calibration")
    return analyze_thresholds([row[field] for row in rows], [row["in_domain"] for row in rows])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="JSON from evaluation.evaluate")
    parser.add_argument("--score-field", choices=["top_reranker_score", "top_hybrid_reranker_score"], default="top_hybrid_reranker_score")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    result = calibrate_query_scores(report["query_scores"], args.score_field)
    print(json.dumps(result["candidates"], indent=2))
    if args.output:
        if args.output.resolve() == args.report.resolve():
            parser.error("Calibration output must not overwrite the evaluation input report")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, allow_nan=False), encoding="utf-8")


if __name__ == "__main__":
    main()
