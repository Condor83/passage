---
title: Wiki Operations Log
type: overview
created: 2026-08-23
updated: 2026-08-23
sources: []
tags: [log, operations, append-only]
---

# Wiki Operations Log

Append-only chronological record of wiki operations.

## [2026-08-23] create | Passage wiki initialized

Created the wiki index, overview, decision log, operation log, analysis and concept sections. Added synchronized `CLAUDE.md` and `AGENTS.md` instructions so future agents can discover and maintain the wiki.

## [2026-08-23] update | Passage name recorded

Recorded the user-confirmed Passage project name. Flagged the scope of the existing `scripture-chat` technical identifiers as an open question.

## [2026-08-23] create | Datalab apparatus repair documented

Documented the parser root causes, evidence rules, repair results, verification commands, privacy boundary, and remaining cross-reference work. Updated the project overview and corpus-fidelity concept page.

## [2026-08-23] update | Long-term content and database direction recorded

Recorded the confirmed expansion from the Book of Mormon to the LDS scripture canon and, later, Church-leader teachings. Recorded PostgreSQL as the long-term durable database while leaving Supabase versus Neon open.

## [2026-08-23] create | Retrieval and concept-link architecture documented

Added a current architecture analysis for exact, relational, lexical, and semantic retrieval. Kept vectors as an evaluated optional lane and kept provenance-backed typed edges separate from embedding similarity.

## [2026-08-23] create | Study-group access direction documented

Recorded the requirement for scripture study group access through a plugin or MCP integration. Added an adapter-first design, a small read-only MCP tool surface, citation requirements, and open authentication and permission questions.

## [2026-08-23] update | New Testament database candidate documented

Recorded the text-free 27-book structure manifest, Datalab and PDF repair extensions, reviewed source-profile corrections, private inactive candidate result, and complete repository gate. No private source path, digest, scripture text, or derived artifact was added to Git.

## [2026-08-23] lint | Wiki health check after New Testament repair

Checked the decision log, overview, analysis, and concept pages for contradictions and stale status. Verified all internal links and found no missing links or orphan pages. The independent editorial comparison and corpus-acceptance questions remain open and are already recorded.

## [2026-08-23] create | Product specification draft evaluated

Reviewed the external draft passage-product-spec-draft-2026-08-23.md against the decision log, concept pages, the 2026-08-16 Product Contract, and checkout 6f652d6. Recorded three primary findings (Phase 0 sequencing gap, note-tools contradiction with the study-group-access page, derived-edge human-review contradiction with the retrieval page) plus the supersessions approval must record. No decision was confirmed or changed; the draft remains awaiting maintainer approval. Added the analysis page and indexed it.

## [2026-08-23] update | Passage product specification approved and recorded

Added the approved specification under `docs/specs/`. Recorded the explicit local-to-hosted, source-use, recall, Supabase, PostgreSQL cutover, Claude, membership, notes, rename, and derived-edge publication decisions. Updated the overview, PostgreSQL, study-group access, retrieval, content-roadmap, corpus-fidelity, review-analysis, and index pages. Documentation approval did not authorize implementation, private-source processing, corpus acceptance, activation, deployment, or public submission.

## [2026-08-23] lint | Wiki health check after product specification approval

Verified required frontmatter, all local Markdown links, inbound links, and decision-log alignment. Found no broken links or orphan pages. Stale pre-approval phrases occur only inside the preserved static review and append-only historical log entry; the review now records their resolution. Current pages distinguish the implemented SQLite, loopback HTTP, and stdio MCP baseline from the approved but unimplemented PostgreSQL, Supabase, remote MCP, note, and derived-graph direction. Open launch and corpus blockers remain listed in the approved specification and decision log.

## [2026-08-23] update | Datalab repair provenance and privacy hardened

Reviewed the uncommitted New Testament and Datalab implementation against repository standards and the approved specification. Moved exact source-specific correction rules out of Git into a private digest-bound profile, required the repair writer to reject repository-local output, and bound each repair identity to its PDF, Datalab JSON, structure, recipe, optional correction profile, normalized corpus, and findings. Updated the Datalab repair analysis and corpus-fidelity concept page. No private source was processed, accepted, or activated.

