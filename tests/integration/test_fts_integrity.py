import sqlite3
from pathlib import Path

import pytest

from scripture_chat.db.builder import CorpusBuilder
from scripture_chat.db.control import ControlStore
from scripture_chat.db.repository import CorpusRepository
from scripture_chat.db.validation import CorpusDatabaseError, validate_database
from tests.integration.test_corpus_build import approval, sample_corpus


def test_fts_rows_use_passage_primary_keys_and_search_exact_content(tmp_path: Path) -> None:
    root = tmp_path / "private"
    with ControlStore(root) as control:
        published = CorpusBuilder(root, control).build(sample_corpus(), approval(), "b" * 64)
        control.activate(published.corpus_version, published.retrieval_config)

        with CorpusRepository.open(control) as repository:
            results = repository.search_fts('"Second verse"', limit=10)

        assert [result.reference for result in results] == ["bofm/1-ne/1/2"]


def test_validation_rejects_missing_fts_row(tmp_path: Path) -> None:
    root = tmp_path / "private"
    with ControlStore(root) as control:
        published = CorpusBuilder(root, control).build(sample_corpus(), approval(), "b" * 64)

    database = published.database_path
    database.chmod(0o600)
    connection = sqlite3.connect(database)
    connection.execute("DELETE FROM passages_fts WHERE rowid = 2")
    connection.commit()
    connection.close()

    with pytest.raises(CorpusDatabaseError, match="FTS reconciliation"):
        validate_database(database, sample_corpus())
