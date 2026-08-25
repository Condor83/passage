from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from argparse import Namespace
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from passage import cli
from passage.db.control import ControlStore
from passage.domain.models import EpubSourceSpan
from passage.ingest.base import ExtractedPassage, ExtractionResult
from passage.ingest.normalize import normalize_extraction, serialize_jsonl
from passage.ingest.validation import StructureManifest, load_default_structure_manifest


def _run(*arguments: str) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
    completed = subprocess.run(
        [sys.executable, "-m", "passage.cli", *arguments],
        check=False,
        capture_output=True,
        text=True,
    )
    output = completed.stdout if completed.returncode == 0 else completed.stderr
    return completed, json.loads(output)


def _write_candidate(
    tmp_path: Path, structure: StructureManifest | None = None
) -> tuple[Path, Path, str]:
    structure = structure or load_default_structure_manifest()
    extraction = ExtractionResult(
        source_path=Path("/private/source.epub"),
        source_format="epub",
        profile="candidate-cli-test-v1",
        passages=[
            ExtractedPassage(
                reference=reference,
                text=f"Synthetic verse {index + 1}",
                source_spans=[
                    EpubSourceSpan(
                        member="chapter.xhtml",
                        start=index,
                        end=index + 1,
                        order=index,
                    )
                ],
            )
            for index, reference in enumerate(structure.expected_references())
        ],
    )
    corpus = normalize_extraction(extraction, structure)
    payload = serialize_jsonl(corpus)
    digest = hashlib.sha256(payload).hexdigest()
    candidate = tmp_path / "candidate.jsonl"
    candidate.write_bytes(payload)
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "scope": "book-of-mormon",
                "artifact": candidate.name,
                "candidate_sha256": digest,
                "normalized_digest": corpus.normalized_digest,
                "source_format": corpus.source_format,
                "status": "review_required",
                "active": False,
                "accepted": False,
                "passage_count": len(corpus.passages),
                "note_anchor_count": 0,
                "edge_count": 0,
            }
        ),
        encoding="utf-8",
    )
    return candidate, manifest, digest


def test_cli_imports_exact_approved_candidate_as_inactive_corpus(tmp_path: Path) -> None:
    candidate, manifest, digest = _write_candidate(tmp_path)
    root = tmp_path / "private"

    completed, payload = _run(
        "corpus",
        "import-candidate",
        "--candidate",
        str(candidate),
        "--manifest",
        str(manifest),
        "--approved-candidate-sha256",
        digest,
        "--edition",
        "maintainer-approved synthetic candidate",
        "--acquisition-url",
        "https://example.test/candidate.jsonl",
        "--acquisition-date",
        "2026-08-24",
        "--data-dir",
        str(root),
    )

    assert completed.returncode == 0
    assert payload["candidate_sha256"] == digest
    assert payload["accepted"] is True
    assert payload["active"] is False
    with ControlStore(root) as control:
        accepted = control.get_accepted(payload["corpus_version"])
        assert accepted is not None
        assert control.get_active() is None
        assert accepted.manifest["source_approval"] == {
            "source_sha256": digest,
            "acquisition_url": "https://example.test/candidate.jsonl",
            "acquisition_date": "2026-08-24",
            "edition": "maintainer-approved synthetic candidate",
            "language": "eng",
        }


def test_cli_rejects_candidate_not_matching_explicit_approval(tmp_path: Path) -> None:
    candidate, manifest, _digest = _write_candidate(tmp_path)
    root = tmp_path / "private"

    completed, payload = _run(
        "corpus",
        "import-candidate",
        "--candidate",
        str(candidate),
        "--manifest",
        str(manifest),
        "--approved-candidate-sha256",
        "a" * 64,
        "--edition",
        "synthetic candidate",
        "--acquisition-url",
        "https://example.test/candidate.jsonl",
        "--acquisition-date",
        "2026-08-24",
        "--data-dir",
        str(root),
    )

    assert completed.returncode == 1
    assert "explicitly approved digest" in payload["error"]["message"]
    with ControlStore(root) as control:
        assert control.accepted_count() == 0


def test_cli_rejects_incomplete_candidate_for_fixed_scope(tmp_path: Path) -> None:
    incomplete = StructureManifest(
        schema_version=1,
        source={"fixture": True},
        books={"1-ne": [2]},
    )
    candidate, manifest, digest = _write_candidate(tmp_path, incomplete)
    root = tmp_path / "private"

    completed, payload = _run(
        "corpus",
        "import-candidate",
        "--candidate",
        str(candidate),
        "--manifest",
        str(manifest),
        "--approved-candidate-sha256",
        digest,
        "--edition",
        "synthetic candidate",
        "--acquisition-url",
        "https://example.test/candidate.jsonl",
        "--acquisition-date",
        "2026-08-24",
        "--data-dir",
        str(root),
    )

    assert completed.returncode == 1
    assert payload["error"]["type"] == "CorpusValidationError"
    with ControlStore(root) as control:
        assert control.accepted_count() == 0


def test_import_does_not_accept_when_review_artifact_publication_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    candidate, manifest, digest = _write_candidate(tmp_path)
    root = tmp_path / "private"
    args = Namespace(
        candidate=candidate,
        manifest=manifest,
        approved_candidate_sha256=digest,
        edition="synthetic candidate",
        acquisition_url="https://example.test/candidate.jsonl",
        acquisition_date=date(2026, 8, 24),
        language="eng",
        data_dir=root,
    )

    def fail_publication(_root: Path, _corpus: object) -> list[str]:
        raise ValueError("injected review artifact failure")

    monkeypatch.setattr(cli, "_publish_review_artifacts", fail_publication)

    with pytest.raises(ValueError, match="injected review artifact failure"):
        cli._import_candidate(args)
    with ControlStore(root) as control:
        assert control.accepted_count() == 0
