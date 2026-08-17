from pathlib import Path

import pytest

from scripture_chat.ingest.base import ExtractionError, ExtractionLimits
from scripture_chat.ingest.worker import inspect_source_in_worker
from tests.unit.ingest.test_epub import VALID_CHAPTER, make_epub


def test_worker_returns_typed_extraction_and_cleans_workspace(tmp_path: Path) -> None:
    source = tmp_path / "book.epub"
    source.write_bytes(make_epub(VALID_CHAPTER))
    workspaces = tmp_path / "workspaces"
    workspaces.mkdir()

    result = inspect_source_in_worker(source, ExtractionLimits(), workspaces)

    assert len(result.passages) == 2
    assert list(workspaces.iterdir()) == []


def test_worker_rejects_source_byte_budget_without_residue(tmp_path: Path) -> None:
    source = tmp_path / "book.epub"
    source.write_bytes(make_epub(VALID_CHAPTER))
    workspaces = tmp_path / "workspaces"
    workspaces.mkdir()

    with pytest.raises(ExtractionError, match="source-byte"):
        inspect_source_in_worker(
            source,
            ExtractionLimits(max_source_bytes=10),
            workspaces,
        )

    assert list(workspaces.iterdir()) == []


def test_worker_rejects_unknown_source_format(tmp_path: Path) -> None:
    source = tmp_path / "book.txt"
    source.write_text("not scripture")
    workspaces = tmp_path / "workspaces"
    workspaces.mkdir()

    with pytest.raises(ExtractionError, match="unsupported source format"):
        inspect_source_in_worker(source, ExtractionLimits(), workspaces)
