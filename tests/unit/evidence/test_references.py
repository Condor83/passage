from passage.domain.models import (
    Direction,
    ExternalChapterReferenceTarget,
    InternalChapterReferenceTarget,
    ReferenceEdge,
)
from passage.evidence.references import traverse


def _edge(edge_id: str, target):
    return ReferenceEdge(
        edge_id=edge_id,
        origin_reference="bofm/1-ne/1/1",
        origin_anchor="a",
        target=target,
        source_attribution="official-footnote",
        grammar_version="official-reference-v2",
        source_spans=[{"kind": "pdf", "page": 1, "bbox": [1, 2, 3, 4], "order": 0}],
    )


def test_traversal_returns_external_sections_without_expanding_them() -> None:
    edge = _edge(
        "external-section",
        ExternalChapterReferenceTarget(
            work="dc",
            book="section",
            chapter=138,
            unit="section",
        ),
    )

    result = traverse(
        [edge],
        "bofm/1-ne/1/1",
        Direction.OUTBOUND,
        max_depth=1,
        max_nodes=10,
        include_external=True,
    )

    assert [node.reference for node in result.nodes] == ["bofm/1-ne/1/1"]
    assert result.external_targets == [edge.target]
    assert result.official_edges == [edge]


def test_traversal_keeps_internal_chapter_ranges_as_edges_without_verse_expansion() -> None:
    edge = _edge(
        "internal-chapters",
        InternalChapterReferenceTarget(book="alma", chapter=1, end_chapter=3),
    )

    result = traverse(
        [edge],
        "bofm/1-ne/1/1",
        Direction.OUTBOUND,
        max_depth=1,
        max_nodes=10,
        include_external=True,
    )

    assert [node.reference for node in result.nodes] == ["bofm/1-ne/1/1"]
    assert result.external_targets == []
    assert result.official_edges == [edge]


def test_inbound_traversal_matches_verses_inside_internal_chapter_targets() -> None:
    edge = _edge(
        "internal-chapters",
        InternalChapterReferenceTarget(book="alma", chapter=2, end_chapter=3),
    )

    result = traverse(
        [edge],
        "bofm/alma/3/7",
        Direction.INBOUND,
        max_depth=1,
        max_nodes=10,
        include_external=False,
    )

    assert [node.reference for node in result.nodes] == [
        "bofm/alma/3/7",
        "bofm/1-ne/1/1",
    ]
    assert result.official_edges == [edge]


def test_inbound_traversal_excludes_verses_outside_internal_chapter_targets() -> None:
    edge = _edge(
        "internal-chapter",
        InternalChapterReferenceTarget(book="alma", chapter=2),
    )

    result = traverse(
        [edge],
        "bofm/alma/3/7",
        Direction.INBOUND,
        max_depth=1,
        max_nodes=10,
        include_external=False,
    )

    assert [node.reference for node in result.nodes] == ["bofm/alma/3/7"]
    assert result.official_edges == []
