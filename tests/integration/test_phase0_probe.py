from pathlib import Path

from passage.domain.models import SnapshotRequest
from passage.eval.phase0 import Phase0ProbeRunner, load_phase0_probe_definition

DEFINITION = Path(__file__).parents[1] / "fixtures/evaluation/phase0_probe.json"


def test_phase0_probe_is_identity_bound_reproducible_and_not_h1(
    service,
    tmp_path: Path,
) -> None:
    definition = load_phase0_probe_definition(DEFINITION)
    metadata = service.get_corpus(SnapshotRequest())
    runner = Phase0ProbeRunner(service)

    first = runner.run(
        definition,
        corpus_version=metadata.corpus_version,
        retrieval_config=metadata.retrieval_config,
        output_directory=tmp_path / "reports",
    )
    second = runner.run(
        definition,
        corpus_version=metadata.corpus_version,
        retrieval_config=metadata.retrieval_config,
        output_directory=tmp_path / "reports",
    )

    assert first.report == second.report
    assert first.path == second.path
    assert first.path is not None
    assert first.path.stat().st_mode & 0o777 == 0o600
    assert first.report.present_lanes == ["exact", "lexical", "official"]
    assert first.report.absent_lanes == ["derived", "experimental"]
    assert first.report.rubric.coverage_metric == "reference_pool_coverage"
    assert first.report.zero_citation_errors is True
    assert first.report.zero_evidence_class_errors is True
    assert first.report.no_fatal_atomic_contract_problem is True
    assert first.report.h1_claim is False
    assert first.report.h1_status == "not_evaluated"
    assert first.report.promotion_eligible is False
    for result in first.report.cases:
        assert [trace.operation for trace in result.traces] == [
            "get_corpus",
            "get_passage",
            "get_context",
            "search_lexical",
            "traverse_references",
            "search_evidence",
        ]
        assert all(
            citation.corpus_version == metadata.corpus_version
            and citation.retrieval_config == metadata.retrieval_config
            for trace in result.traces
            for citation in trace.citations
        )
        assert result.coverage.atomic_ratio >= 0
        assert result.coverage.comparator_ratio >= 0
        assert any(
            item.evidence_class == "official" for trace in result.traces for item in trace.evidence
        )


def test_phase0_probe_detects_snapshot_identity_as_fatal(
    service,
    monkeypatch,
) -> None:
    definition = load_phase0_probe_definition(DEFINITION)
    metadata = service.get_corpus(SnapshotRequest())
    original = service.search_lexical

    def drift(request):
        return original(request).model_copy(update={"corpus_version": "corpus-drift"})

    monkeypatch.setattr(service, "search_lexical", drift)
    report = (
        Phase0ProbeRunner(service)
        .run(
            definition,
            corpus_version=metadata.corpus_version,
            retrieval_config=metadata.retrieval_config,
        )
        .report
    )

    assert report.no_fatal_atomic_contract_problem is False
    assert any("snapshot_identity" in problem for problem in report.fatal_atomic_contract_problems)


def test_phase0_probe_detects_citation_mismatch(service, monkeypatch) -> None:
    definition = load_phase0_probe_definition(DEFINITION)
    metadata = service.get_corpus(SnapshotRequest())
    original = service.search_lexical

    def mismatch(request):
        response = original(request)
        record = response.records[0]
        passage = record.passage.model_copy(update={"content_hash": "f" * 64})
        changed = record.model_copy(update={"passage": passage})
        return response.model_copy(update={"records": [changed, *response.records[1:]]})

    monkeypatch.setattr(service, "search_lexical", mismatch)
    report = (
        Phase0ProbeRunner(service)
        .run(
            definition,
            corpus_version=metadata.corpus_version,
            retrieval_config=metadata.retrieval_config,
        )
        .report
    )

    assert report.zero_citation_errors is False
    assert any("mismatch" in error for error in report.citation_errors)
