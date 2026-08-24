# Scripture Corpus Candidates

This directory contains maintainer-approved, version-controlled snapshots of two
derived scripture corpus candidates:

- `book-of-mormon/candidate.jsonl`
- `new-testament/candidate.jsonl`

Each directory contains a public manifest with the exact candidate digest,
record counts, and lifecycle state.

These snapshots are `review_required`, inactive, and unaccepted. Committing them
does not approve their source edition, establish editorial fidelity, accept a
corpus, activate a corpus, authorize remote delivery, or change the current
runtime. They contain canonical scripture text and official footnote text but no
typed relationship edges.

Raw source files, Datalab output, correction profiles, detailed repair reports,
source paths, acquisition records, and credentials remain outside Git. Routine
tests must continue to use synthetic fixtures unless the maintainer separately
authorizes use of an exact candidate digest.
