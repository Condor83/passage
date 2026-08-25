from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from passage.domain.models import (
    InternalReferenceTarget,
    PdfSourceSpan,
)
from passage.ingest import official_edges
from passage.ingest.base import ExtractedNote, ExtractedPassage, ExtractionResult
from passage.ingest.candidate import load_candidate
from passage.ingest.normalize import normalize_extraction, serialize_jsonl, with_recomputed_digest
from passage.ingest.official_edges import (
    OfficialEdgeDerivation,
    OfficialReferenceCorrectionProfile,
    OfficialReferenceNoteCorrection,
    OfficialReferenceReplacementNote,
    derive_official_edges,
    publish_official_edge_derivation,
)
from passage.ingest.validation import StructureManifest

STRUCTURE = StructureManifest(schema_version=1, source={"fixture": True}, books={"1-ne": [2]})
SPAN = PdfSourceSpan(page=1, bbox=(1.0, 2.0, 3.0, 4.0), order=0)


def _corpus(*notes: ExtractedNote):
    extraction = ExtractionResult(
        source_path=Path("/private/source.pdf"),
        source_format="pdf",
        profile="official-edge-test-v1",
        passages=[
            ExtractedPassage(
                reference="bofm/1-ne/1/1",
                text="First verse",
                source_spans=[SPAN],
            ),
            ExtractedPassage(
                reference="bofm/1-ne/1/2",
                text="Second verse",
                source_spans=[SPAN.model_copy(update={"order": 1})],
            ),
        ],
        notes=list(notes),
    )
    return normalize_extraction(extraction, STRUCTURE)


def _note(note_id: str, anchor: str, text: str | None) -> ExtractedNote:
    return ExtractedNote(
        note_id=note_id,
        origin_reference="bofm/1-ne/1/1",
        anchor=anchor,
        kind="official-footnote",
        label=anchor,
        text=text,
        source_spans=[SPAN.model_copy(update={"order": len(anchor) + 1})],
    )


def _text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _source_sha256(corpus) -> str:
    return hashlib.sha256(serialize_jsonl(corpus)).hexdigest()


def test_derivation_creates_provenance_backed_internal_and_external_edges() -> None:
    corpus = _corpus(
        _note("note-a", "a", "1 Ne. 1:2; John 3:16."),
        _note("note-b", "b", "TG Faith."),
    )

    derived = derive_official_edges(
        corpus, STRUCTURE, source_candidate_sha256=_source_sha256(corpus)
    )

    assert derived.report.complete is True
    assert derived.report.parsed_note_count == 1
    assert derived.report.no_reference_note_count == 1
    assert derived.report.edge_count == 2
    assert {edge.target.kind for edge in derived.corpus.edges} == {"internal", "external"}
    assert all(edge.source_spans for edge in derived.corpus.edges)
    assert all(edge.source_attribution == "official-footnote" for edge in derived.corpus.edges)
    assert all(edge.grammar_version == "official-reference-v2" for edge in derived.corpus.edges)


def test_derivation_counts_typed_chapter_targets_by_work_boundary() -> None:
    corpus = _corpus(_note("note-a", "a", "1 Ne. 1; D&C 2."))

    derived = derive_official_edges(
        corpus, STRUCTURE, source_candidate_sha256=_source_sha256(corpus)
    )

    assert derived.report.complete is True
    assert derived.report.internal_edge_count == 1
    assert derived.report.external_edge_count == 1
    assert {edge.target.kind for edge in derived.corpus.edges} == {
        "internal_chapter",
        "external_chapter",
    }


def test_digest_bound_correction_replaces_text_and_supplies_explicit_targets() -> None:
    original_text = "Editorial explanation without parseable shorthand."
    corpus = _corpus(_note("note-a", "a", original_text))
    source_sha256 = _source_sha256(corpus)
    profile = OfficialReferenceCorrectionProfile(
        schema_version=1,
        profile_id="fixture-corrections-v1",
        source_candidate_sha256=source_sha256,
        corrections=[
            OfficialReferenceNoteCorrection(
                note_id="note-a",
                expected_text_sha256=_text_sha256(original_text),
                replacements=[
                    OfficialReferenceReplacementNote(
                        anchor="a",
                        text="Corrected editorial explanation.",
                        targets=[InternalReferenceTarget(book="1-ne", chapter=1, verse=2)],
                    )
                ],
            )
        ],
    )

    derived = derive_official_edges(
        corpus,
        STRUCTURE,
        source_candidate_sha256=source_sha256,
        correction_profile=profile,
    )

    assert derived.report.complete is True
    assert derived.report.correction_profile_digest is not None
    assert derived.corpus.notes[0].text == "Corrected editorial explanation."
    assert derived.corpus.notes[0].label == "a"
    assert [edge.target.kind for edge in derived.corpus.edges] == ["internal"]


