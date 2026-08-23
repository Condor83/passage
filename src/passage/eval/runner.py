from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import Field

from passage.config import create_private_file
from passage.domain.models import (
    EvidenceSearchRequest,
    Identifier,
    Sha256,
    StrictModel,
)
from passage.eval.cases import EvaluationCase
from passage.eval.metrics import evaluate_ranking
from passage.evidence.service import EvidenceService


class EvaluationIdentities(StrictModel):
    corpus_version: Identifier
    retrieval_config: Identifier
    case_definitions_digest: Sha256
    judgment_digest: Sha256
    annotation_digest: Sha256
    evaluator_code_digest: Sha256
    metric_depths_digest: Sha256


class CaseEvaluation(StrictModel):
    case_id: Identifier
    split: str
    ranked_references: list[str]
    unjudged_candidates: list[str]
    judgment_coverage: float = Field(ge=0, le=1)
    metrics: dict[str, float]


class EvaluationReport(StrictModel):
    schema_version: int = 1
    identities: EvaluationIdentities
    metric_depths: list[int]
    cases: list[CaseEvaluation]
    eligible: bool
    ineligibility_reasons: list[str]
    unjudged_candidates: list[str]
    report_digest: Sha256


@dataclass(frozen=True, slots=True)
class EvaluationRun:
    report: EvaluationReport
    path: Path | None
    diagnostics: dict[str, Any]


