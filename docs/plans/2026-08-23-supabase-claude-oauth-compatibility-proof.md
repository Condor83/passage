# Supabase-to-Claude OAuth Compatibility Proof

Date: 2026-08-23

Status: Live result failed on 2026-08-24. P6 resource and audience binding failed. Teardown is complete.

## Decision and Scope

This proof is the only Phase 1 entry gate. Passage must not start PostgreSQL schema, migration, corpus, or Auth-foundation work before this proof passes. A material failure reopens the identity-provider decision.

The proof uses synthetic identity data and one synthetic read-only MCP tool. It uses no scripture text, private source, repair candidate, corpus artifact, note, PostgreSQL application table, migration, seed, or remote database link. The local Supabase stack stays stopped until its loopback port-binding stop condition is fixed.

## Current Evidence

### Live Result - 2026-08-24 UTC

The gate failed. Claude successfully discovered and registered with Supabase, reached explicit consent, called the synthetic `whoami` tool with an ES256 token, and refreshed a five-minute access token without reconnecting. After one harness correction, a valid inactive member received HTTP 403 before MCP tool dispatch and could not approve a new authorization.

P6 failed in a direct negative probe. A dynamic public client requested `https://wrong-resource.invalid/mcp` during authorization and token exchange. Supabase returned HTTP 200 and issued a token. The custom access-token hook changed that token audience to the Passage MCP resource even though the requested resource was different. The Passage resource server then accepted the token and returned the `whoami` tool list.

This is the exact fail condition in the locked matrix: a wrong-resource request produced a Passage-usable token. The identity-provider decision is reopened. PostgreSQL schema, migration, and Auth-foundation work remain blocked. Sanitized raw evidence is outside Git.

P12 is complete. The Claude connector was disconnected and removed. The public tunnel and local harness were stopped, and the temporary harness directory was removed. The disposable Supabase project was deleted, which removed its grants, sessions, and synthetic user. The local harness URL no longer accepts connections, the former public tunnel returns HTTP 530, and the former Supabase Auth discovery endpoint returns HTTP 410.

The remaining negative matrix rows were not expanded after the decisive P6 failure. They are not inferred as passes.

Current primary documentation shows a plausible path, but it does not prove compatibility:

- Supabase Auth documents OAuth 2.1 authorization code flow, PKCE, dynamic client registration, refresh tokens, asymmetric JWKS validation, custom access-token hooks, consent APIs, and MCP discovery.
- Claude custom connectors use public HTTPS remote MCP servers and delegated per-user OAuth. Current Anthropic guidance supports dynamic client registration, exact OAuth callbacks, and token expiry and refresh.
- The current MCP authorization specification requires protected-resource metadata, authorization-server discovery, `resource` in authorization and token requests, exact token audience validation, PKCE, and bearer authentication on every HTTP request.
- Supabase's published OAuth flow does not document RFC 8707 `resource` handling. Its normal access-token audience is `authenticated`; documentation directs applications to a custom access-token hook when a resource-specific audience is required. Live behavior is therefore unresolved.
- Supabase still labels its OAuth server beta. An older changelog entry projected general availability in Q4 2025. Treat the current product documentation, not the elapsed projection, as the status authority.
- The Supabase changelog records a relevant completed breaking change: the OAuth token endpoint now returns HTTP 200 instead of 201. The harness must accept valid 2xx responses and must not require 201.

## Disposable Topology

Use one short-lived Supabase project and one short-lived public HTTPS harness:

```text
Claude custom connector
  -> https://<proof-host>/mcp
  -> protected-resource metadata on <proof-host>
  -> Supabase OAuth discovery, registration, authorization, token, and JWKS endpoints
  -> https://<proof-host>/oauth/consent
  -> one synthetic `whoami` MCP tool
```

The canonical protected resource is the exact MCP URL: `https://<proof-host>/mcp`. Keep this value byte-identical in protected-resource metadata, authorization and token requests, the access-token `aud` claim, and resource-server validation.

The harness exposes only:

