---
title: Corpus Fidelity and Acceptance
type: concept
created: 2026-08-23
updated: 2026-08-23
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

- a maintainer-approved exact source digest and acquisition record;
- exact equality with the versioned text-free canonical structure manifest;
- nonempty canonical text for every expected passage;
- unique and sequential official apparatus anchors;
- retained source spans for passages and apparatus;
- no unresolved reading-order, structure, anchor, or provenance ambiguity;
- complete persistence and index reconciliation; and
- immutable private artifacts outside Git.

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

The [Datalab PDF Apparatus Repair](../analyses/datalab-pdf-apparatus-repair.md) satisfies the current structural and anchor reconciliation checks for separate Book of Mormon and New Testament repair candidates. Both remain inactive, unaccepted, and `review_required`. The Phase 0 synthetic grammar now defines typed cross-reference edges and fail-closed parsing. Neither private candidate has been processed with that grammar. Accepted-source validation and independent editorial comparison remain open work.

## Related Pages

- [Project Overview](../overview.md)
- [Decision Log](../decisions.md)
- [Official Reference Grammar](official-reference-grammar.md)

## Open Questions

- Which independent source or review method is sufficient to approve exact editorial fidelity?
- What exact accepted-source validation proves that `official-reference-v1`, or a versioned successor, matches the repaired apparatus?