def test_digest_bound_correction_can_split_one_source_note_into_sequential_anchors() -> None:
    original_text = "1 Ne. 1:2. b 1 Ne. 1:1."
    corpus = _corpus(_note("note-a", "a", original_text))
    source_sha256 = _source_sha256(corpus)
    profile = OfficialReferenceCorrectionProfile(
        schema_version=1,
        profile_id="fixture-split-v1",
        source_candidate_sha256=source_sha256,
        corrections=[
            OfficialReferenceNoteCorrection(
                note_id="note-a",
                expected_text_sha256=_text_sha256(original_text),
                replacements=[
                    OfficialReferenceReplacementNote(anchor="a", label="a", text="1 Ne. 1:2."),
                    OfficialReferenceReplacementNote(anchor="b", label="b", text="1 Ne. 1:1."),
                ],
            )
        ],
    )

    derived = derive_official_edges(
        corpus,
        STRUCTURE,
        source_candidate_sha256=source_sha256,
        correction_profile=profile,
    )

    assert derived.report.complete is True
    assert derived.report.total_note_count == 2
    assert [note.anchor for note in derived.corpus.notes] == ["a", "b"]
    assert len({note.note_id for note in derived.corpus.notes}) == 2
    assert len(derived.corpus.edges) == 2


def test_correction_profile_rejects_a_different_source_or_note_text() -> None:
    original_text = "1 Ne. 1:2."
    corpus = _corpus(_note("note-a", "a", original_text))
    source_sha256 = _source_sha256(corpus)
    profile = OfficialReferenceCorrectionProfile(
        schema_version=1,
        profile_id="fixture-mismatch-v1",
        source_candidate_sha256=source_sha256,
        corrections=[
            OfficialReferenceNoteCorrection(
                note_id="note-a",
                expected_text_sha256="0" * 64,
                replacements=[OfficialReferenceReplacementNote(anchor="a", text=original_text)],
            )
        ],
    )

    with pytest.raises(ValueError, match="supplied digest"):
        derive_official_edges(
            corpus,
            STRUCTURE,
            source_candidate_sha256="5" * 64,
            correction_profile=profile,
        )

    with pytest.raises(ValueError, match="note text"):
        derive_official_edges(
            corpus,
            STRUCTURE,
            source_candidate_sha256=source_sha256,
            correction_profile=profile,
        )

    with pytest.raises(ValueError, match="correction profile"):
        derive_official_edges(
            corpus,
            STRUCTURE,
            source_candidate_sha256=source_sha256,
            correction_profile=profile.model_copy(update={"source_candidate_sha256": "6" * 64}),
        )


def test_correction_profile_cannot_publish_duplicate_apparatus_anchors() -> None:
    original_text = "1 Ne. 1:2."
    corpus = _corpus(
        _note("note-a", "a", original_text),
        _note("note-b", "b", "TG Faith."),
    )
    source_sha256 = _source_sha256(corpus)
    profile = OfficialReferenceCorrectionProfile(
        schema_version=1,
        profile_id="fixture-duplicate-anchor-v1",
        source_candidate_sha256=source_sha256,
        corrections=[
            OfficialReferenceNoteCorrection(
                note_id="note-a",
                expected_text_sha256=_text_sha256(original_text),
                replacements=[OfficialReferenceReplacementNote(anchor="b", text="1 Ne. 1:2.")],
            )
        ],
    )

    with pytest.raises(ValueError, match="duplicate apparatus anchors"):
        derive_official_edges(
            corpus,
            STRUCTURE,
            source_candidate_sha256=source_sha256,
            correction_profile=profile,
        )


def test_incomplete_derivation_publishes_report_and_preview_but_not_candidate(
    tmp_path: Path,
) -> None:
    corpus = _corpus(
        _note("note-a", "a", "1 Ne. 1:2."),
        _note("note-b", "b", "1 Ne. 1:2 trailing"),
    )
    derived = derive_official_edges(
        corpus, STRUCTURE, source_candidate_sha256=_source_sha256(corpus)
    )

    published = publish_official_edge_derivation(
        tmp_path / "private",
        derived,
        repository_root=tmp_path / "repository",
        scope="book-of-mormon",
    )

    assert derived.report.complete is False
    assert derived.report.blocking_note_count == 1
    assert published.candidate_path is None
    assert published.manifest_path is None
    assert published.edge_preview_path.is_file()
    report = json.loads(published.report_path.read_text(encoding="utf-8"))
    assert report["findings"] == [
        {
            "anchor": "b",
            "code": "official_reference_unsupported_syntax",
            "note_id": "note-b",
            "origin_reference": "bofm/1-ne/1/1",
            "state": "unsupported",
        }
    ]
    assert "trailing" not in published.report_path.read_text(encoding="utf-8")