- `GET` or `POST /mcp`: Streamable HTTP MCP with one read-only `whoami` tool;
- `GET /.well-known/oauth-protected-resource/mcp`: RFC 9728 protected-resource metadata;
- `GET /oauth/consent`: the explicit Supabase authorization and consent UI; and
- `GET /healthz`: a content-free health result.

An unauthenticated MCP request returns HTTP 401 with a Bearer `WWW-Authenticate` challenge that names the protected-resource metadata URL. Every authenticated MCP request independently validates the token and current synthetic membership state.

## Hosted Supabase Configuration

The authorized proof will:

1. Create a disposable hosted Supabase project with no application schema.
2. Enable OAuth 2.1 server and dynamic client registration.
3. Configure one asymmetric signing key. Do not expose or copy a symmetric JWT secret into the harness.
4. Set the site URL and authorization path to the public consent route.
5. Use the shortest safe access-token lifetime supported by the hosted project so expiry and refresh can be observed in a bounded run.
6. Create one synthetic confirmed user. This does not prove passwordless email delivery and does not select a transactional email provider.
7. Configure a custom access-token hook only if needed to bind `aud` to the canonical MCP resource. The hook must not grant membership or use user-editable metadata.
8. Leave database tables, migrations, seeds, Data API grants, corpus data, and RLS application policies absent.

The synthetic membership registry is service-side test configuration keyed by the token `sub`. It contains only `active` or `disabled`. Change it through the host's protected configuration and restart the disposable harness. Do not create a membership table for this proof.

## Locked Test Matrix

All rows are required. An unobserved required behavior is a failure, not a pass.

| ID | Behavior | Positive proof | Required negative proof | Pass condition |
| --- | --- | --- | --- | --- |
| P1 | Protected-resource discovery | Give Claude only the MCP URL. Claude follows the 401 challenge or well-known URI to the exact metadata document. | Wrong or missing metadata URL cannot start authorization. | Claude discovers the Supabase issuer without manual endpoint entry. |
| P2 | Authorization-server discovery | Supabase metadata returns the exact issuer, authorization endpoint, token endpoint, JWKS URI, PKCE capability, and registration endpoint. | A metadata issuer or endpoint mismatch is rejected by the harness audit. | Observed metadata satisfies the current MCP discovery sequence. |
| P3 | Dynamic client registration | Claude registers itself and reaches consent without a manually supplied client ID or secret. Record the registered client name, public-client method, grant types, and exact redirect URI without recording credentials. | An altered redirect URI is rejected. | DCR succeeds with `authorization_code`, `refresh_token`, and `token_endpoint_auth_method=none`. |
| P4 | PKCE and state | The Claude flow uses PKCE S256 and returns the original state. | Missing challenge, unsupported method, wrong verifier, reused code, and changed state fail. | The live flow and protocol negatives pass. Plain PKCE does not count. |
| P5 | Redirect binding | The exact redirect registered by Claude succeeds. | Changed scheme, host, port, path, or query does not receive a code. | Only a registered exact HTTPS callback succeeds. |
| P6 | Resource and audience binding | The authorization and token transactions carry the canonical `resource`; the issued access token has exact `aud`, exact `iss`, expected `client_id`, and expected `sub`. | A different `resource`, wrong `aud`, wrong `iss`, or token issued for another client never produces an accepted Passage request. | Supabase behavior and Passage validation satisfy RFC 8707 for this resource. Ignoring a wrong `resource` and still issuing a Passage-usable token fails the gate. |
| P7 | Consent | The page shows Claude client identity, exact redirect, requested scopes, and target resource. Explicit approval continues. | Explicit denial returns no usable token and no tool access. Inactive membership cannot approve. | Approval and denial are both observed. Consent is not implicit. |
| P8 | Token validation | A Supabase token signed by a current asymmetric JWKS key reaches `whoami`. The harness validates signature, allowed algorithm, key ID, issuer, audience, expiry, subject, client ID, and membership. | Forged, expired, wrong-key, wrong-algorithm, wrong-issuer, wrong-audience, and missing-subject tokens return 401. | No unverified claim controls access. Tokens never appear in logs or reports. |
| P9 | Expiry and refresh | Call `whoami` before expiry, wait for the configured expiry, and call it again through Claude without reconnecting. Record distinct access-token fingerprints with the same subject and client. | The expired prior access token returns 401 when replayed directly. | Claude refreshes successfully and the rotated session remains usable. |
| P10 | Active-member enforcement | An active synthetic member can call `whoami`. Disable the member in service configuration while the access token is still valid and repeat the call. | The disabled member receives 403 on every tool request and cannot approve a new authorization. | Service authorization checks current membership on every call. Re-enabling requires an explicit configuration change. |
| P11 | Minimal MCP surface | Claude lists and calls only `whoami`; the result contains synthetic identity state and no content. | Unknown or write tool calls fail. | No Passage evidence, note, admin, corpus, or database tool is exposed. |
| P12 | Teardown | Remove the Claude connector, revoke grants and sessions, delete the hosted harness, and delete the disposable Supabase project. | The former URLs no longer serve the proof. | Teardown is verified and recorded. |

