from pathlib import Path

from passage.domain.models import SnapshotRequest
from passage.eval.cases import EvaluationCase, EvidenceJudgment
from passage.eval.performance import measure_performance
from passage.eval.runner import EvaluationRunner


def test_locked_baseline_report_is_identity_bound_and_immutable(
    service,
    tmp_path: Path,
) -> None:
    metadata = service.get_corpus(SnapshotRequest())
    case = EvaluationCase(
        case_id="locked-faith",
        split="locked",
        query="faith charity",
        curator_rationale="Exercises lexical and official evidence.",
        non_authoritative_notes="Grades evidence relevance, not doctrine.",
        judgments=[
            EvidenceJudgment(reference="bofm/1-ne/1/1", grade=3),
            EvidenceJudgment(reference="bofm/1-ne/1/2", grade=2),
        ],
    )
    active_before = service.control.get_active()

    first = EvaluationRunner(service).run(
        [case],
        corpus_version=metadata.corpus_version,
        retrieval_config=metadata.retrieval_config,
        metric_depths=[1, 2],
        output_directory=tmp_path,
    )
    second = EvaluationRunner(service).run(
        [case],
        corpus_version=metadata.corpus_version,
        retrieval_config=metadata.retrieval_config,
        metric_depths=[1, 2],
        output_directory=tmp_path,
    )

    assert first.report == second.report
    assert first.path == second.path
    assert first.path is not None
    assert first.path.stat().st_mode & 0o777 == 0o600
    assert first.report.eligible is False
    assert first.report.ineligibility_reasons == ["no_baseline_comparison"]
    assert first.report.unjudged_candidates == []
    assert first.report.identities.corpus_version == metadata.corpus_version
    assert first.report.identities.retrieval_config == metadata.retrieval_config
    assert service.control.get_active() == active_before


def test_unjudged_candidates_and_missing_locked_cases_block_eligibility(
    service,
) -> None:
    metadata = service.get_corpus(SnapshotRequest())
    incomplete = EvaluationCase(
        case_id="locked-incomplete",
        split="locked",
        query="faith charity",
        curator_rationale="Intentionally incomplete candidate grading.",
        judgments=[EvidenceJudgment(reference="bofm/1-ne/1/1", grade=3)],
    )
    development = EvaluationCase(
        case_id="development-only",
        split="development",
        query="repent",
        curator_rationale="Development cases cannot grant eligibility.",
        judgments=[EvidenceJudgment(reference="bofm/1-ne/1/4", grade=3)],
    )
    empty = EvaluationCase(
        case_id="locked-no-hits",
        split="locked",
        query="unfindable",
        curator_rationale="A candidate with no locked-set contribution cannot be promoted.",
        judgments=[EvidenceJudgment(reference="bofm/1-ne/1/1", grade=3)],
    )

    incomplete_report = (
        EvaluationRunner(service)
        .run(
            [incomplete],
            corpus_version=metadata.corpus_version,
            retrieval_config=metadata.retrieval_config,
        )
        .report
    )
    development_report = (
        EvaluationRunner(service)
        .run(
            [development],
            corpus_version=metadata.corpus_version,
            retrieval_config=metadata.retrieval_config,
        )
        .report
    )

    empty_report = (
        EvaluationRunner(service)
        .run(
            [empty],
            corpus_version=metadata.corpus_version,
            retrieval_config=metadata.retrieval_config,
        )
        .report
    )
    assert incomplete_report.eligible is False
    assert incomplete_report.unjudged_candidates == ["bofm/1-ne/1/2"]
    assert development_report.eligible is False
    assert "no_locked_cases" in development_report.ineligibility_reasons
    assert empty_report.eligible is False
    assert "no_locked_relevant_hits" in empty_report.ineligibility_reasons


def test_every_identity_input_changes_report_digest(service) -> None:
    metadata = service.get_corpus(SnapshotRequest())
    base = EvaluationCase(
        case_id="locked-faith",
        split="locked",
        query="faith charity",
        curator_rationale="Baseline annotation.",
        judgments=[
            EvidenceJudgment(reference="bofm/1-ne/1/1", grade=3),
            EvidenceJudgment(reference="bofm/1-ne/1/2", grade=2),
        ],
    )
    changed_annotation = base.model_copy(update={"curator_rationale": "Changed annotation."})
    runner = EvaluationRunner(service)

    first = runner.run(
        [base],
        corpus_version=metadata.corpus_version,
        retrieval_config=metadata.retrieval_config,
        metric_depths=[1],
    ).report
    changed = runner.run(
        [changed_annotation],
        corpus_version=metadata.corpus_version,
        retrieval_config=metadata.retrieval_config,
        metric_depths=[1, 2],
    ).report

    assert first.identities.annotation_digest != changed.identities.annotation_digest
    assert first.identities.metric_depths_digest != changed.identities.metric_depths_digest
    assert first.report_digest != changed.report_digest


def test_performance_report_is_diagnostic_and_identity_bound(service) -> None:
    report = measure_performance(
        service,
        reference="bofm/1-ne/1/1",
        query="faith",
        warmup_count=1,
        iterations=3,
    )

    assert report.acceptance_gate is False
    assert report.warmup_count == 1
    assert report.measured_iterations == 3
    assert set(report.operations) == {
        "passage_lookup",
        "context_lookup",
        "lexical_search",
        "official_traversal",
    }
    assert all(summary.p95_ms >= 0 for summary in report.operations.values())
