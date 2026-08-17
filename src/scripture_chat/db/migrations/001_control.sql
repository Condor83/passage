PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_meta (
    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
    schema_version INTEGER NOT NULL CHECK (schema_version = 1)
);
INSERT OR IGNORE INTO schema_meta(singleton, schema_version) VALUES (1, 1);

CREATE TABLE IF NOT EXISTS build_attempts (
    attempt_id TEXT PRIMARY KEY,
    build_key TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN ('building', 'accepted', 'rejected', 'quarantined')),
    error_code TEXT,
    corpus_version TEXT,
    created_at TEXT NOT NULL,
    finished_at TEXT
);

CREATE TABLE IF NOT EXISTS accepted_corpora (
    corpus_version TEXT PRIMARY KEY,
    build_key TEXT NOT NULL UNIQUE,
    artifact_digest TEXT NOT NULL UNIQUE,
    normalized_digest TEXT NOT NULL,
    artifact_path TEXT NOT NULL UNIQUE,
    retrieval_config TEXT NOT NULL UNIQUE,
    manifest_json TEXT NOT NULL,
    accepted_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS retrieval_configs (
    config_id TEXT PRIMARY KEY,
    corpus_version TEXT NOT NULL REFERENCES accepted_corpora(corpus_version) ON DELETE RESTRICT,
    config_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (corpus_version, config_id)
);

CREATE TABLE IF NOT EXISTS active_state (
    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
    corpus_version TEXT NOT NULL REFERENCES accepted_corpora(corpus_version) ON DELETE RESTRICT,
    retrieval_config TEXT NOT NULL REFERENCES retrieval_configs(config_id) ON DELETE RESTRICT,
    activated_at TEXT NOT NULL
);
