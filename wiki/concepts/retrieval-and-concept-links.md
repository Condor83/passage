---
title: Retrieval and Concept Links
type: concept
created: 2026-08-23
updated: 2026-08-23
sources:
  - docs/plans/2026-08-16-001-feat-scripture-chat-plan.md
  - docs/specs/2026-08-23-passage-product-specification.md
  - https://www.postgresql.org/docs/current/textsearch.html
  - https://github.com/pgvector/pgvector
  - https://supabase.com/docs/guides/ai/hybrid-search
  - https://neon.com/docs/ai/ai-concepts
tags: [retrieval, full-text-search, vectors, embeddings, concepts, graph]
---

# Retrieval and Concept Links

## Current Position

Candidate discovery is recall-first inside a hard citation-integrity gate. Passage should surface a weak but potentially useful candidate with its correct evidence label instead of silently omitting it. It must never return or publish an unresolved citation or mislabel a model-derived relationship as official.

Vectors remain useful for semantic recall when exact terms differ. They are not necessary for Passage's canonical foundation and do not replace exact references, source provenance, official links, or lexical search.

The recommended long-term design is hybrid and layered:

1. **Canonical relational layer:** exact source records, identities, editions, provenance, and citation spans.
2. **Explicit relationship layer:** official cross-references plus experimental or published derived concept edges with type, evidence, method, confidence, and immutable graph identity.
3. **Lexical layer:** PostgreSQL full-text search for exact words, phrases, names, and inspectable term matches.
4. **Semantic lane:** embeddings and pgvector for conceptually similar passages or teachings that do not share vocabulary.
5. **Fusion and reranking:** combine independently produced candidate lists only after evaluation proves better discovery without weaker citation integrity.

## Why Vectors Are Not the Knowledge Graph

An embedding distance is a model-derived similarity score. It does not prove that two passages teach the same doctrine, that one explains another, or that an official source connects them.

Concept patterns and links are stored as explicit edges. Each derived edge needs:

- origin and target identities;
- relationship type;
- supporting source spans;
- extraction method and model or rule version;
- confidence or review status;
- corpus and retrieval-configuration identity; and
- generator identity, blind verifier identity, deterministic citation checks, and publication-policy status.

Vectors can propose candidates for these edges. They cannot make the relationship authoritative.

## Derived-Edge Publication

A controlled, resumable, owner-bounded enrichment pipeline may generate relationship candidates over one pinned accepted corpus. It uses a small versioned vocabulary plus `other` with a required free-form label.

Every derived edge remains experimental until locked H2 and H3 evaluations pass. H3 includes a blinded, stratified human sample of default-eligible decisions. Disputed edges remain experimental. After promotion, a generator, independent verifier, deterministic checks, and versioned publication policy may publish a successor default graph without routine human approval of every edge. Sampled audits continue.

Published graph versions and retrieval snapshots are immutable. Edge changes create a successor graph and atomically activated retrieval snapshot rather than mutating prior evidence trails.

## Current Technical Evidence

- PostgreSQL provides native full-text parsing, matching, and ranking.
- pgvector supports exact search plus HNSW and IVFFlat approximate indexes. Approximate indexes trade recall for speed.
- pgvector and Supabase document hybrid search that combines full-text and vector result lists, including reciprocal-rank fusion.
- Supabase and Neon both support pgvector in managed PostgreSQL.

## Retrieval Promotion Rule

Keep vectors as an experimental retrieval lane until an immutable, identity-bound evaluation shows value on locked research cases. Compare at least:

- lexical only;
- official-link traversal;
- vector only;
- lexical plus vector hybrid; and
- hybrid plus explicit concept edges when those edges exist.

Measure retrieval quality, citation correctness, evidence-class labeling, judgment coverage, latency, and failure cases. Do not promote a semantic lane because it appears plausible in a few demonstrations. A complete-canon member release may proceed on a validated lexical and official-reference baseline when derived edges remain experimental and the end-to-end survey gate passes.

The [Phase 0 Product Loop Probe](../analyses/phase0-product-loop-probe.md) compares only exact, lexical, and official behavior in a two-question synthetic corpus. Its zero-error result proves that the limited comparison can run with pinned citations and evidence classes. It does not test H1, semantic retrieval, derived edges, or accepted-corpus coverage.

## Related Pages

- [Content Roadmap](content-roadmap.md)
- [PostgreSQL Platform](postgresql-platform.md)
- [Corpus Fidelity and Acceptance](corpus-fidelity-and-acceptance.md)
- [Datalab PDF Apparatus Repair](../analyses/datalab-pdf-apparatus-repair.md)
- [Phase 0 Product Loop Probe](../analyses/phase0-product-loop-probe.md)

## Open Questions

- Which embedding model and passage or chunk unit should be evaluated?
- Should embeddings attach to verses, paragraph-sized windows, talks, talk sections, concepts, or several separate lanes?
- Which generator and verifier models, prompts, agreement threshold, budget, and stopping rule control the first enrichment run?
- Which initial controlled relationship types are sufficient beyond `parallel`, `contrast`, `explains`, `exemplifies`, `promise-fulfillment`, `shared-theme`, and `other`?
- What locked H2 and H3 results permit automatic default publication?