def test_complete_derivation_publishes_importable_candidate_and_manifest(
    tmp_path: Path,
) -> None:
    corpus = _corpus(_note("note-a", "a", "1 Ne. 1:2."))
    derived = derive_official_edges(
        corpus, STRUCTURE, source_candidate_sha256=_source_sha256(corpus)
    )

    published = publish_official_edge_derivation(
        tmp_path / "private",
        derived,
        repository_root=tmp_path / "repository",
        scope="book-of-mormon",
    )

    assert published.candidate_path is not None
    assert published.manifest_path is not None
    manifest = json.loads(published.manifest_path.read_text(encoding="utf-8"))
    assert manifest["candidate_sha256"] == published.successor_candidate_sha256
    assert manifest["normalized_digest"] == derived.corpus.normalized_digest
    assert manifest["edge_count"] == 1
    assert manifest["accepted"] is False
    assert manifest["active"] is False
    assert published.candidate_path.stat().st_mode & 0o777 == 0o600
    assert published.manifest_path.stat().st_mode & 0o777 == 0o600
    assert published.report_path.stat().st_mode & 0o777 == 0o600
    assert published.edge_preview_path.stat().st_mode & 0o777 == 0o600
    assert published.candidate_path.parent.stat().st_mode & 0o777 == 0o700

    loaded = load_candidate(
        published.candidate_path,
        published.manifest_path,
        structure=STRUCTURE,
    )
    assert (
        with_recomputed_digest(loaded.corpus).normalized_digest == loaded.corpus.normalized_digest
    )


def test_publisher_recovers_after_interruption_before_candidate_install(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    corpus = _corpus(_note("note-a", "a", "1 Ne. 1:2."))
    derived = derive_official_edges(
        corpus, STRUCTURE, source_candidate_sha256=_source_sha256(corpus)
    )
    real_link = official_edges.os.link

    def interrupt_candidate(source, destination, *, follow_symlinks):
        if Path(destination).name == "candidate.jsonl":
            raise OSError("injected publication interruption")
        return real_link(source, destination, follow_symlinks=follow_symlinks)

    monkeypatch.setattr(official_edges.os, "link", interrupt_candidate)
    with pytest.raises(OSError, match="injected publication interruption"):
        publish_official_edge_derivation(
            tmp_path / "private",
            derived,
            repository_root=tmp_path / "repository",
            scope="book-of-mormon",
        )

    output_dir = next(
        (tmp_path / "private" / "official-reference-derivations").rglob("report.json")
    ).parent
    assert not (output_dir / "candidate.jsonl").exists()
    assert list(output_dir.glob(".*.tmp")) == []

    monkeypatch.setattr(official_edges.os, "link", real_link)
    published = publish_official_edge_derivation(
        tmp_path / "private",
        derived,
        repository_root=tmp_path / "repository",
        scope="book-of-mormon",
    )
    assert published.candidate_path is not None
    assert published.candidate_path.is_file()
    assert published.manifest_path is not None
    assert published.manifest_path.is_file()


@pytest.mark.parametrize("text", [None, "   ", "1 Ne. 1:2 trailing"])
def test_derivation_quarantines_missing_or_unsupported_note_text(
    text: str | None,
) -> None:
    corpus = _corpus(_note("note-a", "a", text))
    derived = derive_official_edges(
        corpus, STRUCTURE, source_candidate_sha256=_source_sha256(corpus)
    )

    assert derived.report.complete is False
    assert derived.report.blocking_note_count == 1
    assert derived.corpus.edges == []


def test_derivation_rejects_new_testament_until_the_grammar_is_nt_aware() -> None:
    nt_structure = StructureManifest(
        schema_version=1,
        work="nt",
        source={"fixture": True},
        books={"john": [2]},
    )

    with pytest.raises(ValueError, match="only Book of Mormon"):
        derive_official_edges(
            _corpus(_note("note-a", "a", "John 1:2.")),
            nt_structure,
            source_candidate_sha256="e" * 64,
        )


def test_publisher_rejects_repository_as_private_root(tmp_path: Path) -> None:
    corpus = _corpus(_note("note-a", "a", "1 Ne. 1:2."))
    derived = derive_official_edges(
        corpus,
        STRUCTURE,
        source_candidate_sha256=_source_sha256(corpus),
    )

    with pytest.raises(ValueError, match="outside the repository"):
        publish_official_edge_derivation(
            tmp_path,
            derived,
            repository_root=tmp_path,
            scope="book-of-mormon",
        )


def test_publisher_revalidates_report_consistency(tmp_path: Path) -> None:
    corpus = _corpus(_note("note-a", "a", "1 Ne. 1:2 trailing"))
    derived = derive_official_edges(
        corpus,
        STRUCTURE,
        source_candidate_sha256=_source_sha256(corpus),
    )
    inconsistent = OfficialEdgeDerivation(
        corpus=derived.corpus,
        report=derived.report.model_copy(update={"complete": True}),
    )

    with pytest.raises(ValueError, match="complete state"):
        publish_official_edge_derivation(
            tmp_path / "private",
            inconsistent,
            repository_root=tmp_path / "repository",
            scope="book-of-mormon",
        )
