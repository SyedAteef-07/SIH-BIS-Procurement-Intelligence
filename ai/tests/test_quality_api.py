from dataclasses import replace
import logging
import numpy as np
import pytest
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.recommendation.recommender import RecommendationEngine
from app.schemas.recommendation import Standard


class Embedder:
    def encode(self, texts):
        return np.array([[1, 0], [0, 1]], dtype="float32")

    def encode_query(self, query):
        return [[1, 0]]


class Reranker:
    def score(self, query, documents):
        return [7.0 if "Oil" in doc else -3.0 for doc in documents]


def make_engine(**kwargs):
    standards = [Standard(id="IS-DEMO-001", title="Oil", scope="Insulating oil"),
                 Standard(id="IS-DEMO-002", title="Pump", scope="Water pump")]
    return RecommendationEngine(standards, Embedder(), Reranker(), Settings(**kwargs))


def test_no_match_threshold_boundary_and_disabled_state(caplog):
    for threshold, count, reliable in [(None, 2, None), (7.0, 1, True), (7.01, 0, False)]:
        engine = make_engine(min_reranker_score=threshold)
        with TestClient(create_app(engine)) as client, caplog.at_level(logging.INFO):
            response = client.post("/recommend", json={"text": "confidential tender phrase", "top_k": 2})
            assert response.status_code == 200
            body = response.json()
            assert len(body["recommendations"]) == count
            assert body["has_reliable_match"] is reliable
            if not count:
                assert body["match_status"] == "NO_RELIABLE_MATCH"
                assert body["warning"]
    assert "confidential tender phrase" not in caplog.text
    assert "query_length=" in caplog.text


@pytest.mark.parametrize("query", ["ergonomic office chair", "wireless mouse", "coffee machine", "laptop docking station"])
def test_ood_queries_are_accepted_without_fabricated_standards(query):
    engine = make_engine(min_reranker_score=None)
    with TestClient(create_app(engine)) as client:
        body = client.post("/recommend", json={"text": query}).json()
        assert body["has_reliable_match"] is None
        assert body["match_status"] == "NOT_ASSESSED"
        assert {r["standard"]["id"] for r in body["recommendations"]} <= {s.id for s in engine.store.documents}
        assert all(isinstance(r["reranker_score"], float) for r in body["recommendations"])


def test_liveness_is_independent_of_readiness():
    engine = make_engine()
    with TestClient(create_app(engine)) as client:
        assert client.get("/health").json() == {"status": "ok"}
        assert client.get("/ready").json() == {"status": "ready", "standards_count": 2, "retrieval_mode": "hybrid"}
        engine.bm25.index = None
        assert client.get("/ready").status_code == 503
        assert client.get("/health").status_code == 200
        assert client.post("/recommend", json={"text": "oil"}).status_code == 503


@pytest.mark.parametrize("component", ["embedder", "reranker", "index", "dataset"])
def test_readiness_checks_all_required_components(component):
    engine = make_engine(retrieval_mode="semantic")
    with TestClient(create_app(engine)) as client:
        if component == "index":
            engine.store.index.reset()
        elif component == "dataset":
            engine.store.documents.clear()
        else:
            setattr(engine, component, None)
        assert client.get("/ready").status_code == 503


def test_configured_final_k_and_semantic_mode():
    engine = make_engine(retrieval_mode="semantic", final_k=1)
    with TestClient(create_app(engine)) as client:
        result = client.post("/recommend", json={"text": "oil"}).json()
        assert len(result["recommendations"]) == 1
        assert result["recommendations"][0]["retrieval_score_type"] == "cosine"
        assert len(client.post("/recommend", json={"text": "oil", "top_k": 2}).json()["recommendations"]) == 2


def test_reranker_overrides_fused_order():
    engine = make_engine()
    # Pump is promoted by the lexical search; Oil still wins on cross-encoder score.
    result = engine.recommend("pump")
    assert result[0].standard.title == "Oil"
    assert result[0].retrieval_score_type == "rrf"


@pytest.mark.parametrize("kwargs", [{"retrieval_mode": "unknown"}, {"rrf_k": 0}, {"final_k": 0},
    {"final_k": 51}, {"retrieval_k": 2, "final_k": 5}, {"min_reranker_score": float("nan")}, {"min_reranker_score": float("inf")}])
def test_invalid_configuration(kwargs):
    with pytest.raises(ValueError):
        Settings(**kwargs)


def test_configuration_reads_environment_at_instantiation(monkeypatch):
    monkeypatch.setenv("RETRIEVAL_MODE", "semantic")
    monkeypatch.setenv("MIN_RERANKER_SCORE", "null")
    monkeypatch.setenv("FINAL_K", "3")
    assert Settings().retrieval_mode == "semantic"
    assert Settings().final_k == 3
    assert Settings().min_reranker_score is None
    monkeypatch.setenv("MIN_RERANKER_SCORE", "-2.5")
    assert Settings().min_reranker_score == -2.5


def test_errors_are_logged_without_tender_text(caplog):
    engine = make_engine()
    class BrokenReranker:
        def score(self, query, documents):
            raise RuntimeError(query)
    engine.reranker = BrokenReranker()
    with TestClient(create_app(engine)) as client, caplog.at_level(logging.INFO):
        response = client.post("/recommend", json={"text": "secret purchasing details"})
        assert response.status_code == 500
    assert "secret purchasing details" not in caplog.text
    assert "RuntimeError" in caplog.text
