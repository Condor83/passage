---
title: Wiki Operations Log
type: overview
created: 2026-08-23
updated: 2026-08-25
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

## [2026-08-24] update | Local SQLite beta made the immediate product milestone

Recorded the maintainer's decision to prove Passage locally before resuming hosted-platform work. The immediate beta now uses the implemented immutable SQLite, loopback HTTP, and stdio MCP stack and does not require Docker, Supabase, PostgreSQL runtime selection, authentication, or remote exposure. Phase 1 U1-U3 remain completed source-independent groundwork; U4-U7 are paused until an exact Book of Mormon source passes its separate acceptance and activation gates, typed official references are validated, the locked broad-question evaluation has zero unresolved citation or evidence-class failures, repeated local study flows expose no blocking usability problem, and the maintainer explicitly approves resuming the hosted critical path. No private source processing, corpus acceptance, activation, deployment, invitation, or public submission was authorized by this documentation update.

## [2026-08-24] lint | Wiki health check after local-beta sequencing decision

Checked all 13 wiki pages for required frontmatter, local links, index coverage, authoritative decision alignment, historical-versus-current Phase 1 language, and local-beta versus hosted scope. Found no missing frontmatter, broken local links, index gaps, or current-page contradiction. Historical analyses and operation-log entries retain their original Phase 2 and PostgreSQL sequencing context; current living pages and the amended specification make the local SQLite beta the immediate milestone and keep private-source, acceptance, activation, remote, invitation, and deployment authority gates closed.

## [2026-08-24] sync | Mac candidate commit integrated into Linux main

Fetched Origin and found one commit on each side of common base `85b3d6c`: Mac candidate commit `852f354` and Linux PostgreSQL-foundation commit `614b35f`. Rebased the Linux commit onto the Mac commit, preserving both candidate-policy and Phase 1 documentation; the rebased PostgreSQL commit is `e994ad0`. Restored the uncommitted local-beta documentation and the pre-existing EPUB test edit without staging them. Verified the Book of Mormon and New Testament candidate SHA-256 values against their committed manifests (`1dfd7b927e9fe5f4987a5bb5a3c8d1a0398eec6004cd01f45e86d50096a1e6b4` and `7b2c3cc1fca0652b123c4f74eb9aa05c19eb40d9ca41033097f0e86abd63ad15`). Both snapshots remain inactive, unaccepted, `review_required`, and unused by routine tests.

## [2026-08-24] lint | Wiki and candidate health after cross-machine sync

Validated all four candidate JSON/JSONL files as syntactically complete JSON streams, rechecked both candidate digests, and found no merge markers or whitespace errors. Checked all 13 wiki pages for required frontmatter, local links, index coverage, decision order, candidate-versus-source boundaries, and local-beta sequencing. Found no missing frontmatter, broken local links, index gaps, or current-page contradiction. The Linux branch now contains the Mac candidate commit and is one rebased PostgreSQL commit ahead of Origin; restored local documentation and the pre-existing EPUB test edit remain unstaged.

## [2026-08-24] implement | Exact candidate import path added

Added a strict JSONL candidate loader and `passage corpus import-candidate` command. The loader verifies the exact candidate SHA against its manifest, strict record schemas and grouping, canonical serialized bytes, manifest/header identity, counts, complete canonical structure, passage content hashes, source spans, and corpus validation before the existing immutable SQLite builder can register it. Import requires the exact approved candidate SHA and a short source record, produces private review artifacts, and leaves activation as a separate operation. Added focused unit and CLI integration coverage using only synthetic fixtures.

## [2026-08-24] accept | Book of Mormon candidate approved and activated for local beta

The maintainer stated that the scripture editions were manually downloaded from the Church's free public PDF downloads and vouched for this corpus. Loaded and validated exact Book of Mormon candidate SHA-256 `1dfd7b927e9fe5f4987a5bb5a3c8d1a0398eec6004cd01f45e86d50096a1e6b4`: 6,604 passages, 9,826 apparatus notes, zero typed edges, and complete canonical structure. Imported and reconciled immutable artifact `7ba9051125f848e1aed71c46e26cae2897631f6cd7453a4e59a0d98f0ef0af31`, independently verified it, and atomically activated corpus `corpus-7ba9051125f848e1aed71c46` with retrieval configuration `baseline-5e9588f445459e3165de1278` under the private local root. Metadata lookup passed. No Docker, PostgreSQL, remote exposure, or New Testament acceptance was involved.

## [2026-08-24] review | Candidate import boundary hardened

