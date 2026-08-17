from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from scripture_chat.db.control import ControlStore
from scripture_chat.db.validation import validate_published_artifact
from scripture_chat.domain.errors import (
    ConfigUnavailableError,
    CorpusUnavailableError,
    PassageNotFoundError,
)
from scripture_chat.domain.models import Passage


@dataclass(frozen=True, slots=True)
class RepositorySearchHit:
    reference: str
    passage: Passage
    raw_score: float


class CorpusRepository:
    def __init__(
        self,
        database_path: Path,
        corpus_version: str,
        retrieval_config: str,
    ) -> None:
        self.corpus_version = corpus_version
        self.retrieval_config = retrieval_config
        uri = f"file:{database_path.as_posix()}?mode=ro&immutable=1"
        self.connection = sqlite3.connect(uri, uri=True, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA query_only = ON")

    @classmethod
    def open(
        cls,
        control: ControlStore,
        corpus_version: str | None = None,
        retrieval_config: str | None = None,
    ) -> CorpusRepository:
        if (corpus_version is None) != (retrieval_config is None):
            raise ConfigUnavailableError(
                "corpus and retrieval identifiers must be selected together"
            )
        if corpus_version is None:
            active = control.get_active()
            if active is None:
                raise CorpusUnavailableError()
            corpus_version = active.corpus_version
            retrieval_config = active.retrieval_config
        accepted = control.get_accepted(corpus_version)
        if accepted is None or accepted.retrieval_config != retrieval_config:
            raise ConfigUnavailableError("selected corpus/configuration pair is unavailable")
        manifest = validate_published_artifact(accepted.artifact_path)
        if manifest["retrieval_config"] != retrieval_config:
            raise ConfigUnavailableError(
                "artifact retrieval configuration does not match control state"
            )
        return cls(
            accepted.artifact_path / "corpus.sqlite",
            corpus_version,
            retrieval_config,
        )

    def __enter__(self) -> CorpusRepository:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        self.connection.close()

    def get_passage(self, reference: str) -> Passage:
        row = self.connection.execute(
            """SELECT reference, canonical_order, text, content_hash, source_spans_json
               FROM passages WHERE reference = ?""",
            (reference,),
        ).fetchone()
        if row is None:
            raise PassageNotFoundError(reference)
        return _passage(row)

    def get_passage_by_id(self, passage_id: int) -> Passage:
        row = self.connection.execute(
            """SELECT reference, canonical_order, text, content_hash, source_spans_json
               FROM passages WHERE id = ?""",
            (passage_id,),
        ).fetchone()
        if row is None:
            raise PassageNotFoundError(str(passage_id))
        return _passage(row)

    def search_fts(self, query: str, limit: int) -> list[RepositorySearchHit]:
        rows = self.connection.execute(
            """SELECT p.reference, p.canonical_order, p.text, p.content_hash,
                      p.source_spans_json, bm25(passages_fts) AS raw_score
               FROM passages_fts
               JOIN passages p ON p.id = passages_fts.rowid
               WHERE passages_fts MATCH ?
               ORDER BY raw_score, p.canonical_order
               LIMIT ?""",
            (query, limit),
        ).fetchall()
        return [
            RepositorySearchHit(
                reference=row["reference"],
                passage=_passage(row),
                raw_score=float(row["raw_score"]),
            )
            for row in rows
        ]

    def passage_count(self) -> int:
        return int(self.connection.execute("SELECT count(*) FROM passages").fetchone()[0])


def _passage(row: sqlite3.Row) -> Passage:
    return Passage(
        reference=row["reference"],
        canonical_order=row["canonical_order"],
        text=row["text"],
        content_hash=row["content_hash"],
        source_spans=json.loads(row["source_spans_json"]),
    )
