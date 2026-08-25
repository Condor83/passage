from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from argparse import Namespace
from pathlib import Path
from typing import Any

import pytest

from passage import cli
from passage.domain.models import PdfSourceSpan
from passage.ingest.base import ExtractedNote, ExtractedPassage, ExtractionResult
from passage.ingest.candidate import CandidateManifest
from passage.ingest.normalize import normalize_extraction, serialize_jsonl
from passage.ingest.official_edges import (
    OfficialReferenceCorrectionProfile,
    OfficialReferenceNoteCorrection,
    OfficialReferenceReplacementNote,
)
from passage.ingest.validation import load_default_structure_manifest


def _run(*arguments: str) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
    completed = subprocess.run(
        [sys.executable, "-m", "passage.cli", *arguments],
        check=False,
        capture_output=True,
        text=True,
    )
    output = completed.stdout if completed.returncode == 0 else completed.stderr
    return completed, json.loads(output)


def _write_candidate(tmp_path: Path, note_text: str) -> tuple[Path, Path, str]:
    structure = load_default_structure_manifest()
    span = PdfSourceSpan(page=1, bbox=(1.0, 2.0, 3.0, 4.0), order=0)
    extraction = ExtractionResult(
        source_path=Path("/private/source.pdf"),
        source_format="pdf",
        profile="official-edge-cli-test-v1",
        passages=[
            ExtractedPassage(
                reference=reference,
                text=f"Synthetic verse {index + 1}",
                source_spans=[span.model_copy(update={"order": index})],
            )
            for index, reference in enumerate(structure.expected_references())
        ],
        notes=[
            ExtractedNote(
                note_id="note-a",
                origin_reference="bofm/1-ne/1/1",
                anchor="a",
                kind="official-footnote",
                label="a",
                text=note_text,
                source_spans=[span.model_copy(update={"order": 7000})],
            )
        ],
    )
    corpus = normalize_extraction(extraction, structure)
    payload = serialize_jsonl(corpus)
    digest = hashlib.sha256(payload).hexdigest()
    candidate = tmp_path / "candidate.jsonl"
    candidate.write_bytes(payload)
    manifest = tmp_path / "manifest.json"
    candidate_manifest = CandidateManifest(
        schema_version=1,
        scope="book-of-mormon",
        artifact=candidate.name,
        candidate_sha256=digest,
        normalized_digest=corpus.normalized_digest,
        source_format=corpus.source_format,
        status="review_required",
        active=False,
        accepted=False,
        passage_count=len(corpus.passages),
        note_anchor_count=len(corpus.notes),
        edge_count=0,
    )
    manifest.write_text(candidate_manifest.model_dump_json(), encoding="utf-8")
    return candidate, manifest, digest


def test_cli_derives_complete_successor_without_accepting_or_activating(
    tmp_path: Path,
) -> None:
    candidate, manifest, digest = _write_candidate(tmp_path, "1 Ne. 1:2.")
    root = tmp_path / "private"

    completed, payload = _run(
        "corpus",
        "derive-official-edges",
        "--candidate",
        str(candidate),
        "--manifest",
        str(manifest),
        "--approved-candidate-sha256",
        digest,
        "--data-dir",
        str(root),
    )

    assert completed.returncode == 0
    assert payload["complete"] is True
    assert payload["edge_count"] == 1
    assert payload["ready_for_import"] is True
    assert Path(payload["candidate"]).is_file()
    assert Path(payload["manifest"]).is_file()
    assert not (root / "control.sqlite3").exists()


def test_cli_quarantines_incomplete_derivation_without_successor_candidate(
    tmp_path: Path,
) -> None:
    candidate, manifest, digest = _write_candidate(tmp_path, "1 Ne. 1:2 trailing")
    root = tmp_path / "private"

    completed, payload = _run(
        "corpus",
        "derive-official-edges",
        "--candidate",
        str(candidate),
        "--manifest",
        str(manifest),
        "--approved-candidate-sha256",
        digest,
        "--data-dir",
        str(root),
    )

    assert completed.returncode == 0
    assert payload["complete"] is False
    assert payload["blocking_note_count"] == 1
    assert payload["ready_for_import"] is False
    assert payload["candidate"] is None
    assert payload["manifest"] is None
    assert Path(payload["report"]).is_file()


def test_cli_applies_a_private_digest_bound_correction_profile(tmp_path: Path) -> None:
    source_text = "Unparseable editorial explanation."
    candidate, manifest, digest = _write_candidate(tmp_path, source_text)
    private_root = tmp_path / "private"
    corrections = private_root / "corrections.json"
    corrections.parent.mkdir(mode=0o700)
    profile = OfficialReferenceCorrectionProfile(
        schema_version=1,
        profile_id="cli-corrections-v1",
        source_candidate_sha256=digest,
        corrections=[
            OfficialReferenceNoteCorrection(
                note_id="note-a",
                expected_text_sha256=hashlib.sha256(source_text.encode("utf-8")).hexdigest(),
                replacements=[
                    OfficialReferenceReplacementNote(anchor="a", label="a", text="1 Ne. 1:2.")
                ],
            )
        ],
    )
    corrections.write_text(profile.model_dump_json(), encoding="utf-8")

    completed, payload = _run(
        "corpus",
        "derive-official-edges",
        "--candidate",
        str(candidate),
        "--manifest",
        str(manifest),
        "--approved-candidate-sha256",
        digest,
        "--corrections",
        str(corrections),
        "--data-dir",
        str(private_root),
    )

    assert completed.returncode == 0
    assert payload["complete"] is True
    assert payload["correction_profile_digest"]
    assert Path(payload["candidate"]).is_file()


def test_cli_rejects_correction_profile_outside_private_root(tmp_path: Path) -> None:
    source_text = "Unparseable editorial explanation."
    candidate, manifest, digest = _write_candidate(tmp_path, source_text)
    corrections = tmp_path / "corrections.json"
    profile = OfficialReferenceCorrectionProfile(
        schema_version=1,
        profile_id="cli-outside-root-v1",
        source_candidate_sha256=digest,
        corrections=[
            OfficialReferenceNoteCorrection(
                note_id="note-a",
                expected_text_sha256=hashlib.sha256(source_text.encode("utf-8")).hexdigest(),
                replacements=[
                    OfficialReferenceReplacementNote(anchor="a", label="a", text="1 Ne. 1:2.")
                ],
            )
        ],
    )
    corrections.write_text(profile.model_dump_json(), encoding="utf-8")

    completed, payload = _run(
        "corpus",
        "derive-official-edges",
        "--candidate",
        str(candidate),
        "--manifest",
        str(manifest),
        "--approved-candidate-sha256",
        digest,
        "--corrections",
        str(corrections),
        "--data-dir",
        str(tmp_path / "private"),
    )

    assert completed.returncode == 1
    assert payload["error"]["message"] == (
        "official reference correction profiles must remain under the private root"
    )
    assert (
        list((tmp_path / "private").glob("official-reference-derivations/**/candidate.jsonl")) == []
    )


def test_private_root_rejection_does_not_depend_on_current_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    repository_root = Path(__file__).resolve().parents[2]

    with pytest.raises(ValueError, match="outside the repository"):
        cli._private_root(Namespace(data_dir=repository_root / "private-forbidden"))
