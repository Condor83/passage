from __future__ import annotations

from collections.abc import Iterator
from datetime import date
from pathlib import Path

import pytest

from passage.db.builder import CorpusBuilder
from passage.db.control import ControlStore
from passage.domain.models import SourceApproval
from passage.evidence.service import EvidenceService
from passage.ingest.normalize import normalize_extraction
from passage.ingest.validation import StructureManifest
from tests.unit.ingest.test_validation import extraction


@pytest.fixture
def service(tmp_path: Path) -> Iterator[EvidenceService]:
    root = tmp_path / "private"
    manifest = StructureManifest(
        schema_version=1,
        source={},
        books={"1-ne": [4], "2-ne": [2]},
    )
    corpus = normalize_extraction(
        extraction(
            [
                ("bofm/1-ne/1/1", "Faith hope and charity."),
                ("bofm/1-ne/1/2", "Faith is things hoped for."),
                ("bofm/1-ne/1/3", "Hope and charity endure."),
                ("bofm/1-ne/1/4", "Repent and remember."),
                ("bofm/2-ne/1/1", "A faithful witness speaks."),
                ("bofm/2-ne/1/2", "Faith and hope remain."),
            ],
            [
                ("bofm/1-ne/1/1", "bofm/1-ne/1/2"),
                ("bofm/1-ne/1/1", "bible/john/3/16"),
                ("bofm/1-ne/1/2", "bofm/1-ne/1/3"),
                ("bofm/1-ne/1/3", "bofm/1-ne/1/1"),
            ],
        ),
        manifest,
    )
    approval = SourceApproval(
        source_sha256="a" * 64,
        acquisition_url="https://example.test/source.epub",
        acquisition_date=date(2026, 8, 16),
        edition="Current Church edition",
    )
    control = ControlStore(root)
    published = CorpusBuilder(root, control).build(corpus, approval, "b" * 64)
    control.activate(published.corpus_version, published.retrieval_config)
    try:
        yield EvidenceService(control)
    finally:
        control.close()
