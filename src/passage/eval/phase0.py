from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import Field, StringConstraints, field_validator, model_validator

from passage.config import create_private_file
from passage.db.contracts import EvidenceRepository
from passage.domain.identifiers import CanonicalReference
from passage.domain.models import (
    Completeness,
    ContextRequest,
    Direction,
    EvidenceLane,
    EvidenceResponse,
    EvidenceSearchRequest,
    ExternalReferenceTarget,
    Identifier,
    InternalReferenceTarget,
    LexicalSearchRequest,
    Passage,
    PassageRequest,
    ReferenceEdge,
    Sha256,
    SnapshotRequest,
    StrictModel,
    TraversalRequest,
)
from passage.evidence.service import EvidenceService

PHASE0_PROBE_VERSION: Literal["phase0-product-loop-v1"] = "phase0-product-loop-v1"
_PRESENT_LANES = ["exact", "lexical", "official"]
_ABSENT_LANES = ["derived", "experimental"]
_ATOMIC_OPERATIONS = [
    "get_corpus",
    "get_passage",
    "get_context",
    "search_lexical",
    "traverse_references",
]


class Phase0ProbeCase(StrictModel):
    case_id: Identifier
    question: Annotated[str, StringConstraints(min_length=1, max_length=500)]
    query: Annotated[str, StringConstraints(min_length=1, max_length=512, strip_whitespace=True)]
    exact_reference: str
    context_reference: str
    context_before: int = Field(default=1, ge=0, le=20)
    context_after: int = Field(default=1, ge=0, le=20)
    traversal_reference: str
    traversal_depth: int = Field(default=1, ge=0, le=3)
    traversal_nodes: int = Field(default=20, ge=1, le=200)
    result_limit: int = Field(default=20, ge=1, le=100)
    reference_pool: list[str]

    @field_validator("exact_reference", "context_reference", "traversal_reference")
    @classmethod
    def validate_single_reference(cls, value: str) -> str:
        reference = CanonicalReference.parse(value)
        if reference.end_verse is not None:
            raise ValueError("probe operation references must identify one passage")
        return value

    @field_validator("reference_pool")
    @classmethod
    def validate_reference_pool(cls, values: list[str]) -> list[str]:
        if not values or len(values) != len(set(values)):
            raise ValueError("reference_pool must be non-empty and unique")
        for value in values:
            reference = CanonicalReference.parse(value)
            if reference.end_verse is not None:
                raise ValueError("reference_pool entries must identify one passage")
        return values


class Phase0ProbeRubric(StrictModel):
    coverage_metric: Literal["reference_pool_coverage"] = "reference_pool_coverage"
    require_resolvable_citations: Literal[True] = True
    require_correct_evidence_classes: Literal[True] = True
    require_one_pinned_snapshot: Literal[True] = True
    require_complete_operation_contracts: Literal[True] = True


class Phase0ProbeDefinition(StrictModel):
    schema_version: Literal[1] = 1
    probe_id: Identifier
    scope: Literal["directional_phase_0"] = "directional_phase_0"
    present_lanes: list[Literal["exact", "lexical", "official"]]
    absent_lanes: list[Literal["derived", "experimental"]]
    rubric: Phase0ProbeRubric
    cases: list[Phase0ProbeCase]

    @model_validator(mode="after")
    def validate_locked_scope(self) -> Phase0ProbeDefinition:
        if self.present_lanes != _PRESENT_LANES:
            raise ValueError("Phase 0 present lanes must be exact, lexical, official")
        if self.absent_lanes != _ABSENT_LANES:
            raise ValueError("Phase 0 absent lanes must be derived, experimental")
        if not self.cases:
            raise ValueError("Phase 0 requires at least one locked synthetic case")
        identifiers = [case.case_id for case in self.cases]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("Phase 0 case identifiers must be unique")
        return self


class ProbeCitation(StrictModel):
    corpus_version: Identifier
    retrieval_config: Identifier
    reference: str
    content_hash: Sha256
    source_spans_digest: Sha256