Reviewed the exact-candidate import path for correctness, project standards, testing, maintainability, and adversarial bypasses. Moved review-artifact publication ahead of corpus acceptance, rejected mismatched provenance-span kinds and duplicate or non-sequential official-footnote anchors, removed the production structure override so fixed scripture scopes always use the packaged complete canonical structure, and expanded synthetic tests for persistence, provenance, manifest identity, validation, and failed publication. The exact approved Book of Mormon candidate still passes all new gates. Unit and integration suites, focused candidate checks, Ruff, formatting, mypy, and whitespace checks passed. Current Python 3.14 transport tests still hang in the pre-existing HTTP/TestClient and real-transport paths, so those cases were reported separately rather than treated as importer failures.

## [2026-08-24] implement | Accepted-source official-reference v2 derivation

Added the fail-closed `official-reference-v2` grammar for the Church-PDF notation present in the approved Book of Mormon candidate. Added exact-candidate-bound derivation, provenance-backed stable edge construction, text-free blocker reports, private edge previews, and conditional successor publication. The command emits an inactive, unaccepted, `review_required` successor only after every reference-bearing note parses; it never imports or activates a corpus. Synthetic unit and CLI integration tests cover internal and external targets, topic-only notes, unsupported forms, report privacy, complete publication, and incomplete quarantine.

## [2026-08-24] analyze | Exact Book of Mormon official-reference run quarantined

Ran `official-reference-v2` exhaustively against approved candidate SHA-256 `1dfd7b927e9fe5f4987a5bb5a3c8d1a0398eec6004cd01f45e86d50096a1e6b4`. Of 9,826 official footnotes, 7,194 reference-bearing notes parsed and 2,624 contained no reference. The private preview contains 13,098 edges: 7,944 internal and 5,154 typed external. Eight notes failed closed across whole-section, whole-chapter or chapter-range, invalid-target, explanatory-JST, and merged-anchor cases. Passage wrote only the private text-free report and edge preview; it created no successor candidate and did not accept, activate, or alter the current active corpus.

## [2026-08-24] lint | Wiki health after official-reference v2 analysis

Checked all 13 wiki pages for required frontmatter, local links, and index coverage after recording the v2 implementation and exact-corpus result. Found no missing frontmatter, broken local links, or index gaps. The overview, fidelity boundary, official-reference concept, product specification, and candidate documentation agree that the current active corpus remains edge-free and that a separately reviewed successor is blocked on eight fail-closed notes.

## [2026-08-24] correct | Whole-chapter references removed from no-reference class

The simplification review found that whole-section and whole-chapter citations without a colon could be misclassified as non-reference notes. Hardened v2 so empty official-note text and recognized chapter- or section-only forms fail closed. The exact candidate rerun retained the same 7,194 parsed notes, 13,098 edges, edge counts, normalized digest, and successor-preview digest, but correctly moved 10 notes from `no_reference` to blockers: 2,614 notes now contain no reference and 18 notes block successor publication. Updated current living pages and the product status; the earlier log entries remain as the append-only record of the pre-hardening result.

## [2026-08-24] review | Hobby-scale official-reference boundary review completed

Right-sized the final review to material corpus-integrity, privacy, and lifecycle risks. Corrected repository-boundary validation so invoking the CLI from another current directory cannot permit derived artifacts inside the checkout; added and passed an outside-CWD regression test. The final exact-corpus run was idempotent at 7,194 parsed notes, 2,614 no-reference notes, 18 blockers, 13,098 preview edges, and successor-preview SHA-256 `3b3b3249f1f0a826d0fdae088d4cbb147e079155601330ce1653c72ebf7e82b8`. Formatting, Ruff, mypy across 50 source files, 133 focused unit and integration tests, whitespace checks, and the 13-page wiki health check passed. No successor candidate was created, accepted, or activated.

## [2026-08-24] decide | Typed whole-unit targets and exact repairs approved

Recorded the maintainer's decision to keep whole chapters, chapter ranges, and Doctrine and Covenants sections as typed official targets rather than expanding them into verse edges. Recorded the exact three approved repairs for source candidate `1dfd7b927e9fe5f4987a5bb5a3c8d1a0398eec6004cd01f45e86d50096a1e6b4`: `Po.` to `Ps.`, explicit 1 Nephi/JST targets, and the merged k/l anchor split. The rules live only in a private source- and note-digest-bound profile.

## [2026-08-24] create | Complete official-reference successor derived

Implemented typed internal and external whole-unit targets, JSON persistence and traversal behavior without verse expansion, and private digest-bound note replacement, splitting, and explicit-target overrides. The exact run produced correction-profile digest `cb2b49d84c68b9f1ee8a1ffe92224c631c92277bc0e4f76c8c12c31169d03e7b` and inactive, unaccepted, `review_required` successor SHA-256 `6cd8df42378c18b7b5eafdbac422c40bde9c88d9ae22b51a5ebe2e8fcb5d0342`. Its 9,827 notes classify as 7,213 reference-bearing and 2,614 no-reference, with zero blockers and 13,136 edges: 7,972 internal and 5,164 external. Strict loader reconciliation passed. The active edge-free corpus was not imported, replaced, or modified.

