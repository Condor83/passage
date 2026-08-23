# Passage Autonomous Build Readiness

Date: 2026-08-23

Status: Repository preparation complete. This document defines the inputs for a later goal prompt. It is not the goal prompt.

## Recommendation

Use one Codex Goal-mode session in the dedicated `codex/passage-product-build` worktree. Make Phase 0 the first goal. Use synthetic fixtures only. Stop before Phase 1 needs a live Supabase-to-Claude OAuth proof.

Do not ask one run to cross every product phase. The approved specification contains owner, source, cost, identity, and deployment gates that an unsupervised session cannot approve for itself. A Phase 0 goal is large enough to prove the working method and small enough to finish with objective evidence.

## Prepared start state

- Primary checkout: `/Users/mark/scripture-chat` on `main`.
- Execution checkout: `/Users/mark/.codex/worktrees/passage-product-build` on `codex/passage-product-build`.
- Product authority: `docs/specs/2026-08-23-passage-product-specification.md`.
- Decision authority: `wiki/decisions.md`.
- Execution grounding: `.agents/skills/passage-grounding/SKILL.md`.
- Agent limit: three subagents in addition to the primary agent.
- Mechanical agent: GPT-5.3 Codex Spark, workspace write, narrow tasks only.
- Reviewer: GPT-5.6 Sol at high reasoning, read only.
- Baseline: Ruff format and lint passed, mypy passed, and 171 tests passed on 2026-08-23.
- Supabase CLI and lean local configuration are present. The local stack stays stopped because Docker exposed configured ports on all host interfaces.

## Decisions needed before the goal starts

1. Confirm that the first autonomous build goal is Phase 0 only.
2. Confirm that the execution agent may edit and commit on `codex/passage-product-build`.
3. Keep private repair candidates out of the run unless the maintainer separately approves an exact artifact for disposable local test use.
4. Confirm that the agent must stop at every external-service, source-acceptance, cost, deployment, push, and publication gate.

The recommended answers are Phase 0 only, commits allowed on the execution branch, synthetic fixtures only, and all listed gates closed.

## Goal prompt outline

The later goal prompt should contain these sections in this order:

1. **Outcome** — State the Phase 0 product result in observable terms.
2. **Authority order** — Name `AGENTS.md`, the decision log, the approved specification, the Phase 0 roadmap, current code, and tests.
3. **Starting evidence** — Name the branch, worktree, baseline, current SQLite interfaces, and unimplemented future systems.
4. **In scope** — List the exact Phase 0 outputs and affected contracts.
5. **Out of scope** — List Phase 1 and later work plus every closed authority gate.
6. **Orchestration contract** — Define agent roles, file ownership, task packets, review points, and integration ownership.
7. **Implementation sequence** — Require small vertical slices with focused checks before the complete gate.
8. **Verification** — Name the exact tests, contract checks, review criteria, and wiki updates that prove completion.
9. **Stop conditions** — State when the agent must preserve state and return a blocker.
10. **Final report** — Require commits, files changed, checks, findings, open gates, and no unsupported completion claims.

The outcome must describe what done means. It must not say only “implement the specification.”

## Recommended Phase 0 work packages

1. Re-ground the exact execution checkout and confirm a clean baseline.
2. Define O1 official-reference grammar and synthetic validity rules.
3. Implement the grammar through domain, ingestion, and synthetic contract tests.
4. Build the limited atomic-versus-combined product-loop probe over lanes present in synthetic fixtures.
5. Lock the small Phase 0 question set and rubric without claiming H1 success.
6. Complete the `scripture-chat` to Passage technical identifier rename without compatibility aliases.
7. Run focused checks after each slice and the complete source-independent gate at integration points.
8. Run an independent read-only review, resolve all material findings, and rerun affected checks.
9. Update the living wiki with exact implemented status and remaining Phase 1 gates.
10. Commit coherent slices and finish with a clean worktree.

The primary agent may adjust package boundaries after it inspects code dependencies. It may not expand the product phase or authority.

## Subagent orchestration

The primary agent owns the plan, architecture, file-ownership map, integration, tests, wiki alignment, and commits.

Use the built-in explorer or a read-only subagent for repository maps and impact analysis. Use the `mechanical` Spark role only when all of these are true:

- the task has one exact outcome;
- owned files are explicit and do not overlap another writer;
- no product, architecture, schema, authorization, security, corpus, or source-use judgment is needed; and
- one or more objective checks can prove the task.

A mechanical task packet must include the objective, owned files, forbidden files, constraints, exact check, and return format. The agent does not commit.

Use the `reviewer` role after each material integration point and before completion. It stays read only. It reports actionable findings with exact file and line references. The primary agent resolves findings and owns the final proof.

Do not let two agents edit the same files at the same time. Prefer one mechanical writer plus one read-only investigator or reviewer. Use a second writer only for clearly disjoint files.

## Proof cadence

For each work package:

1. Inspect current code and closest tests.
2. Run or add the smallest failing or characterization check.
3. Make the smallest complete change.
4. Run the focused check.
5. Review the diff for scope and privacy.
6. Integrate and run the affected contract or parity checks.

At phase completion, run:

```bash
uv sync --all-extras --dev
uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv run pytest
git diff --check
```

Completion also requires a clean `git status`, coherent commits, an independent review with no unresolved material finding, and a wiki health check.

## Hard stop conditions

Stop, preserve the current branch, and report the exact blocker when any of these conditions occurs:

- The worktree contains unexpected user changes or overlapping agent edits.
- Two controlling documents conflict in a way that changes implementation.
- Work needs private source bytes, private derived artifacts, source paths, or an unapproved repair candidate.
- Work needs corpus acceptance, activation, or a claim of editorial fidelity.
- Work needs a live Supabase link, Claude OAuth connection, transactional email, paid external model or enrichment run, remote host, public HTTPS, push, deployment, or publication.
- Local Supabase or another service binds a configured private port beyond loopback.
- Work changes product scope, source-use policy, authorization roles, or a recorded decision.
- A migration or command could destroy or irreversibly rewrite owner data.
- A required test cannot pass without weakening a contract, privacy rule, citation rule, or safety boundary.
- The remaining work no longer fits Phase 0 or cannot be verified in the current checkout.

A hard stop is not failure. The final report must name completed work, preserved state, the exact unmet authority or decision, and the smallest next action for the maintainer.

## Completion contract

The session is complete only when every agreed Phase 0 output exists in committed code or documentation, the complete source-independent gate passes, current wiki pages match the implementation, and the worktree is clean.

The session must not claim that Passage has an accepted corpus, a proven H1 result, a working remote OAuth path, a deployed service, or a member release.

## Why Goal mode

Codex Goal mode treats the goal text as both the first prompt and the completion criteria. The official guidance recommends an outcome, constraints, and verification. It also preserves the existing sandbox and approval policy. A dedicated worktree prevents the long run from changing the primary checkout.

Use `codex exec` later for bounded scripted or CI work. It is not needed for this first repository build session.

## Official Codex references

- [Long-running work](https://learn.chatgpt.com/docs/long-running-work)
- [Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)
- [Git worktrees](https://learn.chatgpt.com/docs/environments/git-worktrees)
- [Non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode)
- [Configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)