class ProbeEvidenceItem(StrictModel):
    evidence_class: Literal["source", "official"]
    citation: ProbeCitation
    official_edge_id: Identifier | None = None
    evidence_spans_digest: Sha256

    @model_validator(mode="after")
    def validate_class_shape(self) -> ProbeEvidenceItem:
        if self.evidence_class == "source" and self.official_edge_id is not None:
            raise ValueError("source evidence cannot carry an official edge identifier")
        if self.evidence_class == "official" and self.official_edge_id is None:
            raise ValueError("official evidence requires an official edge identifier")
        return self


class ProbeOperationTrace(StrictModel):
    path: Literal["atomic", "comparator"]
    operation: str
    request: dict[str, Any]
    applied: dict[str, Any]
    completeness: Completeness | None = None
    returned_references: list[str]
    citations: list[ProbeCitation]
    evidence: list[ProbeEvidenceItem]


class ProbeCoverage(StrictModel):
    reference_pool: list[str]
    atomic_references: list[str]
    comparator_references: list[str]
    atomic_covered: list[str]
    comparator_covered: list[str]
    atomic_ratio: float = Field(ge=0, le=1)
    comparator_ratio: float = Field(ge=0, le=1)


class Phase0CaseResult(StrictModel):
    case_id: Identifier
    traces: list[ProbeOperationTrace]
    coverage: ProbeCoverage


class Phase0ProbeReport(StrictModel):
    schema_version: Literal[1] = 1
    probe_version: Literal["phase0-product-loop-v1"] = PHASE0_PROBE_VERSION
    scope: Literal["directional_phase_0"] = "directional_phase_0"
    corpus_version: Identifier
    retrieval_config: Identifier
    definition_digest: Sha256
    evaluator_code_digest: Sha256
    present_lanes: list[str]
    absent_lanes: list[str]
    rubric: Phase0ProbeRubric
    atomic_operations: list[str]
    comparator_operation: Literal["search_evidence"] = "search_evidence"
    cases: list[Phase0CaseResult]
    citation_errors: list[str]
    evidence_class_errors: list[str]
    fatal_atomic_contract_problems: list[str]
    zero_citation_errors: bool
    zero_evidence_class_errors: bool
    no_fatal_atomic_contract_problem: bool
    h1_claim: Literal[False] = False
    h1_status: Literal["not_evaluated"] = "not_evaluated"
    promotion_eligible: Literal[False] = False
    report_digest: Sha256


@dataclass(frozen=True, slots=True)
class Phase0ProbeRun:
    report: Phase0ProbeReport
    path: Path | None


def load_phase0_probe_definition(path: Path) -> Phase0ProbeDefinition:
    return Phase0ProbeDefinition.model_validate_json(path.read_text(encoding="utf-8"))


