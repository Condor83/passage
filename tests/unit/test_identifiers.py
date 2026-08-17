from datetime import date

import pytest
from pydantic import ValidationError

from scripture_chat.domain.identifiers import CanonicalReference
from scripture_chat.domain.models import (
    Direction,
    EvidenceLane,
    EvidenceSearchRequest,
    LexicalMode,
    LexicalSearchRequest,
    SearchFilters,
    SnapshotSelector,
    SourceApproval,
    TraversalRequest,
)


def test_canonical_reference_round_trip() -> None:
    reference = CanonicalReference.parse("bofm/1-ne/3/7-9")

    assert reference.book == "1-ne"
    assert reference.chapter == 3
    assert reference.verse == 7
    assert reference.end_verse == 9
    assert str(reference) == "bofm/1-ne/3/7-9"


@pytest.mark.parametrize(
    "value",
    [
        "1-ne/3/7",
        "bofm/first-nephi/3/7",
        "bofm/1-ne/0/7",
        "bofm/1-ne/3/9-7",
        "bofm/1-ne/3/7/extra",
    ],
)
def test_canonical_reference_rejects_invalid_or_ambiguous_forms(value: str) -> None:
    with pytest.raises(ValueError):
        CanonicalReference.parse(value)


def test_source_approval_requires_sha256_and_acquisition_record() -> None:
    approval = SourceApproval(
        source_sha256="a" * 64,
        acquisition_url="https://example.test/book-of-mormon.epub",
        acquisition_date=date(2026, 8, 16),
        edition="Current Church edition",
    )

    assert approval.language == "eng"

    with pytest.raises(ValidationError):
        SourceApproval(
            source_sha256="not-a-digest",
            acquisition_url="https://example.test/source",
            acquisition_date=date(2026, 8, 16),
            edition="Current Church edition",
        )


def test_snapshot_selector_requires_both_or_neither_identifier() -> None:
    assert SnapshotSelector().corpus_version is None
    selected = SnapshotSelector(corpus_version="corpus-1", retrieval_config="baseline-1")
    assert selected.retrieval_config == "baseline-1"

    with pytest.raises(ValidationError):
        SnapshotSelector(corpus_version="corpus-1")


def test_search_contract_defaults_and_boundaries() -> None:
    request = LexicalSearchRequest(query=" faith ")

    assert request.query == "faith"
    assert request.mode is LexicalMode.TERMS
    assert request.limit == 20
    assert request.near_distance is None

    near = LexicalSearchRequest(query="faith hope", mode=LexicalMode.NEAR)
    assert near.near_distance == 5

    with pytest.raises(ValidationError):
        LexicalSearchRequest(query="faith", mode=LexicalMode.PHRASE, near_distance=5)
    with pytest.raises(ValidationError):
        LexicalSearchRequest(query="x" * 513)
    with pytest.raises(ValidationError):
        LexicalSearchRequest(query="faith", limit=101)


def test_filter_contract_rejects_empty_duplicates_and_unknown_books() -> None:
    assert SearchFilters(books=["alma"], reference_ranges=["bofm/alma/32/21-23"])

    with pytest.raises(ValidationError):
        SearchFilters(books=[])
    with pytest.raises(ValidationError):
        SearchFilters(books=["alma", "alma"])
    with pytest.raises(ValidationError):
        SearchFilters(books=["unknown"])


def test_traversal_and_evidence_contracts_are_explicit() -> None:
    traversal = TraversalRequest(reference="bofm/alma/32/21")
    assert traversal.direction is Direction.OUTBOUND
    assert traversal.max_depth == 1
    assert traversal.max_nodes == 50
    assert traversal.include_external is True

    evidence = EvidenceSearchRequest(query="faith in Jesus Christ")
    assert evidence.lanes == [EvidenceLane.LEXICAL, EvidenceLane.OFFICIAL]
    assert evidence.official_depth == 1

    with pytest.raises(ValidationError):
        EvidenceSearchRequest(query="faith", lanes=[EvidenceLane.OFFICIAL])
    with pytest.raises(ValidationError):
        TraversalRequest(reference="bofm/alma/32/21", max_depth=4)
