---
title: PostgreSQL Platform
type: concept
created: 2026-08-23
updated: 2026-08-24
sources:
  - user-confirmed-conversation
  - docs/specs/2026-08-23-passage-product-specification.md
  - docs/plans/2026-08-23-supabase-claude-oauth-compatibility-proof.md
  - docs/plans/2026-08-24-0634-feat-postgres-auth-foundation-plan.md
  - https://supabase.com/docs/guides/auth/oauth-server
  - https://supabase.com/docs/guides/platform/backups
  - https://supabase.com/docs/guides/ai/hybrid-search
  - https://neon.com/docs/ai/ai-concepts
  - https://github.com/pgvector/pgvector
tags: [postgresql, supabase, neon, pgvector, storage]
---

# PostgreSQL Platform

## Confirmed Direction

Supabase Postgres and Supabase Auth remain Passage's first managed platform. The maintainer accepts Supabase Auth's failed wrong-resource binding for the invite-only hobby service without claiming strict RFC 8707 compliance. PostgreSQL becomes the primary application store only after the approved parity and cutover gates pass.

The existing immutable SQLite implementation remains the working local baseline and rollback reference through the alpha. Phase 1 U1 provides a source-independent local Supabase harness on native Docker Engine with a pinned CLI invocation, a loopback-default bridge, automatic port-boundary rejection, secret-suppressed startup, and ephemeral synthetic teardown.

Phase 1 U2 separates the evidence service from backend-specific storage through minimal control-state, request-scoped snapshot, repository-read, lexical-intent, and cleanup contracts. SQLite remains the only application repository and compiles FTS5 syntax inside its adapter.

Phase 1 U3 implements the local PostgreSQL schema and connection foundation without selecting it as a runtime. The private `passage` schema has versioned evidence, complete immutable retrieval-snapshot bindings, lifecycle and accepted-row guards, PostgreSQL full-text search, separate least-privilege logins, forced RLS, and transaction-local request identity through separate bounded pools. Supabase Data API schemas cannot resolve it for anonymous, authenticated, or service-role clients. The importer, PostgreSQL repository, Auth verifier, hosted service, cutover, and real-corpus migration remain unimplemented.

## Why PostgreSQL Fits

PostgreSQL can keep canonical content, source provenance, typed relationships, full-text search, and optional vector embeddings in one transactional system. `pgvector` supports exact and approximate nearest-neighbor search alongside normal SQL joins and constraints.

Supabase supports pgvector and documents PostgreSQL hybrid search with `tsvector` and pgvector. Vector storage remains optional. No semantic lane becomes a default until a locked evaluation proves useful contribution without citation regression.

## Initial Operating Model

- Start with Supabase Free and a hobby or scale-to-zero Python application host.
- Use the Passage application as the only client-facing data authority. MCP clients do not depend on Supabase Data API shapes, roles, or provider URLs.
- Build complete staged corpus versions and atomically activate a compatible corpus, graph, and retrieval snapshot.
- Use standard PostgreSQL migrations where practical and preserve tested `pg_dump` and `pg_restore` paths.
- Create one encrypted off-provider logical backup each day while Supabase Free has no managed downloadable backup path. Test an isolated restore each quarter.
- Upgrade to Supabase Pro when measured storage, cold-start, availability, backup, or operating-cost evidence requires it.

## Authentication Gate

Supabase Auth is selected under a proportionate hobby-project threat model. In the live proof, Supabase accepted a deliberately wrong RFC 8707 resource and the proof-only audience hook still produced a Passage-usable token. P6 remains failed historical evidence. The maintainer accepts this limitation because it does not expose a member's device or chat-provider account credentials and because Passage remains invite-only and read-only at first.

The completed [Supabase-to-Claude OAuth Compatibility Proof](../../docs/plans/2026-08-23-supabase-claude-oauth-compatibility-proof.md) unblocks local PostgreSQL and Auth-foundation work. Remote alpha still requires the proven positive flow, exact token validation, explicit consent, approved callback hosts, current-member enforcement on every call, transactional email, and a bounded Claude regression. Passage does not claim exact RFC 8707 resource binding.

Passwordless member access also requires custom transactional email. Supabase's default project mail service is not the group delivery path.

## Implementation Requirements

- Normal service requests must use a database role that cannot bypass row-level security and must pass verified member identity into each transaction.
- A separate elevated credential may support narrow owner operations only.
- Policy tests must cover normal and elevated roles. User-editable metadata must not control authorization.
- Every accepted corpus and retrieval snapshot remains citation-resolvable after later activations and restores.
- Database size, embedding size, transfer, connector cold starts, and backup results must be measured before the provider plan changes.

Supabase changes frequently. Recheck its changelog and current Auth, RLS, backup, and pricing documentation when implementation starts.

The earlier Docker Desktop route exposed local Supabase ports on all host interfaces. Phase 1 U1 resolved that development blocker by using native Docker Engine and a dedicated bridge whose default published-port address is `127.0.0.1`; the live synthetic stack and automated boundary test both proved only loopback bindings. See [Local Supabase](../../docs/development/supabase-local.md).

## Related Pages

- [Decision Log](../decisions.md)
- [Content Roadmap](content-roadmap.md)
- [Retrieval and Concept Links](retrieval-and-concept-links.md)

## Open Questions

- How will immutable corpus versions map to PostgreSQL schemas, partitions, or version-keyed rows without permitting partial mixed-version reads?
- Which non-bypass role and transaction-claim method will the Passage service use?
- Which hobby application host, transactional email provider, backup destination, and retention policy will be selected?
- What exact parity event permits PostgreSQL cutover and later retirement of the SQLite rollback path?
