from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from passage.domain.models import EpubSourceSpan, PdfSourceSpan
from passage.ingest.base import ExtractedNote, ExtractedPassage, ExtractionResult
from passage.ingest.candidate import load_candidate
from passage.ingest.normalize import normalize_extraction, serialize_jsonl
from passage.ingest.validation import StructureManifest

STRUCTURE = StructureManifest(schema_version=1, source={"fixture": True}, books={"1-ne": [2]})


def _extraction() -> ExtractionResult:
    return ExtractionResult(
        source_path=Path("/private/source.epub"),
        source_format="epub",
        profile="candidate-test-v1",
        passages=[
            ExtractedPassage(
                reference="bofm/1-ne/1/1",
                text="First verse",
                source_spans=[EpubSourceSpan(member="chapter.xhtml", start=0, end=1, order=0)],
            ),
            ExtractedPassage(
                reference="bofm/1-ne/1/2",
                text="Second verse",
                source_spans=[EpubSourceSpan(member="chapter.xhtml", start=1, end=2, order=1)],
            ),
        ],
    )


def _write_candidate(
    tmp_path: Path, extraction: ExtractionResult | None = None
) -> tuple[Path, Path]:
    extraction = extraction or _extraction()
    corpus = normalize_extraction(extraction, STRUCTURE)
    payload = serialize_jsonl(corpus)
    candidate = tmp_path / "candidate.jsonl"
    candidate.write_bytes(payload)
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "scope": "book-of-mormon",
                "artifact": candidate.name,
                "candidate_sha256": hashlib.sha256(payload).hexdigest(),
                "normalized_digest": corpus.normalized_digest,
                "source_format": corpus.source_format,
                "status": "review_required",
                "active": False,
                "accepted": False,
                "passage_count": len(corpus.passages),
                "note_anchor_count": len(corpus.notes),
                "edge_count": len(corpus.edges),
            }
        ),
        encoding="utf-8",
    )
    return candidate, manifest


def test_load_candidate_verifies_identity_and_structure(tmp_path: Path) -> None:
    candidate, manifest = _write_candidate(tmp_path)

    loaded = load_candidate(candidate, manifest, structure=STRUCTURE)

    assert loaded.candidate_sha256 == hashlib.sha256(candidate.read_bytes()).hexdigest()
    assert loaded.corpus.normalized_digest == loaded.manifest.normalized_digest
    assert [passage.reference for passage in loaded.corpus.passages] == [
        "bofm/1-ne/1/1",
        "bofm/1-ne/1/2",
    ]


def test_load_candidate_rejects_changed_bytes_before_parsing(tmp_path: Path) -> None:
    candidate, manifest = _write_candidate(tmp_path)
    candidate.write_bytes(candidate.read_bytes() + b"\n")

    with pytest.raises(ValueError, match="candidate digest does not match manifest"):
        load_candidate(candidate, manifest, structure=STRUCTURE)


def test_load_candidate_rejects_reordered_records(tmp_path: Path) -> None:
    candidate, manifest = _write_candidate(tmp_path)
    records = candidate.read_text(encoding="utf-8").splitlines()
    records[1], records[2] = records[2], records[1]
    payload = ("\n".join(records) + "\n").encode()
    candidate.write_bytes(payload)
    raw_manifest = json.loads(manifest.read_text(encoding="utf-8"))
    raw_manifest["candidate_sha256"] = hashlib.sha256(payload).hexdigest()
    manifest.write_text(json.dumps(raw_manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="canonical serialized form"):
        load_candidate(candidate, manifest, structure=STRUCTURE)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("normalized_digest", "a" * 64, "normalized digest"),
        ("source_format", "pdf", "source format"),
        ("passage_count", 3, "passage count"),
        ("note_anchor_count", 1, "note count"),
        ("edge_count", 1, "edge count"),
    ],
)
def test_load_candidate_rejects_manifest_identity_mismatch(
    tmp_path: Path, field: str, value: str | int, message: str
) -> None:
    candidate, manifest = _write_candidate(tmp_path)
    raw_manifest = json.loads(manifest.read_text(encoding="utf-8"))
    raw_manifest[field] = value
    manifest.write_text(json.dumps(raw_manifest), encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        load_candidate(candidate, manifest, structure=STRUCTURE)


def test_load_candidate_rejects_duplicate_apparatus_anchors(tmp_path: Path) -> None:
    span = EpubSourceSpan(member="chapter.xhtml", start=2, end=3, order=2)
    extraction = _extraction().model_copy(
        update={
            "notes": [
                ExtractedNote(
                    note_id="note-a",
                    origin_reference="bofm/1-ne/1/1",
                    anchor="a",
                    kind="official-footnote",
                    source_spans=[span],
                ),
                ExtractedNote(
                    note_id="note-b",
                    origin_reference="bofm/1-ne/1/1",
                    anchor="a",
                    kind="official-footnote",
                    source_spans=[span],
                ),
            ]
        }
    )
    candidate, manifest = _write_candidate(tmp_path, extraction)

    with pytest.raises(ValueError, match="duplicate apparatus anchors"):
        load_candidate(candidate, manifest, structure=STRUCTURE)


def test_load_candidate_rejects_nonsequential_official_anchors(tmp_path: Path) -> None:
    extraction = _extraction().model_copy(
        update={
            "notes": [
                ExtractedNote(
                    note_id="note-b",
                    origin_reference="bofm/1-ne/1/1",
                    anchor="b",
                    kind="official-footnote",
                    source_spans=[EpubSourceSpan(member="chapter.xhtml", start=2, end=3, order=2)],
                )
            ]
        }
    )
    candidate, manifest = _write_candidate(tmp_path, extraction)

    with pytest.raises(ValueError, match="not sequential"):
        load_candidate(candidate, manifest, structure=STRUCTURE)


def test_load_candidate_rejects_source_span_kind_mismatch(tmp_path: Path) -> None:
    extraction = _extraction()
    mismatched_passage = extraction.passages[0].model_copy(
        update={"source_spans": [PdfSourceSpan(page=1, bbox=(0.0, 0.0, 1.0, 1.0), order=0)]}
    )
    extraction = extraction.model_copy(
        update={"passages": [mismatched_passage, extraction.passages[1]]}
    )
    candidate, manifest = _write_candidate(tmp_path, extraction)

    with pytest.raises(ValueError, match="source span kind"):
        load_candidate(candidate, manifest, structure=STRUCTURE)
