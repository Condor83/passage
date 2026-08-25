import pytest

from passage.domain.references import reference_target_key
from passage.ingest.apparatus import (
    CHURCH_PDF_REFERENCE_GRAMMAR_VERSION,
    OFFICIAL_REFERENCE_GRAMMAR_VERSION,
    OfficialReferenceParseCode,
    OfficialReferenceParseError,
    OfficialReferenceParseState,
    parse_church_pdf_footnote,
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


def test_church_pdf_grammar_parses_internal_shorthand_and_external_targets() -> None:
    result = parse_church_pdf_footnote(
        "2 Ne. 9:39; 32:8; Alma 30:42 (42, 53).",
        valid_internal_references={
            "bofm/2-ne/9/39",
            "bofm/2-ne/32/8",
            "bofm/alma/30/42",
        },
    )

    assert result.grammar_version == CHURCH_PDF_REFERENCE_GRAMMAR_VERSION
    assert result.state is OfficialReferenceParseState.PARSED
    assert result.normalized_text == ("bofm/2-ne/9/39; bofm/2-ne/32/8; bofm/alma/30/42")
    assert [target.label for target in result.targets] == [
        "2 Ne. 9:39",
        "2 Ne. 32:8",
        "Alma 30:42 (42, 53)",
    ]


def test_church_pdf_grammar_parses_verse_lists_ranges_and_topic_suffix() -> None:
    result = parse_church_pdf_footnote(
        "Gen. 19:5, 24 (24–25); 2 Ne. 23:19. TG Homosexual Behavior.",  # noqa: RUF001
        valid_internal_references={"bofm/2-ne/23/19"},
    )

    assert result.state is OfficialReferenceParseState.UNRESOLVED_EXTERNAL
    assert [
        (target.work, target.book, target.chapter, target.verse, target.end_verse)
        for target in result.targets
    ] == [
        ("bible", "gen", 19, 5, None),
        ("bible", "gen", 19, 24, None),
        ("bofm", "2-ne", 23, 19, None),
    ]


def test_church_pdf_grammar_keeps_explicit_ranges() -> None:
    result = parse_church_pdf_footnote(
        "Morm. 3:18–19; D&C 121:41-43; Moses 1:10.",  # noqa: RUF001
        valid_internal_references={
            "bofm/morm/3/18",
            "bofm/morm/3/19",
        },
    )

    assert result.state is OfficialReferenceParseState.UNRESOLVED_EXTERNAL
    assert [target.end_verse for target in result.targets] == [19, 43, None]
    assert [target.work for target in result.targets] == ["bofm", "dc", "pgp"]


def test_church_pdf_grammar_distinguishes_non_reference_notes() -> None:
    result = parse_church_pdf_footnote(
        "TG Faith.",
        valid_internal_references=VALID_INTERNAL,
    )

    assert result.state is OfficialReferenceParseState.NO_REFERENCE
    assert result.code is OfficialReferenceParseCode.NO_REFERENCE
    assert result.targets == []


def test_church_pdf_grammar_quarantines_unknown_reference_abbreviations() -> None:
    result = parse_church_pdf_footnote(
        "Po. 42:2.",
        valid_internal_references=VALID_INTERNAL,
    )

    assert result.state is OfficialReferenceParseState.UNSUPPORTED
    assert result.code is OfficialReferenceParseCode.UNSUPPORTED_SYNTAX
    assert result.targets == []


@pytest.mark.parametrize("value", ["", "   "])
def test_church_pdf_grammar_blocks_empty_note_text(value: str) -> None:
    result = parse_church_pdf_footnote(
        value,
        valid_internal_references=VALID_INTERNAL,
    )

    assert result.state is OfficialReferenceParseState.UNSUPPORTED
    assert result.targets == []


def test_church_pdf_grammar_preserves_whole_chapters_and_sections_as_typed_targets() -> None:
    result = parse_church_pdf_footnote(
        "Heb. 11; D&C 138; Alma 1–3.",  # noqa: RUF001
        valid_internal_references={
            "bofm/alma/1/1",
            "bofm/alma/2/1",
            "bofm/alma/3/1",
        },
    )

    assert result.state is OfficialReferenceParseState.UNRESOLVED_EXTERNAL
    assert [target.model_dump(mode="json") for target in result.targets] == [
        {
            "kind": "external_chapter",
            "work": "bible",
            "book": "heb",
            "chapter": 11,
            "end_chapter": None,
            "unit": "chapter",
            "label": "Heb. 11",
            "resolution": "unresolved_external",
        },
        {
            "kind": "external_chapter",
            "work": "dc",
            "book": "section",
            "chapter": 138,
            "end_chapter": None,
            "unit": "section",
            "label": "D&C 138",
            "resolution": "unresolved_external",
        },
        {
            "kind": "internal_chapter",
            "work": "bofm",
            "book": "alma",
            "chapter": 1,
            "end_chapter": 3,
            "unit": "chapter",
            "label": "Alma 1–3",  # noqa: RUF001
        },
    ]
    assert result.normalized_text == "bible/heb/11; dc/section/138; bofm/alma/1-3"


def test_church_pdf_grammar_parses_chapter_units_mixed_with_verse_shorthand() -> None:
    result = parse_church_pdf_footnote(
        "IE across the record. Alma 1:2; 2; 3; 4:1-2.",
        valid_internal_references={
            "bofm/alma/1/2",
            "bofm/alma/2/1",
            "bofm/alma/3/1",
            "bofm/alma/4/1",
            "bofm/alma/4/2",
        },
    )

    assert [reference_target_key(target) for target in result.targets] == [
        "bofm/alma/1/2",
        "bofm/alma/2",
        "bofm/alma/3",
        "bofm/alma/4/1-2",
    ]


@pytest.mark.parametrize(
    "value",
    [
        "A long ministry spans Alma 1–3.",  # noqa: RUF001
        "See Alma 1-3 for the complete account.",
        "IE as recorded in Alma 1-3.",
        "See accounts of the mission in Alma 1–3.",  # noqa: RUF001
    ],
)
def test_church_pdf_grammar_accepts_bounded_prose_around_chapter_ranges(value: str) -> None:
    result = parse_church_pdf_footnote(
        value,
        valid_internal_references={
            "bofm/alma/1/1",
            "bofm/alma/2/1",
            "bofm/alma/3/1",
        },
    )

    assert [reference_target_key(target) for target in result.targets] == ["bofm/alma/1-3"]


def test_church_pdf_grammar_parses_chapter_range_then_see_also_verse_targets() -> None:
    result = parse_church_pdf_footnote(
        "See 1 Ne. 1–2. See also 1 Ne. 3:1; 2 Ne. 1:1.",  # noqa: RUF001
        valid_internal_references={
            "bofm/1-ne/1/1",
            "bofm/1-ne/2/1",
            "bofm/1-ne/3/1",
            "bofm/2-ne/1/1",
        },
    )

    assert [reference_target_key(target) for target in result.targets] == [
        "bofm/1-ne/1-2",
        "bofm/1-ne/3/1",
        "bofm/2-ne/1/1",
    ]


def test_church_pdf_grammar_parses_chapter_ranges_joined_by_explanatory_prose() -> None:
    result = parse_church_pdf_footnote(
        "IE Mal. 3–4, quoted in 3 Ne. 24–25.",  # noqa: RUF001
        valid_internal_references={"bofm/3-ne/24/1", "bofm/3-ne/25/1"},
    )

    assert [reference_target_key(target) for target in result.targets] == [
        "bible/mal/3-4",
        "bofm/3-ne/24-25",
    ]


def test_church_pdf_grammar_parses_explicit_references_after_explanatory_prose() -> None:
    result = parse_church_pdf_footnote(
        "IE depend upon. 2 Kgs. 16:8 (7-9).",
        valid_internal_references=VALID_INTERNAL,
    )

    assert result.state is OfficialReferenceParseState.UNRESOLVED_EXTERNAL
    actual = [(target.work, target.book, target.chapter, target.verse) for target in result.targets]
    assert actual == [("bible", "2-kgs", 16, 8)]


def test_church_pdf_grammar_rejects_invalid_internal_target_without_partial_edges() -> None:
    result = parse_church_pdf_footnote(
        "1 Ne. 1:2; 9:99; John 3:16.",
        valid_internal_references={"bofm/1-ne/1/2"},
    )

    assert result.state is OfficialReferenceParseState.INVALID
    assert result.code is OfficialReferenceParseCode.INVALID_CANONICAL_TARGET
    assert result.targets == []


@pytest.mark.parametrize(
    "value",
    [
        "Ezek.1:1; 1 Ne.1:2 (1–2).",  # noqa: RUF001
        "1 Ne. 1:2. [OMNI]",
        "1 Ne. 1:2;",
    ],
)
def test_church_pdf_grammar_accepts_mechanical_pdf_artifacts(value: str) -> None:
    result = parse_church_pdf_footnote(
        value,
        valid_internal_references={"bofm/1-ne/1/2"},
    )

    assert result.targets


def test_church_pdf_grammar_types_jst_references_as_external() -> None:
    result = parse_church_pdf_footnote(
        "Rev. 2:27; JST Rev. 2:27 (Bible Appendix).",
        valid_internal_references=VALID_INTERNAL,
    )

    assert result.state is OfficialReferenceParseState.UNRESOLVED_EXTERNAL
    assert [(target.work, target.book) for target in result.targets] == [
        ("bible", "rev"),
        ("bible", "jst-rev"),
    ]


def test_church_pdf_grammar_parses_see_also_after_a_bd_prelude() -> None:
    result = parse_church_pdf_footnote(
        "BD Lost books. See also Alma 33:15; 34:7.",
        valid_internal_references={"bofm/alma/33/15", "bofm/alma/34/7"},
    )

    assert [reference_target_key(target) for target in result.targets] == [
        "bofm/alma/33/15",
        "bofm/alma/34/7",
    ]


def test_church_pdf_grammar_ignores_nonreference_see_also_suffix() -> None:
    result = parse_church_pdf_footnote(
        "D&C 3:18 (16-20). See also title page of the Book of Mormon.",
        valid_internal_references=VALID_INTERNAL,
    )

    assert [reference_target_key(target) for target in result.targets] == ["dc/section/3/18"]


def test_church_pdf_grammar_preserves_jst_note_context_in_label() -> None:
    result = parse_church_pdf_footnote(
        "JST Matt. 6:14 (Matt. 6:13 note a).",
        valid_internal_references=VALID_INTERNAL,
    )

    assert [reference_target_key(target) for target in result.targets] == ["bible/jst-matt/6/14"]
