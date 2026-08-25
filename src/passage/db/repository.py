from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import TypeAdapter

from passage.db.contracts import LexicalQuery, RepositorySearchHit, RepositorySearchPage
from passage.db.control import ControlStore
from passage.db.validation import validate_published_artifact
from passage.domain.errors import (
    ConfigUnavailableError,
    CorpusUnavailableError,
    InvalidQueryError,
    PassageNotFoundError,
)
from passage.domain.identifiers import CanonicalReference
from passage.domain.models import (
    LexicalMode,
    Passage,
    ReferenceEdge,
    ReferenceTarget,
    SearchFilters,
)

if TYPE_CHECKING:
    from passage.evidence.service import EvidenceService

_REFERENCE_TARGET_ADAPTER: TypeAdapter[ReferenceTarget] = TypeAdapter(ReferenceTarget)


class CorpusRepository:
    def __init__(
        self,
        database_path: Path,
        corpus_version: str,
        retrieval_config: str,
    ) -> None:
        self.corpus_version = corpus_version
        self.retrieval_config = retrieval_config
        uri = f"{database_path.resolve().as_uri()}?mode=ro&immutable=1"
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

    def get_context(self, reference: str, before: int, after: int) -> list[Passage]:
        passage = self.get_passage(reference)
        rows = self.connection.execute(
            """SELECT reference, canonical_order, text, content_hash, source_spans_json
               FROM passages
               WHERE canonical_order BETWEEN ? AND ? AND canonical_order != ?
               ORDER BY canonical_order""",
            (
                max(0, passage.canonical_order - before),
                passage.canonical_order + after,
                passage.canonical_order,
            ),
        ).fetchall()
        return [_passage(row) for row in rows]

    def search_lexical(
        self,
        query: LexicalQuery,
        filters: SearchFilters | None,
        after: tuple[float, int] | None,
        limit: int,
    ) -> RepositorySearchPage:
        try:
            return self._search_lexical(query, filters, after, limit)
        except sqlite3.OperationalError as exc:
            raise InvalidQueryError("query is not valid for lexical search") from exc
        except ValueError as exc:
            raise InvalidQueryError(str(exc)) from exc

    def _search_lexical(
        self,
        query: LexicalQuery,
        filters: SearchFilters | None,
        after: tuple[float, int] | None,
        limit: int,
    ) -> RepositorySearchPage:
        fts_query = _compile_fts5_query(query)
        books = filters.books if filters is not None else None
        reference_ranges = filters.reference_ranges if filters is not None else None
        books_json = json.dumps(books) if books is not None else None
        ranges_json = (
            json.dumps([self._range_bounds(value) for value in reference_ranges])
            if reference_ranges is not None
            else None
        )
        after_score = after[0] if after is not None else None
        after_order = after[1] if after is not None else None
        rows = self.connection.execute(
            """WITH ranked AS (
                SELECT p.reference, p.canonical_order, p.text, p.content_hash,
                       p.source_spans_json, bm25(passages_fts) AS raw_score
                FROM passages_fts
                JOIN passages p ON p.id = passages_fts.rowid
                WHERE passages_fts MATCH ?
                  AND (
                    ? IS NULL
                    OR p.book IN (SELECT value FROM json_each(?))
                  )
                  AND (
                    ? IS NULL
                    OR EXISTS (
                      SELECT 1
                      FROM json_each(?) AS requested_range
                      WHERE p.canonical_order BETWEEN
                        json_extract(requested_range.value, '$[0]')
                        AND json_extract(requested_range.value, '$[1]')
                    )
                  )
            )
            SELECT * FROM ranked
            WHERE (
              ? IS NULL
              OR raw_score > ?
              OR (raw_score = ? AND canonical_order > ?)
            )
            ORDER BY raw_score, canonical_order
            LIMIT ?""",
            (
                fts_query,
                books_json,
                books_json,
                ranges_json,
                ranges_json,
                after_score,
                after_score,
                after_score,
                after_order,
                limit + 1,
            ),
        ).fetchall()
        hits = [
            RepositorySearchHit(
                reference=row["reference"],
                passage=_passage(row),
                raw_score=float(row["raw_score"]),
            )
            for row in rows[:limit]
        ]
        return RepositorySearchPage(hits=hits, has_more=len(rows) > limit)

    def all_edges(self) -> list[ReferenceEdge]:
        rows = self.connection.execute(
            """SELECT e.edge_id, p.reference AS origin_reference, e.origin_anchor,
                      e.target_json, e.source_attribution, e.grammar_version,
                      e.source_spans_json
               FROM reference_edges e
               JOIN passages p ON p.id = e.origin_passage_id
               ORDER BY p.canonical_order, e.edge_id"""
        ).fetchall()
        return [
            ReferenceEdge(
                edge_id=row["edge_id"],
                origin_reference=row["origin_reference"],
                origin_anchor=row["origin_anchor"],
                target=_REFERENCE_TARGET_ADAPTER.validate_json(row["target_json"]),
                source_attribution=row["source_attribution"],
                grammar_version=row["grammar_version"],
                source_spans=json.loads(row["source_spans_json"]),
            )
            for row in rows
        ]

    def _range_bounds(self, value: str) -> tuple[int, int]:
        reference = CanonicalReference.parse(value)
        start = str(reference.passages()[0])
        end = str(reference.passages()[-1])
        rows = self.connection.execute(
            """SELECT reference, canonical_order FROM passages
               WHERE reference IN (?, ?)""",
            (start, end),
        ).fetchall()
        orders = {row["reference"]: int(row["canonical_order"]) for row in rows}
        if start not in orders or end not in orders:
            raise ValueError(f"reference range is outside the corpus: {value}")
        return orders[start], orders[end]

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


class SQLiteRepositoryFactory:
    def __init__(self, control: ControlStore) -> None:
        self.control = control

    def __call__(self, corpus_version: str, retrieval_config: str) -> CorpusRepository:
        return CorpusRepository.open(
            self.control,
            corpus_version=corpus_version,
            retrieval_config=retrieval_config,
        )


def create_sqlite_evidence_service(control: ControlStore) -> EvidenceService:
    from passage.evidence.service import EvidenceService
    from passage.evidence.snapshot import SnapshotManager

    return EvidenceService(SnapshotManager(control, SQLiteRepositoryFactory(control)))


def _compile_fts5_query(query: LexicalQuery) -> str:
    if query.mode is LexicalMode.PHRASE:
        return _quote_fts5(query.text)
    terms = query.text.split()
    if not terms:
        raise InvalidQueryError("query must contain a searchable token")
    if query.mode is LexicalMode.TERMS:
        return " AND ".join(_quote_fts5(term) for term in terms)
    if query.mode is LexicalMode.PREFIX:
        return " AND ".join(f"{_quote_fts5(term)}*" for term in terms)
    distance = query.near_distance if query.near_distance is not None else 5
    return f"NEAR({' '.join(_quote_fts5(term) for term in terms)}, {distance})"


def _quote_fts5(value: str) -> str:
    return f'"{value.replace(chr(34), chr(34) * 2)}"'


def _passage(row: sqlite3.Row) -> Passage:
    return Passage(
        reference=row["reference"],
        canonical_order=row["canonical_order"],
        text=row["text"],
        content_hash=row["content_hash"],
        source_spans=json.loads(row["source_spans_json"]),
    )
