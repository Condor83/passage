---
title: Corpus Fidelity and Acceptance
type: concept
created: 2026-08-23
updated: 2026-08-25
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
- a source-specific terminal boundary when the canonical work ends before the source asset ends;
- no unresolved reading-order, structure, anchor, or provenance ambiguity;
- complete persistence and index reconciliation; and
- immutable artifacts with exact digests and a separate private backup. A maintainer may approve an inactive candidate snapshot for version control without accepting or activating it.

For a PDF source, glyph and overlay evidence must support the extracted tokens and anchors. Visual review is a useful sanity check, but it does not replace exhaustive reconciliation.

Source-specific extraction corrections must live in a private profile outside Git. The profile must bind to the exact source and extraction-input digests before the parser can apply it. Repair artifacts must also record the structure and recipe identities used to produce them.

The current checkout also fails closed when scripture passage text exceeds 10,000 characters, source provenance exceeds 64 spans, or PDF provenance spans more than eight pages. The Datalab writer validates normalized output before it creates repair files, candidate import applies the same checks, and published SQLite artifacts revalidate every passage before repository access. These are corruption backstops, not substitutes for exact source review or maintainer approval.

## Lifecycle

1. Inspect and fingerprint the source.
2. Build an isolated candidate.
3. Validate structure, provenance, apparatus, persistence, and indexes.
4. Record maintainer acceptance for the exact source and artifact identities.
5. Activate the compatible corpus and baseline retrieval configuration in a separate atomic action.

Every accepted corpus version and retrieval snapshot remains resolvable for the product lifetime. A later archival design may move old records out of hot storage only if the same citation identity remains automatically resolvable.

Failure at any step leaves the prior active state unchanged.

## Current Application

The [Datalab PDF Apparatus Repair](../analyses/datalab-pdf-apparatus-repair.md) previously appeared to satisfy Book of Mormon structure and anchor reconciliation because all 6,604 canonical identities were present. A later text-free audit found that the final canonical record contained 1,027,420 characters, 3,486 source spans, and pages 554-795. The parser had no terminal source boundary and appended post-canon material to that record. Structure equality, hashes, and persistence reconciliation therefore did not establish editorial fidelity.

The maintainer confirmed the defect on 2026-08-25 and withdrew editorial authority from exact base candidate SHA-256 `1dfd7b927e9fe5f4987a5bb5a3c8d1a0398eec6004cd01f45e86d50096a1e6b4`, private local corpus `corpus-7ba9051125f848e1aed71c46`, and typed successor SHA-256 `5207e9c1c003f12798053c667a997e8e0697495f8f4a9cafb2e112ef3aee7fa5`. All three are quarantined from evidence and evaluation. The control pointer may still technically select the old corpus, but that state is not editorial acceptance and must not be used.

The current checkout implements a digest-bound terminal-page cutoff that must match the last canonical reference, must be encountered, and fails if the parser reaches it before that reference. Exact-input-bound, fragment-fingerprinted verse-one overrides handle three ambiguous chapter starts without weakening default summary inference. The Datalab writer validates normalized output, publishes a strict adjacent manifest, and round-trips the immutable result through the candidate loader. The character, span, and page-window backstops above also reject a digest-consistent legacy artifact at repository open even when private control state already records it as accepted.

The maintainer restored a matching private PDF and Datalab JSON pair, but no surviving report proves historical raw-byte identity and the original Datalab profile remains unavailable. Passage created a newly identified reconstructed profile and private base candidate SHA-256 `f1d0abb72460121179ec944ee43ff3b569a2321265358dd66f20e39ee8b6aa66`. The rebuilt terminal record contains 278 characters, one span, and PDF page 554; all nonterminal passage records and all note identities and text match the quarantined lineage. Whole-corpus source-block and nonempty-overlay checks passed.

The rederived typed-edge successor is SHA-256 `35ed3713ee222c2778d58f3962c016ea2fef888bc0f8be4edb2b6aacf5641a4d`, with 9,827 notes, zero blockers, and 13,136 edges. It remains inactive, unaccepted, and `review_required`. Acceptance is blocked until a truthful acquisition record binds the restored raw identities, a separate encrypted off-workstation backup and restore path are verified, and the maintainer approves this exact successor digest. Import verification and activation remain separate. The New Testament candidate remains inactive, unaccepted, and `review_required`.

## Related Pages

- [Project Overview](../overview.md)
- [Decision Log](../decisions.md)
- [Official Reference Grammar](official-reference-grammar.md)

## Open Questions

- Which encrypted off-workstation backup destination and restore procedure will satisfy the acceptance gate?
