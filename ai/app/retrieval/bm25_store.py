"""Local BM25 with identical technical tokenization for documents and queries."""
import re
from rank_bm25 import BM25Okapi
from app.config import DEFAULT_RETRIEVAL_K
from app.nlp.preprocess import clean_text


def tokenize(text: str) -> list[str]:
    text = clean_text(text).casefold()
    # Align 11kV with 11 kV, and retain IP65, PVC, LED and decimal quantities.
    text = re.sub(r"(?<=\d)(?=(?:kv|kva|kw|hz|mm|mpa|v|a|w)\b)", " ", text)
    tokens = re.findall(r"\d+(?:\.\d+)?|[^\W\d_]+\d*", text)
    quantities = [tokens[i] + tokens[i + 1] for i in range(len(tokens) - 1)
                  if re.fullmatch(r"\d+(?:\.\d+)?", tokens[i])
                  and tokens[i + 1] in {"kv", "v", "kva", "kw", "w", "a", "hz", "mm", "mpa"}]
    return tokens + quantities


class BM25Store:
    def __init__(self, documents):
        self.documents = list(documents)
        if len({d.id for d in self.documents}) != len(self.documents):
            raise ValueError("Duplicate standard IDs in BM25 corpus")
        corpus = [tokenize(d.to_retrieval_text()) for d in self.documents]
        self.token_sets = [set(tokens) for tokens in corpus]
        self.index = BM25Okapi(corpus) if corpus and any(corpus) else None

    def search(self, query: str, top_k: int = DEFAULT_RETRIEVAL_K):
        if top_k < 1:
            raise ValueError("top_k must be positive")
        tokens = tokenize(query)
        if self.index is None or not tokens:
            return []
        scores = self.index.get_scores(tokens)
        # Do not contribute arbitrary zero-overlap documents to RRF. Retain
        # matching documents even when Okapi IDF is zero/negative in tiny corpora.
        matches = [(doc, float(scores[i])) for i, doc in enumerate(self.documents)
                   if self.token_sets[i].intersection(tokens)]
        return sorted(matches, key=lambda item: (-item[1], item[0].id))[:top_k]
