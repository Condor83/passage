from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from passage.domain.identifiers import CanonicalReference
from passage.domain.models import (
    Direction,
    ExternalChapterReferenceTarget,
    ExternalReferenceTarget,
    InternalChapterReferenceTarget,
    InternalReferenceTarget,
    ReferenceEdge,
    ReferenceTarget,
)
from passage.domain.references import reference_target_key


@dataclass(frozen=True, slots=True)
class TraversedNode:
    reference: str
    relationship_path: list[str]


@dataclass(frozen=True, slots=True)
class TraversalResult:
    nodes: list[TraversedNode]
    external_targets: list[ReferenceTarget]
    official_edges: list[ReferenceEdge]
    frontier: list[str]

    @property
    def truncated(self) -> bool:
        return bool(self.frontier)


def traverse(
    edges: list[ReferenceEdge],
    origin: str,
    direction: Direction,
    max_depth: int,
    max_nodes: int,
    include_external: bool,
) -> TraversalResult:
    queue: deque[tuple[str, int, list[str]]] = deque([(origin, 0, [])])
    visited = {origin}
    nodes: list[TraversedNode] = []
    external_targets: dict[str, ReferenceTarget] = {}
    official_edges: dict[str, ReferenceEdge] = {}
    frontier: set[str] = set()

    while queue:
        reference, depth, path = queue.popleft()
        nodes.append(TraversedNode(reference=reference, relationship_path=path))
        if depth >= max_depth:
            continue
        for edge, target_reference, external in _neighbors(edges, reference, direction):
            official_edges[edge.edge_id] = edge
            if external is not None:
                if include_external:
                    external_targets[reference_target_key(external)] = external
                continue
            if target_reference is None or target_reference in visited:
                continue
            next_path = [*path, edge.edge_id]
            if len(visited) >= max_nodes:
                frontier.add(target_reference)
                continue
            visited.add(target_reference)
            queue.append((target_reference, depth + 1, next_path))

    return TraversalResult(
        nodes=nodes,
        external_targets=list(external_targets.values()),
        official_edges=list(official_edges.values()),
        frontier=sorted(frontier),
    )


def _neighbors(
    edges: list[ReferenceEdge],
    reference: str,
    direction: Direction,
):
    if direction in (Direction.OUTBOUND, Direction.BOTH):
        for edge in edges:
            if edge.origin_reference != reference:
                continue
            if isinstance(edge.target, (ExternalReferenceTarget, ExternalChapterReferenceTarget)):
                yield edge, None, edge.target
                continue
            if isinstance(edge.target, InternalChapterReferenceTarget):
                yield edge, None, None
                continue
            for target_reference in _target_references(edge.target):
                yield edge, target_reference, None
    if direction in (Direction.INBOUND, Direction.BOTH):
        for edge in edges:
            if _internal_target_contains(edge.target, reference):
                yield edge, edge.origin_reference, None


def _target_references(target: ReferenceTarget) -> tuple[str, ...]:
    if not isinstance(target, InternalReferenceTarget):
        return ()
    reference = CanonicalReference(
        book=target.book,
        chapter=target.chapter,
        verse=target.verse,
        end_verse=target.end_verse,
    )
    return tuple(str(item) for item in reference.passages())


def _internal_target_contains(target: ReferenceTarget, reference: str) -> bool:
    if isinstance(target, InternalReferenceTarget):
        return reference in _target_references(target)
    if not isinstance(target, InternalChapterReferenceTarget):
        return False
    parsed = CanonicalReference.parse(reference)
    end_chapter = target.end_chapter or target.chapter
    return target.book == parsed.book and target.chapter <= parsed.chapter <= end_chapter
