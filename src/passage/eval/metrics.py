from __future__ import annotations

import math


def evaluate_ranking(
    ranked_references: list[str],
    judgments: dict[str, int],
    depths: list[int],
) -> dict[str, float]:
    relevant_total = sum(grade > 0 for grade in judgments.values())
    metrics: dict[str, float] = {}
    for depth in depths:
        observed = ranked_references[:depth]
        grades = [judgments.get(reference, 0) for reference in observed]
        relevant = sum(grade > 0 for grade in grades)
        metrics[f"precision_at_{depth}"] = relevant / depth
        metrics[f"recall_at_{depth}"] = relevant / relevant_total if relevant_total else 0.0
        metrics[f"ndcg_at_{depth}"] = _ndcg(grades, judgments, depth)
    metrics["mrr"] = next(
        (
            1.0 / rank
            for rank, reference in enumerate(ranked_references, start=1)
            if judgments.get(reference, 0) > 0
        ),
        0.0,
    )
    return metrics


def _ndcg(grades: list[int], judgments: dict[str, int], depth: int) -> float:
    actual = _discounted_gain(grades)
    ideal_grades = sorted(judgments.values(), reverse=True)[:depth]
    ideal = _discounted_gain(ideal_grades)
    return actual / ideal if ideal else 0.0


def _discounted_gain(grades: list[int]) -> float:
    return sum(((2**grade) - 1) / math.log2(rank + 1) for rank, grade in enumerate(grades, start=1))
