# Scripture Corpus Candidates

This directory contains maintainer-approved, version-controlled snapshots of two
derived scripture corpus candidates:

- `book-of-mormon/candidate.jsonl`
- `new-testament/candidate.jsonl`

Each directory contains a public manifest with the exact candidate digest,
record counts, and lifecycle state.

The committed manifests preserve the snapshots' initial `review_required`,
inactive, and unaccepted state. On 2026-08-24 the maintainer separately approved
and locally activated the exact Book of Mormon candidate, but a 2026-08-25
terminal-boundary audit invalidated its editorial fidelity: the final canonical
record had absorbed post-canon material. Editorial authority is therefore
withdrawn from base SHA-256
`1dfd7b927e9fe5f4987a5bb5a3c8d1a0398eec6004cd01f45e86d50096a1e6b4`,
technically selected local corpus `corpus-7ba9051125f848e1aed71c46`, and private
typed successor SHA-256
`5207e9c1c003f12798053c667a997e8e0697495f8f4a9cafb2e112ef3aee7fa5`.
All three are quarantined from evidence and evaluation. The control pointer may
still technically select the old corpus, but that does not preserve editorial
acceptance. The successor must not be imported or accepted.

Neither committed candidate contains typed relationship edges. The
`official-reference-v2` grammar remains implemented capability. A repaired
private base and complete 13,136-edge successor now exist outside Git. Exact
successor SHA-256
`35ed3713ee222c2778d58f3962c016ea2fef888bc0f8be4edb2b6aacf5641a4d`
was accepted and verified as private corpus `corpus-eb076af14ec6fff84eb40cf0`
on 2026-08-25, but it remains inactive. The New Testament candidate remains
unaccepted and inactive.

Raw source files, Datalab output, correction profiles, detailed repair reports,
source paths, acquisition records, and credentials remain outside Git. Routine
tests must continue to use synthetic fixtures unless the maintainer separately
authorizes use of an exact candidate digest.

Runtime acceptance and activation live in the private control store rather than
these commit-time manifests. The next Book of Mormon gate is separate activation
of the accepted repaired corpus. The maintainer waived off-workstation backup
only as a pre-acceptance gate for this single-maintainer local-only beta and
accepted rebuild risk; backup and recovery remain required before remote
delivery or irreplaceable member data. None of this authorizes remote delivery.
