---
title: Official Reference Grammar
type: concept
created: 2026-08-23
updated: 2026-08-23
sources:
  - docs/specs/2026-08-23-passage-product-specification.md
  - src/passage/ingest/apparatus.py
tags: [official-references, grammar, phase-0, synthetic, provenance]
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

Each accepted edge records a discriminated internal or external target, grammar version, origin reference and anchor, source attribution, and ordered source spans. Multiple targets reuse the exact originating span evidence and receive separate stable edge identities. Corpus schema v2 stores and exactly reconciles these fields. Traversal and combined evidence search return the official edge records used by their paths through the shared HTTP and MCP contract.

## Closed and Open Boundaries

The current EPUB synthetic profile supplies already normalized `data-target` values. Phase 0 does not parse Datalab repair-note prose, private footnote text, or real source abbreviations. Unsupported source forms fail closed.

Phase 2 must validate and, if necessary, version the grammar against the exact maintainer-accepted Book of Mormon source before official traversal becomes release-eligible. That work requires separate private-source and corpus-acceptance authority.

## Related Pages

- [Corpus Fidelity and Acceptance](corpus-fidelity-and-acceptance.md)
- [Retrieval and Concept Links](retrieval-and-concept-links.md)
- [Project Overview](../overview.md)