## [2026-08-24] review | Typed-reference successor boundary hardened

The final local review found and corrected five concrete defects: inbound traversal now recognizes typed internal chapter targets; correction profiles must remain under the configured private root; citation-shaped unknown abbreviations fail closed instead of passing as no-reference; normalized successor digests use canonical record ordering; and deterministic publication installs fully written files atomically so interrupted runs remain retryable. Added focused regressions for each boundary. The external cross-model route was blocked by the environment's data-egress policy, so no repository content left the machine; nine local review lenses and one independent validator batch completed.

## [2026-08-24] create | Canonically reproducible successor regenerated

Preserved the initial unaccepted successor under a private archive name, then reran the exact approved source and correction profile. The complete, idempotent result remains at 9,827 notes, 7,213 reference-bearing notes, 2,614 no-reference notes, zero blockers, and 13,136 edges: 7,972 internal and 5,164 external. Canonical normalized digest `db73a19fcb8e8b8b904dce79d536de4335a7dc418e66e67f25cb870a7feaa836` now survives strict serialization, reload, and recomputation. The current inactive, unaccepted, `review_required` successor SHA-256 is `5207e9c1c003f12798053c667a997e8e0697495f8f4a9cafb2e112ef3aee7fa5`; the active edge-free corpus remains `corpus-7ba9051125f848e1aed71c46` with retrieval configuration `baseline-5e9588f445459e3165de1278`.

## [2026-08-24] verify | Typed-reference successor final gate

The final 171-test unit and focused integration gate passed. Thirty-one MCP tests and twelve contract tests passed before the known Python 3.14 real-stdio and real-transport cases reached their bounded timeout; those pre-existing transport hangs produced no failure output and were not counted as passes. All 158 files passed the format check, Ruff passed, mypy passed across 51 source files, the Git whitespace check passed, and the 13-page wiki health check found no missing frontmatter, broken local links, index gaps, or current-state contradiction. The exact private successor reran idempotently, strict loading and normalized-digest recomputation passed, all publication files are mode `0600` under a `0700` directory, and the active corpus identity remained unchanged.

## [2026-08-25] sync | Typed-reference successor documentation status aligned

Rechecked the pushed implementation, living wiki, candidate documentation, plans, and approved product specification. Corrected stale forward-looking language that still described Book of Mormon typed-reference conversion as pending or treated both candidate families as edge-free. The current pages now agree that the original edge-free Book of Mormon corpus remains active, the complete typed-edge successor remains inactive and `review_required` pending a separate exact-digest approval, the New Testament remains unaccepted without typed edges, and Docker/Supabase work stays paused until the local-beta exit gate passes.

## [2026-08-25] diagnose | Book of Mormon terminal-boundary corruption confirmed and quarantined

A text-free audit found that the final canonical Book of Mormon record contained 1,027,420 characters, 3,486 source spans, and PDF provenance across pages 554-795 because the parser had no terminal source boundary and appended post-canon material. The maintainer confirmed the defect, withdrew editorial authority from base candidate SHA-256 `1dfd7b927e9fe5f4987a5bb5a3c8d1a0398eec6004cd01f45e86d50096a1e6b4`, technically selected local corpus `corpus-7ba9051125f848e1aed71c46`, and typed successor SHA-256 `5207e9c1c003f12798053c667a997e8e0697495f8f4a9cafb2e112ef3aee7fa5`, and quarantined all three from evidence and evaluation. The control pointer may still technically select the old corpus, but it no longer conveys editorial authority. The maintainer authorized repair and private rebuild; acceptance of a new exact digest and activation remain separate decisions. New Testament, platform, and remote-delivery status did not change.

## [2026-08-25] implement | Terminal fidelity safeguards added to current checkout

The current checkout now supports a digest-bound terminal-page cutoff tied to the final canonical reference, validates normalized output before the Datalab writer creates repair files, and rejects scripture passages over 10,000 characters, 64 source spans, or an eight-page PDF provenance window. Focused regressions cover legitimate final-verse continuation, later-page exclusion, fail-closed boundary mismatches, writer rejection, and digest-consistent import rejection without control-state change. This records implemented safeguards only. The exact approved PDF, Marker JSON, and original Datalab profile are absent on this host, so no repaired private candidate, rederived edge set, full gate, new digest, acceptance, or activation is claimed.

## [2026-08-25] review | Existing published corpus now fails closed at repository access

