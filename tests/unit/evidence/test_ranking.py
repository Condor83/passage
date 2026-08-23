from passage.domain.models import EvidenceLane, RetrievalBasis
from passage.evidence.ranking import RankedCandidate, rank_candidates


def test_ranking_prefers_lexical_then_score_then_canonical_order() -> None:
    candidates = [
        RankedCandidate(
            reference="bofm/1-ne/1/3",
            canonical_order=2,
            basis=[
                RetrievalBasis(
                    lane=EvidenceLane.OFFICIAL,
                    match_kind="official_reference",
                    tie_break=2,
                )
            ],
        ),
        RankedCandidate(
            reference="bofm/1-ne/1/2",
            canonical_order=1,
            basis=[
                RetrievalBasis(
                    lane=EvidenceLane.LEXICAL,
                    match_kind="terms",
                    raw_score=-1.0,
                    score_components={"bm25": -1.0},
                    tie_break=1,
                )
            ],
        ),
        RankedCandidate(
            reference="bofm/1-ne/1/1",
            canonical_order=0,
            basis=[
                RetrievalBasis(
                    lane=EvidenceLane.LEXICAL,
                    match_kind="terms",
                    raw_score=-1.0,
                    score_components={"bm25": -1.0},
                    tie_break=0,
                )
            ],
        ),
    ]

    assert [item.reference for item in rank_candidates(candidates)] == [
        "bofm/1-ne/1/1",
        "bofm/1-ne/1/2",
        "bofm/1-ne/1/3",
    ]
