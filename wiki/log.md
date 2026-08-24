---
title: Wiki Operations Log
type: overview
created: 2026-08-23
updated: 2026-08-24
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

## [2026-08-23] create | Phase 0 product loop probe recorded

Documented the committed two-question synthetic definition, fixed reference-pool rubric, five atomic operations, `search_evidence` comparator, pinned identity and evidence audits, and measured report identity. Recorded exact, lexical, and official lanes as present; derived and experimental as absent; zero citation errors; zero evidence-class errors; and no fatal atomic contract problem. Preserved `h1_status: not_evaluated` and no promotion claim. Generated reports remain outside Git.

## [2026-08-23] lint | Wiki health check after Phase 0 probe

Checked all 13 wiki pages for required frontmatter, local links, inbound links, index coverage, decision alignment, contradictions, stale claims, resolved open questions, and Phase 0 versus Phase 2 scope. Found no critical, warning, or informational findings. Current pages distinguish the measured synthetic zero-error result from H1, accepted-corpus evaluation, private-source validation, and promotion eligibility.

## [2026-08-23] fix | Official-edge EPUB provenance hardened

Changed synthetic EPUB official-edge spans to locate the unique reference-element start tag instead of matching the first occurrence of short anchor text. Reconciliation now checks the exact origin, anchor, target, and source attribution. Added repeated-anchor, ambiguous-element, target-tamper, and attribution-tamper regression coverage. Re-ran the deterministic synthetic Phase 0 probe and updated its corpus, retrieval, and report identities. The measured result remains zero citation errors, zero evidence-class errors, no fatal atomic contract problem, `h1_status: not_evaluated`, and not promotion eligible. No private source was processed, accepted, or activated.

## [2026-08-23] lint | Wiki health check after provenance fix

Checked all 13 wiki pages for required frontmatter, local links, and index coverage. Found no missing frontmatter, broken links, or unindexed current pages. The provenance correction changes synthetic artifact identities but does not change a product decision or open a private-source, corpus, H1, deployment, or publication gate.

## [2026-08-23] update | Phase 0 landed and Phase 1 OAuth gate designed

Fast-forwarded `main` from `988f7cb` to Phase 0 commit `7eaa011`, passed the complete source-independent gate with 200 tests and the two known dependency warnings, and pushed `main` to `origin`. Researched current Supabase, Claude, and MCP primary documentation. Added the locked synthetic Supabase-to-Claude proof design and recorded that it is the only Phase 1 entry gate. PostgreSQL schema work remains blocked. Live proof execution awaits explicit authority for a disposable hosted Supabase project, public HTTPS harness, and Claude connection. The local Supabase stack remains stopped.

## [2026-08-23] lint | Wiki health check after Phase 1 gate design

Checked all 13 wiki pages for required frontmatter, local links, index coverage, decision and overview alignment, stale Phase 0 status, and the Phase 1 authority boundary. Found no missing frontmatter, broken links, unindexed current pages, decision conflict, or stale current-state claim. The live OAuth result, hosted-project authority, public-harness authority, Claude connection, local port-binding fix, and PostgreSQL foundation remain open or blocked as recorded.

## [2026-08-23] update | Supabase Auth compatibility gate failed and identity decision reopened

Ran the authorized synthetic Supabase-to-Claude proof with no scripture or private source content. Claude completed discovery, dynamic registration, exact callback consent, ES256 validation, a five-minute refresh cycle, and the single `whoami` tool path. After one proof-harness correction, a valid inactive member received HTTP 403 before tool dispatch and could not approve authorization. P6 failed: a dynamic client requested a deliberately wrong RFC 8707 resource, Supabase issued a token, the proof-only hook assigned the Passage audience, and Passage accepted the token. Reopened the identity-provider decision and kept PostgreSQL schema, migration, Auth foundation, local Supabase startup, and private-source work blocked. Sanitized raw evidence remains outside Git. Teardown is pending.

## [2026-08-23] lint | Wiki health check after OAuth gate failure

Checked all 13 wiki pages for required frontmatter, local links, index coverage, decision alignment, contradictions, stale OAuth status, and resolved open questions. Found no missing frontmatter, broken links, index gaps, or current-page conflict. Historical Supabase Auth selection remains in the decision record with an explicit supersession. Current pages keep Supabase Postgres separate from the reopened identity-provider choice. Teardown remained the only open proof operation; PostgreSQL and Auth foundation work remained blocked.

## [2026-08-23] delete | Phase 1 OAuth proof teardown completed

