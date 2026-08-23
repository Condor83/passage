from pathlib import Path

import pytest

from passage.eval.phase0 import (
    Phase0ProbeDefinition,
    ProbeCitation,
    ProbeEvidenceItem,
    _evidence_class_errors,
    load_phase0_probe_definition,
)

DEFINITION = Path(__file__).parents[2] / "fixtures/evaluation/phase0_probe.json"


def test_locked_phase0_definition_has_only_present_synthetic_lanes() -> None:
    definition = load_phase0_probe_definition(DEFINITION)

    assert definition.scope == "directional_phase_0"
    assert definition.present_lanes == ["exact", "lexical", "official"]
    assert definition.absent_lanes == ["derived", "experimental"]
    assert definition.rubric.coverage_metric == "reference_pool_coverage"
    assert len(definition.cases) == 2


def test_definition_rejects_lane_scope_drift() -> None:
    payload = load_phase0_probe_definition(DEFINITION).model_dump(mode="json")
    payload["present_lanes"] = ["exact", "lexical"]

    with pytest.raises(ValueError, match="present lanes"):
        Phase0ProbeDefinition.model_validate(payload)


def test_evidence_class_audit_detects_mislabeled_items() -> None:
    citation = ProbeCitation(
        corpus_version="corpus-test",
        retrieval_config="baseline-test",
        reference="bofm/1-ne/1/1",
        content_hash="a" * 64,
        source_spans_digest="b" * 64,
    )
    mislabeled = ProbeEvidenceItem.model_construct(
        evidence_class="official",
        citation=citation,
        official_edge_id=None,
        evidence_spans_digest="c" * 64,
    )

    assert _evidence_class_errors("case", "operation", [mislabeled]) == [
        "case:operation:official_missing_edge"
    ]


def test_evidence_item_contract_rejects_class_shape_errors() -> None:
    citation = ProbeCitation(
        corpus_version="corpus-test",
        retrieval_config="baseline-test",
        reference="bofm/1-ne/1/1",
        content_hash="a" * 64,
        source_spans_digest="b" * 64,
    )

    with pytest.raises(ValueError, match="requires an official edge"):
        ProbeEvidenceItem(
            evidence_class="official",
            citation=citation,
            evidence_spans_digest="c" * 64,
        )
