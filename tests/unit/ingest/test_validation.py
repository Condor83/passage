from pathlib import Path

import pytest

from passage.domain.models import EpubSourceSpan, InternalReferenceTarget
from passage.ingest.base import (
    ExtractedEdge,
    ExtractedPassage,
    ExtractionResult,
)
from passage.ingest.normalize import normalize_extraction, serialize_jsonl
from passage.ingest.validation import (
    CorpusValidationError,
    StructureManifest,
    load_new_testament_structure_manifest,
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
        profile="passage-v1",
        passages=extracted,
        edges=extracted_edges,
    )


MANIFEST = StructureManifest(schema_version=1, source={}, books={"1-ne": [2]})


def test_structure_manifest_supports_new_testament_references() -> None:
    manifest = StructureManifest(
        schema_version=1,
        work="nt",
        source={"fixture": True},
        books={"matt": [2]},
    )

    assert manifest.expected_references() == ["nt/matt/1/1", "nt/matt/1/2"]


def test_new_testament_structure_manifest_is_complete() -> None:
    manifest = load_new_testament_structure_manifest()
    references = manifest.expected_references()

    assert manifest.work == "nt"
    assert len(manifest.books) == 27
    assert sum(len(chapters) for chapters in manifest.books.values()) == 260
    assert len(references) == 7_957
    assert references[0] == "nt/matt/1/1"
    assert references[-1] == "nt/rev/22/21"


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
            [("bofm/1-ne/1/1", "bofm/1-ne/1/2")],
        ),
        MANIFEST,
    )
    broken = corpus.edges[0].model_copy(
        update={"target": InternalReferenceTarget(book="1-ne", chapter=1, verse=3)}
    )
    corpus = corpus.model_copy(update={"edges": [broken]})

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
    assert corpus.edges[0].target.kind == "external"
    assert corpus.edges[0].target.resolution == "unresolved_external"


def test_normalization_expands_explicit_targets_and_preserves_edge_evidence() -> None:
    source = extraction(
        [
            ("bofm/1-ne/1/1", "First verse"),
            ("bofm/1-ne/1/2", "Second verse"),
        ],
        [("bofm/1-ne/1/1", "bofm/1-ne/1/2; bible/john/3/16")],
    )

    corpus = normalize_extraction(source, MANIFEST)

    assert [edge.target.kind for edge in corpus.edges] == ["internal", "external"]
    assert len({edge.edge_id for edge in corpus.edges}) == 2
    assert all(edge.grammar_version == "official-reference-v1" for edge in corpus.edges)
    assert all(edge.source_spans == source.edges[0].source_spans for edge in corpus.edges)
