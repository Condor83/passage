from pathlib import Path

import pytest

from scripture_chat.domain.models import EpubSourceSpan
from scripture_chat.ingest.base import (
    ExtractedEdge,
    ExtractedPassage,
    ExtractionResult,
)
from scripture_chat.ingest.normalize import normalize_extraction, serialize_jsonl
from scripture_chat.ingest.validation import (
    CorpusValidationError,
    StructureManifest,
    validate_corpus,
)


def extraction(
    passages: list[tuple[str, str]], edges: list[tuple[str, str]] | None = None
) -> ExtractionResult:
    extracted = [
        ExtractedPassage(
            reference=reference,
            text=text,
            source_spans=[
                EpubSourceSpan(member="chapter.xhtml", start=index, end=index + 1, order=index)
            ],
        )
        for index, (reference, text) in enumerate(passages)
    ]
    extracted_edges = [
        ExtractedEdge(
            origin_reference=origin,
            origin_anchor="a",
            target=target,
            source_attribution="official-footnote",
            source_spans=[
                EpubSourceSpan(member="chapter.xhtml", start=0, end=1, order=100 + index)
            ],
        )
        for index, (origin, target) in enumerate(edges or [])
    ]
    return ExtractionResult(
        source_path=Path("/private/source.epub"),
        source_format="epub",
        profile="scripture-chat-v1",
        passages=extracted,
        edges=extracted_edges,
    )


MANIFEST = StructureManifest(schema_version=1, source={}, books={"1-ne": [2]})


def test_normalized_jsonl_is_deterministic_and_content_addressed() -> None:
    source = extraction(
        [
            ("bofm/1-ne/1/1", "I, Nephi, having been born of goodly parents."),
            ("bofm/1-ne/1/2", "Yea, I make a record in the language of my father."),
        ]
    )

    corpus = normalize_extraction(source, MANIFEST)
    validate_corpus(corpus, MANIFEST)

    first = serialize_jsonl(corpus)
    second = serialize_jsonl(normalize_extraction(source, MANIFEST))
    assert first == second
    assert corpus.normalized_digest in first.decode()
    assert corpus.passages[0].canonical_order == 0


def test_validation_requires_exact_reference_set() -> None:
    corpus = normalize_extraction(
        extraction([("bofm/1-ne/1/1", "First verse")]),
        MANIFEST,
    )

    with pytest.raises(CorpusValidationError) as failure:
        validate_corpus(corpus, MANIFEST)

    assert "missing_passage" in {finding.code for finding in failure.value.findings}


def test_validation_rejects_duplicate_and_broken_local_edge() -> None:
    corpus = normalize_extraction(
        extraction(
            [
                ("bofm/1-ne/1/1", "First verse"),
                ("bofm/1-ne/1/1", "Duplicate verse"),
                ("bofm/1-ne/1/2", "Second verse"),
            ],
            [("bofm/1-ne/1/1", "bofm/1-ne/1/3")],
        ),
        MANIFEST,
    )

    with pytest.raises(CorpusValidationError) as failure:
        validate_corpus(corpus, MANIFEST)

    codes = {finding.code for finding in failure.value.findings}
    assert {"duplicate_passage", "broken_local_edge"} <= codes


def test_well_formed_external_edge_is_not_a_broken_link() -> None:
    corpus = normalize_extraction(
        extraction(
            [
                ("bofm/1-ne/1/1", "First verse"),
                ("bofm/1-ne/1/2", "Second verse"),
            ],
            [("bofm/1-ne/1/1", "bible/john/3/16")],
        ),
        MANIFEST,
    )

    validate_corpus(corpus, MANIFEST)
    assert corpus.edges[0].target.in_corpus is False