## Evidence Record

Keep raw proof artifacts outside Git. They may contain transient project URLs, authorization identifiers, client records, or provider logs. The checked-in result may contain only:

- UTC start and end times;
- exact Passage commit and dependency versions;
- digests of protected-resource and authorization-server metadata;
- a hash of the disposable project reference and registered client ID;
- sanitized redirect URI, scope, issuer, audience, status, and error-code observations;
- access-token fingerprints, never access or refresh tokens;
- each matrix result with evidence location and reason;
- teardown confirmation; and
- the final `pass`, `fail`, or `incomplete` result.

Logs must omit tokens, credentials, authorization codes, cookies, email addresses, consent query strings, source content, study queries, and private paths. A missing capture for P1 through P12 produces `incomplete` or `fail`; it never becomes inferred success.

## Decision Rule

The proof passes only when every P1 through P12 row passes against the real Claude custom-connector flow and the disposable Supabase project.

Stop and reopen the identity-provider decision when any of these remains after one bounded diagnosis and correction cycle:

- Claude cannot discover the authorization server from the protected resource;
- DCR cannot register Claude with its exact redirect;
- PKCE S256, consent, expiry, or refresh is incompatible;
- Supabase ignores or mishandles `resource` in a way that permits a Passage-usable wrong-audience token;
- Passage cannot validate asymmetric tokens with exact issuer and audience;
- a valid token bypasses current active-member state; or
- the required evidence cannot be observed without logging secrets.

A passing proof permits PostgreSQL and Auth foundation work to begin. It does not prove passwordless email delivery, application RLS, PostgreSQL contract parity, remote alpha readiness, private-source use, corpus acceptance, deployment fitness, or public release.

## Authority Required to Execute

Before execution, the maintainer must explicitly authorize all of these actions:

1. Create and later delete one disposable hosted Supabase project.
2. Enable hosted OAuth, DCR, asymmetric signing, a custom access-token hook if required, and one synthetic user.
3. Deploy and publicly expose the synthetic HTTPS harness for the bounded proof window.
4. Add the custom connector to the maintainer's Claude account and complete the interactive authorization and consent steps.
5. Store sanitized raw evidence outside Git and perform the teardown in P12.

Authority for this proof does not include PostgreSQL schema work, local Supabase startup, private-source processing, corpus acceptance or activation, scripture content deployment, paid model calls, group-member invitations, or durable production infrastructure.

## Primary References

- [Supabase OAuth 2.1 Server](https://supabase.com/docs/guides/auth/oauth-server)
- [Supabase OAuth Getting Started](https://supabase.com/docs/guides/auth/oauth-server/getting-started)
- [Supabase OAuth Flows](https://supabase.com/docs/guides/auth/oauth-server/oauth-flows)
- [Supabase MCP Authentication](https://supabase.com/docs/guides/auth/oauth-server/mcp-authentication)
- [Supabase Token Security](https://supabase.com/docs/guides/auth/oauth-server/token-security)
- [Supabase changelog](https://supabase.com/changelog.md)
- [Claude custom connectors](https://support.claude.com/en/articles/11175166-get-started-with-custom-connectors-using-remote-mcp)
- [MCP Authorization specification](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization)
