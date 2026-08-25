---
title: Project Overview
type: overview
created: 2026-08-23
updated: 2026-08-24
sources:
  - docs/plans/2026-08-16-001-feat-scripture-chat-plan.md
  - docs/specs/2026-08-23-passage-product-specification.md
  - docs/plans/2026-08-23-supabase-claude-oauth-compatibility-proof.md
  - docs/plans/2026-08-24-0634-feat-postgres-auth-foundation-plan.md
tags: [overview, passage, evidence, postgresql, mcp, study-group]
---

# Passage Overview

## What This Project Is

Passage is a structured evidence and relationship platform for the English LDS scripture canon and, later, English General Conference talks. It converts maintainer-approved sources into private, immutable, citation-ready records. PostgreSQL becomes the primary application store after an approved cutover. A shared domain service exposes exact lookup, context, lexical retrieval, official-reference traversal, and evaluated model-derived relationships. A small owner-managed scripture study group will access that service through authenticated client adapters.

The product returns inspectable evidence. It does not generate authoritative doctrinal conclusions.

## Current Status

- The immediate product milestone is now a single-maintainer local beta on immutable SQLite, loopback HTTP, and stdio MCP. Docker, Supabase, PostgreSQL runtime work, authentication, and hosted delivery are not on the local-beta critical path.
- The base repository implements bounded EPUB and text-layer PDF extraction, canonical normalization and validation, immutable SQLite corpus construction, lexical retrieval, HTTP, and MCP.
- A Datalab-specific PDF repair candidate reconstructs all 6,604 canonical passages and links 9,826 unique, nonempty official footnote anchors. See [Datalab PDF Apparatus Repair](analyses/datalab-pdf-apparatus-repair.md).
- A separate New Testament repair candidate reconstructs all 27 books, 260 chapters, and 7,957 verses with 10,091 unique, nonempty official footnote anchors.
- Exact snapshots of both repair candidates are version-controlled under `candidates/`. The maintainer has approved the exact Book of Mormon candidate digest as derived from the Church's free public English 2013 PDF edition; its verified immutable SQLite artifact is accepted and active in the private local runtime. The New Testament snapshot remains inactive, unaccepted, and `review_required`.
- The version-controlled candidates and active Book of Mormon corpus still contain no relationship edges. The maintainer-approved `official-reference-v2` successor now parses all 7,213 reference-bearing notes, retains 2,614 no-reference notes, and contains 13,136 provenance-backed edges: 7,972 internal and 5,164 typed external. The k/l repair increases its note count from 9,826 to 9,827.
- Phase 0 retains the deterministic `official-reference-v1` synthetic grammar. The v2 Church-PDF grammar adds real printed-reference notation, typed verse and whole-unit targets, exact source-candidate and private-correction-profile binding, and fail-closed reporting. Whole chapters, chapter ranges, and D&C sections remain single typed targets instead of expanding into verse edges.
- Complete private successor SHA-256 `5207e9c1c003f12798053c667a997e8e0697495f8f4a9cafb2e112ef3aee7fa5` is inactive, unaccepted, and `review_required`. Its normalized digest is reproducible after canonical serialization and reload. The previously accepted edge-free corpus remains active and unchanged.
- The limited [Phase 0 Product Loop Probe](analyses/phase0-product-loop-probe.md) ran two locked synthetic questions over exact, lexical, and official lanes. It found zero citation or evidence-class errors and no fatal atomic contract problem. Derived and experimental lanes were absent. The result makes no H1 or promotion claim.
- Phase 0 is landed on `main` at `7eaa011`. The complete source-independent gate passes formatting, lint, mypy, and 200 tests. The two remaining warnings come from dependencies.
- The current implementation uses immutable local SQLite corpus artifacts, loopback HTTP, and stdio MCP. No hosted service, PostgreSQL runtime, authentication system, note surface, or derived graph is implemented.
- Phase 1 U1 adds a source-independent local Supabase harness on native Docker Engine. A pinned CLI invocation, dedicated Docker bridge, and environment tests fail closed unless every published API, database, and mail port binds to `127.0.0.1`; the fixture suppresses secret-bearing output and removes its synthetic database volume after each session.
- Phase 1 U2 extracts backend-neutral control, snapshot-session, repository-read, lexical-intent, and cleanup contracts. `EvidenceService` no longer imports SQLite types or compiles FTS5 syntax; the SQLite adapter owns native query compilation and domain-error translation while HTTP, MCP, CLI, evaluation, and the Phase 0 probe retain their existing behavior and SQLite composition. No PostgreSQL repository or runtime cutover exists yet.
- Phase 1 U3 adds the imperative local PostgreSQL foundation in a non-exposed `passage` schema: versioned evidence and complete retrieval-snapshot tables, lifecycle and immutability guards, stored full-text search with a GIN index, separate non-bypass request and maintenance logins, forced RLS, explicit grants, and bounded synchronous Psycopg pools. Synthetic schema, role, policy, context-cleanup, and anon/authenticated/service-role Data API probes pass. No PostgreSQL importer, repository, Auth verifier, runtime selection, hosted service, or cutover exists yet.
- Phase 1 U1-U3 remain completed source-independent groundwork, but U4-U7 are paused. The Book of Mormon acceptance and activation gate is now closed. The next work is to convert and validate typed official references, exercise the real local HTTP/MCP study flow, and run the full local product-loop evaluation.
- The live [Supabase-to-Claude OAuth Compatibility Proof](../docs/plans/2026-08-23-supabase-claude-oauth-compatibility-proof.md) failed P6. Supabase issued a Passage-usable token after a client requested a deliberately wrong resource. Discovery, dynamic registration, exact callback consent, asymmetric validation, refresh, minimal MCP access, and current-member enforcement otherwise worked.
- On 2026-08-24, the maintainer retained Supabase Auth for the invite-only hobby service and accepted the P6 behavior as a documented compatibility limitation. This unblocks local PostgreSQL and Auth-foundation planning and implementation. It does not authorize hosted deployment or claim strict RFC 8707 compliance.

