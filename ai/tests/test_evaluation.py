import json
import pytest
from app.config import ROOT, Settings
from app.retrieval.search import load_standards
from evaluation.evaluate import CATEGORIES, load_queries, run_evaluation
from test_quality_api import make_engine


def test_evaluation_fixtures_are_complete_and_consistent():
    standards = load_standards(Settings().dataset_path)
    assert 30 <= len(standards) <= 50
    assert all(s.is_mock and s.id.startswith("IS-DEMO-") and s.abstract for s in standards)
    queries = load_queries(ROOT / "evaluation/queries.json", {s.id for s in standards})
    assert len(queries) >= 80
    assert len({q["query"] for q in queries}) == len(queries)
    assert {q["category"] for q in queries} == CATEGORIES


def test_runner_separates_ood_and_records_uncalibrated_scores():
    engine = make_engine()
    queries = [
        {"id": "Q1", "query": "oil", "category": "exact", "relevant": ["IS-DEMO-001"], "relevance": {"IS-DEMO-001": 3}},
        {"id": "Q2", "query": "wireless mouse", "category": "out_of_domain", "relevant": [], "relevance": {}},
    ]
    result = run_evaluation(engine, queries)
    assert len(result["records"]) == 6
    for system, categories in result["summary"].items():
        assert categories["overall"]["ranking_query_count"] == 1
        assert categories["overall"]["metrics"]["recall@1"] == 1
        assert categories["out_of_domain"]["metrics"] is None
        assert categories["out_of_domain"]["ood_return_rate"] == 1
    assert result["score_distributions"]["out_of_domain"]["count"] == 2
    assert all(record["predictions"] for record in result["records"])
    assert {p["standard_id"] for r in result["records"] for p in r["predictions"]} <= {s.id for s in engine.store.documents}


@pytest.mark.parametrize("change", [
    {"relevant": ["unknown"], "relevance": {"unknown": 3}},
    {"category": "out_of_domain"}, {"relevance": {"IS-DEMO-001": 4}},
    {"query": " "}, {"relevance": {"IS-DEMO-001": 1}},
])
def test_bad_evaluation_labels_rejected(tmp_path, change):
    query = {"id": "Q1", "query": "oil", "category": "exact", "relevant": ["IS-DEMO-001"], "relevance": {"IS-DEMO-001": 3}}
    path = tmp_path / "queries.json"
    path.write_text(json.dumps([query | change]))
    with pytest.raises(ValueError):
        load_queries(path, {"IS-DEMO-001"})
