from datetime import date
from pathlib import Path

from passage.db.builder import CorpusBuilder
from passage.db.control import ControlStore
from passage.db.repository import CorpusRepository
from passage.domain.models import SourceApproval
from passage.ingest.normalize import normalize_extraction
from tests.unit.ingest.test_validation import MANIFEST, extraction


def sample_corpus(second_text: str = "Second verse"):
    return normalize_extraction(
        extraction(
            [
                ("bofm/1-ne/1/1", "First verse"),
                ("bofm/1-ne/1/2", second_text),
            ],
            [("bofm/1-ne/1/1", "bible/john/3/16")],
        ),
        MANIFEST,
    )


def approval(digest: str = "a" * 64) -> SourceApproval:
    return SourceApproval(
        source_sha256=digest,
        acquisition_url="https://example.test/source.epub",
        acquisition_date=date(2026, 8, 16),
        edition="Current Church edition",
    )


def test_build_publishes_content_addressed_immutable_corpus(tmp_path: Path) -> None:
    root = tmp_path / "private"
    with ControlStore(root) as control:
        published = CorpusBuilder(root, control).build(sample_corpus(), approval(), "b" * 64)

        assert published.directory.name == published.artifact_digest
        assert published.database_path.exists()
        assert published.database_path.stat().st_mode & 0o777 == 0o600
        assert published.manifest_path.stat().st_mode & 0o777 == 0o600
        assert control.get_active() is None
        control.activate(published.corpus_version, published.retrieval_config)

        with CorpusRepository.open(control) as repository:
            assert repository.get_passage("bofm/1-ne/1/2").text == "Second verse"


def test_equivalent_build_is_idempotent(tmp_path: Path) -> None:
    root = tmp_path / "private"
    with ControlStore(root) as control:
        builder = CorpusBuilder(root, control)
        first = builder.build(sample_corpus(), approval(), "b" * 64)
        second = builder.build(sample_corpus(), approval(), "b" * 64)

        assert second == first
        assert control.accepted_count() == 1
