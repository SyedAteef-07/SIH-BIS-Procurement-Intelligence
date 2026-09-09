from threading import Lock
from app.nlp.preprocess import clean_text
from app.retrieval.vector_store import VectorStore
from app.schemas.recommendation import Recommendation


class RecommendationEngine:
    def __init__(self, standards, embedder, reranker):
        self.embedder = embedder
        self.reranker = reranker
        self.store = VectorStore()
        self.store.add(embedder.encode([s.document_text for s in standards]), standards)
        self._lock = Lock()

    def recommend(self, query: str, retrieval_k: int = 20, final_k: int = 5):
        query = clean_text(query)
        if not query:
            raise ValueError("Query must not be empty")
        if not 1 <= final_k <= retrieval_k:
            raise ValueError("Require 1 <= final_k <= retrieval_k")
        with self._lock:
            candidates = self.store.search(self.embedder.encode_query(query), retrieval_k)
            scores = self.reranker.score(query, [s.document_text for s, _ in candidates])
        if len(scores) != len(candidates):
            raise RuntimeError("Reranker score count mismatch")
        results = [Recommendation(standard=s, retrieval_score=retrieval_score, reranker_score=score, supporting_evidence=[s.scope]) for (s, retrieval_score), score in zip(candidates, scores)]
        return sorted(results, key=lambda r: (-r.reranker_score, -r.retrieval_score, r.standard.id))[:final_k]


def build_engine(settings):
    from app.nlp.embeddings import EmbeddingModel
    from app.nlp.reranker import Reranker
    from app.retrieval.search import load_standards
    return RecommendationEngine(load_standards(settings.dataset_path), EmbeddingModel(settings.embedding_model, settings.device), Reranker(settings.reranker_model, settings.device))