class Phase0ProbeRunner:
    def __init__(self, service: EvidenceService) -> None:
        self.service = service

    def run(
        self,
        definition: Phase0ProbeDefinition,
        *,
        corpus_version: str,
        retrieval_config: str,
        output_directory: Path | None = None,
    ) -> Phase0ProbeRun:
        definition_digest = _digest(definition.model_dump(mode="json"))
        selector = {
            "corpus_version": corpus_version,
            "retrieval_config": retrieval_config,
        }
        citation_errors: list[str] = []
        evidence_class_errors: list[str] = []
        fatal_problems: list[str] = []
        case_results: list[Phase0CaseResult] = []

        with self.service.snapshots.pin(
            SnapshotRequest(
                corpus_version=corpus_version,
                retrieval_config=retrieval_config,
            )
        ) as snapshot:
            repository = snapshot.repository
            config = snapshot.config
            self._audit_lanes(definition, config, repository, fatal_problems)
            for case in definition.cases:
                traces = self._run_case(
                    case,
                    selector,
                    repository,
                    citation_errors,
                    evidence_class_errors,
                    fatal_problems,
                )
                case_results.append(
                    Phase0CaseResult(
                        case_id=case.case_id,
                        traces=traces,
                        coverage=_coverage(case, traces),
                    )
                )

        expected_sequence = [*_ATOMIC_OPERATIONS, "search_evidence"]
        for result in case_results:
            observed = [trace.operation for trace in result.traces]
            if observed != expected_sequence:
                fatal_problems.append(f"{result.case_id}:operation_sequence")

        report_core = {
            "schema_version": 1,
            "probe_version": PHASE0_PROBE_VERSION,
            "scope": "directional_phase_0",
            "corpus_version": corpus_version,
            "retrieval_config": retrieval_config,
            "definition_digest": definition_digest,
            "evaluator_code_digest": _evaluator_code_digest(),
            "present_lanes": definition.present_lanes,
            "absent_lanes": definition.absent_lanes,
            "rubric": definition.rubric.model_dump(mode="json"),
            "atomic_operations": _ATOMIC_OPERATIONS,
            "comparator_operation": "search_evidence",
            "cases": [result.model_dump(mode="json") for result in case_results],
            "citation_errors": sorted(set(citation_errors)),
            "evidence_class_errors": sorted(set(evidence_class_errors)),
            "fatal_atomic_contract_problems": sorted(set(fatal_problems)),
            "zero_citation_errors": not citation_errors,
            "zero_evidence_class_errors": not evidence_class_errors,
            "no_fatal_atomic_contract_problem": not fatal_problems,
            "h1_claim": False,
            "h1_status": "not_evaluated",
            "promotion_eligible": False,
        }
        report = Phase0ProbeReport.model_validate(
            {**report_core, "report_digest": _digest(report_core)}
        )
        path = self._publish(report, output_directory) if output_directory else None
        return Phase0ProbeRun(report=report, path=path)

    def _run_case(
        self,
        case: Phase0ProbeCase,
        selector: dict[str, str],
        repository: EvidenceRepository,
        citation_errors: list[str],
        evidence_class_errors: list[str],
        fatal_problems: list[str],
    ) -> list[ProbeOperationTrace]:
        metadata_request = SnapshotRequest(**selector)
        metadata_response = self.service.get_corpus(metadata_request)
        traces = [
            ProbeOperationTrace(
                path="atomic",
                operation="get_corpus",
                request=metadata_request.model_dump(mode="json"),
                applied={"bounds": metadata_response.bounds},
                returned_references=[],
                citations=[],
                evidence=[],
            )
        ]
        if (
            metadata_response.corpus_version != repository.corpus_version
            or metadata_response.retrieval_config != repository.retrieval_config
        ):
            fatal_problems.append(f"{case.case_id}:get_corpus_identity_drift")

        operations: list[
            tuple[
                str,
                EvidenceResponse,
                StrictModel,
                Literal["atomic", "comparator"],
            ]
        ] = []
        passage_request = PassageRequest(reference=case.exact_reference, **selector)
        operations.append(
            ("get_passage", self.service.get_passage(passage_request), passage_request, "atomic")
        )
        context_request = ContextRequest(
            reference=case.context_reference,
            before=case.context_before,
            after=case.context_after,
            **selector,
        )
        operations.append(
            ("get_context", self.service.get_context(context_request), context_request, "atomic")
        )
        lexical_request = LexicalSearchRequest(
            query=case.query,
            limit=case.result_limit,
            corpus_version=selector["corpus_version"],
            retrieval_config=selector["retrieval_config"],
        )
        operations.append(
            (
                "search_lexical",
                self.service.search_lexical(lexical_request),
                lexical_request,
                "atomic",
            )
        )
        traversal_request = TraversalRequest(
            reference=case.traversal_reference,
            direction=Direction.OUTBOUND,
            max_depth=case.traversal_depth,
            max_nodes=case.traversal_nodes,
            include_external=True,
            **selector,
        )
        operations.append(
            (
                "traverse_references",
                self.service.traverse_references(traversal_request),
                traversal_request,
                "atomic",
            )
        )
        comparator_request = EvidenceSearchRequest(
            query=case.query,
            lanes=[EvidenceLane.LEXICAL, EvidenceLane.OFFICIAL],
            official_depth=case.traversal_depth,
            limit=case.result_limit,
            corpus_version=selector["corpus_version"],
            retrieval_config=selector["retrieval_config"],
        )
        operations.append(
            (
                "search_evidence",
                self.service.search_evidence(comparator_request),
                comparator_request,
                "comparator",
            )
        )

        for operation, response, request, path in operations:
            traces.append(
                self._trace_response(
                    case.case_id,
                    operation,
                    path,
                    request,
                    response,
                    repository,
                    citation_errors,
                    evidence_class_errors,
                    fatal_problems,
                )
            )
        return traces

    def _trace_response(
        self,
        case_id: str,
        operation: str,
        path: Literal["atomic", "comparator"],
        request: StrictModel,
        response: EvidenceResponse,
        repository: EvidenceRepository,
        citation_errors: list[str],
        evidence_class_errors: list[str],
        fatal_problems: list[str],
    ) -> ProbeOperationTrace:
        if (
            response.corpus_version != repository.corpus_version
            or response.retrieval_config != repository.retrieval_config
        ):
            fatal_problems.append(f"{case_id}:{operation}:snapshot_identity")
        if response.applied.get("operation") != operation:
            fatal_problems.append(f"{case_id}:{operation}:applied_operation")
        for required in _required_applied_fields(operation):
            if required not in response.applied:
                fatal_problems.append(f"{case_id}:{operation}:missing_bound:{required}")

        passages = [
            passage for record in response.records for passage in [record.passage, *record.context]
        ]
        citations: list[ProbeCitation] = []
        evidence: list[ProbeEvidenceItem] = []
        for passage in passages:
            citation = _citation(repository, passage, citation_errors, case_id, operation)
            citations.append(citation)
            evidence.append(
                ProbeEvidenceItem(
                    evidence_class="source",
                    citation=citation,
                    evidence_spans_digest=_digest_spans(passage.source_spans),
                )
            )
        for edge in response.official_edges:
            citation = _edge_citation(
                repository,
                edge,
                citation_errors,
                case_id,
                operation,
            )
            citations.append(citation)
            evidence.append(
                ProbeEvidenceItem(
                    evidence_class="official",
                    citation=citation,
                    official_edge_id=edge.edge_id,
                    evidence_spans_digest=_digest_spans(edge.source_spans),
                )
            )
        evidence_class_errors.extend(_evidence_class_errors(case_id, operation, evidence))
        return ProbeOperationTrace(
            path=path,
            operation=operation,
            request=request.model_dump(mode="json"),
            applied=response.applied,
            completeness=response.completeness,
            returned_references=_unique(passage.reference for passage in passages),
            citations=citations,
            evidence=evidence,
        )

    def _audit_lanes(
        self,
        definition: Phase0ProbeDefinition,
        config: dict[str, object],
        repository: EvidenceRepository,
        fatal_problems: list[str],
    ) -> None:
        actual = ["exact"]
        configured_lanes = config.get("lanes")
        if not isinstance(configured_lanes, list):
            fatal_problems.append("retrieval_configuration_lanes_invalid")
            return
        if EvidenceLane.LEXICAL.value in configured_lanes:
            actual.append("lexical")
        if EvidenceLane.OFFICIAL.value in configured_lanes and repository.all_edges():
            actual.append("official")
        if actual != definition.present_lanes:
            fatal_problems.append("declared_present_lanes_do_not_match_fixture")
        if set(actual).intersection(definition.absent_lanes):
            fatal_problems.append("absent_lane_executed")

    def _publish(self, report: Phase0ProbeReport, output_directory: Path) -> Path:
        output_directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        path = output_directory / f"phase0-probe-{report.report_digest}.json"
        payload = (_canonical_json(report.model_dump(mode="json")) + "\n").encode("utf-8")
        if path.exists():
            if path.read_bytes() != payload:
                raise ValueError("existing Phase 0 probe does not match its identity")
            return path
        create_private_file(path, payload)
        return path


