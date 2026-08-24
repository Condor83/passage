---
title: Project Overview
type: overview
created: 2026-08-23
updated: 2026-08-23
sources:
  - docs/plans/2026-08-16-001-feat-scripture-chat-plan.md
  - docs/specs/2026-08-23-passage-product-specification.md
  - docs/plans/2026-08-23-supabase-claude-oauth-compatibility-proof.md
tags: [overview, passage, evidence, postgresql, mcp, study-group]
---

# Passage Overview

## What This Project Is

Passage is a structured evidence and relationship platform for the English LDS scripture canon and, later, English General Conference talks. It converts maintainer-approved sources into private, immutable, citation-ready records. PostgreSQL becomes the primary application store after an approved cutover. A shared domain service exposes exact lookup, context, lexical retrieval, official-reference traversal, and evaluated model-derived relationships. A small owner-managed scripture study group will access that service through authenticated client adapters.

The product returns inspectable evidence. It does not generate authoritative doctrinal conclusions.

## Current Status

- The base repository implements bounded EPUB and text-layer PDF extraction, canonical normalization and validation, immutable SQLite corpus construction, lexical retrieval, HTTP, and MCP.
- A Datalab-specific PDF repair candidate reconstructs all 6,604 canonical passages and links 9,826 unique, nonempty official footnote anchors. See [Datalab PDF Apparatus Repair](analyses/datalab-pdf-apparatus-repair.md).
- A separate New Testament repair candidate reconstructs all 27 books, 260 chapters, and 7,957 verses with 10,091 unique, nonempty official footnote anchors.
- Both private repair candidates remain inactive, unaccepted, and marked `review_required`.
- Official cross-reference targets have not been parsed from the repaired footnote text. The candidates currently contain no relationship edges.
- Phase 0 implements the deterministic `official-reference-v1` synthetic grammar, typed internal and unresolved external targets, persisted edge provenance, and inspectable traversal evidence. It has not been validated against either private repair candidate.
- The limited [Phase 0 Product Loop Probe](analyses/phase0-product-loop-probe.md) ran two locked synthetic questions over exact, lexical, and official lanes. It found zero citation or evidence-class errors and no fatal atomic contract problem. Derived and experimental lanes were absent. The result makes no H1 or promotion claim.
- Phase 0 is landed on `main` at `7eaa011`. The complete source-independent gate passes formatting, lint, mypy, and 200 tests. The two remaining warnings come from dependencies.
- The current implementation uses immutable local SQLite corpus artifacts, loopback HTTP, and stdio MCP. No hosted service, PostgreSQL runtime, authentication system, note surface, or derived graph is implemented.
- The live [Supabase-to-Claude OAuth Compatibility Proof](../docs/plans/2026-08-23-supabase-claude-oauth-compatibility-proof.md) failed P6. Supabase issued a Passage-usable token after a client requested a deliberately wrong resource. The identity-provider decision is reopened. PostgreSQL schema and Auth-foundation work remain blocked.
- The maintainer approved the [Passage Product Specification](../docs/specs/2026-08-23-passage-product-specification.md) on 2026-08-23. Supabase Postgres remains its first database provider. The later failed OAuth gate supersedes its Supabase Auth selection and reopens identity-provider choice.

## Operating Boundaries

- Private scripture source bytes and all derived corpus artifacts stay outside the repository.
- Canonical acceptance requires the maintainer to approve the exact source digest and acquisition record.
- Ambiguous reading order, structure, anchors, or provenance fails closed.
- Corpus versions are immutable. Activation is a separate explicit action.
- Documentation approval does not approve any private source, candidate, corpus activation, implementation, or remote deployment.
- Candidate discovery is recall-first only inside a hard citation-integrity and evidence-class gate.
- The owner accepts unresolved source-use risk for planned invite-only, noncommercial delivery. Passage does not treat that decision as legal clearance.

See [Corpus Fidelity and Acceptance](concepts/corpus-fidelity-and-acceptance.md) for current acceptance rules, the [approved product specification](../docs/specs/2026-08-23-passage-product-specification.md) for approved evolution, and the 2026-08-16 Product Contract for the implemented local baseline.

## Key Decisions

- The project name and all active technical identifiers are **Passage**. The Phase 0 rename removed the prior package, CLI, environment, service, and MCP identifiers without compatibility aliases. Historical plan filenames remain unchanged. See [Decision Log](decisions.md#2026-08-23---all-active-technical-identifiers-will-use-passage).
- The long-term corpus covers the LDS scripture canon, followed by teachings from Church leaders. See [Content Roadmap](concepts/content-roadmap.md).
- Supabase Postgres remains the first PostgreSQL provider. The Supabase Auth selection is reopened after the failed resource-binding gate. PostgreSQL becomes primary only after contract parity and cutover acceptance. See [PostgreSQL Platform](concepts/postgresql-platform.md).
- Claude remote MCP is the first hosted client. Phase 2 is evidence-only; Phase 3 adds the owner/member note model. See [Study Group Access](concepts/study-group-access.md).
- Model-derived relationships remain experimental until the locked H2 and H3 evaluations, including a human sample, pass. See [Retrieval and Concept Links](concepts/retrieval-and-concept-links.md).
- Official target grammar v1 supports only explicit canonical slash forms and semicolon-separated targets. Real-source validation remains a Phase 2 gate. See [Official Reference Grammar](concepts/official-reference-grammar.md).

## Open Questions

- Which accepted-source syntax extensions, if any, will Phase 2 require beyond `official-reference-v1`?
- What independent comparison or review is required before the repaired private candidate can be accepted?
- What evaluation result would justify promoting vectors or hybrid retrieval to a default lane?
- Which identity provider can satisfy the locked Claude remote MCP contract after Supabase Auth failed resource binding?
- Which hobby application host, transactional email provider, and encrypted backup destination will Passage use?
- Which exact source catalogs and citation units will define the complete canon and General Conference corpus versions?
