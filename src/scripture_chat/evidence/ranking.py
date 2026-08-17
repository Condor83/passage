from __future__ import annotations

from dataclasses import dataclass

from scripture_chat.domain.models import EvidenceLane, RetrievalBasis


@dataclass(frozen=True, slots=True)
class RankedCandidate:
    reference: str
    canonical_order: int
    basis: list[RetrievalBasis]


def rank_candidates(candidates: list[RankedCandidate]) -> list[RankedCandidate]:
    return sorted(candidates, key=_rank_key)


def _rank_key(candidate: RankedCandidate) -> tuple[int, float, int]:
    lexical_scores = [
        basis.raw_score
        for basis in candidate.basis
        if basis.lane is EvidenceLane.LEXICAL and basis.raw_score is not None
    ]
    if lexical_scores:
        return 0, min(lexical_scores), candidate.canonical_order
    return 1, 0.0, candidate.canonical_order