def _coverage(case: Phase0ProbeCase, traces: list[ProbeOperationTrace]) -> ProbeCoverage:
    atomic = _unique(
        reference
        for trace in traces
        if trace.path == "atomic"
        for reference in trace.returned_references
    )
    comparator = _unique(
        reference
        for trace in traces
        if trace.path == "comparator"
        for reference in trace.returned_references
    )
    pool = set(case.reference_pool)
    atomic_covered = [reference for reference in case.reference_pool if reference in atomic]
    comparator_covered = [reference for reference in case.reference_pool if reference in comparator]
    return ProbeCoverage(
        reference_pool=case.reference_pool,
        atomic_references=atomic,
        comparator_references=comparator,
        atomic_covered=atomic_covered,
        comparator_covered=comparator_covered,
        atomic_ratio=len(atomic_covered) / len(pool),
        comparator_ratio=len(comparator_covered) / len(pool),
    )


def _citation(
    repository: EvidenceRepository,
    passage: Passage,
    errors: list[str],
    case_id: str,
    operation: str,
) -> ProbeCitation:
    try:
        resolved = repository.get_passage(passage.reference)
    except Exception:
        errors.append(f"{case_id}:{operation}:{passage.reference}:unresolved")
        resolved = passage
    if resolved != passage:
        errors.append(f"{case_id}:{operation}:{passage.reference}:mismatch")
    return ProbeCitation(
        corpus_version=repository.corpus_version,
        retrieval_config=repository.retrieval_config,
        reference=passage.reference,
        content_hash=passage.content_hash,
        source_spans_digest=_digest_spans(passage.source_spans),
    )


