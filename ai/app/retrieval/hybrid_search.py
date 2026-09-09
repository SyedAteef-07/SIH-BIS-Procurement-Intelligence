from app.config import DEFAULT_RETRIEVAL_K, DEFAULT_RRF_K


def reciprocal_rank_fusion(rankings, top_k=DEFAULT_RETRIEVAL_K, rrf_k=DEFAULT_RRF_K):
    """Fuse one-based ranks; raw component scores are never mixed."""
    if top_k < 1 or rrf_k < 1:
        raise ValueError("top_k and rrf_k must be positive")
    documents, scores = {}, {}
    for ranking in rankings:
        seen = set()
        for document, _ in ranking:
            if document.id in seen:
                continue
            seen.add(document.id)
            rank = len(seen)
            documents[document.id] = document
            scores[document.id] = scores.get(document.id, 0.0) + 1 / (rrf_k + rank)
    ids = sorted(scores, key=lambda identifier: (-scores[identifier], identifier))[:top_k]
    return [(documents[identifier], scores[identifier]) for identifier in ids]


class HybridRetriever:
    def __init__(self, embedder, vector_store, bm25_store, rrf_k=DEFAULT_RRF_K):
        self.embedder = embedder
        self.vector_store = vector_store
        self.bm25_store = bm25_store
        self.rrf_k = rrf_k

    def search(self, query: str, top_k: int = DEFAULT_RETRIEVAL_K):
        semantic = self.vector_store.search(self.embedder.encode_query(query), top_k)
        lexical = self.bm25_store.search(query, top_k)
        return reciprocal_rank_fusion([semantic, lexical], top_k, self.rrf_k)
