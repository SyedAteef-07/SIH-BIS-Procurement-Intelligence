import json
import math
import pytest
from evaluation.calibration import analyze_thresholds, calibrate_query_scores, threshold_metrics
from evaluation.diagnostics import (compare_rankings, distribution, hybrid_query_stats,
                                    query_score_distributions, regression_report, summarize_hybrid)
from evaluation.evaluate import run_evaluation
from evaluation.rank_fusion import fuse_rankings
from evaluation.reporting import write_diagnostic_reports
from test_quality_api import make_engine


def query(relevant=None):
    relevant = ["a"] if relevant is None else relevant
    return {"id": "Q1", "query": "technical query", "category": "exact" if relevant else "out_of_domain",
            "relevant": relevant, "relevance": {key: 3 for key in relevant}}


@pytest.mark.parametrize("before,after,outcome,delta", [
    (["x", "a"], ["a", "x"], "improved", 1),
    (["a", "x"], ["x", "a"], "worsened", -1),
    (["a", "x"], ["a", "y"], "preserved", 0),
    (["x", "y"], ["a", "x"], "improved", 2),
    (["a", "x"], ["x", "y"], "worsened", -2),
    (["x", "y"], ["x", "z"], "preserved", 0),
])
def test_regression_rank_changes(before, after, outcome, delta):
    row = compare_rankings(query(), before, after)
    assert row["outcome"] == outcome
    assert row["rank_change"] == delta
    assert row["expected_standards"] == ["a"]
    assert row["query"] == "technical query"


def test_regression_report_excludes_ood_and_limits_largest_changes():
    rows = [compare_rankings(query(), ["x", "a"], ["a", "x"]),
            compare_rankings(query(), ["a", "x"], ["x", "a"]),
            compare_rankings(query([]), ["x"], ["y"])]
    report = regression_report(rows, limit=1)
    assert report["counts"] == {"improved": 1, "preserved": 0, "worsened": 1, "not_applicable": 1}
    assert report["largest_regressions"][0]["rank_change"] == -1
    assert rows[-1]["rank_change"] is None


def test_query_level_percentiles_and_class_counts():
    values = distribution([1, 2, 3, 4, 5])
    assert values["p05"] == pytest.approx(1.2)
    assert values["p95"] == pytest.approx(4.8)
    assert values["count"] == 5 and values["median"] == 3
    rows = [{"in_domain": flag, "top_semantic_score": value,
             "top_reranker_score": value * 2, "top_hybrid_reranker_score": value * 3}
            for flag, value in [(True, 2), (True, 3), (False, -1)]]
    summaries = query_score_distributions(rows)
    assert summaries["in_domain"]["top_reranker_score"]["count"] == 2
    assert summaries["out_of_domain"]["top_semantic_score"]["max"] == -1
    assert distribution([])["count"] == 0
    with pytest.raises(ValueError):
        distribution([math.nan])


def test_threshold_confusion_matrix_and_inclusive_boundary():
    result = threshold_metrics([0.5, 0.4, 0.5, 0.1], [True, True, False, False], 0.5)
    assert [result[key] for key in ("true_positive", "false_positive", "false_negative", "true_negative")] == [1, 1, 1, 1]
    assert result["precision"] == result["recall"] == result["f1"] == 0.5
    assert result["in_domain_false_rejection_rate"] == result["ood_false_acceptance_rate"] == 0.5


def test_threshold_sweep_covers_all_decisions_and_constraints():
    result = analyze_thresholds([0.9, 0.8, 0.2, 0.1], [True, True, False, False])
    assert result["thresholds"][0]["in_domain_acceptance_rate"] == 1
    assert result["thresholds"][0]["ood_rejection_rate"] == 0
    assert result["thresholds"][-1]["in_domain_acceptance_rate"] == 0
    assert result["thresholds"][-1]["ood_rejection_rate"] == 1
    for candidate in result["candidates"].values():
        assert candidate["threshold"] == 0.8
        assert candidate["f1"] == 1


def test_identical_scores_cannot_be_separated():
    result = analyze_thresholds([1, 1], [True, False])
    assert result["candidates"]["maximum_f1"]["ood_false_acceptance_rate"] == 1
    strict = result["candidates"]["ood_rejection_at_least_99_percent"]
    assert strict["ood_rejection_rate"] == 1 and strict["recall"] == 0