def _edge_citation(
    repository: EvidenceRepository,
    edge: ReferenceEdge,
    errors: list[str],
    case_id: str,
    operation: str,
) -> ProbeCitation:
    origin = repository.get_passage(edge.origin_reference)
    if not edge.source_spans:
        errors.append(f"{case_id}:{operation}:{edge.edge_id}:missing_edge_spans")
    if isinstance(edge.target, InternalReferenceTarget):
        reference = CanonicalReference(
            book=edge.target.book,
            chapter=edge.target.chapter,
            verse=edge.target.verse,
            end_verse=edge.target.end_verse,
        )
        for target in reference.passages():
            try:
                repository.get_passage(str(target))
            except Exception:
                errors.append(f"{case_id}:{operation}:{edge.edge_id}:unresolved_target")
    elif not isinstance(edge.target, ExternalReferenceTarget) or (
        edge.target.resolution != "unresolved_external"
    ):
        errors.append(f"{case_id}:{operation}:{edge.edge_id}:external_target_class")
    return _citation(repository, origin, errors, case_id, operation)


def _evidence_class_errors(
    case_id: str,
    operation: str,
    items: list[ProbeEvidenceItem],
) -> list[str]:
    errors = []
    for item in items:
        if item.evidence_class == "source" and item.official_edge_id is not None:
            errors.append(f"{case_id}:{operation}:source_labeled_official")
        if item.evidence_class == "official" and item.official_edge_id is None:
            errors.append(f"{case_id}:{operation}:official_missing_edge")
    return errors


def _required_applied_fields(operation: str) -> tuple[str, ...]:
    return {
        "get_passage": ("reference",),
        "get_context": ("before", "after"),
        "search_lexical": ("mode", "limit", "filters"),
        "traverse_references": ("max_depth", "max_nodes", "include_external"),
        "search_evidence": ("lanes", "official_depth", "candidate_pool_size", "limit"),
    }[operation]


def _digest_spans(spans: list[Any]) -> str:
    return _digest([span.model_dump(mode="json") for span in spans])


def _evaluator_code_digest() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _unique(values) -> list[str]:
    return list(dict.fromkeys(values))
