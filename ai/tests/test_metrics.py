from math import log2
import pytest
from evaluation.metrics import recall_at_k, precision_at_k, reciprocal_rank, ndcg_at_k


def test_ranking_metrics_have_known_values():
    predicted = ["wrong", "a", "b"]
    assert recall_at_k(predicted, ["a", "b"], 1) == 0
    assert recall_at_k(predicted, ["a", "b"], 2) == 0.5
    assert recall_at_k(predicted, ["a", "b"], 3) == 1
    assert precision_at_k(predicted, ["a", "b"], 5) == 0.4
    assert reciprocal_rank(predicted, ["a", "b"]) == 0.5
    expected = (7 / log2(3) + 3 / log2(4)) / (7 + 3 / log2(3))
    assert ndcg_at_k(predicted, {"a": 3, "b": 2}, 5) == pytest.approx(expected)


def test_duplicates_short_lists_and_empty_relevance():
    assert recall_at_k(["a", "a"], ["a", "b"], 5) == 0.5
    assert precision_at_k(["a", "a"], ["a"], 5) == 0.2
    assert ndcg_at_k(["a", "a"], {"a": 3}, 5) == 1
    assert recall_at_k(["x"], [], 5) == 0
    assert reciprocal_rank([], ["a"]) == 0
    assert ndcg_at_k(["x"], {}, 5) == 0


@pytest.mark.parametrize("function,args", [
    (recall_at_k, ([], [], 0)), (precision_at_k, ([], [], -1)),
    (ndcg_at_k, ([], {}, 0)), (ndcg_at_k, ([], {"a": -1}, 5)),
])
def test_invalid_metric_arguments(function, args):
    with pytest.raises(ValueError):
        function(*args)
