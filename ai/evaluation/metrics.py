"""Ranking metrics. Empty relevance yields zero; runners exclude OOD from means."""
from math import log2


def _check_k(k):
    if k < 1:
        raise ValueError("k must be positive")


def recall_at_k(predicted, relevant, k):
    _check_k(k)
    relevant = set(relevant)
    return len(set(predicted[:k]) & relevant) / len(relevant) if relevant else 0.0


def precision_at_k(predicted, relevant, k):
    _check_k(k)
    # Missing ranks count as non-relevant, so short lists cannot inflate P@K.
    return len(set(predicted[:k]) & set(relevant)) / k


def reciprocal_rank(predicted, relevant):
    relevant = set(relevant)
    return next((1 / rank for rank, identifier in enumerate(predicted, 1)
                 if identifier in relevant), 0.0)


def ndcg_at_k(predicted, relevance_map, k):
    _check_k(k)
    if any(grade < 0 for grade in relevance_map.values()):
        raise ValueError("Relevance grades must be nonnegative")
    seen, dcg = set(), 0.0
    for rank, identifier in enumerate(predicted[:k], 1):
        if identifier not in seen:
            dcg += (2 ** relevance_map.get(identifier, 0) - 1) / log2(rank + 1)
            seen.add(identifier)
    ideal = sum((2 ** grade - 1) / log2(rank + 1)
                for rank, grade in enumerate(sorted(relevance_map.values(), reverse=True)[:k], 1))
    return dcg / ideal if ideal else 0.0
