import pytest
from app.config import Settings
from app.retrieval.bm25_store import BM25Store, tokenize
from app.retrieval.hybrid_search import HybridRetriever, reciprocal_rank_fusion
from app.retrieval.search import load_standards
from app.schemas.recommendation import Standard


def standard(identifier):
    return Standard(id=identifier, title=identifier, scope="example scope")


def test_technical_tokenization():
    assert tokenize("11kV/433V, 50Hz PVC LED IP65") == tokenize("11 kV / 433 V, 50 Hz PVC LED IP65")
    assert {"11kv", "433v", "50hz", "pvc", "led", "ip65"}.issubset(tokenize("11 kV 433 V 50 Hz PVC LED IP65"))
    assert "not" in tokenize("not suitable")


@pytest.mark.parametrize("query,expected", [
    ("transformer insulating oil", "IS-DEMO-014"),
    ("IP65 luminaire enclosure protection", "IS-DEMO-022"),
    ("33kV XLPE high voltage cable", "IS-DEMO-024"),
    ("pump mechanical shaft seals", "IS-DEMO-039"),
])
def test_bm25_near_confusers(query, expected):
    store = BM25Store(load_standards(Settings().dataset_path))
    assert store.search(query)[0][0].id == expected
    assert store.search("xyznonexistent") == []
    assert store.search("") == []


def test_empty_bm25_and_invalid_k():
    store = BM25Store([])
    assert store.search("query") == []
    with pytest.raises(ValueError):
        store.search("query", 0)


def test_rrf_uses_ranks_deduplicates_and_breaks_ties_by_id():
    a, b, c = [standard(key) for key in "abc"]
    results = reciprocal_rank_fusion([[(a, 0.99), (b, 0.1)], [(b, 1000), (c, 999)]], 3, 60)
    assert [s.id for s, _ in results] == ["b", "a", "c"]
    assert results[0][1] == pytest.approx(1 / 62 + 1 / 61)
    assert reciprocal_rank_fusion([[(a, 1), (a, 2), (b, 0)]], 5) == [(a, 1 / 61), (b, 1 / 62)]
    assert reciprocal_rank_fusion([[], []]) == []


def test_hybrid_fetches_both_retrievers():
    a, b = standard("a"), standard("b")
    class Embedder:
        def encode_query(self, query):
            assert query == "technical input"
            return [[1, 0]]
    class Vectors:
        def search(self, vector, top_k):
            assert vector == [[1, 0]] and top_k == 2
            return [(a, 0.9), (b, 0.1)]
    class Lexical:
        def search(self, query, top_k):
            assert query == "technical input" and top_k == 2
            return [(b, 5)]
    retriever = HybridRetriever(Embedder(), Vectors(), Lexical())
    assert retriever.search("technical input", 2)[0][0].id == "b"


def test_content_only_retrieval_text():
    s = Standard(id="IS-DEMO-001", title="Pump", scope="Pumps water.", abstract="High flow.", keywords=["impeller"])
    assert s.to_retrieval_text() == "Pump. Pumps water. High flow. impeller"
    assert s.document_text == s.to_retrieval_text()
    assert s.id not in s.to_retrieval_text()
