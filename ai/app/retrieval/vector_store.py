import faiss
import numpy as np


class VectorStore:
    def __init__(self):
        self.index = None
        self.documents = []

    @staticmethod
    def _vectors(values):
        values = np.array(values, dtype="float32", order="C", copy=True)
        if values.ndim != 2 or not np.isfinite(values).all() or np.any(np.linalg.norm(values, axis=1) == 0):
            raise ValueError("Expected finite, nonzero two-dimensional vectors")
        faiss.normalize_L2(values)
        return values

    def add(self, embeddings, documents):
        vectors = self._vectors(embeddings)
        if len(vectors) != len(documents) or not documents:
            raise ValueError("Embeddings must match a nonempty document list")
        if self.index is None:
            self.index = faiss.IndexFlatIP(vectors.shape[1])
        if vectors.shape[1] != self.index.d:
            raise ValueError("Embedding dimension mismatch")
        self.index.add(vectors)
        self.documents.extend(documents)

    def search(self, query_embedding, top_k=20):
        if top_k < 1:
            raise ValueError("top_k must be positive")
        if self.index is None:
            return []
        query = self._vectors(query_embedding)
        if query.shape != (1, self.index.d):
            raise ValueError("Expected one query with the index dimension")
        scores, indices = self.index.search(query, min(top_k, len(self.documents)))
        return [(self.documents[int(i)], float(score)) for i, score in zip(indices[0], scores[0]) if i >= 0]
