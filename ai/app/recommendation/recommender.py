import logging
import math
from threading import Lock
from app.config import Settings
from app.nlp.preprocess import clean_text
from app.retrieval.bm25_store import BM25Store
from app.retrieval.hybrid_search import HybridRetriever
from app.retrieval.vector_store import VectorStore
from app.schemas.recommendation import Recommendation
logger = logging.getLogger(__name__)


class RecommendationEngine:
    def __init__(self, standards, embedder, reranker, settings=None):
        self.settings = settings or Settings()
        self.embedder = embedder
        self.reranker = reranker
        self.store = VectorStore()
        self.store.add(embedder.encode([s.to_retrieval_text() for s in standards]), standards)
        self.bm25 = BM25Store(standards) if self.settings.retrieval_mode == "hybrid" else None
        self.hybrid = HybridRetriever(embedder, self.store, self.bm25, self.settings.rrf_k) if self.bm25 else None
        self._lock = Lock()

    def is_ready(self):
        return bool(self.embedder is not None and self.reranker is not None
                    and self.store.index is not None and self.store.documents
                    and self.store.index.ntotal == len(self.store.documents)
                    and (self.settings.retrieval_mode == "semantic"
                         or (self.bm25 is not None and self.bm25.index is not None
                             and len(self.bm25.documents) == len(self.store.documents))))

    def retrieve(self, query, top_k):
        if self.hybrid is not None:
            return self.hybrid.search(query, top_k)
        return self.store.search(self.embedder.encode_query(query), top_k)

    @staticmethod
    def rank_candidates(candidates, scores, score_type="cosine"):
        if len(scores) != len(candidates) or not all(math.isfinite(score) for score in scores):
            raise RuntimeError("Reranker returned invalid scores")
        results = [Recommendation(standard=s, retrieval_score=retrieval_score,
                                  retrieval_score_type=score_type, reranker_score=score,
                                  supporting_evidence=[s.scope])
                   for (s, retrieval_score), score in zip(candidates, scores)]
        return sorted(results, key=lambda r: (-r.reranker_score, -r.retrieval_score, r.standard.id))

    def recommend(self, query: str, retrieval_k: int | None = None, final_k: int | None = None):
        retrieval_k = self.settings.retrieval_k if retrieval_k is None else retrieval_k
        final_k = self.settings.final_k if final_k is None else final_k
        query = clean_text(query)
        if not query:
            raise ValueError("Query must not be empty")
        if not 1 <= final_k <= retrieval_k:
            raise ValueError("Require 1 <= final_k <= retrieval_k")
        with self._lock:
            candidates = self.retrieve(query, retrieval_k)
            logger.info("retrieval mode=%s candidates=%d reranking_count=%d", self.settings.retrieval_mode, len(candidates), len(candidates))
            scores = self.reranker.score(query, [s.to_retrieval_text() for s, _ in candidates])
        score_type = "rrf" if self.hybrid is not None else "cosine"
        results = self.rank_candidates(candidates, scores, score_type)
        threshold = self.settings.min_reranker_score
        if threshold is not None:
            results = [r for r in results if r.reranker_score >= threshold]
        results = results[:final_k]
        logger.info("recommendation final_count=%d no_match=%s", len(results), not results)
        return results


def build_engine(settings):
    from app.nlp.embeddings import EmbeddingModel
    from app.nlp.reranker import Reranker
    from app.retrieval.search import load_standards
    return RecommendationEngine(load_standards(settings.dataset_path), EmbeddingModel(settings.embedding_model, settings.device), Reranker(settings.reranker_model, settings.device), settings)
