---
title: Study Group Access
type: concept
created: 2026-08-23
updated: 2026-08-24
sources:
  - user-confirmed-conversation
  - docs/specs/2026-08-23-passage-product-specification.md
  - docs/plans/2026-08-23-supabase-claude-oauth-compatibility-proof.md
  - docs/plans/2026-08-24-0634-feat-postgres-auth-foundation-plan.md
  - https://modelcontextprotocol.io/specification/2025-11-25/basic
  - https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization
tags: [access, mcp, plugin, api, authentication, study-group]
---

# Study Group Access

## Confirmed Direction

Claude remote MCP is the first hosted client for Passage. A private ChatGPT developer-mode beta follows against the same domain contract. Public plugin submission requires a separate public-delivery gate and does not open registration or corpus access.

Passage serves a small, trusted group. Members authenticate with passwordless email. Only verified addresses on an owner-managed allowlist can receive access. The first release has only `owner` and `member` roles.

## Architecture Boundary

The corpus, retrieval, citation, and permission rules belong in a shared Passage domain service. MCP, a host plugin, an HTTP API, and a future study application are adapters over that service.

This boundary prevents client-specific payloads from becoming the database schema. It also gives every client the same evidence and access-control rules.

## Phase 2 MCP Surface

The first remote surface is evidence-only, atomic, and read-only:

- `lookup_passage` returns an exact canonical passage and its identity;
- `get_context` returns a bounded passage window;
- `search_passages` runs lexical retrieval and any evaluated semantic lane;
- `traverse_connections` traverses official and explicitly enabled experimental or published typed edges; and
- `get_provenance` returns edition and citation metadata without exposing private source paths.

Every result must include stable source identities and citation-ready locations. Results must distinguish canonical source text, official apparatus, and derived analysis.

Note tools are not discoverable or callable in Phase 2.

## Phase 3 Note Surface

Phase 3 adds citation-linked Markdown notes after permission, visibility, member-removal, backup, and recovery gates pass.

- Every create request states `shared` or `private` explicitly. If the host cannot prove affirmative shared-note choice, it creates a private draft and requires a separate share action.
- Shared notes are readable by all active members. Private notes are readable only by the author.
- Only the author can update, delete, or change visibility through note tools.
- Disabling a member revokes access but preserves notes. Shared notes show disabled authorship. Private notes remain inaccessible until re-enable.
- Permanent removal is a separate owner action that offers export when practical, deletes the member's live notes, and retains only an audit tombstone. Backup copies expire under the published retention policy.
- Note search remains separate from canonical evidence retrieval and labels all note text as untrusted member content.

## Remote Access and Security

A group-facing remote MCP server requires authenticated HTTPS access. Supabase Auth failed P6 of the live [Supabase-to-Claude OAuth Compatibility Proof](../../docs/plans/2026-08-23-supabase-claude-oauth-compatibility-proof.md): a wrong-resource request produced a Passage-usable token. The maintainer accepts that behavior for the invite-only hobby service without claiming strict RFC 8707 compliance. Remote alpha remains separately gated by the bounded positive-flow regression, transactional email, application authorization, and deployment authority.

Use least privilege. Phase 2 enables evidence read only. Phase 3 adds note read and note write. Enforce authorization in the Passage service and PostgreSQL row-level policies. Do not pass client tokens through to upstream services or expose PostgreSQL directly to MCP clients.

## Delivery Sequence

1. Retain Supabase Auth, document the accepted wrong-resource limitation, and preserve the positive behaviors observed in the Claude proof.
2. Preserve HTTP, MCP, and domain-service result parity while PostgreSQL and application authorization are introduced.
3. Connect Claude to the Phase 2 evidence-only surface and pass the broad-question evidence journey.
4. Add the owner/member allowlist and the gated Phase 3 note surface for the complete-canon member release.
5. Test the same contract in a private ChatGPT developer-mode beta.
6. Consider public submission only after a separate public audience, support, policy, and content-rights decision.

## Related Pages

- [Project Overview](../overview.md)
- [Decision Log](../decisions.md)
- [PostgreSQL Platform](postgresql-platform.md)
- [Retrieval and Concept Links](retrieval-and-concept-links.md)
- [Content Roadmap](content-roadmap.md)

## Open Questions

- Which passwordless email method, transactional email provider, and sender domain will Passage use?
- What bounded result and identity-rate limits preserve normal broad study without enabling bulk extraction?
- What exact backup retention and export workflow applies before permanent member removal?
- What public audience and content-distribution basis, if any, would justify later public ChatGPT submission?
