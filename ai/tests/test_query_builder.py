import logging
import pytest
from app.config import Settings
from app.nlp.extractor import RequirementExtractor
from app.nlp.query_builder import QueryBuilder
from test_quality_api import make_engine
from evaluation.evaluate_enrichment import run_enrichment_evaluation, SYSTEMS


def test_preserves_query_and_skips_empty_and_negative_fields():
    text = "  pump\n15 kW. Not suitable for indoor use."
    result = QueryBuilder().build(text, RequirementExtractor().extract(text))
    assert result.startswith("pump 15 kW. Not suitable for indoor use.")
    assert "Power rating: 15 kW." in result
    assert "Installation: indoor" not in result and "Voltage:" not in result
    ood = "ergonomic office chair"
    assert QueryBuilder().build(ood, RequirementExtractor().extract(ood)) == ood


def test_budget_only_removes_added_fields_and_rejects_wrong_extraction():
    text = "pump 15 kW"
    requirements = RequirementExtractor().extract(text)
    assert QueryBuilder().build(text, requirements, token_count=len, max_tokens=len(text)) == text
    with pytest.raises(ValueError):
        QueryBuilder().build("different intent", requirements)


@pytest.mark.parametrize("enabled", [False, True])
def test_engine_uses_original_for_reranking_and_private_logging(enabled, monkeypatch, caplog):
    engine = make_engine(query_enrichment=enabled)
    retrieval, reranking = [], []
    old_retrieve, old_score = engine.retrieve, engine.reranker.score
    monkeypatch.setattr(engine, "retrieve", lambda q, k: (retrieval.append(q), old_retrieve(q, k))[1])
    monkeypatch.setattr(engine.reranker, "score", lambda q, d: (reranking.append(q), old_score(q, d))[1])
    with caplog.at_level(logging.INFO):
        engine.recommend("  secret\nwater pump 15 kW ")
    assert reranking == ["secret water pump 15 kW"]
    assert (retrieval[0] != reranking[0]) == enabled
    assert "secret" not in caplog.text
    assert "product_identified=True" in caplog.text


def test_enrichment_default_and_environment(monkeypatch):
    monkeypatch.delenv("QUERY_ENRICHMENT", raising=False)
    assert Settings().query_enrichment is False
    monkeypatch.setenv("QUERY_ENRICHMENT", "true")
    assert Settings().query_enrichment is True
    monkeypatch.setenv("QUERY_ENRICHMENT", "typo")
    with pytest.raises(ValueError):
        Settings()


def test_engine_budget_includes_bge_prefix():
    from types import SimpleNamespace
    engine = make_engine(query_enrichment=True)
    engine.embedder.query_prefix = "BGE instruction: "
    text = "pump 15 kW"
    engine.embedder.model = SimpleNamespace(
        tokenizer=SimpleNamespace(encode=lambda text, truncation: list(text)),
        max_seq_length=len(engine.embedder.query_prefix + text))
    original, _, enriched = engine.prepare_query(text)
    assert enriched == original == text


def test_controlled_evaluation_and_ood(monkeypatch):
    engine = make_engine(query_enrichment=False)
    queries = [{"id": "q1", "query": "water pump 15 kW", "category": "technical", "relevant": ["IS-DEMO-002"], "relevance": {"IS-DEMO-002": 3}},
               {"id": "q2", "query": "office chair", "category": "out_of_domain", "relevant": [], "relevance": {}}]
    calls = []
    old_score = engine.reranker.score
    monkeypatch.setattr(engine.reranker, "score", lambda q, d: (calls.append(q), old_score(q, d))[1])
    report = run_enrichment_evaluation(engine, queries)
    assert calls == [q["query"] for q in queries]
    assert set(report["summary"]) == set(SYSTEMS)
    assert len(report["records"]) == 16
    assert report["summary"]["hybrid_raw_rerank"]["overall"]["ranking_query_count"] == 1
    assert engine.settings.query_enrichment is False
    assert report["diagnostics"][1]["extracted"].get("product") is None
