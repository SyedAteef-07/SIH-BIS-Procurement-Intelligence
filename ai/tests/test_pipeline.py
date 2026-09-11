import numpy as np
import pytest
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.recommendation.recommender import RecommendationEngine
from app.retrieval.search import load_standards
from app.retrieval.vector_store import VectorStore


class FakeEmbedder:
    def encode(self, texts):
        return np.array([[1, 0], [0.8, 0.6]], dtype="float32")

    def encode_query(self, query):
        return [[1, 0]]


class FakeReranker:
    def score(self, query, documents):
        return [1.0, 7.91]


@pytest.fixture
def engine():
    standards = load_standards(Settings().dataset_path)[:2]
    return RecommendationEngine(standards, FakeEmbedder(), FakeReranker())


def test_reranker_changes_order_preserves_evidence(engine):
    results = engine.recommend("transformer", final_k=2)
    assert [r.standard.id for r in results] == ["IS-DEMO-002", "IS-DEMO-001"]
    assert results[0].reranker_score == 7.91
    assert results[0].supporting_evidence == [results[0].standard.scope]
    assert results[0].validity == "unverified"


def test_vector_store_normalization_and_small_corpus():
    store = VectorStore()
    assert store.search([[1, 0]]) == []
    store.add([[10, 0], [0, 3]], ["a", "b"])
    results = store.search([[2, 0]], top_k=20)
    assert results == [("a", 1.0), ("b", 0.0)]
    with pytest.raises(ValueError):
        store.search([[0, 0]])
    with pytest.raises(ValueError):
        store.add([[1, 0, 0]], ["c"])


def test_api(engine):
    with TestClient(create_app(engine)) as client:
        assert client.get("/").json()["status"] == "ready"
        response = client.post("/recommend", json={"text": "  transformer\n", "top_k": 2})
        assert response.status_code == 200
        body = response.json()
        assert body["query"] == "transformer"
        assert len(body["recommendations"]) == 2
        assert "fictional" in body["warnings"][0]
        for payload in [{"text": " \n"}, {"text": "\u200b"}, {"text": "x", "top_k": 0}, {"text": "x", "top_k": 51}, {"text": "x" * 2001}, {}]:
            assert client.post("/recommend", json=payload).status_code == 422


def test_invalid_dataset(tmp_path):
    path = tmp_path / "standards.json"
    path.write_text("[]")
    with pytest.raises(ValueError, match="empty"):
        load_standards(path)
    path.write_text('[{"id":"a","title":"A","scope":"scope"},{"id":"a","title":"B","scope":"scope"}]')
    with pytest.raises(ValueError, match="duplicate"):
        load_standards(path)