## [2026-08-23] lint | Wiki health check after Datalab hardening

Checked all 11 wiki pages for decision alignment, contradictions, stale open questions, frontmatter, local links, index coverage, and inbound links. Found no contradictions, broken links, missing frontmatter, unindexed pages, or orphan pages. The accepted-source, independent editorial comparison, and official-reference grammar questions remain open by design.

## [2026-08-23] update | Agent grounding and database skills prepared

Synchronized `AGENTS.md` and `CLAUDE.md` with the approved current-versus-future product boundary and the small-group simplicity rule. Replaced the stale local-only grounding skill with a Passage grounding skill under `.agents/skills/`. Added pinned Supabase and PostgreSQL guidance for the planned database work. No product decision, remote infrastructure, or private source state changed.

## [2026-08-23] update | Local Supabase configuration initialized

Upgraded the local Supabase CLI from 2.53.6 to 2.115.0 and initialized a lean `passage` project configuration without a schema, seed, remote link, or deployment. Verified PostgreSQL 17.6 and Auth v2.195.0 health with synthetic empty state. Stopped the stack after Docker Desktop published ports on all host interfaces despite the documented loopback network option. Added the loopback stop condition to the PostgreSQL concept page and local development note.

## [2026-08-23] lint | Wiki health check after local Supabase initialization

Verified all 11 wiki pages, frontmatter, local links, inbound links, and index coverage. Found no broken links, orphan pages, index gaps, decision conflicts, or resolved open questions left stale. The new loopback binding question is recorded as an implementation stop condition, not a provider decision change.

## [2026-08-23] update | Bounded Codex subagent roles configured

Added project-scoped Codex configuration for at most three concurrent subagents. A GPT-5.3 Codex Spark mechanical role handles only precise, low-risk, objectively verifiable edits. A stronger read-only reviewer checks correctness, evidence integrity, authorization, data safety, and missing tests. The primary agent retains architecture and integration ownership. Both roles preserve the private-source, corpus, remote-infrastructure, commit, push, and deployment authority boundaries.

## [2026-08-23] create | Autonomous build readiness recorded

Documented the prepared execution worktree, validated baseline, goal-prompt outline, Phase 0 recommendation, subagent contract, proof cadence, completion criteria, and hard stop conditions. The document does not contain the actual goal prompt and does not authorize product implementation or any closed external, source, corpus, cost, deployment, push, or publication gate.

## [2026-08-23] lint | Wiki health check after autonomous build preparation

Checked all 11 wiki pages for required frontmatter, local links, inbound links, index coverage, decision alignment, contradictions, stale claims, unresolved questions, and missing concept coverage. Found no broken links, orphan pages, index gaps, decision conflicts, stale resolved questions, or material concept gaps. The readiness document preserves the Phase 0 boundary and all current source, corpus, OAuth, cost, deployment, and publication gates.

## [2026-08-23] update | Active technical identifiers renamed to Passage

Renamed the Python distribution and package, CLI command, configuration prefix, source-independent profile identities, HTTP title, MCP identity, imports, tests, and active technical documentation to Passage. No compatibility package, command alias, environment fallback, or duplicate MCP identity remains. Preserved the historical product-plan filename and its intentional references. Regenerated only the synthetic EPUB and PDF fixtures and updated their synthetic approval digests. No private source was processed, accepted, or activated.

## [2026-08-23] update | Phase 0 official reference grammar implemented

Recorded `official-reference-v1` as the narrow synthetic Phase 0 contract. Documented canonical slash syntax, explicit semicolon lists, typed internal and unresolved external targets, stable failure codes, full-input rejection, source-span evidence, corpus schema v2 persistence, and inspectable traversal output. Confirmed that private repair-note prose, real-source validation, corpus acceptance, and activation remain closed.

## [2026-08-23] lint | Wiki health check after official reference grammar

Checked all 12 wiki pages for required frontmatter, local links, inbound links, index coverage, decision alignment, contradictions, stale claims, and resolved open questions. Found no critical, warning, or informational findings. The grammar is recorded as synthetic Phase 0 behavior, while accepted-source validation, editorial comparison, candidate acceptance, activation, and Phase 1 service work remain open or blocked by their existing gates.
