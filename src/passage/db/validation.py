from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import TypeAdapter, ValidationError

from passage.domain.models import Passage, SourceSpan
from passage.ingest.validation import passage_integrity_findings

if TYPE_CHECKING:
    from passage.ingest.normalize import NormalizedCorpus


_SOURCE_SPANS_ADAPTER: TypeAdapter[list[SourceSpan]] = TypeAdapter(list[SourceSpan])


class CorpusDatabaseError(ValueError):
    pass


def validate_database(path: Path, corpus: NormalizedCorpus) -> None:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    try:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise CorpusDatabaseError(f"SQLite integrity check failed: {integrity}")
        foreign_keys = connection.execute("PRAGMA foreign_key_check").fetchall()
        if foreign_keys:
            raise CorpusDatabaseError("foreign-key integrity check failed")
        try:
            connection.execute("INSERT INTO passages_fts(passages_fts) VALUES ('integrity-check')")
        except sqlite3.DatabaseError as exc:
            raise CorpusDatabaseError("FTS reconciliation failed integrity check") from exc
        passage_rows = connection.execute(
            """SELECT reference, canonical_order, text, content_hash, source_spans_json
               FROM passages ORDER BY canonical_order"""
        ).fetchall()
        expected = [
            (
                passage.reference,
                passage.canonical_order,
                passage.text,
                passage.content_hash,
                _json([span.model_dump(mode="json") for span in passage.source_spans]),
            )
            for passage in sorted(corpus.passages, key=lambda item: item.canonical_order)
        ]
        observed = [tuple(row) for row in passage_rows]
        if observed != expected:
            raise CorpusDatabaseError("passage reconciliation failed")
        indexed_ids = {
            int(row[0]) for row in connection.execute("SELECT DISTINCT doc FROM passages_fts_vocab")
        }
        passage_ids = {int(row[0]) for row in connection.execute("SELECT id FROM passages")}
        if indexed_ids != passage_ids:
            raise CorpusDatabaseError("FTS reconciliation failed: indexed rowids differ")
        note_rows = connection.execute(
            """SELECT n.note_id, p.reference, n.anchor, n.label, n.text,
                      n.note_kind, n.source_spans_json
               FROM apparatus_notes n
               JOIN passages p ON p.id = n.origin_passage_id
               ORDER BY n.note_id"""
        ).fetchall()
        expected_notes = [
            (
                note.note_id,
                note.origin_reference,
                note.anchor,
                note.label,
                note.text,
                note.note_kind,
                _json([span.model_dump(mode="json") for span in note.source_spans]),
            )
            for note in sorted(corpus.notes, key=lambda item: item.note_id)
        ]
        edge_rows = connection.execute(
            """SELECT e.edge_id, p.reference, e.origin_anchor, e.target_json,
                      e.source_attribution, e.grammar_version, e.source_spans_json
               FROM reference_edges e
               JOIN passages p ON p.id = e.origin_passage_id
               ORDER BY e.edge_id"""
        ).fetchall()
        expected_edges = [
            (
                edge.edge_id,
                edge.origin_reference,
                edge.origin_anchor,
                _json(edge.target.model_dump(mode="json")),
                edge.source_attribution,
                edge.grammar_version,
                _json([span.model_dump(mode="json") for span in edge.source_spans]),
            )
            for edge in sorted(corpus.edges, key=lambda item: item.edge_id)
        ]
        if [tuple(row) for row in note_rows] != expected_notes:
            raise CorpusDatabaseError("apparatus note reconciliation failed")
        if [tuple(row) for row in edge_rows] != expected_edges:
            raise CorpusDatabaseError("apparatus reconciliation failed")
    finally:
        connection.close()


def validate_published_artifact(directory: Path) -> dict[str, Any]:
    manifest_path = directory / "manifest.json"
    config_path = directory / "retrieval.json"
    database_path = directory / "corpus.sqlite"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        config_bytes = config_path.read_bytes()
        database_bytes = database_path.read_bytes()
    except (OSError, json.JSONDecodeError) as exc:
        raise CorpusDatabaseError("published corpus artifact is incomplete") from exc
    database_digest = hashlib.sha256(database_bytes).hexdigest()
    if manifest.get("database_sha256") != database_digest:
        raise CorpusDatabaseError("published corpus database digest mismatch")
    artifact_digest = manifest.get("artifact_digest")
    corpus_version = manifest.get("corpus_version")
    core = {
        key: value
        for key, value in manifest.items()
        if key not in {"artifact_digest", "corpus_version"}
    }
    expected_artifact = hashlib.sha256(
        database_bytes + _json(core).encode("utf-8") + config_bytes
    ).hexdigest()
    if artifact_digest != expected_artifact or directory.name != expected_artifact:
        raise CorpusDatabaseError("published corpus artifact digest mismatch")
    if corpus_version != f"corpus-{expected_artifact[:24]}":
        raise CorpusDatabaseError("published corpus version mismatch")
    _validate_published_passages(database_path)
    return manifest


def _validate_published_passages(database_path: Path) -> None:
    uri = f"{database_path.resolve().as_uri()}?mode=ro&immutable=1"
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(uri, uri=True)
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """SELECT reference, canonical_order, text, content_hash, source_spans_json
               FROM passages ORDER BY canonical_order"""
        ).fetchall()
        findings = []
        for row in rows:
            passage = Passage(
                reference=row["reference"],
                canonical_order=row["canonical_order"],
                text=row["text"],
                content_hash=row["content_hash"],
                source_spans=_SOURCE_SPANS_ADAPTER.validate_python(
                    json.loads(row["source_spans_json"])
                ),
            )
            findings.extend(passage_integrity_findings(passage))
    except (json.JSONDecodeError, sqlite3.DatabaseError, ValidationError) as exc:
        raise CorpusDatabaseError("published corpus passage records cannot be validated") from exc
    finally:
        if connection is not None:
            connection.close()
    if findings:
        codes = ", ".join(sorted({finding.code for finding in findings}))
        raise CorpusDatabaseError(f"published corpus passage integrity check failed: {codes}")


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
