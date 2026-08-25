---
title: Official Reference Grammar
type: concept
created: 2026-08-23
updated: 2026-08-25
sources:
  - docs/specs/2026-08-23-passage-product-specification.md
  - src/passage/ingest/apparatus.py
  - src/passage/ingest/official_edges.py
tags: [official-references, grammar, local-beta, provenance]
---

# Official Reference Grammar

## Phase 0 Contract

Phase 0 implements `official-reference-v1`. This is a deterministic synthetic contract. It is not a claim about the syntax or editorial fidelity of any private source.

The grammar accepts only the canonical slash forms already supported by Passage:

- internal: `bofm/<book>/<chapter>/<verse>` with an optional same-chapter verse range;
- external: `bible`, `dc`, or `pgp` with a book label, chapter, verse, and optional same-chapter verse range; and
- multiple targets: two or more complete targets separated by an explicit semicolon.

The parser trims surrounding whitespace, normalizes spacing around semicolons, and permits one terminal period. It consumes the full input. It does not infer targets from commas, conjunctions, prose, abbreviations, or model output.

## Result States and Codes

- `parsed` / `official_reference_parsed`: every target is a valid internal canonical target.
- `unresolved_external` / `official_reference_unresolved_external_target`: syntax is valid and at least one target is a typed unresolved external target.
- `unsupported` / `official_reference_unsupported_syntax`: the input uses a form outside grammar v1.
- `ambiguous` / `official_reference_ambiguous_syntax`: punctuation or conjunction syntax could imply more than one target without the explicit delimiter.
- `invalid` / `official_reference_invalid_canonical_target`: a known target form is malformed, reversed, or outside the selected synthetic internal structure.
- `invalid` / `official_reference_duplicate_target`: the explicit list repeats a target.

Any failure returns zero targets. A valid prefix never creates an edge when the remainder fails.

## Evidence and Persistence

Each accepted edge records a discriminated internal or external target, grammar version, origin reference and anchor, source attribution, and ordered source spans. An EPUB edge span locates the unique reference-element start tag. Reconciliation checks its exact origin, anchor, target, and source-attribution attributes. Ambiguous or missing reference elements fail closed. Multiple targets reuse the exact originating span evidence and receive separate stable edge identities. Corpus schema v2 stores and exactly reconciles these fields. Traversal and combined evidence search return the official edge records used by their paths through the shared HTTP and MCP contract.

## Book of Mormon PDF Grammar Capability

`official-reference-v2` is the deterministic grammar developed for the Book of Mormon PDF notation. It recognizes canonical book abbreviations, semicolon-separated references with book carry-forward, comma-separated verse lists, verse ranges, whole chapters, chapter ranges, whole Doctrine and Covenants sections, selected parenthetical context, cross-work targets, and non-reference topic or explanatory suffixes. Internal Book of Mormon targets must resolve against the complete structure manifest. Bible, Doctrine and Covenants, and Pearl of Great Price targets remain explicitly typed external references. Every edge retains the originating footnote span and is attributed as an official footnote. This grammar capability remains valid even though the prior exact corpus used to prove it is now quarantined.

Whole chapters, chapter ranges, and sections use distinct `internal_chapter` or `external_chapter` targets with an explicit `chapter` or `section` unit. Passage preserves one edge at the source's printed granularity and does not expand the target into one edge per verse. The originating edge remains visible during traversal; internal whole-unit targets do not fabricate passage-level traversal nodes.

The parser also classifies footnotes with no reference as `no_reference` / `official_reference_not_present`. Any unsupported, invalid, or duplicate form still returns zero targets for that note; a parseable prefix is never persisted when the complete note fails.

The `corpus derive-official-edges` command binds derivation to an explicitly approved source-candidate SHA. Optional source-specific repairs come only from a private correction profile that binds the same SHA and the exact original text digest for each repaired note. It always writes a private, text-free report and edge preview. It writes an inactive, unaccepted, `review_required` successor candidate only when every reference-bearing note parses successfully. Derivation does not import or activate a corpus.

## Quarantined and Rebuilt Book of Mormon Runs

The maintainer chose typed whole-unit targets and approved the three remaining exact reference repairs for source candidate SHA-256 `1dfd7b927e9fe5f4987a5bb5a3c8d1a0398eec6004cd01f45e86d50096a1e6b4`. Those grammar and reference-repair choices remain in force.

The prior v2 derivation classified 9,827 official footnotes:

- 7,213 reference-bearing notes parsed successfully;
- 2,614 notes correctly contained no reference;
- 13,136 provenance-backed edges were derived: 7,972 internal and 5,164 typed external; and
- zero notes failed closed.

Those parser counts resolve O1 as a grammar-capability question, but they no longer prove exact-corpus correctness. The base candidate's final canonical record contained 1,027,420 characters, 3,486 spans, and pages 554-795 because a missing terminal boundary admitted post-canon material. Base SHA-256 `1dfd7b927e9fe5f4987a5bb5a3c8d1a0398eec6004cd01f45e86d50096a1e6b4`, technically selected corpus `corpus-7ba9051125f848e1aed71c46`, and successor SHA-256 `5207e9c1c003f12798053c667a997e8e0697495f8f4a9cafb2e112ef3aee7fa5` are quarantined from evidence and evaluation. The successor must not be imported or accepted.

The private repaired base candidate is SHA-256 `f1d0abb72460121179ec944ee43ff3b569a2321265358dd66f20e39ee8b6aa66`. After the three already approved official-note repairs were rebound only after note-ID and note-text-hash verification, `official-reference-v2` reproduced the same complete classification: 9,827 notes, 7,213 parsed reference-bearing notes, 2,614 no-reference notes, zero blockers, and 13,136 edges (7,972 internal and 5,164 external). The maintainer accepted exact successor SHA-256 `35ed3713ee222c2778d58f3962c016ea2fef888bc0f8be4edb2b6aacf5641a4d` as private corpus `corpus-eb076af14ec6fff84eb40cf0`. Post-import verification passed; activation did not occur.

## Closed and Open Boundaries

The current EPUB synthetic profile supplies already normalized `data-target` values. Phase 0 does not parse Datalab repair-note prose, private footnote text, or real source abbreviations. Unsupported source forms fail closed.

The v2 grammar and approved reference repairs remain implemented capability. The repaired successor now establishes an accepted exact-corpus result. Activation remains a separate maintainer decision. Off-workstation backup was explicitly waived only as a pre-acceptance gate for this local-only beta; it remains required before remote delivery or irreplaceable member data.

## Related Pages

- [Corpus Fidelity and Acceptance](corpus-fidelity-and-acceptance.md)
- [Retrieval and Concept Links](retrieval-and-concept-links.md)
- [Project Overview](../overview.md)