Disconnected and removed the Claude custom connector. Stopped the proof harness and its public tunnel, then removed the temporary harness directory. Deleted the disposable Supabase project, including its synthetic user, grants, and sessions. Verified that the local harness no longer accepts connections, the former public tunnel returns HTTP 530, and the former Supabase Auth discovery endpoint returns HTTP 410. Kept the sanitized evidence record outside Git. PostgreSQL and Auth foundation work remain blocked by the failed P6 gate.

## [2026-08-23] lint | Wiki health check after OAuth proof teardown

Checked all 13 wiki pages for required frontmatter, local links, index coverage, decision alignment, contradictions, stale OAuth status, and resolved open questions. Found no missing frontmatter, broken links, index gaps, or current-page conflict. Current pages record the failed P6 gate, the reopened identity-provider decision, the completed teardown, and the continued PostgreSQL and Auth foundation block.

## [2026-08-23] create | Scripture candidate snapshots added to Git

Added the exact current Book of Mormon and New Testament candidate JSONL snapshots under `candidates/` with public digest and lifecycle manifests. Scanned both artifacts for embedded local paths, credentials, email addresses, URLs, and unexpected fields before copying them. Both remain inactive, unaccepted, `review_required`, and without relationship edges. Raw PDFs, Datalab output, correction profiles, detailed repair reports, source paths, and acquisition records remain outside Git.

## [2026-08-23] lint | Wiki health check after candidate snapshot decision

Checked all 13 wiki pages for required frontmatter, local links, index coverage, decision alignment, and the revised candidate privacy boundary. Found no missing frontmatter, broken links, index gaps, or current-page conflict. The current pages distinguish version control from source approval, corpus acceptance, activation, routine test use, and remote delivery.

## [2026-08-24] update | Supabase Auth retained and Phase 1 continuation planned

Recorded the maintainer's proportionate hobby-project decision to retain Supabase Auth. Preserved P6 as a failed wrong-resource test and accepted it as a compatibility limitation without claiming strict RFC 8707 compliance. Updated the product specification so supported OIDC scopes establish identity while Passage enforces tool capabilities and current membership. Created the implementation-ready local Phase 1 plan for a loopback-safe PostgreSQL harness, backend-neutral storage boundary, versioned schema, synthetic lifecycle, backend parity, and Auth membership foundation. Hosted deployment, transactional email, member invitations, private-source work, corpus acceptance, activation, and public submission remain closed.

## [2026-08-24] lint | Wiki health check after Phase 1 continuation plan

Checked all 13 wiki pages for required frontmatter, local links, index coverage, decision alignment, current-versus-historical OAuth status, and implemented-versus-approved claims. Found no missing frontmatter, broken links, index gaps, current-page contradiction, or whitespace error. The plan review tightened connection-role separation, synthetic authenticated dispatch, lexical parity, and retry semantics while keeping hosted deployment, real-corpus work, and public access closed.

## [2026-08-24] create | Phase 1 loopback-safe PostgreSQL harness

Implemented Phase 1 U1 with native Docker Engine, the pinned `npx --yes supabase@2.115.0` CLI path, a dedicated loopback-default bridge, and a guarded session fixture. The fixture verifies Node.js, CLI, and Docker prerequisites before startup, suppresses secret-bearing command output, rejects missing services and every non-`127.0.0.1` published binding, and stops the Passage project after success or failure. The live synthetic PostgreSQL, Auth, API, and mail stack passed 15 environment tests and left no containers running. No application schema, migration, private source, corpus operation, hosted link, remote exposure, invitation, or deployment was added.

## [2026-08-24] lint | Wiki health check after Phase 1 U1

Checked all 13 wiki pages for required frontmatter, local links, index coverage, and alignment between the U1 implementation, overview, PostgreSQL concept, and controlling decisions. Found no missing frontmatter, broken links, index gaps, or claim that the local harness is an application runtime. The PostgreSQL schema, Auth implementation, private-source, corpus, hosted, remote-access, invitation, and deployment gates remain closed.

## [2026-08-24] verify | Phase 1 U1 source-independent gate

Verified the loopback harness through the complete source-independent gate: 143 files passed the format check, Ruff and mypy passed, and all 215 tests passed with the two known dependency warnings. The live Supabase fixture again started only on `127.0.0.1`, stopped after the session, and left no Passage containers running. `git diff --check` also passed.

## [2026-08-24] update | Phase 1 backend-neutral storage contracts

Implemented Phase 1 U2 with backend-neutral control-state, request-scoped snapshot, repository-read, structured lexical-intent, and cleanup contracts. Moved FTS5 compilation and SQLite exception translation into the SQLite repository adapter, adapted CLI and evaluation composition, and preserved the existing HTTP and MCP service factories without backend conditionals. Added characterization for normal, domain-failure, and cancellation cleanup plus structured lexical intent and adapter error translation. Focused SQLite integration, API, MCP, contract, acceptance, CLI, evaluation, and Phase 0 behavior passed 107 tests with the two known dependency warnings. No PostgreSQL schema, repository, private-source operation, hosted exposure, authentication, corpus activation, or cutover was added.