class EvaluationRunner:
    def __init__(self, service: EvidenceService) -> None:
        self.service = service

    def run(
        self,
        cases: list[EvaluationCase],
        *,
        corpus_version: str,
        retrieval_config: str,
        metric_depths: list[int] | None = None,
        output_directory: Path | None = None,
    ) -> EvaluationRun:
        depths = metric_depths or [1, 3, 5, 10, 20]
        _validate_depths(depths)
        _validate_cases(cases)
        identities = EvaluationIdentities(
            corpus_version=corpus_version,
            retrieval_config=retrieval_config,
            case_definitions_digest=_digest(_case_definitions(cases)),
            judgment_digest=_digest(_judgments(cases)),
            annotation_digest=_digest(_annotations(cases)),
            evaluator_code_digest=_evaluator_code_digest(),
            metric_depths_digest=_digest(depths),
        )
        case_results: list[CaseEvaluation] = []
        query_timings: dict[str, float] = {}
        locked_unjudged: set[str] = set()
        all_unjudged: set[str] = set()
        for case in cases:
            started = time.perf_counter()
            ranked_references = self._retrieve(
                case,
                corpus_version=corpus_version,
                retrieval_config=retrieval_config,
            )
            query_timings[case.case_id] = (time.perf_counter() - started) * 1000
            judgments = {judgment.reference: judgment.grade for judgment in case.judgments}
            unjudged = sorted(set(ranked_references) - judgments.keys())
            all_unjudged.update(unjudged)
            if case.split == "locked":
                locked_unjudged.update(unjudged)
            coverage = (
                (len(ranked_references) - len(unjudged)) / len(ranked_references)
                if ranked_references
                else 1.0
            )
            case_results.append(
                CaseEvaluation(
                    case_id=case.case_id,
                    split=case.split,
                    ranked_references=ranked_references,
                    unjudged_candidates=unjudged,
                    judgment_coverage=coverage,
                    metrics=evaluate_ranking(ranked_references, judgments, depths),
                )
            )
        reasons = ["no_baseline_comparison"]
        locked_cases = [case for case in cases if case.split == "locked"]
        if not locked_cases:
            reasons.append("no_locked_cases")
        elif not _has_locked_relevant_hit(locked_cases, case_results):
            reasons.append("no_locked_relevant_hits")
        if locked_unjudged:
            reasons.append("incomplete_locked_judgments")
        report_core = {
            "schema_version": 1,
            "identities": identities.model_dump(mode="json"),
            "metric_depths": depths,
            "cases": [result.model_dump(mode="json") for result in case_results],
            "eligible": not reasons,
            "ineligibility_reasons": reasons,
            "unjudged_candidates": sorted(all_unjudged),
        }
        report = EvaluationReport(
            schema_version=1,
            identities=identities,
            metric_depths=depths,
            cases=case_results,
            eligible=not reasons,
            ineligibility_reasons=reasons,
            unjudged_candidates=sorted(all_unjudged),
            report_digest=_digest(report_core),
        )
        path = self._publish(report, output_directory) if output_directory else None
        return EvaluationRun(
            report=report,
            path=path,
            diagnostics={
                "warm_query_ms": query_timings,
                "timing_is_acceptance_gate": False,
            },
        )

    def _retrieve(
        self,
        case: EvaluationCase,
        *,
        corpus_version: str,
        retrieval_config: str,
    ) -> list[str]:
        references: list[str] = []
        cursor = None
        while True:
            response = self.service.search_evidence(
                EvidenceSearchRequest(
                    query=case.query,
                    filters=case.filters,
                    limit=100,
                    cursor=cursor,
                    corpus_version=corpus_version,
                    retrieval_config=retrieval_config,
                )
            )
            references.extend(record.passage.reference for record in response.records)
            cursor = response.completeness.cursor
            if cursor is None:
                return references

    def _publish(
        self,
        report: EvaluationReport,
        output_directory: Path,
    ) -> Path:
        output_directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        path = output_directory / f"evaluation-{report.report_digest}.json"
        data = (
            json.dumps(
                report.model_dump(mode="json"),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("utf-8")
        if path.exists():
            if path.read_bytes() != data:
                raise ValueError("existing evaluation artifact does not match report identity")
            return path
        create_private_file(path, data)
        return path


def _validate_depths(depths: list[int]) -> None:
    if not depths or len(depths) != len(set(depths)):
        raise ValueError("metric depths must be a non-empty unique list")
    if any(depth < 1 or depth > 100 for depth in depths):
        raise ValueError("metric depths must be between 1 and 100")
    if depths != sorted(depths):
        raise ValueError("metric depths must be in ascending order")


def _validate_cases(cases: list[EvaluationCase]) -> None:
    if not cases:
        raise ValueError("at least one evaluation case is required")
    identifiers = [case.case_id for case in cases]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("evaluation case identifiers must be unique")


def _has_locked_relevant_hit(
    cases: list[EvaluationCase],
    results: list[CaseEvaluation],
) -> bool:
    relevant_by_case = {
        case.case_id: {judgment.reference for judgment in case.judgments if judgment.grade > 0}
        for case in cases
    }
    return any(
        relevant_by_case[result.case_id].intersection(result.ranked_references)
        for result in results
        if result.split == "locked"
    )


def _case_definitions(cases: list[EvaluationCase]) -> list[dict[str, Any]]:
    return [
        {
            "case_id": case.case_id,
            "schema_version": case.schema_version,
            "split": case.split,
            "query": case.query,
            "filters": (case.filters.model_dump(mode="json") if case.filters is not None else None),
        }
        for case in cases
    ]


def _judgments(cases: list[EvaluationCase]) -> list[dict[str, Any]]:
    return [
        {
            "case_id": case.case_id,
            "judgments": sorted(
                (judgment.model_dump(mode="json") for judgment in case.judgments),
                key=lambda value: value["reference"],
            ),
        }
        for case in cases
    ]


def _annotations(cases: list[EvaluationCase]) -> list[dict[str, str]]:
    return [
        {
            "case_id": case.case_id,
            "curator_rationale": case.curator_rationale,
            "non_authoritative_notes": case.non_authoritative_notes,
        }
        for case in cases
    ]


def _evaluator_code_digest() -> str:
    directory = Path(__file__).parent
    digest = hashlib.sha256()
    for name in ("cases.py", "metrics.py", "runner.py"):
        digest.update(name.encode("utf-8"))
        digest.update((directory / name).read_bytes())
    return digest.hexdigest()


def _digest(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
