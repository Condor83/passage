PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = FULL;

CREATE TABLE metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
) WITHOUT ROWID;

CREATE TABLE passages (
    id INTEGER PRIMARY KEY,
    reference TEXT NOT NULL UNIQUE,
    book TEXT NOT NULL,
    chapter INTEGER NOT NULL CHECK (chapter > 0),
    verse INTEGER NOT NULL CHECK (verse > 0),
    canonical_order INTEGER NOT NULL UNIQUE CHECK (canonical_order >= 0),
    text TEXT NOT NULL CHECK (length(text) > 0),
    content_hash TEXT NOT NULL CHECK (length(content_hash) = 64),
    source_spans_json TEXT NOT NULL
);

CREATE TABLE apparatus_notes (
    note_id TEXT PRIMARY KEY,
    origin_passage_id INTEGER NOT NULL REFERENCES passages(id),
    anchor TEXT NOT NULL,
    label TEXT,
    text TEXT,
    note_kind TEXT NOT NULL,
    source_spans_json TEXT NOT NULL
) WITHOUT ROWID;

CREATE TABLE reference_edges (
    edge_id TEXT PRIMARY KEY,
    origin_passage_id INTEGER NOT NULL REFERENCES passages(id),
    origin_anchor TEXT NOT NULL,
    target_json TEXT NOT NULL,
    source_attribution TEXT NOT NULL,
    grammar_version TEXT NOT NULL,
    source_spans_json TEXT NOT NULL
) WITHOUT ROWID;

CREATE VIRTUAL TABLE passages_fts USING fts5(
    text,
    content='passages',
    content_rowid='id',
    tokenize='unicode61 remove_diacritics 2'
);

CREATE VIRTUAL TABLE passages_fts_vocab USING fts5vocab(passages_fts, 'instance');
