import numpy as np
from sentence_transformers import SentenceTransformer
from app.config import DEFAULT_EMBEDDING_MODEL


class EmbeddingModel:
    def __init__(self, model_name=DEFAULT_EMBEDDING_MODEL, device="cpu"):
        self.model = SentenceTransformer(model_name, device=device)
        self.query_prefix = "Represent this sentence for searching relevant passages: " if model_name.startswith("BAAI/bge-") else ""

    def encode(self, texts):
        texts = list(texts)
        for text in texts:
            if len(self.model.tokenizer.encode(text, truncation=False)) > self.model.max_seq_length:
                raise ValueError("Text exceeds the embedding model token limit. Submit a shorter requirement; document chunking is not yet supported.")
        return np.asarray(self.model.encode(texts, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False), dtype="float32")

    def encode_query(self, query):
        return self.encode([self.query_prefix + query])
