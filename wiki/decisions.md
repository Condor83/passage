---
title: Decision Log
type: overview
created: 2026-08-23
updated: 2026-08-25
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
- **Authority boundary:** This decision is proven only with synthetic fixtures. It does not validate either candidate snapshot or authorize candidate use, acceptance, activation, or editorial-fidelity claims.
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

### 2026-08-24 - Supabase Auth is retained with a hobby-scale compatibility exception

- **Decision:** Use Supabase Auth for Passage. Accept its failure to bind a deliberately wrong RFC 8707 resource for the invite-only hobby service. Do not claim that P6 passed or that Supabase Auth provides strict RFC 8707 resource binding.
- **Rationale:** The live proof showed that the failure can expose Passage access only after a member authorizes a client. It does not expose a member's computer or Claude, Codex, Anthropic, or OpenAI account credentials. Provider migration and enterprise-grade controls are disproportionate for the small trusted group and nonsensitive evidence-only alpha.
- **Required controls:** Validate asymmetric signature, algorithm, key, issuer, Passage audience, expiry, subject, and client identity. Require explicit consent, restrict accepted callback hosts, check current owner-managed membership before every tool dispatch, keep the first remote catalog read-only, and never log or pass through tokens.
- **OAuth capability boundary:** Use Supabase-supported OIDC scopes for identity. Passage enforces evidence and later note capabilities in the application because Supabase Auth does not provide Passage-specific OAuth scopes.
- **Supersedes:** The identity-provider reopening and PostgreSQL/Auth-foundation block in [Supabase Auth failed the Phase 1 resource-binding gate](#2026-08-23---supabase-auth-failed-the-phase-1-resource-binding-gate). The failed proof remains historical evidence and is not rewritten as a pass.
- **Authority boundary:** This decision permits planning and local source-independent implementation. It does not authorize local non-loopback exposure, hosted deployment, member invitations, transactional email, private-source processing, corpus acceptance, activation, or public submission.
- **Pages updated:** [Project Overview](overview.md), [PostgreSQL Platform](concepts/postgresql-platform.md), [Study Group Access](concepts/study-group-access.md), and the [Passage Product Specification](../docs/specs/2026-08-23-passage-product-specification.md).

### 2026-08-24 - Passage will complete a local SQLite beta before hosted platform work resumes

- **Decision:** Make a usable, single-maintainer local beta the immediate product milestone. Run it on the implemented immutable SQLite, loopback HTTP, and stdio MCP stack. Docker, Supabase, PostgreSQL runtime work, authentication, and remote delivery are not required for this beta and remain paused until its exit gate passes.
- **Rationale:** Passage needs to prove that an accepted corpus and the host-composed evidence workflow are useful in real local study before investing further in multi-user infrastructure.
- **Local beta scope:** Accept one exact Book of Mormon source through the existing authority gates; validate typed official references; exercise lookup, context, lexical search, official traversal, HTTP/MCP parity, and the locked broad-question product-loop evaluation; record usability gaps from actual local use.
- **Exit gate:** Resume the hosted platform critical path only after the local beta has a maintainer-accepted corpus, zero unresolved citation or evidence-class failures in its locked evaluation, and an explicit maintainer decision that the local workflow is useful enough to share remotely.
- **Supersedes:** The execution order that made the remaining PostgreSQL/Auth foundation the next critical path before a real local product beta. It does not reverse PostgreSQL, Supabase Auth, or invite-only hosted access as possible later direction.
- **Existing work:** Phase 1 U1-U3 remain completed, source-independent groundwork. U4-U7 of the PostgreSQL/Auth foundation plan are paused; the historical implementation and test evidence remain valid.
- **Authority boundary:** This documentation decision does not itself authorize private-source processing, candidate acceptance, corpus activation, non-loopback exposure, hosted deployment, member invitations, or public submission.
- **Pages updated:** [Project Overview](overview.md), [PostgreSQL Platform](concepts/postgresql-platform.md), [Study Group Access](concepts/study-group-access.md), [Content Roadmap](concepts/content-roadmap.md), [Official Reference Grammar](concepts/official-reference-grammar.md), and the [Passage Product Specification](../docs/specs/2026-08-23-passage-product-specification.md).

### 2026-08-24 - Exact Book of Mormon candidate approved and activated locally

- **Decision:** Accept candidate SHA-256 `1dfd7b927e9fe5f4987a5bb5a3c8d1a0398eec6004cd01f45e86d50096a1e6b4` as the exact Book of Mormon input for the local beta and activate its verified immutable SQLite artifact.
- **Source record:** The maintainer manually downloaded and vouches for the Church's freely available English 2013 Book of Mormon PDF edition. Passage records the official Church PDF URL and the exact derived candidate digest; it does not require the original PDF bytes to be copied into this Linux checkout.
- **Rationale:** The exact committed candidate, its digest manifest, complete 6,604-passage structure, 9,826 apparatus anchors, retained source spans, content hashes, and reconciled SQLite artifact provide a proportionate acceptance record for the single-maintainer local beta.
- **Runtime identity:** Corpus `corpus-7ba9051125f848e1aed71c46` with retrieval configuration `baseline-5e9588f445459e3165de1278` is active under the configured private local root. The root path is local operational state and is not recorded as a portable repository default.
- **Boundary:** This approval applies only to the exact Book of Mormon candidate and local SQLite use. It does not approve the New Testament candidate, claim that typed official-reference edges exist, authorize remote delivery, or resolve public-release permissions.
- **Supersedes:** The Book of Mormon portion of the earlier unaccepted-candidate state and the requirement that this local beta retain the original PDF bytes or digest after the exact candidate and source record are approved. The commit-time candidate manifest remains historical lifecycle evidence.
- **Pages updated:** [Project Overview](overview.md), [Corpus Fidelity and Acceptance](concepts/corpus-fidelity-and-acceptance.md), [Content Roadmap](concepts/content-roadmap.md), [Wiki Index](index.md), and [Scripture Corpus Candidates](../candidates/README.md).

### 2026-08-24 - Whole scripture units remain typed and three exact official-reference repairs are approved

- **Decision:** Represent an official citation to a whole chapter, chapter range, or Doctrine and Covenants section as one typed target. Do not expand it into one edge per verse.
- **Approved repairs:** For exact source candidate SHA-256 `1dfd7b927e9fe5f4987a5bb5a3c8d1a0398eec6004cd01f45e86d50096a1e6b4`, correct the printed `Po. 42:2` target to `Ps. 42:2`; treat the explanatory note at `bofm/1-ne/21/24` as targeting `bofm/1-ne/21/25` and `JST Isa. 49:25`; and split the merged `k`/`l` note at `bofm/1-ne/19/10` into separate sequential anchors.
- **Rationale:** A whole-unit target preserves the source's actual citation granularity and remains inspectable without fabricating a denser verse-level graph. The three source-specific repairs are maintainer-confirmed and remain isolated in a private profile bound to the exact source candidate digest.
- **Resulting candidate:** Correction-profile digest `cb2b49d84c68b9f1ee8a1ffe92224c631c92277bc0e4f76c8c12c31169d03e7b` produced inactive, unaccepted successor SHA-256 `5207e9c1c003f12798053c667a997e8e0697495f8f4a9cafb2e112ef3aee7fa5` with 9,827 notes and 13,136 official edges. This identity supersedes the initial unaccepted derivation after canonical digest ordering was corrected. All reference-bearing notes parse; the active edge-free corpus remains unchanged.
- **Authority boundary:** This decision authorizes the exact repairs and successor derivation only. The successor remains `review_required`; import, acceptance, and activation require a separate maintainer decision.
- **Pages updated:** [Project Overview](overview.md), [Official Reference Grammar](concepts/official-reference-grammar.md), [Corpus Fidelity and Acceptance](concepts/corpus-fidelity-and-acceptance.md), and [Scripture Corpus Candidates](../candidates/README.md).

### 2026-08-25 - Corrupted Book of Mormon corpus authority is withdrawn and repair is authorized

- **Decision:** Withdraw editorial authority from Book of Mormon base candidate SHA-256 `1dfd7b927e9fe5f4987a5bb5a3c8d1a0398eec6004cd01f45e86d50096a1e6b4`, local corpus `corpus-7ba9051125f848e1aed71c46`, and typed successor SHA-256 `5207e9c1c003f12798053c667a997e8e0697495f8f4a9cafb2e112ef3aee7fa5`. Quarantine all three identities from evidence and evaluation. Do not import or accept the successor.
- **Evidence:** The final canonical record contained 1,027,420 characters, 3,486 source spans, and provenance across PDF pages 554-795 because the parser had no terminal source boundary and appended post-canon material. This text-free diagnosis is sufficient to invalidate the earlier corpus-fidelity conclusion.
- **Operational boundary:** The private control pointer may still technically select `corpus-7ba9051125f848e1aed71c46`. That pointer records local operational state only; it no longer conveys acceptance or editorial authority and must not be used for evidence or evaluation.
- **Repair result:** The maintainer restored a matching private PDF and Datalab JSON pair. The original correction profile was not recoverable, so the repair used a newly identified, exact-input-bound reconstructed profile with a terminal cutoff and three fingerprinted verse-one boundary overrides. The private base candidate is SHA-256 `f1d0abb72460121179ec944ee43ff3b569a2321265358dd66f20e39ee8b6aa66`; the complete rederived typed-edge successor is SHA-256 `35ed3713ee222c2778d58f3962c016ea2fef888bc0f8be4edb2b6aacf5641a4d`. Both remain inactive, unaccepted, and `review_required`. No import or activation occurred.
- **Next gate:** Bind a truthful acquisition record to the restored raw identities, create and verify a separate encrypted off-workstation backup, and present exact successor SHA-256 `35ed3713ee222c2778d58f3962c016ea2fef888bc0f8be4edb2b6aacf5641a4d` for maintainer approval. Import and post-import verification follow approval. Activation remains a separate decision.
- **Preserved direction:** `official-reference-v2` remains grammar-capability resolved, including typed whole-unit targets and the three approved reference repairs. Its prior exact-corpus result is quarantined and must be rederived. New Testament, local-beta-first sequencing, PostgreSQL, Supabase Auth, hosted-delivery, and remote-authorization status do not change.
- **Supersedes:** The editorial acceptance and evidence-use effects of [Exact Book of Mormon candidate approved and activated locally](#2026-08-24---exact-book-of-mormon-candidate-approved-and-activated-locally), while preserving its historical account of what the control store did. It also supersedes the prior successor's eligibility for exact-digest acceptance in [Whole scripture units remain typed and three exact official-reference repairs are approved](#2026-08-24---whole-scripture-units-remain-typed-and-three-exact-official-reference-repairs-are-approved), without reversing the grammar or approved reference-repair choices.
- **Pages updated:** [Project Overview](overview.md), [Corpus Fidelity and Acceptance](concepts/corpus-fidelity-and-acceptance.md), [Official Reference Grammar](concepts/official-reference-grammar.md), [Content Roadmap](concepts/content-roadmap.md), [Datalab PDF Apparatus Repair](analyses/datalab-pdf-apparatus-repair.md), [Wiki Index](index.md), [Scripture Corpus Candidates](../candidates/README.md), and the [Passage Product Specification](../docs/specs/2026-08-23-passage-product-specification.md).

### 2026-08-25 - Repaired Book of Mormon successor accepted locally but not activated

- **Decision:** Accept exact successor SHA-256 `35ed3713ee222c2778d58f3962c016ea2fef888bc0f8be4edb2b6aacf5641a4d` for the single-maintainer local beta. Manual content review is not required because exhaustive source-block, PDF-span, structure, passage-integrity, apparatus, edge, persistence, and index reconciliation passed with zero blockers.
- **Source record:** The private approval record binds the restored PDF and Datalab JSON digests, the actual publication identity (*The Book of Mormon*, English, Version 1/24, printed 02/2026), reconstructed correction profile, base candidate, official-reference profile, exact successor, and normalized digest. It records exact current supplied bytes and a source-block lineage match without claiming identity with lost historical raw bytes.
- **Backup waiver:** For this exact local-only beta corpus, the maintainer explicitly waives the off-workstation encrypted backup as a pre-acceptance gate and accepts loss/rebuild risk. No backup or restore-path claim is made. R95b remains required before remote delivery or irreplaceable member data.
- **Runtime identity:** Accepted inactive corpus `corpus-eb076af14ec6fff84eb40cf0`, artifact SHA-256 `eb076af14ec6fff84eb40cf02e6371dc807512efde0f1ba2f78f5750eb227fb0`, and baseline retrieval configuration `baseline-27ce2c9404b2a0e0df20859b`. Post-import verification passed. The active pointer remains the quarantined old corpus/configuration pair.
- **Authority boundary:** Activation remains separately gated and is not authorized by this decision. The accepted corpus must not serve, evaluate, or supply evidence through the default active pointer until activation is explicitly approved. This decision does not authorize remote delivery, member access, or public submission.
- **Supersedes:** The acceptance and backup prerequisites in the prior repair decision for this exact successor only. It preserves the quarantine of the corrupted historical lineage and the separate activation gate.
- **Pages updated:** [Project Overview](overview.md), [Corpus Fidelity and Acceptance](concepts/corpus-fidelity-and-acceptance.md), [Official Reference Grammar](concepts/official-reference-grammar.md), [Content Roadmap](concepts/content-roadmap.md), [Datalab PDF Apparatus Repair](analyses/datalab-pdf-apparatus-repair.md), [Wiki Index](index.md), [Scripture Corpus Candidates](../candidates/README.md), and the [Passage Product Specification](../docs/specs/2026-08-23-passage-product-specification.md).

### 2026-08-25 - Repaired Book of Mormon corpus activated for the local beta

- **Decision:** Activate accepted corpus `corpus-eb076af14ec6fff84eb40cf0` with its compatible baseline `baseline-27ce2c9404b2a0e0df20859b` for the single-maintainer local SQLite beta.
- **Verification:** The activation command opened and revalidated the immutable artifact before atomically changing the pointer. Independent control-store checks confirmed the exact new pair and integrity `ok`. The supported metadata surface reports the Version 1/24, printed 02/2026 edition, schema v2, and both lexical and official lanes. In-process HTTP and stdio MCP checks agreed on the corpus/configuration pair, corrected terminal-passage hash and length, lexical result ordering, and two terminal-passage official edges.
- **Prior state:** The corrupted historical corpus remains immutable and accepted as historical control data but is no longer active and retains no editorial authority. Its quarantine from evidence and evaluation remains in force.
- **Next gate:** Run the locked broad-question product-loop evaluation against this active pair, require zero citation-resolution and evidence-class failures, exercise repeated real local study flows, and record whether the local workflow is useful enough to pass the beta exit gate.
- **Authority boundary:** Activation authorizes local loopback HTTP and stdio MCP evidence use only. It does not authorize non-loopback exposure, hosted deployment, member access, PostgreSQL cutover, or public submission. The narrow local-beta backup waiver remains unchanged.
- **Supersedes:** The inactive runtime state and separate activation question in [Repaired Book of Mormon successor accepted locally but not activated](#2026-08-25---repaired-book-of-mormon-successor-accepted-locally-but-not-activated). It preserves that decision's exact source, corpus, backup-waiver, and remote-delivery boundaries.
- **Pages updated:** [Project Overview](overview.md), [Corpus Fidelity and Acceptance](concepts/corpus-fidelity-and-acceptance.md), [Official Reference Grammar](concepts/official-reference-grammar.md), [Content Roadmap](concepts/content-roadmap.md), [Datalab PDF Apparatus Repair](analyses/datalab-pdf-apparatus-repair.md), [Wiki Index](index.md), [Scripture Corpus Candidates](../candidates/README.md), and the [Passage Product Specification](../docs/specs/2026-08-23-passage-product-specification.md).

## Open Questions

- Vector storage and semantic retrieval are not confirmed as default behavior. They require a measured retrieval evaluation.
- Does the locked broad-question evaluation and repeated real local study flow establish zero citation/evidence-class failures and enough usefulness to pass the local-beta exit gate?
- The generator, verifier, embedding model, prompts, cost ceiling, and edge-publication thresholds are not selected.
- The hobby application host, transactional email provider, backup destination, and retention schedule are not selected.
- The exact accepted editions and digests for the New Testament and later standard works remain unapproved.
- General Conference talk-span citation units and dated source catalogs remain undefined.
