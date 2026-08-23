import pytest

from passage.ingest.apparatus import (
    OFFICIAL_REFERENCE_GRAMMAR_VERSION,
    OfficialReferenceParseCode,
    OfficialReferenceParseError,
    OfficialReferenceParseState,
    parse_official_references,
    require_official_references,
)

VALID_INTERNAL = {f"bofm/1-ne/1/{verse}" for verse in range(1, 5)}


def parse(value: str):
    return parse_official_references(value, valid_internal_references=VALID_INTERNAL)


def test_v1_parses_one_internal_target_and_preserves_identity() -> None:
    result = parse("bofm/1-ne/1/2")

    assert result.grammar_version == OFFICIAL_REFERENCE_GRAMMAR_VERSION
    assert result.state is OfficialReferenceParseState.PARSED
    assert result.code is OfficialReferenceParseCode.PARSED
    assert result.normalized_text == "bofm/1-ne/1/2"
    assert result.targets[0].model_dump(mode="json") == {
        "kind": "internal",
        "work": "bofm",
        "book": "1-ne",
        "chapter": 1,
        "verse": 2,
        "end_verse": None,
        "label": None,
    }


def test_v1_keeps_external_target_typed_and_unresolved() -> None:
    result = parse("bible/john/3/16")

    assert result.state is OfficialReferenceParseState.UNRESOLVED_EXTERNAL
    assert result.code is OfficialReferenceParseCode.UNRESOLVED_EXTERNAL_TARGET
    assert result.targets[0].kind == "external"
    assert result.targets[0].resolution == "unresolved_external"


def test_v1_supports_only_explicit_semicolon_multiple_targets() -> None:
    result = parse("  bofm/1-ne/1/2 ; bible/john/3/16.  ")

    assert result.normalized_text == "bofm/1-ne/1/2; bible/john/3/16"
    assert [target.kind for target in result.targets] == ["internal", "external"]


def test_v1_supports_internal_and_external_ranges() -> None:
    internal = parse("bofm/1-ne/1/2-4")
    external = parse("dc/section/1/1-3")

    assert internal.targets[0].end_verse == 4
    assert external.targets[0].end_verse == 3


@pytest.mark.parametrize(
    ("value", "state", "code"),
    [
        (
            "bofm/1-ne/1/2 trailing",
            OfficialReferenceParseState.UNSUPPORTED,
            OfficialReferenceParseCode.UNSUPPORTED_SYNTAX,
        ),
        (
            "bofm/1-ne/1/2, bible/john/3/16",
            OfficialReferenceParseState.AMBIGUOUS,
            OfficialReferenceParseCode.AMBIGUOUS_SYNTAX,
        ),
        (
            "bofm/unknown/1/1",
            OfficialReferenceParseState.INVALID,
            OfficialReferenceParseCode.INVALID_CANONICAL_TARGET,
        ),
        (
            "bofm/1-ne/1/5",
            OfficialReferenceParseState.INVALID,
            OfficialReferenceParseCode.INVALID_CANONICAL_TARGET,
        ),
        (
            "unknown/work/1/1",
            OfficialReferenceParseState.UNSUPPORTED,
            OfficialReferenceParseCode.UNSUPPORTED_SYNTAX,
        ),
        (
            "bofm/1-ne/1/2; unsupported",
            OfficialReferenceParseState.UNSUPPORTED,
            OfficialReferenceParseCode.UNSUPPORTED_SYNTAX,
        ),
        (
            "bofm/1-ne/1/2; bofm/1-ne/1/2",
            OfficialReferenceParseState.INVALID,
            OfficialReferenceParseCode.DUPLICATE_TARGET,
        ),
    ],
)
def test_v1_fails_closed_without_partial_targets(
    value: str,
    state: OfficialReferenceParseState,
    code: OfficialReferenceParseCode,
) -> None:
    result = parse(value)

    assert result.state is state
    assert result.code is code
    assert result.targets == []
    assert result.normalized_text is None


def test_required_parse_exposes_stable_failure_result() -> None:
    with pytest.raises(OfficialReferenceParseError) as failure:
        require_official_references(
            "bofm/1-ne/1/2 and bible/john/3/16",
            valid_internal_references=VALID_INTERNAL,
        )

    assert failure.value.result.code is OfficialReferenceParseCode.AMBIGUOUS_SYNTAX


def test_v1_duplicate_and_output_behavior_is_deterministic() -> None:
    first = parse("bofm/1-ne/1/2; bible/john/3/16")
    second = parse("bofm/1-ne/1/2; bible/john/3/16")

    assert first.model_dump_json() == second.model_dump_json()
