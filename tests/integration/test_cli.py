from __future__ import annotations

import json
import os
import subprocess
import sys
from importlib import metadata, util
from pathlib import Path
from typing import Any
from zipfile import ZipFile

from passage.db.control import ControlStore
from passage.domain.models import PassageRequest
from passage.evidence.service import EvidenceService

FIXTURES = Path(__file__).parents[1] / "fixtures"


def _run(*arguments: str) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
    completed = subprocess.run(
        [sys.executable, "-m", "passage.cli", *arguments],
        check=False,
        capture_output=True,
        text=True,
    )
    output = completed.stdout if completed.returncode == 0 else completed.stderr
    return completed, json.loads(output)


def test_installed_package_and_console_command_use_only_passage_identity() -> None:
    distribution = metadata.distribution("passage")
    console_scripts = {
        entry.name: entry.value
        for entry in distribution.entry_points
        if entry.group == "console_scripts"
    }

    assert console_scripts == {"passage": "passage.cli:main"}
    assert util.find_spec("passage") is not None
    assert util.find_spec("scripture" + "_chat") is None


def test_mcp_server_does_not_read_legacy_private_root_environment(tmp_path: Path) -> None:
    environment = os.environ.copy()
    environment.pop("PASSAGE_PRIVATE_ROOT", None)
    environment["SCRIPTURE" + "_CHAT_PRIVATE_ROOT"] = str(tmp_path)

    completed = subprocess.run(
        [sys.executable, "-m", "passage.mcp.server"],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )

    assert completed.returncode != 0
    assert "PASSAGE_PRIVATE_ROOT is required" in completed.stderr


def test_fixture_cli_builds_verify_and_evaluate_both_formats(tmp_path: Path) -> None:
    roots: dict[str, Path] = {}
    build_reports: dict[str, dict[str, Any]] = {}
    for suffix in ("epub", "pdf"):
        source = FIXTURES / "corpus" / f"sample.{suffix}"
        root = tmp_path / suffix
        roots[suffix] = root
        inspected, inspection = _run(
            "corpus",
            "inspect",
            "--source",
            str(source),
            "--data-dir",
            str(root),
        )
        built, build = _run(
            "corpus",
            "build",
            "--source",
            str(source),
            "--edition",
            "synthetic-v1",
            "--data-dir",
            str(root),
        )
        verified, verification = _run(
            "corpus",
            "verify",
            "--data-dir",
            str(root),
        )
        assert inspected.returncode == built.returncode == verified.returncode == 0
        assert inspection["passage_count"] == 2
        assert verification["artifact_digest"] == build["artifact_digest"]
        assert build["active"] is False
        assert all(Path(path).is_file() for path in build["derived_artifacts"])
        build_reports[suffix] = build

    assert any(path.endswith("overlays.json") for path in build_reports["pdf"]["derived_artifacts"])
    canonical = []
    for root in roots.values():
        with ControlStore(root) as control:
            accepted = control.latest_accepted()
            assert accepted is not None
            response = EvidenceService(control).get_passage(
                PassageRequest(
                    reference="bofm/1-ne/1/1",
                    corpus_version=accepted.corpus_version,
                    retrieval_config=accepted.retrieval_config,
                )
            )
            passage = response.records[0].passage
            canonical.append((passage.reference, passage.text, passage.content_hash))
    assert canonical[0] == canonical[1]

    evaluated, evaluation = _run(
        "evaluate",
        "--data-dir",
        str(roots["epub"]),
        "--cases",
        str(FIXTURES / "evaluation" / "cases.jsonl"),
    )
    assert evaluated.returncode == 0
    assert evaluation["eligible"] is False
    assert evaluation["ineligibility_reasons"] == ["no_baseline_comparison"]
    assert Path(evaluation["report_path"]).is_file()


def test_build_rejects_unreconciled_epub_spans_without_registration(
    tmp_path: Path,
) -> None:
    source = tmp_path / "unreconciled.epub"
    with (
        ZipFile(FIXTURES / "corpus" / "sample.epub") as original,
        ZipFile(source, "w") as modified,
    ):
        for member in original.infolist():
            payload = original.read(member)
            if member.filename == "OEBPS/chapter.xhtml":
                payload = payload.replace(
                    b"Faith hope and charity.",
                    b"Faith <em>hope</em> and charity.",
                )
            modified.writestr(member, payload)

    root = tmp_path / "private"
    completed, payload = _run(
        "corpus",
        "build",
        "--source",
        str(source),
        "--edition",
        "synthetic-v1",
        "--acquisition-url",
        "https://example.test/unreconciled.epub",
        "--acquisition-date",
        "2026-08-16",
        "--data-dir",
        str(root),
    )

    assert completed.returncode == 1
    assert payload["error"]["type"] == "CorpusValidationError"
    with ControlStore(root) as control:
        assert control.accepted_count() == 0


def test_activation_revalidates_target_before_replacing_active_pair(tmp_path: Path) -> None:
    root = tmp_path / "private"
    builds = []
    for suffix in ("epub", "pdf"):
        completed, payload = _run(
            "corpus",
            "build",
            "--source",
            str(FIXTURES / "corpus" / f"sample.{suffix}"),
            "--edition",
            "synthetic-v1",
            "--data-dir",
            str(root),
        )
        assert completed.returncode == 0
        builds.append(payload)

    activated, _ = _run(
        "corpus",
        "activate",
        "--corpus-version",
        builds[0]["corpus_version"],
        "--retrieval-config",
        builds[0]["retrieval_config"],
        "--data-dir",
        str(root),
    )
    assert activated.returncode == 0

    with ControlStore(root) as control:
        corrupt = control.get_accepted(builds[1]["corpus_version"])
        assert corrupt is not None
        (corrupt.artifact_path / "manifest.json").unlink()

    rejected, _ = _run(
        "corpus",
        "activate",
        "--corpus-version",
        builds[1]["corpus_version"],
        "--retrieval-config",
        builds[1]["retrieval_config"],
        "--data-dir",
        str(root),
    )
    assert rejected.returncode == 1
    with ControlStore(root) as control:
        active = control.get_active()
        assert active is not None
        assert active.corpus_version == builds[0]["corpus_version"]
        assert active.retrieval_config == builds[0]["retrieval_config"]


def test_cli_failures_are_nonzero_machine_readable_and_private(tmp_path: Path) -> None:
    source = tmp_path / "unsupported.txt"
    source.write_text("private scripture text", encoding="utf-8")

    completed, payload = _run(
        "corpus",
        "inspect",
        "--source",
        str(source),
        "--data-dir",
        str(tmp_path / "private"),
    )

    assert completed.returncode == 1
    assert payload["ok"] is False
    assert payload["error"]["type"] == "ExtractionError"
    assert "private scripture text" not in completed.stderr
