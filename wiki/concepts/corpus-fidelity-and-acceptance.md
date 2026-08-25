---
title: Corpus Fidelity and Acceptance
type: concept
created: 2026-08-23
updated: 2026-08-24
sources:
  - docs/plans/2026-08-16-001-feat-scripture-chat-plan.md
  - docs/specs/2026-08-23-passage-product-specification.md
  - wiki/analyses/datalab-pdf-apparatus-repair.md
tags: [corpus, fidelity, validation, privacy, acceptance]
---

# Corpus Fidelity and Acceptance

## Core Distinction

A repair candidate is not an accepted corpus. Passage keeps extraction, validation, acceptance, and activation as separate authority levels.

## Required Evidence

An accepted corpus requires:

- maintainer-approved exact import bytes and a truthful acquisition or source record;
- exact equality with the versioned text-free canonical structure manifest;
- nonempty canonical text for every expected passage;
- unique and sequential official apparatus anchors;
- retained source spans for passages and apparatus;
- no unresolved reading-order, structure, anchor, or provenance ambiguity;
- complete persistence and index reconciliation; and
- immutable artifacts with exact digests and a separate private backup. A maintainer may approve an inactive candidate snapshot for version control without accepting or activating it.

For a PDF source, glyph and overlay evidence must support the extracted tokens and anchors. Visual review is a useful sanity check, but it does not replace exhaustive reconciliation.

Source-specific extraction corrections must live in a private profile outside Git. The profile must bind to the exact source and extraction-input digests before the parser can apply it. Repair artifacts must also record the structure and recipe identities used to produce them.

## Lifecycle

1. Inspect and fingerprint the source.
2. Build an isolated candidate.
3. Validate structure, provenance, apparatus, persistence, and indexes.
4. Record maintainer acceptance for the exact source and artifact identities.
5. Activate the compatible corpus and baseline retrieval configuration in a separate atomic action.

Every accepted corpus version and retrieval snapshot remains resolvable for the product lifetime. A later archival design may move old records out of hot storage only if the same citation identity remains automatically resolvable.

Failure at any step leaves the prior active state unchanged.

## Current Application

The [Datalab PDF Apparatus Repair](../analyses/datalab-pdf-apparatus-repair.md) satisfies the structural and anchor reconciliation checks for separate Book of Mormon and New Testament repair candidates. Exact snapshots are committed under `candidates/` with public digest manifests. On 2026-08-24 the maintainer vouched that the Book of Mormon input came from the Church's free public English 2013 PDF edition and approved exact candidate SHA-256 `1dfd7b927e9fe5f4987a5bb5a3c8d1a0398eec6004cd01f45e86d50096a1e6b4`. Passage imported, reconciled, verified, accepted, and activated the resulting immutable SQLite artifact locally. The New Testament candidate remains inactive, unaccepted, and `review_required`.

The exact candidate SHA is the local-beta import identity. Its embedded normalized digest is retained as the repair-pipeline identity; because the historical serializer sorted note records after calculating that digest, the JSONL cannot reproduce it independently. Passage therefore verifies the manifest-to-header digest, the exact file SHA, canonical JSONL form, every passage content hash, counts, source spans, complete structure, SQLite rows and indexes, and the final artifact digest.

The acceptance gate for the edge-free candidate is closed. The maintainer subsequently chose typed whole-unit reference targets and approved three exact, digest-bound repairs. `official-reference-v2` produced complete private successor SHA-256 `5207e9c1c003f12798053c667a997e8e0697495f8f4a9cafb2e112ef3aee7fa5` with 9,827 official notes and 13,136 provenance-backed typed edges. The strict candidate loader independently reconciled its manifest and canonical bytes, and its normalized digest is stable after serialization and reload.

That successful derivation does not extend the earlier acceptance decision. The successor remains inactive, unaccepted, and `review_required`; the active corpus remains the earlier edge-free artifact. Import, verification, acceptance, and activation require a separate exact-digest decision.

## Related Pages

- [Project Overview](../overview.md)
- [Decision Log](../decisions.md)
- [Official Reference Grammar](official-reference-grammar.md)

## Open Questions

- What proportionate exact-digest review is required before the complete successor is accepted and activated?