@pytest.mark.parametrize("scores,labels", [([], []), ([1], [True]), ([1, 2], [False, False]),
    ([1, 2], [True]), ([math.inf, 0], [True, False]), ([1, 2], [1, 0])])
def test_invalid_calibration_inputs(scores, labels):
    with pytest.raises(ValueError):
        analyze_thresholds(scores, labels)


def test_missing_top_scores_are_not_silently_dropped():
    with pytest.raises(ValueError):
        calibrate_query_scores([{"in_domain": True, "top_reranker_score": None}])


@pytest.mark.parametrize("weight,first", [(0, "a"), (0.5, "a"), (1, "a"), (1.5, "b"), (2, "b")])
def test_fusion_weights_and_tie_policy(weight, first):
    result = fuse_rankings(["a", "b"], ["b", "a"], weight)
    assert result[0][0] == first
    assert dict(result)["a"] == pytest.approx(1 / 61 + weight / 62)


def test_fusion_handles_duplicates_and_missing_ids():
    result = fuse_rankings(["a", "a", "b"], ["c", "b", "b"], 1)
    assert len(result) == 3 and result[0][0] == "b"
    assert fuse_rankings(["a"], ["c"], 0) == [("a", 1 / 61)]
    assert fuse_rankings([], []) == []


@pytest.mark.parametrize("weight,k", [(-1, 60), (math.nan, 60), (math.inf, 60), (1, 0), (1, math.inf)])
def test_invalid_fusion_configuration(weight, k):
    with pytest.raises(ValueError):
        fuse_rankings(["a"], ["a"], weight, k)


def test_hybrid_overlap_and_cross_encoder_overrides_order():
    row = hybrid_query_stats(["a", "b"], ["b", "c"], ["b", "a"], ["a", "b"], ["a", "b"], 20)
    assert row["faiss_only_candidate_ids"] == ["a"]
    assert row["bm25_only_candidate_ids"] == ["c"]
    assert row["overlapping_candidate_ids"] == ["b"]
    summary = summarize_hybrid([row], 20)
    assert summary["mean_overlap_at_k"] == 0.05
    assert summary["mean_jaccard"] == pytest.approx(1 / 3)
    assert summary["mean_bm25_unique_candidates_per_query"] == 1
    assert summary["hybrid_changes_top5_percent"] == 100
    assert summary["hybrid_changes_final_top5_percent"] == 0
    assert summary["erased_percent_of_rrf_changed_queries"] == 100


def test_complete_experiments_preserve_production_and_write_reports(tmp_path):
    engine = make_engine()
    settings = engine.settings
    rows = [{"id": "Q1", "query": "oil or pump", "category": "ambiguous", "relevant": ["IS-DEMO-001", "IS-DEMO-002"],
             "relevance": {"IS-DEMO-001": 3, "IS-DEMO-002": 2}},
            {"id": "Q2", "query": "wireless mouse", "category": "out_of_domain", "relevant": [], "relevance": {}}]
    before = engine.recommend("oil")
    report = run_evaluation(engine, rows, (0.5, 1.0, 1.5, 2.0))
    assert len(report["records"]) == 6 and len(report["experiment_records"]) == 18
    assert len(report["experiment_summary"]) == 9
    assert engine.settings == settings and engine.recommend("oil") == before
    assert len(report["ambiguous_queries"]) == 1
    assert len(report["ambiguous_queries"][0]["top5_by_system"]) == 12
    assert report["query_score_distributions"]["out_of_domain"]["top_reranker_score"]["count"] == 1
    assert report["experiment_configuration"]["production_configuration_changed"] is False
    write_diagnostic_reports(report, tmp_path)
    assert json.loads((tmp_path / "regressions.json").read_text())["semantic_vs_reranked"]["counts"]["not_applicable"] == 1
    assert "NDCG@5" in (tmp_path / "ambiguous_queries.txt").read_text()
    assert "semantic" in (tmp_path / "comparison.txt").read_text().lower() or "BGE" in (tmp_path / "comparison.txt").read_text()
