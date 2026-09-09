import numpy as np
from sentence_transformers import CrossEncoder
from torch import nn


class Reranker:
    def __init__(self, model_name="cross-encoder/ms-marco-MiniLM-L-6-v2", device="cpu"):
        self.model = CrossEncoder(model_name, device=device, activation_fn=nn.Identity())

    def score(self, query, documents):
        if not documents:
            return []
        scores = np.asarray(self.model.predict([(query, document) for document in documents], show_progress_bar=False)).reshape(-1)
        if len(scores) != len(documents) or not np.isfinite(scores).all():
            raise RuntimeError("Reranker returned invalid scores")
        return scores.tolist()
