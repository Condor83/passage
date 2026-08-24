import asyncio
import sqlite3

import pytest

from passage.db.contracts import LexicalQuery
from passage.db.repository import CorpusRepository
from passage.domain.errors import InvalidQueryError, PassageNotFoundError
from passage.domain.models import (
    ContextRequest,
    Direction,
    EvidenceSearchRequest,
    LexicalMode,
    LexicalSearchRequest,
    PassageRequest,
    SnapshotRequest,
    TraversalRequest,
)
from passage.evidence.service import EvidenceService


def test_metadata_lookup_and_context_pin_one_snapshot(service: EvidenceService) -> None:
    metadata = service.get_corpus(SnapshotRequest())
    lookup = service.get_passage(PassageRequest(reference="bofm/1-ne/1/2"))
    context = service.get_context(ContextRequest(reference="bofm/1-ne/1/3", before=2, after=1))

    assert metadata.edition == "Current Church edition"
    assert lookup.records[0].passage.text == "Faith is things hoped for."
    assert [item.reference for item in context.records[0].context] == [
        "bofm/1-ne/1/1",
        "bofm/1-ne/1/2",
        "bofm/1-ne/1/4",
    ]
    assert {
        lookup.corpus_version,
        context.corpus_version,
        lookup.records[0].corpus_version,
        context.records[0].corpus_version,
    } == {metadata.corpus_version}


@pytest.mark.parametrize(
    ("mode", "query", "expected"),
    [
        (LexicalMode.PHRASE, "Faith hope", ["bofm/1-ne/1/1"]),
        (LexicalMode.TERMS, "faith charity", ["bofm/1-ne/1/1"]),
        (
            LexicalMode.PREFIX,
            "faith",
            ["bofm/1-ne/1/1", "bofm/2-ne/1/1", "bofm/2-ne/1/2", "bofm/1-ne/1/2"],
        ),
        (LexicalMode.NEAR, "faith charity", ["bofm/1-ne/1/1"]),
    ],
)
def test_lexical_modes_expose_basis(
    service: EvidenceService,
    mode: LexicalMode,
    query: str,
    expected: list[str],
) -> None:
    response = service.search_lexical(LexicalSearchRequest(query=query, mode=mode))

    assert [record.passage.reference for record in response.records] == expected
    assert all(record.basis[0].match_kind == mode.value for record in response.records)
    assert all("bm25" in record.basis[0].score_components for record in response.records)


def test_lexical_filters_intersect_and_cursor_is_request_bound(
    service: EvidenceService,
) -> None:
    first = service.search_lexical(LexicalSearchRequest(query="faith", limit=1))
    second = service.search_lexical(
        LexicalSearchRequest(query="faith", limit=1, cursor=first.completeness.cursor)
    )
    filtered = service.search_lexical(
        LexicalSearchRequest(
            query="faith",
            filters={"books": ["2-ne"], "reference_ranges": ["bofm/2-ne/1/2"]},
        )
    )

    assert first.completeness.truncated is True
    assert first.completeness.cursor is not None
    assert first.records[0].passage.reference != second.records[0].passage.reference
    assert [record.passage.reference for record in filtered.records] == ["bofm/2-ne/1/2"]
    with pytest.raises(InvalidQueryError, match="cursor"):
        service.search_lexical(
            LexicalSearchRequest(query="hope", limit=1, cursor=first.completeness.cursor)
        )


def test_traversal_is_bounded_cycle_safe_and_keeps_external_targets(
    service: EvidenceService,
) -> None:
    response = service.traverse_references(
        TraversalRequest(
            reference="bofm/1-ne/1/1",
            direction=Direction.OUTBOUND,
            max_depth=2,
            max_nodes=2,
        )
    )

    assert [record.passage.reference for record in response.records] == [
        "bofm/1-ne/1/1",
        "bofm/1-ne/1/2",
    ]
    assert response.external_targets[0].work == "bible"
    assert {edge.target.kind for edge in response.official_edges} == {"internal", "external"}
    assert all(edge.grammar_version == "official-reference-v1" for edge in response.official_edges)
    assert all(edge.source_spans for edge in response.official_edges)
    assert response.completeness.truncated is True
    assert response.completeness.frontier == ["bofm/1-ne/1/3"]


def test_evidence_search_combines_lexical_and_official_basis(
    service: EvidenceService,
) -> None:
    response = service.search_evidence(EvidenceSearchRequest(query="faith charity"))

    assert [record.passage.reference for record in response.records] == [
        "bofm/1-ne/1/1",
        "bofm/1-ne/1/2",
    ]
    assert response.records[0].basis[0].lane.value == "lexical"
    assert response.records[1].basis[0].lane.value == "official"
    assert {edge.target.kind for edge in response.official_edges} == {"internal", "external"}
    assert all(edge.source_spans for edge in response.official_edges)
    assert response.applied["lanes"] == ["lexical", "official"]


def test_empty_search_is_success(service: EvidenceService) -> None:
    response = service.search_lexical(LexicalSearchRequest(query="unfindable"))

    assert response.records == []
    assert response.completeness.truncated is False


def test_service_passes_structured_lexical_intent_to_repository(
    service: EvidenceService,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: list[LexicalQuery] = []
    original = CorpusRepository.search_lexical

    def record_query(
        repository: CorpusRepository,
        query: LexicalQuery,
        filters,
        after: tuple[float, int] | None,
        limit: int,
    ):
        observed.append(query)
        return original(repository, query, filters, after, limit)

    monkeypatch.setattr(CorpusRepository, "search_lexical", record_query)

    service.search_lexical(
        LexicalSearchRequest(query="faith hope", mode=LexicalMode.NEAR, near_distance=3)
    )
    service.search_evidence(EvidenceSearchRequest(query="faith hope"))

    assert observed == [
        LexicalQuery("faith hope", LexicalMode.NEAR, 3),
        LexicalQuery("faith hope", LexicalMode.TERMS),
    ]


def test_sqlite_adapter_translates_invalid_filter_range(
    service: EvidenceService,
) -> None:
    with pytest.raises(InvalidQueryError, match="outside the corpus"):
        service.search_lexical(
            LexicalSearchRequest(
                query="faith",
                filters={"reference_ranges": ["bofm/alma/1/1"]},
            )
        )


def test_pinned_snapshot_closes_repository_after_normal_completion(
    service: EvidenceService,
) -> None:
    with service.snapshots.pin(SnapshotRequest()) as snapshot:
        connection = snapshot.repository.connection
        assert snapshot.repository.passage_count() > 0

    with pytest.raises(sqlite3.ProgrammingError):
        connection.execute("SELECT 1")


def test_pinned_snapshot_closes_repository_after_domain_failure(
    service: EvidenceService,
) -> None:
    with (
        pytest.raises(PassageNotFoundError),
        service.snapshots.pin(SnapshotRequest()) as snapshot,
    ):
        connection = snapshot.repository.connection
        snapshot.repository.get_passage("bofm/1-ne/1/99")

    with pytest.raises(sqlite3.ProgrammingError):
        connection.execute("SELECT 1")


def test_pinned_snapshot_closes_repository_after_cancellation(
    service: EvidenceService,
) -> None:
    with (
        pytest.raises(asyncio.CancelledError),
        service.snapshots.pin(SnapshotRequest()) as snapshot,
    ):
        connection = snapshot.repository.connection
        raise asyncio.CancelledError

    with pytest.raises(sqlite3.ProgrammingError):
        connection.execute("SELECT 1")
