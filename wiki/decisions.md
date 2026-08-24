---
title: Decision Log
type: overview
created: 2026-08-23
updated: 2026-08-23
sources:
  - user-confirmed-conversation
  - docs/specs/2026-08-23-passage-product-specification.md
  - docs/plans/2026-08-23-supabase-claude-oauth-compatibility-proof.md
tags: [decisions, authoritative, passage]
---

# Decision Log

This is the authoritative record of confirmed Passage project decisions. When another living wiki page disagrees with this page, this page controls until the user updates the decision.

## Confirmed Decisions

### 2026-08-23 - Project name is Passage

- **Decision:** Use **Passage** as the project name.
- **Rationale:** The name matches the remote repository and gives the project one human-facing identity.
- **Supersedes:** The human-facing project name **Scripture Chat**.
- **Scope:** Wiki and project-facing documentation created from this decision use Passage.
- **Pages updated:** [Project Overview](overview.md), [Wiki Index](index.md), `CLAUDE.md`, and `AGENTS.md`.

### 2026-08-23 - Long-term corpus includes the LDS canon and Church-leader teachings

- **Decision:** Expand Passage from the current Book of Mormon validation scope to the complete LDS scripture canon, then add talks and teachings from Church leaders.
- **Rationale:** The long-term product should support structured research across the canon and the wider body of authoritative Church teaching.
- **Supersedes:** The assumption that the Book of Mormon is the final corpus boundary. It remains the first implementation and validation scope.
- **Pages updated:** [Project Overview](overview.md) and [Content Roadmap](concepts/content-roadmap.md).

### 2026-08-23 - PostgreSQL is the long-term durable database

