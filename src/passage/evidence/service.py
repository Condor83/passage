from __future__ import annotations

from typing import Any

from passage.db.contracts import (
    LexicalQuery,
    RepositorySearchHit,
    SnapshotProvider,
    SnapshotSession,
)
from passage.domain.errors import ConfigUnavailableError
from passage.domain.models import (
    Completeness,
    ContextRequest,
    CorpusMetadata,
    Direction,
    EvidenceLane,
    EvidenceRecord,
    EvidenceResponse,
    EvidenceSearchRequest,
    LexicalMode,
    LexicalSearchRequest,
    Passage,
    PassageRequest,
    ReferenceEdge,
    RetrievalBasis,
    SnapshotRequest,
    TraversalRequest,
    TraversalResponse,
)
from passage.evidence.lexical import (
    CursorPosition,
    decode_cursor,
    encode_cursor,
    request_fingerprint,
)
from passage.evidence.ranking import RankedCandidate, rank_candidates
from passage.evidence.references import traverse


class EvidenceService:
    def __init__(self, snapshots: SnapshotProvider) -> None:
        self.snapshots = snapshots

    def get_corpus(self, request: SnapshotRequest) -> CorpusMetadata:
        with self.snapshots.pin(request) as snapshot:
            manifest = snapshot.accepted.manifest
            approval = manifest["source_approval"]
            lanes = snapshot.config["lanes"]
            if not isinstance(lanes, list):
                raise ConfigUnavailableError("evidence lane configuration is invalid")
            return CorpusMetadata(
                corpus_version=snapshot.corpus_version,
                retrieval_config=snapshot.retrieval_config,
                edition=approval["edition"],
                language=approval["language"],
                source_sha256=approval["source_sha256"],
                schema_version=manifest["schema_version"],
                importer_version=manifest["importer_version"],
                enabled_lanes=[EvidenceLane(lane) for lane in lanes],
                supported_operations=[
                    "get_corpus",
                    "get_passage",
                    "get_context",
                    "search_lexical",
                    "traverse_references",
                    "search_evidence",
                ],
                bounds={
                    "query_characters": 512,
                    "search_limit": 100,
                    "context_neighbor_limit": 40,
                    "traversal_depth": 3,
                    "traversal_nodes": 200,
                    "books_filter": 15,
                    "reference_ranges_filter": 50,
                },
                accepted_at=snapshot.accepted.accepted_at,
            )

    def get_passage(self, request: PassageRequest) -> EvidenceResponse:
        with self.snapshots.pin(request) as snapshot:
            passage = snapshot.repository.get_passage(request.reference)
            record = self._record(
                snapshot,
                passage,
                basis=[_lookup_basis(passage, "exact_lookup")],
                limits={"records": 1},
            )
            return self._response(
                snapshot,
                [record],
                applied={"operation": "get_passage", "reference": request.reference},
            )

    def get_context(self, request: ContextRequest) -> EvidenceResponse:
        with self.snapshots.pin(request) as snapshot:
            passage = snapshot.repository.get_passage(request.reference)
            context = snapshot.repository.get_context(
                request.reference,
                before=request.before,
                after=request.after,
            )
            limits: dict[str, int | bool | str] = {
                "before": request.before,
                "after": request.after,
            }
            record = self._record(
                snapshot,
                passage,
                context=context,
                basis=[_lookup_basis(passage, "context_lookup")],
                limits=limits,
            )
            return self._response(
                snapshot,
                [record],
                applied={"operation": "get_context", **limits},
            )

    def search_lexical(self, request: LexicalSearchRequest) -> EvidenceResponse:
        with self.snapshots.pin(request) as snapshot:
            query = LexicalQuery(request.query, request.mode, request.near_distance)
            fingerprint = request_fingerprint(
                {
                    "operation": "search_lexical",
                    "corpus_version": snapshot.corpus_version,
                    "retrieval_config": snapshot.retrieval_config,
                    "request": request.model_dump(mode="json", exclude={"cursor"}),
                }
            )
            after = None
            if request.cursor is not None:
                position = decode_cursor(request.cursor, fingerprint)
                after = (position.raw_score, position.canonical_order)
            page = snapshot.repository.search_lexical(
                query,
                request.filters,
                after,
                request.limit,
            )
            records = [self._lexical_record(snapshot, hit, request) for hit in page.hits]
            cursor = None
            if page.has_more and page.hits:
                last = page.hits[-1]
                cursor = encode_cursor(
                    fingerprint,
                    CursorPosition(last.raw_score, last.passage.canonical_order),
                )
            return self._response(
                snapshot,
                records,
                applied={
                    "operation": "search_lexical",
                    "mode": request.mode.value,
                    "near_distance": request.near_distance,
                    "limit": request.limit,
                    "filters": _dump_filters(request),
                },
                completeness=Completeness(
                    truncated=page.has_more,
                    cursor=cursor,
                ),
            )

    def traverse_references(self, request: TraversalRequest) -> TraversalResponse:
        with self.snapshots.pin(request) as snapshot:
            snapshot.repository.get_passage(request.reference)
            result = traverse(
                snapshot.repository.all_edges(),
                request.reference,
                request.direction,
                request.max_depth,
                request.max_nodes,
                request.include_external,
            )
            records = []
            for node in result.nodes:
                passage = snapshot.repository.get_passage(node.reference)
                records.append(
                    self._record(
                        snapshot,
                        passage,
                        basis=[
                            RetrievalBasis(
                                lane=EvidenceLane.OFFICIAL,
                                match_kind=(
                                    "traversal_origin"
                                    if not node.relationship_path
                                    else "official_reference"
                                ),
                                tie_break=passage.canonical_order,
                                relationship_path=node.relationship_path,
                            )
                        ],
                        limits={
                            "max_depth": request.max_depth,
                            "max_nodes": request.max_nodes,
                            "include_external": request.include_external,
                        },
                    )
                )
            return TraversalResponse(
                records=records,
                corpus_version=snapshot.corpus_version,
                retrieval_config=snapshot.retrieval_config,
                applied={
                    "operation": "traverse_references",
                    "direction": request.direction.value,
                    "max_depth": request.max_depth,
                    "max_nodes": request.max_nodes,
                    "include_external": request.include_external,
                },
                completeness=Completeness(
                    truncated=result.truncated,
                    frontier=result.frontier,
                ),
                official_edges=result.official_edges,
                external_targets=result.external_targets,
            )

    def search_evidence(self, request: EvidenceSearchRequest) -> EvidenceResponse:
        with self.snapshots.pin(request) as snapshot:
            lexical_config = snapshot.config["lexical"]
            if not isinstance(lexical_config, dict):
                raise ConfigUnavailableError("lexical retrieval configuration is invalid")
            candidate_pool = int(lexical_config["candidate_pool_size"])
            lexical_query = LexicalQuery(request.query, LexicalMode.TERMS)
            lexical_page = snapshot.repository.search_lexical(
                lexical_query,
                request.filters,
                None,
                candidate_pool,
            )

            candidates: dict[str, tuple[Passage, list[RetrievalBasis]]] = {}
            official_edges: dict[str, ReferenceEdge] = {}
            for hit in lexical_page.hits:
                candidates[hit.reference] = (
                    hit.passage,
                    [_lexical_basis(hit, "terms")],
                )
            if EvidenceLane.OFFICIAL in request.lanes and request.official_depth > 0:
                edges = snapshot.repository.all_edges()
                max_nodes = snapshot.repository.passage_count()
                for hit in lexical_page.hits:
                    expanded = traverse(
                        edges,
                        hit.reference,
                        Direction.OUTBOUND,
                        request.official_depth,
                        max_nodes,
                        include_external=False,
                    )
                    official_edges.update((edge.edge_id, edge) for edge in expanded.official_edges)
                    for node in expanded.nodes[1:]:
                        passage = snapshot.repository.get_passage(node.reference)
                        basis = RetrievalBasis(
                            lane=EvidenceLane.OFFICIAL,
                            match_kind="official_reference",
                            tie_break=passage.canonical_order,
                            relationship_path=node.relationship_path,
                        )
                        if node.reference in candidates:
                            candidates[node.reference][1].append(basis)
                        else:
                            candidates[node.reference] = (passage, [basis])

            ranked = rank_candidates(
                [
                    RankedCandidate(
                        reference=reference,
                        canonical_order=passage.canonical_order,
                        basis=basis,
                    )
                    for reference, (passage, basis) in candidates.items()
                ]
            )
            fingerprint = request_fingerprint(
                {
                    "operation": "search_evidence",
                    "corpus_version": snapshot.corpus_version,
                    "retrieval_config": snapshot.retrieval_config,
                    "request": request.model_dump(mode="json", exclude={"cursor"}),
                }
            )
            start = 0
            if request.cursor is not None:
                position = decode_cursor(request.cursor, fingerprint)
                cursor_key = (
                    position.lane_priority,
                    position.raw_score,
                    position.canonical_order,
                )
                start = next(
                    (
                        index
                        for index, candidate in enumerate(ranked)
                        if _candidate_key(candidate) > cursor_key
                    ),
                    len(ranked),
                )
            selected = ranked[start : start + request.limit]
            has_more = start + request.limit < len(ranked)
            cursor = None
            if has_more and selected:
                lane, score, order = _candidate_key(selected[-1])
                cursor = encode_cursor(
                    fingerprint,
                    CursorPosition(score, order, lane_priority=lane),
                )
            records = [
                self._record(
                    snapshot,
                    candidates[item.reference][0],
                    basis=item.basis,
                    filters=request.filters,
                    limits={
                        "limit": request.limit,
                        "candidate_pool_size": candidate_pool,
                        "official_depth": request.official_depth,
                    },
                )
                for item in selected
            ]
            return self._response(
                snapshot,
                records,
                applied={
                    "operation": "search_evidence",
                    "lanes": [lane.value for lane in request.lanes],
                    "official_depth": request.official_depth,
                    "candidate_pool_size": candidate_pool,
                    "limit": request.limit,
                    "filters": _dump_filters(request),
                },
                completeness=Completeness(
                    truncated=has_more or lexical_page.has_more,
                    cursor=cursor,
                ),
                official_edges=list(official_edges.values()),
            )

    def _lexical_record(
        self,
        snapshot: SnapshotSession,
        hit: RepositorySearchHit,
        request: LexicalSearchRequest,
    ) -> EvidenceRecord:
        return self._record(
            snapshot,
            hit.passage,
            basis=[_lexical_basis(hit, request.mode.value)],
            filters=request.filters,
            limits={
                "limit": request.limit,
                "mode": request.mode.value,
                "near_distance": request.near_distance or 0,
            },
        )

    def _record(
        self,
        snapshot: SnapshotSession,
        passage: Passage,
        *,
        basis: list[RetrievalBasis],
        context: list[Passage] | None = None,
        filters=None,
        limits: dict[str, int | bool | str],
    ) -> EvidenceRecord:
        return EvidenceRecord(
            passage=passage,
            context=context or [],
            corpus_version=snapshot.corpus_version,
            retrieval_config=snapshot.retrieval_config,
            applied_filters=filters,
            applied_limits=limits,
            basis=basis,
            provenance=passage.source_spans,
        )

    def _response(
        self,
        snapshot: SnapshotSession,
        records: list[EvidenceRecord],
        *,
        applied: dict[str, Any],
        completeness: Completeness | None = None,
        official_edges: list[ReferenceEdge] | None = None,
    ) -> EvidenceResponse:
        return EvidenceResponse(
            records=records,
            corpus_version=snapshot.corpus_version,
            retrieval_config=snapshot.retrieval_config,
            applied=applied,
            completeness=completeness or Completeness(),
            official_edges=official_edges or [],
        )


def _lookup_basis(passage: Passage, match_kind: str) -> RetrievalBasis:
    return RetrievalBasis(
        lane=EvidenceLane.LEXICAL,
        match_kind=match_kind,
        tie_break=passage.canonical_order,
    )


def _lexical_basis(hit: RepositorySearchHit, match_kind: str) -> RetrievalBasis:
    return RetrievalBasis(
        lane=EvidenceLane.LEXICAL,
        match_kind=match_kind,
        raw_score=hit.raw_score,
        score_components={"bm25": hit.raw_score},
        tie_break=hit.passage.canonical_order,
    )


def _candidate_key(candidate: RankedCandidate) -> tuple[int, float, int]:
    lexical_scores = [
        basis.raw_score
        for basis in candidate.basis
        if basis.lane is EvidenceLane.LEXICAL and basis.raw_score is not None
    ]
    if lexical_scores:
        return 0, min(lexical_scores), candidate.canonical_order
    return 1, 0.0, candidate.canonical_order


def _dump_filters(request: LexicalSearchRequest | EvidenceSearchRequest):
    if request.filters is None:
        return None
    return request.filters.model_dump(mode="json")
