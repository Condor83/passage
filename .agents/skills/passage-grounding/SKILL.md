---
name: passage-grounding
description: Ground consequential Passage planning, implementation, diagnosis, and review in the exact checkout, living wiki, approved product specification, privacy boundary, current runtime, and executable tests. Do not use for general scripture study or doctrinal questions.
---

# Passage Grounding

Ground claims in the exact checkout before planning, editing, reviewing, or reporting status. Use current files as implementation evidence. Treat plans and the wiki as authority for intent and decisions.

## Start from the exact checkout

1. Resolve the repository root with `git rev-parse --show-toplevel` and confirm it is the intended Passage checkout.
2. Read every applicable `AGENTS.md` from the repository root to the target path.
3. Record `git status --short --branch`, `git log -5 --oneline --decorate`, and `git remote -v`. Distinguish committed code, user changes, generated files, and untracked private artifacts.
4. Read `wiki/index.md`, `wiki/overview.md`, `wiki/decisions.md`, and the relevant linked pages.
5. Read `docs/specs/2026-08-23-passage-product-specification.md` for approved work beyond the local baseline. Read `docs/plans/2026-08-16-001-feat-scripture-chat-plan.md` when the task concerns the implemented SQLite, loopback HTTP, or stdio MCP baseline. Report conflicts instead of silently choosing one.
6. Inspect the current code and tests for the requested area. Do not infer implementation from an approved plan.
7. Before consequential work, state the checkout, branch and HEAD, dirty state, controlling documents, scope, authority limits, and verification plan.

Read [references/repository-map.md](references/repository-map.md) when the task needs architecture, runtime commands, test routing, corpus operations, or interface details.

## Preserve the product boundary

- Passage returns exact, inspectable evidence. It does not generate authoritative doctrinal conclusions.
- The current runtime uses immutable SQLite corpus artifacts, loopback HTTP, and stdio MCP. Supabase PostgreSQL, authenticated remote MCP, member notes, and the complete-canon release are approved future work, not current behavior.
- Canonical content comes only from a maintainer-approved exact source digest and acquisition record. A repair candidate is not an accepted corpus.
- Keep raw source bytes, Datalab output, correction profiles, detailed review artifacts, source paths, acquisition records, study queries, and credentials outside Git. Exact maintainer-approved derived candidate snapshots may live under `candidates/` only with digest manifests and explicit inactive, unaccepted, `review_required` status.
- Use synthetic fixtures for routine development. Do not process a private source or use an unaccepted candidate, even for a local test, without explicit maintainer authority.
- Do not accept, activate, deploy, expose remotely, or submit publicly without the separate authority defined for that action.
- Preserve stable canonical identities, immutable source versions, citation resolvability, and the distinction between canonical content, official apparatus, member notes, and model-derived analysis.
- Preserve HTTP, MCP, and shared domain-service parity. Change contract and parity tests together when a public operation or error changes.
- Keep source-specific correction rules in digest-bound private profiles. Generic parser code and synthetic correction fixtures may live in Git.
- Favor the smallest useful vertical slice for the small trusted group. Do not add speculative scale, enterprise administration, or generic SaaS controls.

## Work from the relevant proof

- Inspect the implementation module, its closest tests, and every affected contract, transport, persistence, or acceptance test.
- Run the smallest relevant test first. Run the complete source-independent gate when the change affects shared contracts, persistence, privacy, activation, authentication, or transport parity.
- Cite exact files and current test results. Do not present plan checkboxes, old commits, or prior runs as current proof.
- Keep independent concerns in separate commits. Do not stage user-owned or unrelated changes.
- A real-source result proves only the exact private inputs and recipe used. It does not establish editorial acceptance, legal clearance, or remote-delivery approval.

## Report the result

State what was verified in this checkout, what remains unverified, and which authority gates remain closed. Never equate synthetic success or a repaired private candidate with corpus approval.
