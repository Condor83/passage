---
title: Product Spec Draft Review (2026-08-23)
type: analysis
created: 2026-08-23
updated: 2026-08-23
sources:
  - docs/specs/2026-08-23-passage-product-specification.md
  - wiki/decisions.md
  - docs/plans/2026-08-16-001-feat-scripture-chat-plan.md
tags: [product-spec, review, roadmap, mcp, supabase, governance]
---

# Product Spec Draft Review (2026-08-23)

Review of the external draft that became the approved [Passage Product Specification](../../docs/specs/2026-08-23-passage-product-specification.md), against the decision log, concept pages, the 2026-08-16 Product Contract, and checkout `6f652d6`. This page preserves the pre-approval review and its resolution.

## Resolution

The maintainer approved the revised specification on 2026-08-23 after every primary and secondary finding below was addressed:

- Phase 0 became a limited available-lane feasibility probe, with the complete H1 gate moved to Phase 2 after accepted evidence and typed official links exist.
- Phase 2 remained evidence-only; note tools moved to Phase 3.
- All derived edges remained experimental until H2 and H3 pass, including a blinded human sample before automatic default publication.
- Superseded-corpus resolvability, New Testament status, removed-member note behavior, and HTTP/MCP parity became explicit requirements.
- The decision log now records the local-to-hosted, source-use, recall, provider, client, identity, note, and technical-rename supersessions.

Specification approval authorized documentation updates only. It did not authorize implementation, private-source processing, corpus acceptance, activation, deployment, or public submission.

## Verdict

The draft is coherent, internally consistent, and unusually honest about legal and reliability risk. It is approvable after three findings are resolved: a Phase 0 sequencing gap, and two contradictions with recorded wiki direction that require an explicit maintainer decision rather than silent supersession.

## Finding 1 - Phase 0 gate depends on assets Phases 1-2 produce

Phase 0 requires the host-composed atomic research loop to beat a fixed survey workflow on locked broad questions using the current local surface, before PostgreSQL and remote hosting become the critical path. But no accepted corpus exists (the Book of Mormon repair candidate is unaccepted, inactive, `review_required`), and it contains zero official reference edges because footnote-target parsing (O1) is scheduled in Phase 1. The rubric's evidence-class-separation and edge-traversal grading cannot fully run. Options: pull O1 forward, explicitly authorize test-only local use of the unaccepted candidate, and scope the Phase 0 rubric to available lanes with a full re-run in Phase 2. Note the current surface otherwise maps cleanly: the six existing operations are five atomic tools plus combined evidence search, which is exactly the fixed-workflow comparator H1 needs.

## Finding 2 - Contradiction: study-note write tools in the first MCP surface

[Study Group Access](../concepts/study-group-access.md) records: write tools for notes "should not enter the first MCP surface." The draft's first remote contract includes six note-write tools and AC9 requires a note save in one end-to-end session. This is reconcilable if the Phase 2 remote alpha surface is evidence-only and notes ship with the Phase 3 member release, but the draft does not say so. The maintainer should either phase the note tools explicitly or record the supersession.

## Finding 3 - Contradiction: human review of derived edges

[Retrieval and Concept Links](../concepts/retrieval-and-concept-links.md) requires human review when a derived edge could be presented as a meaningful teaching relationship. The draft publishes default-graph edges on generator + blind verifier + deterministic checks alone (Decision 12, R44), with humans sampling only evaluation judgments (R51b); H3 explicitly hypothesizes human edge review is unnecessary. Until H3 has evidence, either require human sample review of default-graph edges or keep the derived graph experimental (the draft's Phase 3 fallback already permits releasing on the lexical and official-reference baseline).

## Approval must record supersessions

Approving the draft overturns or resolves recorded positions; each needs a dated decision-log entry:

- Local-first, loopback-only, no multi-user hosting (2026-08-16 Product Contract scope and stop condition) → remote hosted invite-only service.
- Redistribution of protected source text listed as outside product identity → owner-accepted unresolved risk for invite-only delivery (R23). Sharpest supersession; deserves its own entry.
- Citation-integrity-over-recall emphasis → "retrieval is recall-first" (Decision 16; integrity still controls via R5).
- Open questions resolved: Supabase over Neon (Decision 18), rename scope including package and CLI (Decision 25), Claude as first host, PostgreSQL as primary runtime store, notes and membership model.

Overview and three concept pages also need updates after approval.

## Secondary findings

- O6 (Supabase OAuth server versus Claude remote MCP requirements) is high-probability, not hypothetical; R63a's reopening clause is right, but it should be the first Phase 1 task, not a late gate.
- Retention of superseded accepted corpus versions is unspecified; note citations pin original corpus and snapshot identity, which requires old versions to stay resolvable or a citation-migration rule.
- Draft §5 mentions only the Book of Mormon repair candidate; the New Testament repair candidate (27 books, 260 chapters, 7,957 verses) and in-progress NT manifest work are omitted.
- No data rule for a removed member's notes (retain, export, or delete).
- HTTP/MCP transport parity is a current repo invariant enforced by contract tests; the remote architecture implies it (R53) but should require it explicitly.
- Trivial: tool names drifted from the concept page (`follow_references`/`get_source_provenance` vs `traverse_connections`/`get_provenance`).

## Strengths

Honest legal posture (R23/R24), no-content logging, prompt-injection treatment of all corpus and note text as data, fail-closed note visibility, owner-bounded enrichment spend, immutable retrieval snapshots (R9a), measurable and modest gates (AC16a-c, AC17-19), provider-exit requirements, and reopening clauses on identity and hosting decisions.

## Related Pages

- [Decision Log](../decisions.md)
- [Project Overview](../overview.md)
- [Study Group Access](../concepts/study-group-access.md)
- [Retrieval and Concept Links](../concepts/retrieval-and-concept-links.md)
- [PostgreSQL Platform](../concepts/postgresql-platform.md)
- [Content Roadmap](../concepts/content-roadmap.md)
