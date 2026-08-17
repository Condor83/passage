from __future__ import annotations

import json
import os
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class AcceptedCorpus:
    corpus_version: str
    build_key: str
    artifact_digest: str
    normalized_digest: str
    artifact_path: Path
    retrieval_config: str
    manifest: dict[str, Any]
    accepted_at: datetime


@dataclass(frozen=True, slots=True)
class ActiveState:
    corpus_version: str
    retrieval_config: str


class ControlStore:
    def __init__(self, private_root: Path) -> None:
        self.private_root = private_root.absolute()
        self.private_root.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(self.private_root, 0o700, follow_symlinks=False)
        self.path = self.private_root / "control.sqlite"
        self.connection = sqlite3.connect(self.path, isolation_level=None)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.execute("PRAGMA journal_mode = WAL")
        self.connection.execute("PRAGMA synchronous = FULL")
        schema = (Path(__file__).parent / "migrations/001_control.sql").read_text()
        self.connection.executescript(schema)
        os.chmod(self.path, 0o600, follow_symlinks=False)
        self._chmod_sidecars()

    def __enter__(self) -> ControlStore:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        if self.connection is not None:
            self.connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            self.connection.close()
            self._chmod_sidecars()

    def begin_attempt(self, build_key: str) -> str:
        attempt_id = uuid.uuid4().hex
        self.connection.execute(
            """INSERT INTO build_attempts(
                attempt_id, build_key, state, created_at
            ) VALUES (?, ?, 'building', ?)""",
            (attempt_id, build_key, _now()),
        )
        return attempt_id

    def finish_attempt(
        self,
        attempt_id: str,
        state: str,
        *,
        error_code: str | None = None,
        corpus_version: str | None = None,
    ) -> None:
        self.connection.execute(
            """UPDATE build_attempts
               SET state = ?, error_code = ?, corpus_version = ?, finished_at = ?
               WHERE attempt_id = ?""",
            (state, error_code, corpus_version, _now(), attempt_id),
        )

    def register_accepted(
        self,
        *,
        attempt_id: str,
        build_key: str,
        corpus_version: str,
        artifact_digest: str,
        normalized_digest: str,
        artifact_path: Path,
        retrieval_config: str,
        manifest: dict[str, Any],
        config: dict[str, Any],
    ) -> None:
        timestamp = _now()
        manifest_json = _json(manifest)
        config_json = _json(config)
        with self.connection:
            self.connection.execute(
                """INSERT INTO accepted_corpora(
                    corpus_version, build_key, artifact_digest, normalized_digest,
                    artifact_path, retrieval_config, manifest_json, accepted_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    corpus_version,
                    build_key,
                    artifact_digest,
                    normalized_digest,
                    str(artifact_path),
                    retrieval_config,
                    manifest_json,
                    timestamp,
                ),
            )
            self.connection.execute(
                """INSERT INTO retrieval_configs(
                    config_id, corpus_version, config_json, created_at
                ) VALUES (?, ?, ?, ?)""",
                (retrieval_config, corpus_version, config_json, timestamp),
            )
            self.connection.execute(
                """UPDATE build_attempts
                   SET state = 'accepted', corpus_version = ?, finished_at = ?
                   WHERE attempt_id = ?""",
                (corpus_version, timestamp, attempt_id),
            )

    def find_by_build_key(self, build_key: str) -> AcceptedCorpus | None:
        row = self.connection.execute(
            "SELECT * FROM accepted_corpora WHERE build_key = ?", (build_key,)
        ).fetchone()
        return _accepted(row) if row else None

    def get_accepted(self, corpus_version: str) -> AcceptedCorpus | None:
        row = self.connection.execute(
            "SELECT * FROM accepted_corpora WHERE corpus_version = ?", (corpus_version,)
        ).fetchone()
        return _accepted(row) if row else None

    def get_config(self, config_id: str) -> dict[str, Any] | None:
        row = self.connection.execute(
            "SELECT config_json FROM retrieval_configs WHERE config_id = ?", (config_id,)
        ).fetchone()
        return json.loads(row["config_json"]) if row else None

    def activate(self, corpus_version: str, retrieval_config: str) -> None:
        compatible = self.connection.execute(
            """SELECT 1 FROM retrieval_configs
               JOIN accepted_corpora USING (corpus_version)
               WHERE corpus_version = ? AND config_id = ?""",
            (corpus_version, retrieval_config),
        ).fetchone()
        if compatible is None:
            raise ValueError("activation requires a compatible accepted corpus/configuration pair")
        with self.connection:
            self.connection.execute(
                """INSERT INTO active_state(
                    singleton, corpus_version, retrieval_config, activated_at
                ) VALUES (1, ?, ?, ?)
                ON CONFLICT(singleton) DO UPDATE SET
                    corpus_version = excluded.corpus_version,
                    retrieval_config = excluded.retrieval_config,
                    activated_at = excluded.activated_at""",
                (corpus_version, retrieval_config, _now()),
            )

    def get_active(self) -> ActiveState | None:
        row = self.connection.execute(
            "SELECT corpus_version, retrieval_config FROM active_state WHERE singleton = 1"
        ).fetchone()
        if row is None:
            return None
        return ActiveState(row["corpus_version"], row["retrieval_config"])

    def accepted_count(self) -> int:
        return int(self.connection.execute("SELECT count(*) FROM accepted_corpora").fetchone()[0])

    def _chmod_sidecars(self) -> None:
        for suffix in ("-wal", "-shm"):
            sidecar = Path(f"{self.path}{suffix}")
            if sidecar.exists():
                os.chmod(sidecar, 0o600, follow_symlinks=False)


def _accepted(row: sqlite3.Row) -> AcceptedCorpus:
    return AcceptedCorpus(
        corpus_version=row["corpus_version"],
        build_key=row["build_key"],
        artifact_digest=row["artifact_digest"],
        normalized_digest=row["normalized_digest"],
        artifact_path=Path(row["artifact_path"]),
        retrieval_config=row["retrieval_config"],
        manifest=json.loads(row["manifest_json"]),
        accepted_at=datetime.fromisoformat(row["accepted_at"]),
    )


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
