from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from passage.config import create_private_file
from passage.db.control import AcceptedCorpus, ControlStore
from passage.db.validation import validate_database, validate_published_artifact
from passage.domain.identifiers import CanonicalReference
from passage.domain.models import SourceApproval
from passage.ingest.normalize import NormalizedCorpus

CORPUS_SCHEMA_VERSION = 2


class BuildFault(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class PublishedCorpus:
    corpus_version: str
    retrieval_config: str
    artifact_digest: str
    directory: Path

    @property
    def database_path(self) -> Path:
        return self.directory / "corpus.sqlite"

    @property
    def manifest_path(self) -> Path:
        return self.directory / "manifest.json"


class CorpusBuilder:
    def __init__(self, private_root: Path, control: ControlStore) -> None:
        self.private_root = private_root.absolute()
        self.control = control
        self.corpora_root = self.private_root / "corpora"
        self.attempts_root = self.private_root / "attempts"
        for directory in (self.corpora_root, self.attempts_root):
            directory.mkdir(mode=0o700, parents=True, exist_ok=True)
            os.chmod(directory, 0o700, follow_symlinks=False)

    def build(
        self,
        corpus: NormalizedCorpus,
        approval: SourceApproval,
        recipe_fingerprint: str,
        *,
        importer_version: str = "0.1.0",
        fault_at: str | None = None,
    ) -> PublishedCorpus:
        build_key = _sha256(
            _json(
                {
                    "approval": approval.model_dump(mode="json"),
                    "recipe_fingerprint": recipe_fingerprint,
                    "normalized_digest": corpus.normalized_digest,
                    "schema_version": CORPUS_SCHEMA_VERSION,
                    "importer_version": importer_version,
                }
            )
        )
        existing = self.control.find_by_build_key(build_key)
        if existing is not None:
            validate_published_artifact(existing.artifact_path)
            return _published(existing)
        attempt_id = self.control.begin_attempt(build_key)
        attempt_directory = self.attempts_root / f"{attempt_id}-{uuid.uuid4().hex}"
        attempt_directory.mkdir(mode=0o700)
        database_path = attempt_directory / "corpus.sqlite"
        try:
            self._populate(database_path, corpus)
            _fault(fault_at, "after_commit")
            connection = sqlite3.connect(database_path)
            connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            connection.close()
            _fault(fault_at, "after_checkpoint")
            _chmod_database_files(database_path)
            _fault(fault_at, "after_close")
            validate_database(database_path, corpus)
            _fault(fault_at, "after_reconcile")
            database_bytes = database_path.read_bytes()
            database_sha256 = _sha256(database_bytes)
            config = _baseline_config(corpus.normalized_digest)
            config_bytes = _json(config)
            retrieval_config = f"baseline-{_sha256(config_bytes)[:24]}"
            config_file_bytes = (config_bytes + "\n").encode("utf-8")
            core_manifest = {
                "schema_version": CORPUS_SCHEMA_VERSION,
                "source_approval": approval.model_dump(mode="json"),
                "source_profile": corpus.source_profile,
                "source_format": corpus.source_format,
                "recipe_fingerprint": recipe_fingerprint,
                "normalized_digest": corpus.normalized_digest,
                "database_sha256": database_sha256,
                "retrieval_config": retrieval_config,
                "importer_version": importer_version,
            }
            artifact_digest = hashlib.sha256(
                database_bytes + _json(core_manifest).encode("utf-8") + config_file_bytes
            ).hexdigest()
            corpus_version = f"corpus-{artifact_digest[:24]}"
            manifest = {
                "artifact_digest": artifact_digest,
                "corpus_version": corpus_version,
                **core_manifest,
            }
            create_private_file(
                attempt_directory / "manifest.json",
                (_json(manifest) + "\n").encode("utf-8"),
            )
            create_private_file(
                attempt_directory / "retrieval.json",
                config_file_bytes,
            )
            _fsync_file(database_path)
            _fsync_directory(attempt_directory)
            _fault(fault_at, "after_file_fsync")
            destination = self.corpora_root / artifact_digest
            if destination.exists():
                shutil.rmtree(attempt_directory)
            else:
                os.rename(attempt_directory, destination)
                _fsync_directory(destination)
                _fsync_directory(self.corpora_root)
            _fault(fault_at, "after_rename")
            validate_published_artifact(destination)
            self.control.register_accepted(
                attempt_id=attempt_id,
                build_key=build_key,
                corpus_version=corpus_version,
                artifact_digest=artifact_digest,
                normalized_digest=corpus.normalized_digest,
                artifact_path=destination,
                retrieval_config=retrieval_config,
                manifest=manifest,
                config=config,
                before_commit=lambda: _fault(fault_at, "after_registration"),
            )
            return PublishedCorpus(
                corpus_version=corpus_version,
                retrieval_config=retrieval_config,
                artifact_digest=artifact_digest,
                directory=destination,
            )
        except BuildFault:
            self.control.finish_attempt(attempt_id, "rejected", error_code="injected_fault")
            raise
        except Exception:
            self.control.finish_attempt(attempt_id, "rejected", error_code="build_failed")
            raise

    def _populate(self, path: Path, corpus: NormalizedCorpus) -> None:
        connection = sqlite3.connect(path)
        try:
            schema = (Path(__file__).parent / "migrations/002_corpus.sql").read_text()
            connection.executescript(schema)
            reference_ids: dict[str, int] = {}
            with connection:
                connection.executemany(
                    "INSERT INTO metadata(key, value) VALUES (?, ?)",
                    (
                        ("normalized_digest", corpus.normalized_digest),
                        ("source_format", corpus.source_format),
                        ("source_profile", corpus.source_profile),
                    ),
                )
                for passage in sorted(corpus.passages, key=lambda item: item.canonical_order):
                    reference = CanonicalReference.parse(passage.reference)
                    cursor = connection.execute(
                        """INSERT INTO passages(
                            reference, book, chapter, verse, canonical_order, text,
                            content_hash, source_spans_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            passage.reference,
                            reference.book,
                            reference.chapter,
                            reference.verse,
                            passage.canonical_order,
                            passage.text,
                            passage.content_hash,
                            _json([span.model_dump(mode="json") for span in passage.source_spans]),
                        ),
                    )
                    if cursor.lastrowid is None:
                        raise RuntimeError("passage insert did not return a row identifier")
                    passage_id = cursor.lastrowid
                    reference_ids[passage.reference] = passage_id
                    connection.execute(
                        "INSERT INTO passages_fts(rowid, text) VALUES (?, ?)",
                        (passage_id, passage.text),
                    )
                for note in corpus.notes:
                    connection.execute(
                        """INSERT INTO apparatus_notes(
                            note_id, origin_passage_id, anchor, label, text,
                            note_kind, source_spans_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (
                            note.note_id,
                            reference_ids[note.origin_reference],
                            note.anchor,
                            note.label,
                            note.text,
                            note.note_kind,
                            _json([span.model_dump(mode="json") for span in note.source_spans]),
                        ),
                    )
                for edge in corpus.edges:
                    connection.execute(
                        """INSERT INTO reference_edges(
                            edge_id, origin_passage_id, origin_anchor,
                            target_json, source_attribution, grammar_version,
                            source_spans_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (
                            edge.edge_id,
                            reference_ids[edge.origin_reference],
                            edge.origin_anchor,
                            _json(edge.target.model_dump(mode="json")),
                            edge.source_attribution,
                            edge.grammar_version,
                            _json([span.model_dump(mode="json") for span in edge.source_spans]),
                        ),
                    )
            connection.commit()
        finally:
            connection.close()
        _chmod_database_files(path)


def _baseline_config(normalized_digest: str) -> dict[str, Any]:
    return {
        "schema_version": CORPUS_SCHEMA_VERSION,
        "normalized_digest": normalized_digest,
        "lanes": ["lexical", "official"],
        "lexical": {"algorithm": "fts5-bm25", "candidate_pool_size": 100},
        "context": {"before": 3, "after": 3},
        "official": {"depth": 1},
        "ranking": ["lane_priority", "raw_score", "canonical_order"],
    }


def _published(corpus: AcceptedCorpus) -> PublishedCorpus:
    return PublishedCorpus(
        corpus_version=corpus.corpus_version,
        retrieval_config=corpus.retrieval_config,
        artifact_digest=corpus.artifact_digest,
        directory=corpus.artifact_path,
    )


def _fault(requested: str | None, stage: str) -> None:
    if requested == stage:
        raise BuildFault(f"injected build fault at {stage}")


def _chmod_database_files(path: Path) -> None:
    for candidate in (path, Path(f"{path}-wal"), Path(f"{path}-shm")):
        if candidate.exists():
            os.chmod(candidate, 0o600, follow_symlinks=False)


def _fsync_file(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _sha256(payload: bytes | str) -> str:
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
