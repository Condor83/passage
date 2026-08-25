# Scripture Corpus Candidates

This directory contains maintainer-approved, version-controlled snapshots of two
derived scripture corpus candidates:

- `book-of-mormon/candidate.jsonl`
- `new-testament/candidate.jsonl`

Each directory contains a public manifest with the exact candidate digest,
record counts, and lifecycle state.

The committed manifests preserve the snapshots' initial `review_required`,
inactive, and unaccepted state. On 2026-08-24 the maintainer separately approved
the exact Book of Mormon candidate digest for the local beta, identified its
source as the Church's free public English 2013 PDF edition, and imported and
activated it in the private local SQLite runtime. The New Testament candidate
remains unaccepted and inactive. Neither committed candidate contains typed
relationship edges. A private, digest-bound `official-reference-v2` derivation
of the exact approved Book of Mormon candidate applies three maintainer-approved
repairs and produced a complete 13,136-edge successor. That successor remains
outside Git, inactive, unaccepted, and `review_required`; it did not change the
active edge-free corpus.

Raw source files, Datalab output, correction profiles, detailed repair reports,
source paths, acquisition records, and credentials remain outside Git. Routine
tests must continue to use synthetic fixtures unless the maintainer separately
authorizes use of an exact candidate digest.

Runtime acceptance and activation live in the private control store rather than
these commit-time manifests. They do not authorize remote delivery.