- **Decision:** Store the long-term structured corpus and derived research data in PostgreSQL.
- **Rationale:** One relational system can preserve canonical identities, provenance, typed links, full-text indexes, and optional vector embeddings.
- **Provider status:** Updated by [Supabase is the first managed platform](#2026-08-23---supabase-is-the-first-managed-platform-and-postgresql-becomes-primary-after-cutover).
- **Supersedes:** SQLite as the assumed final durable platform. Immutable SQLite remains the implemented local-first baseline until a separate migration is designed and approved.
- **Pages updated:** [Project Overview](overview.md) and [PostgreSQL Platform](concepts/postgresql-platform.md).

### 2026-08-23 - Passage must support study-group client access

- **Decision:** Let the scripture study group access Passage through a supported plugin or MCP integration.
- **Rationale:** Group members should use the same citation-ready corpus and retrieval service from the AI clients they already use.
- **Architecture boundary:** Keep client protocols outside the corpus and retrieval domain model. MCP is an adapter over the Passage service, not the durable data contract.
- **Selection status:** Updated by [Claude remote MCP and the owner-managed group model](#2026-08-23---claude-remote-mcp-and-the-owner-managed-group-model-are-selected).
- **Pages updated:** [Project Overview](overview.md) and [Study Group Access](concepts/study-group-access.md).

## Reversed or Updated Decisions

### 2026-08-23 - Passage product specification approved

- **Decision:** Approve the [Passage Product Specification](../docs/specs/2026-08-23-passage-product-specification.md) as the current product authority for work beyond the implemented local baseline.
- **Rationale:** The specification records the completed product interview, measurable gates, review reconciliation, and explicit boundaries between current implementation and approved evolution.
- **Supersedes:** Conflicting product direction in the 2026-08-16 Product Contract. That document remains the historical authority for the implemented local SQLite baseline.
- **Authority boundary:** Approval authorizes documentation updates only. It does not authorize implementation, private-source processing, test-only candidate use, corpus acceptance, activation, deployment, or public submission.
- **Pages updated:** [Project Overview](overview.md), [PostgreSQL Platform](concepts/postgresql-platform.md), [Study Group Access](concepts/study-group-access.md), [Retrieval and Concept Links](concepts/retrieval-and-concept-links.md), and [Content Roadmap](concepts/content-roadmap.md).

### 2026-08-23 - Passage evolves from local-only use to an invite-only hosted group service

- **Decision:** Keep the current loopback HTTP and stdio MCP implementation as the local baseline, then add a separately gated, authenticated remote service for a small owner-managed study group.
- **Rationale:** Group members should use Passage through the AI clients they already use while the shared Passage service preserves one evidence and authorization contract.
- **Supersedes:** The 2026-08-16 local-first, loopback-only, single-user scope and its stop condition against remote exposure. Remote work remains blocked until the approved OAuth, authorization, content-risk, and operations gates pass.
- **Pages updated:** [Project Overview](overview.md) and [Study Group Access](concepts/study-group-access.md).

### 2026-08-23 - Owner accepts unresolved source-use risk for invite-only delivery

- **Decision:** Permit planning for noncommercial, invite-only remote delivery of manually acquired Church-supplied PDFs despite unresolved redistribution permission.
- **Rationale:** The owner accepts the unresolved risk so the small study group can test the product, while Passage preserves attribution, bounded results, no bulk-export tool, takedown controls, and an immediate service-disable path.
- **Supersedes:** The 2026-08-16 position that redistribution without verified permission is outside the product's identity.
- **Boundary:** This is not legal clearance. It does not authorize scraping, automatic Church-site downloads, public corpus access, commercial use, or corpus activation without exact source approval.
- **Pages updated:** [Project Overview](overview.md), [Content Roadmap](concepts/content-roadmap.md), and [Study Group Access](concepts/study-group-access.md).

### 2026-08-23 - Candidate discovery is recall-first within a citation-integrity gate

- **Decision:** Prefer recall when generating clearly labeled candidates, but reject unresolved citations and evidence-class errors from every returned or published relationship.
- **Rationale:** Passage exists to surface patterns a person may not know to request. A broad candidate set supports that goal only when every item remains inspectable and correctly labeled.
- **Supersedes:** The earlier emphasis that selected citation integrity over recall as if they were competing release goals. Citation integrity remains a hard gate; recall controls candidate discovery inside that gate.
- **Pages updated:** [Retrieval and Concept Links](concepts/retrieval-and-concept-links.md).

### 2026-08-23 - Supabase is the first managed platform and PostgreSQL becomes primary after cutover

- **Decision:** Use Supabase Postgres and Auth as the first managed platform. Start on Supabase Free with a hobby or scale-to-zero application host and upgrade to Pro when measured limits require it.
- **Rationale:** Supabase provides managed PostgreSQL and the first identity path in one service for the small group. Standard PostgreSQL migrations, logical backups, and provider-exit tests limit lock-in.
- **Supersedes:** The open Supabase-versus-Neon provider choice and the assumption that immutable SQLite remains the final primary runtime store.
- **Cutover boundary:** The current SQLite system remains the implemented local reference and rollback path until PostgreSQL contract parity and atomic cutover acceptance pass. Supabase OAuth-to-Claude compatibility is the first Phase 1 proof and may reopen the identity-provider choice.
- **Pages updated:** [Project Overview](overview.md) and [PostgreSQL Platform](concepts/postgresql-platform.md).

### 2026-08-23 - Claude remote MCP and the owner-managed group model are selected

- **Decision:** Use Claude remote MCP as the first hosted client. Use passwordless email, an owner-managed allowlist, and only `owner` and `member` roles. Run a private ChatGPT developer-mode beta after Claude.
- **MCP sequence:** Phase 2 exposes atomic read-only evidence tools. Phase 3 adds private and group-visible citation-linked Markdown notes after its permission, visibility, member-removal, backup, and recovery gates pass.
- **Note authority:** The normal choice is group-visible, but every create request states visibility explicitly. Only the author can change a note through note tools. Permanent member removal is the narrow owner deletion exception.
- **Supersedes:** The open first-host, authentication, role, note, and permission questions in the earlier study-group access direction.
- **Pages updated:** [Project Overview](overview.md) and [Study Group Access](concepts/study-group-access.md).

### 2026-08-23 - All active technical identifiers will use Passage

- **Decision:** Rename the Python distribution and package, CLI command, configuration prefix, service titles, MCP identity, and active documentation to Passage without long-lived compatibility aliases.
- **Rationale:** One technical and product identity reduces permanent migration surface and client confusion.
- **Supersedes:** The open question that limited Passage to a human-facing name.
- **Historical boundary:** Existing plan filenames remain unchanged as historical records.
- **Pages updated:** [Project Overview](overview.md).

### 2026-08-23 - Automatic derived-edge publication requires evidence first

- **Decision:** Keep every model-derived relationship experimental until locked H2 and H3 evaluations pass. H3 includes a blinded, stratified human sample. After promotion, generator, independent verifier, deterministic checks, and a versioned policy may publish default edges without routine per-edge human approval.
- **Rationale:** This preserves the automated long-running discovery goal without silently removing the wiki's human-review safeguard before evidence exists.
- **Supersedes:** The unresolved derived-edge review workflow and any reading that either required permanent human approval of every edge or allowed immediate automatic default publication.
- **Pages updated:** [Retrieval and Concept Links](concepts/retrieval-and-concept-links.md).

### 2026-08-23 - Official reference grammar v1 is synthetic and fail closed

- **Decision:** Phase 0 uses `official-reference-v1`: complete canonical slash targets, explicit semicolon-separated multiple targets, typed internal or unresolved external results, full-input consumption, and stable parse states and codes.
- **Rationale:** The current canonical identity contract supports these forms without inventing private source syntax or inferring official relationships from prose.
- **Failure rule:** Ambiguous, unsupported, invalid, duplicate, or partially parsed input creates no edge. External syntax remains unresolved until its source work is accepted and available.
- **Evidence rule:** Every edge preserves its origin anchor, source attribution, grammar version, and ordered source spans through persistence and traversal.
- **Authority boundary:** This decision is proven only with synthetic fixtures. It does not validate either private repair candidate or authorize real-source processing, acceptance, activation, or editorial-fidelity claims.
- **Pages updated:** [Official Reference Grammar](concepts/official-reference-grammar.md), [Project Overview](overview.md), and [Corpus Fidelity and Acceptance](concepts/corpus-fidelity-and-acceptance.md).

### 2026-08-23 - Phase 1 starts with the Supabase-to-Claude OAuth proof

- **Decision:** The live Supabase-to-Claude OAuth compatibility proof is the only Phase 1 entry gate. Do not start PostgreSQL schema work first.
- **Rationale:** Current documentation shows a plausible OAuth path but does not prove Claude interoperability, RFC 8707 resource handling, exact audience binding, token refresh, or current-member enforcement.
- **Failure rule:** A material failure after one bounded correction cycle reopens the identity-provider decision. Do not work around a failed identity gate by starting the database foundation.
- **Pass effect:** A complete pass permits the PostgreSQL and Auth foundation to begin. It does not prove passwordless email, RLS, remote alpha, corpus, deployment, or release readiness.
- **Authority boundary:** Design is approved. Live execution requires separate authority for the disposable hosted Supabase project, public HTTPS harness, and Claude connection.
- **Pages updated:** [Project Overview](overview.md), [PostgreSQL Platform](concepts/postgresql-platform.md), and [Study Group Access](concepts/study-group-access.md).

### 2026-08-23 - Supabase Auth failed the Phase 1 resource-binding gate

- **Decision:** Reopen the identity-provider decision. Do not start PostgreSQL schema, migration, or Auth-foundation work.
- **Evidence:** A public OAuth client requested a deliberately wrong RFC 8707 resource. Supabase issued a token, the proof-only hook assigned the Passage audience, and the Passage resource server accepted the token. This fails P6 of the locked [Supabase-to-Claude OAuth Compatibility Proof](../docs/plans/2026-08-23-supabase-claude-oauth-compatibility-proof.md).
- **What passed:** Claude discovery, dynamic registration, exact callback, explicit consent, asymmetric token validation, a five-minute refresh cycle, minimal MCP listing and call, HTTP 403 inactive-member enforcement, and inactive-member consent blocking were observed.
- **Supersedes:** The Supabase Auth part of [Supabase is the first managed platform](#2026-08-23---supabase-is-the-first-managed-platform-and-postgresql-becomes-primary-after-cutover). Supabase Postgres remains the selected first PostgreSQL provider. No replacement identity provider is selected.
- **Boundary:** The proof used only synthetic identity and `whoami` data. It did not start the local Supabase stack, create an application schema, process private sources, or deploy scripture content.
- **Pages updated:** [Project Overview](overview.md), [PostgreSQL Platform](concepts/postgresql-platform.md), and [Study Group Access](concepts/study-group-access.md).

### 2026-08-23 - Exact scripture candidate snapshots may be committed

- **Decision:** Commit the exact current Book of Mormon and New Testament derived candidate snapshots under `candidates/` with public digest manifests.
- **Lifecycle boundary:** Both snapshots remain inactive, unaccepted, and `review_required`. The commit does not approve a source edition, establish editorial fidelity, authorize routine test use, activate a corpus, or authorize remote delivery.
- **Privacy boundary:** Raw PDFs, Datalab output, correction profiles, detailed repair reports, source paths, acquisition records, and credentials remain outside Git.
- **Supersedes:** The blanket rule that all derived corpus data and scripture text must stay outside Git. The exception applies only to exact candidate snapshots that the maintainer explicitly approves.
- **Pages updated:** [Project Overview](overview.md), [Corpus Fidelity and Acceptance](concepts/corpus-fidelity-and-acceptance.md), [Content Roadmap](concepts/content-roadmap.md), and [Datalab PDF Apparatus Repair](analyses/datalab-pdf-apparatus-repair.md).

## Open Questions

- Vector storage and semantic retrieval are not confirmed as default behavior. They require a measured retrieval evaluation.
- Accepted-source validation evidence and any required successor to `official-reference-v1` remain undefined.
- The generator, verifier, embedding model, prompts, cost ceiling, and edge-publication thresholds are not selected.
- Which identity provider can satisfy Claude discovery, PKCE, exact redirects, RFC 8707 resource binding, consent, refresh, asymmetric validation, and current-member enforcement?
- The hobby application host, transactional email provider, backup destination, and retention schedule are not selected.
- The exact accepted editions and digests for each standard work remain unapproved.
- General Conference talk-span citation units and dated source catalogs remain undefined.
