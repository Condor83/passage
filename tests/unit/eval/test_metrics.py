import pytest

from passage.eval.metrics import evaluate_ranking


def test_metrics_match_hand_checked_ranking() -> None:
    metrics = evaluate_ranking(
        ranked_references=["a", "b", "c"],
        judgments={"a": 3, "b": 0, "c": 1, "d": 2},
        depths=[1, 3],
    )

    assert metrics["precision_at_1"] == 1.0
    assert metrics["precision_at_3"] == pytest.approx(2 / 3)
    assert metrics["recall_at_1"] == pytest.approx(1 / 3)
    assert metrics["recall_at_3"] == pytest.approx(2 / 3)
    assert metrics["mrr"] == 1.0
    assert metrics["ndcg_at_1"] == 1.0
    assert 0.0 < metrics["ndcg_at_3"] < 1.0


def test_empty_ranking_has_zero_metrics() -> None:
    metrics = evaluate_ranking([], {"a": 1}, depths=[1, 5])

    assert metrics == {
        "precision_at_1": 0.0,
        "recall_at_1": 0.0,
        "ndcg_at_1": 0.0,
        "precision_at_5": 0.0,
        "recall_at_5": 0.0,
        "ndcg_at_5": 0.0,
        "mrr": 0.0,
    }