## [2026-08-24] lint | Wiki health check after Phase 1 U2

Checked all 13 wiki pages for required frontmatter, local links, index coverage, decision alignment, and implemented-versus-approved claims. Found no missing frontmatter, broken links, index gaps, decision conflict, or current-state drift. Current pages identify SQLite as the only implemented repository, the U2 contracts as backend-neutral preparation, and the PostgreSQL schema, repository, Auth runtime, hosted exposure, private-source, corpus, activation, and cutover gates as still closed.

## [2026-08-24] verify | Phase 1 U2 source-independent gate

Verified the backend-neutral storage extraction through the complete source-independent gate: dependency sync succeeded, 144 files passed the format check, Ruff passed, mypy passed across 46 source files, and all 220 tests passed with the two known dependency warnings. The focused U2 suite separately passed 107 SQLite integration, API, MCP, contract, acceptance, CLI, evaluation, and Phase 0 tests. SQLite remains the active local backend; no PostgreSQL runtime, private corpus, remote exposure, authentication, activation, or cutover was exercised.

## [2026-08-24] update | Phase 1 PostgreSQL schema and security foundation

Implemented Phase 1 U3 through the CLI-generated imperative migration `20260824221345_phase1_foundation.sql`. The non-exposed `passage` schema now defines synthetic source, corpus lifecycle, canonical and versioned passage, apparatus, official-edge, retrieval-configuration, complete retrieval-snapshot, active-pointer, and membership records. Constraints and triggers enforce lifecycle transitions, retry claims, validated and accepted immutability, rejected cleanup, one snapshot per corpus/configuration pair, activation timestamps, and stored English `tsvector` search with a GIN index. Separate non-inheriting, non-bypass request and maintenance logins receive explicit grants under forced RLS. Bounded Psycopg pools use distinct redacted DSNs and parameter-bound transaction-local issuer, subject, and client context. The ephemeral local fixture removes stale synthetic volumes before startup and after shutdown; it never uses the unsafe local reset path that republished PostgreSQL beyond loopback.

## [2026-08-24] review | Independent Phase 1 U3 schema and policy review

Three read-only scouts investigated migration structure, database roles, and RLS/Data API behavior. After maintainer review, Main applied snapshot-identity uniqueness, lifecycle/retry, transitive role, staging-visibility, malformed-context, API-role, and clean-start corrections. An independent reviewer then assessed the resulting schema, privileges, policies, pools, and tests and found no blocker. Main applied its remaining documentation, activation-timestamp, fail-closed child-guard, stale-stack, and credential-redaction recommendations. No subagent edited repository files.

## [2026-08-24] verify | Focused Phase 1 U3 PostgreSQL suite

Verified the final U3 foundation against a fresh loopback-only local Supabase stack. All 39 PostgreSQL checks passed, covering migration application and recorded history, database advisors, schema and index shape, full-text search, lifecycle and retry transitions, accepted-row immutability, complete snapshot binding, login attributes, transitive role separation, forced RLS, active/disabled/absent and malformed request context, staging and rejected visibility, connection reuse after success/error/cancellation, credential redaction, and anonymous/authenticated/service-role REST and GraphQL non-exposure. The fixture stopped the stack and deleted its synthetic database volume. PostgreSQL import, repository parity, Auth verification, runtime selection, hosted delivery, private-source work, corpus activation, and cutover remain closed.

## [2026-08-24] lint | Wiki health check after Phase 1 U3

Checked all 13 wiki pages for required frontmatter, local links, index coverage, decision alignment, and implemented-versus-approved claims. Found no missing frontmatter, broken links, index gaps, decision conflict, or current-state drift. Current pages identify the U3 migration and security foundation as local synthetic infrastructure while keeping SQLite as the only application repository and runtime; PostgreSQL import, parity, Auth, hosted access, private-source, activation, and cutover gates remain closed.

## [2026-08-24] verify | Phase 1 U3 source-independent gate

Verified U3 through the complete source-independent gate: dependency sync succeeded, 149 files passed the format check, Ruff passed, mypy passed across 48 source files, and all 244 tests passed with the two known dependency warnings. The PostgreSQL fixture applied the generated migration to a fresh local database, kept all published ports on `127.0.0.1`, passed migration-history and database-advisor checks, and removed every Passage container and synthetic database volume after the session.