## Operating Boundaries

- Raw scripture source bytes, Datalab output, correction profiles, detailed repair reports, source paths, and acquisition records stay outside the repository. Only the two explicitly approved candidate snapshots and their public digest manifests are version-controlled under `candidates/`.
- Canonical acceptance requires the maintainer to approve the exact import bytes and a truthful source record. For the current local beta, the exact committed candidate digest plus the maintainer's Church-PDF attestation satisfies that requirement without copying the original PDF into this checkout.
- Ambiguous reading order, structure, anchors, or provenance fails closed.
- Corpus versions are immutable. Activation is a separate explicit action.
- Documentation approval does not approve any private source, candidate, corpus activation, implementation, or remote deployment.
- Candidate discovery is recall-first only inside a hard citation-integrity and evidence-class gate.
- The owner accepts unresolved source-use risk for planned invite-only, noncommercial delivery. Passage does not treat that decision as legal clearance.

See [Corpus Fidelity and Acceptance](concepts/corpus-fidelity-and-acceptance.md) for current acceptance rules, the [approved product specification](../docs/specs/2026-08-23-passage-product-specification.md) for approved evolution, and the 2026-08-16 Product Contract for the implemented local baseline.

## Key Decisions

- The project name and all active technical identifiers are **Passage**. The Phase 0 rename removed the prior package, CLI, environment, service, and MCP identifiers without compatibility aliases. Historical plan filenames remain unchanged. See [Decision Log](decisions.md#2026-08-23---all-active-technical-identifiers-will-use-passage).
- The long-term corpus covers the LDS scripture canon, followed by teachings from Church leaders. See [Content Roadmap](concepts/content-roadmap.md).
- Supabase Postgres and Supabase Auth remain the first managed platform under the documented hobby-scale P6 exception. PostgreSQL becomes primary only after contract parity and cutover acceptance. See [PostgreSQL Platform](concepts/postgresql-platform.md).
- A useful local SQLite beta must pass before the PostgreSQL/Auth and hosted-delivery critical path resumes. Docker is not required to run the beta. See [Decision Log](decisions.md#2026-08-24---passage-will-complete-a-local-sqlite-beta-before-hosted-platform-work-resumes).
- Claude remote MCP is the first hosted client. Phase 2 is evidence-only; Phase 3 adds the owner/member note model. See [Study Group Access](concepts/study-group-access.md).
- Model-derived relationships remain experimental until the locked H2 and H3 evaluations, including a human sample, pass. See [Retrieval and Concept Links](concepts/retrieval-and-concept-links.md).
- Official target grammar v2 now covers every reference-bearing note in the approved Book of Mormon source candidate and produces a complete, review-required successor with 13,136 typed edges. See [Official Reference Grammar](concepts/official-reference-grammar.md).

## Open Questions

- What independent comparison or review is required before a repaired candidate snapshot can be accepted?
- What evaluation result would justify promoting vectors or hybrid retrieval to a default lane?
- Which hobby application host, transactional email provider, and encrypted backup destination will Passage use?
- Which exact source catalogs and citation units will define the complete canon and General Conference corpus versions?