Independent review found that import and writer checks alone did not enforce the quarantine against an already accepted SQLite artifact. Published-artifact validation now parses every persisted passage and applies the same whitespace, character, content-hash, source-span, and PDF-page-window rules before repository access. A regression constructs a digest-consistent oversized legacy artifact, records and activates it in synthetic control state, and confirms that repository opening raises `passage_text_budget_exceeded`. A follow-up review fixed SQLite read-only URI construction so valid private-root names containing URI delimiters remain usable. No real private control state or artifact was changed.

## [2026-08-25] lint | Terminal-fidelity repair documentation and source-independent gate verified

Verified all 13 wiki pages for required frontmatter, local-link integrity, and index coverage with zero findings. Reviewed current decision, overview, specification, candidate, fidelity, grammar, roadmap, and analysis claims for consistent quarantine and rebuild gates. Ruff formatting and lint, mypy across `src`, and the complete 321-test suite pass; two existing dependency warnings remain. No raw source text, source path, correction profile, acquisition detail, or credential entered Git.

## [2026-08-25] rebuild | Reconstructed Book of Mormon candidate and typed successor created privately

The maintainer restored a matching private PDF and Datalab JSON pair and authorized repair. A dry rebuild exposed three ambiguous verse-one boundaries that the broad summary heuristic would truncate. Added exact-input-bound, fragment-fingerprinted verse-one overrides with duplicate, scope, fingerprint, range, and consumption checks; preserved default inference for all other chapters. The Datalab writer now publishes a strict adjacent inactive manifest and round-trips it through the candidate loader. The private base candidate is SHA-256 `f1d0abb72460121179ec944ee43ff3b569a2321265358dd66f20e39ee8b6aa66`, with 6,604 passages, 9,826 notes, zero edges, and a 278-character terminal record on PDF page 554. All nonterminal passage records and all note identities and text match the quarantined lineage. The original private profile remains unrecoverable, so the new profile is explicitly labeled reconstructed.

## [2026-08-25] derive | Repaired typed-edge successor completed without acceptance

Verified that the three already approved official-note corrections still match the rebuilt note IDs and text hashes, rebound them to the new base digest, and reran `official-reference-v2`. The complete private successor is SHA-256 `35ed3713ee222c2778d58f3962c016ea2fef888bc0f8be4edb2b6aacf5641a4d`: 9,827 notes, 7,213 parsed reference-bearing notes, 2,614 no-reference notes, zero blockers, and 13,136 edges (7,972 internal and 5,164 external). Strict loading passed. All 10,280 unique PDF span regions were nonempty; every passage reconciled exactly to its Datalab source block. The private control database still contains one accepted corpus and still points to the quarantined old corpus. Neither new candidate was imported, accepted, or activated. Acceptance remains gated on a truthful raw-source acquisition record, a separate encrypted off-workstation backup with a verified restore path, and maintainer approval of the exact successor digest.

## [2026-08-25] verify | Rebuild code, private artifacts, and wiki passed the right-sized gate

A focused independent code review found no actionable defects. Ruff formatting and lint passed, mypy passed across 51 source files, and all 328 tests passed with the two existing dependency warnings. The 13-page wiki health check found no missing frontmatter, broken local links, or index gaps. Private artifact review verified strict manifests, `review_required` lifecycle flags, immutable permissions, complete derivation counts, and unchanged acceptance and activation state. Raw sources, private profiles, source paths, detailed audit data, and acquisition details remain outside Git.

## [2026-08-25] accept | Repaired Book of Mormon successor accepted inactive

The maintainer approved the truthful private acquisition record and exact successor SHA-256 `35ed3713ee222c2778d58f3962c016ea2fef888bc0f8be4edb2b6aacf5641a4d`, waived off-workstation backup only as a pre-acceptance gate for the single-maintainer local-only beta, accepted rebuild risk, and explicitly withheld activation authority. The source record identifies *The Book of Mormon*, English, Version 1/24, printed 02/2026, and binds the restored raw-input, reconstructed-profile, base, official-reference-profile, successor, and normalized identities without claiming equality with lost historical raw bytes. Exact private source copies remain outside Git under restrictive permissions.

`corpus import-candidate` created accepted inactive corpus `corpus-eb076af14ec6fff84eb40cf0`, artifact SHA-256 `eb076af14ec6fff84eb40cf02e6371dc807512efde0f1ba2f78f5750eb227fb0`, and baseline `baseline-27ce2c9404b2a0e0df20859b`. Explicit-version verification passed. Independent SQLite checks confirmed 6,604 passages, 9,827 apparatus notes, 13,136 edges, integrity `ok`, no foreign-key findings, and a 278-character terminal record with one page-554 span. The private control store now contains two accepted corpus versions, while the active pointer remains the quarantined old corpus/configuration pair. No activation, serving, evaluation, remote exposure, or public submission occurred.
