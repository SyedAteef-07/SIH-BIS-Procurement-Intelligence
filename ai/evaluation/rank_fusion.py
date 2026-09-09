"""Evaluation-only fusion: no production reranking behavior is changed."""
import math
from app.config import DEFAULT_RRF_K


def fuse_rankings(base_ranking, reranker_ranking, reranker_fusion_weight=1.0, rrf_k=DEFAULT_RRF_K):
    """Weighted RRF of ID lists, deduplicated within each list, one-based ranks.

    Missing IDs contribute zero. Ties retain base rank, then reranker rank,
    then ID. In particular, weight zero preserves the base ranking exactly.
    """
    if not math.isfinite(reranker_fusion_weight) or reranker_fusion_weight < 0:
        raise ValueError("reranker_fusion_weight must be finite and nonnegative")
    if not math.isfinite(rrf_k) or rrf_k <= 0:
        raise ValueError("rrf_k must be finite and positive")
    base = list(dict.fromkeys(base_ranking))
    reranked = list(dict.fromkeys(reranker_ranking))
    base_ranks = {identifier: rank for rank, identifier in enumerate(base, 1)}
    reranker_ranks = {identifier: rank for rank, identifier in enumerate(reranked, 1)}
    scores = {identifier: 1 / (rrf_k + rank) for identifier, rank in base_ranks.items()}
    if reranker_fusion_weight:
        for identifier, rank in reranker_ranks.items():
            scores[identifier] = scores.get(identifier, 0.0) + reranker_fusion_weight / (rrf_k + rank)
    identifiers = sorted(scores, key=lambda identifier: (
        -scores[identifier], base_ranks.get(identifier, math.inf),
        reranker_ranks.get(identifier, math.inf), identifier))
    return [(identifier, scores[identifier]) for identifier in identifiers]
