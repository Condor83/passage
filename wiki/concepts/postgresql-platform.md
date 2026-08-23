---
title: PostgreSQL Platform
type: concept
created: 2026-08-23
updated: 2026-08-23
sources:
  - user-confirmed-conversation
  - docs/specs/2026-08-23-passage-product-specification.md
  - https://supabase.com/docs/guides/auth/oauth-server
  - https://supabase.com/docs/guides/platform/backups
  - https://supabase.com/docs/guides/ai/hybrid-search
  - https://neon.com/docs/ai/ai-concepts
  - https://github.com/pgvector/pgvector
tags: [postgresql, supabase, neon, pgvector, storage]
---

# PostgreSQL Platform

## Confirmed Direction

Supabase Postgres and Auth are Passage's first managed platform. PostgreSQL becomes the primary application store after the approved parity and cutover gates pass.

The existing immutable SQLite implementation remains the working local baseline and rollback reference through the alpha. A lean local Supabase configuration now exists for source-independent development, but the PostgreSQL application schema, migration, hosted service, and cutover are not implemented. The wiki must not describe the approved direction as current runtime state.

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

Supabase Auth is the first identity system, not a proven Claude integration. Supabase documents OAuth 2.1, PKCE, MCP-compatible dynamic registration, JWKS, and audience customization. Its OAuth server is in public beta.

The first Phase 1 task is a narrow Supabase-to-Claude compatibility proof. Remote work stops and the identity-provider choice reopens if protected-resource metadata, dynamic client registration, PKCE, exact redirect handling, audience binding, consent, asymmetric token validation, expiry, or active-membership enforcement fails.

Passwordless member access also requires custom transactional email. Supabase's default project mail service is not the group delivery path.

## Implementation Requirements

- Normal service requests must use a database role that cannot bypass row-level security and must pass verified member identity into each transaction.
- A separate elevated credential may support narrow owner operations only.
- Policy tests must cover normal and elevated roles. User-editable metadata must not control authorization.
- Every accepted corpus and retrieval snapshot remains citation-resolvable after later activations and restores.
- Database size, embedding size, transfer, connector cold starts, and backup results must be measured before the provider plan changes.

Supabase changes frequently. Recheck its changelog and current Auth, RLS, backup, and pricing documentation when implementation starts.

The first local stack check passed PostgreSQL and Auth health checks, then stopped because Docker Desktop published its ports on all host interfaces despite the documented loopback network option. Keep that stack synthetic and stopped until every published port proves a `127.0.0.1` binding. See [Local Supabase](../../docs/development/supabase-local.md).

## Related Pages

- [Decision Log](../decisions.md)
- [Content Roadmap](content-roadmap.md)
- [Retrieval and Concept Links](retrieval-and-concept-links.md)

## Open Questions

- How will immutable corpus versions map to PostgreSQL schemas, partitions, or version-keyed rows without permitting partial mixed-version reads?
- Which non-bypass role and transaction-claim method will the Passage service use?
- Can the Supabase OAuth server satisfy the complete Claude remote MCP contract?
- How will the local Supabase stack enforce loopback-only Docker port bindings on the current workstation?
- Which hobby application host, transactional email provider, backup destination, and retention policy will be selected?
- What exact parity event permits PostgreSQL cutover and later retirement of the SQLite rollback path?
