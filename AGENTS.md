# Passage - Living Wiki Instructions

Created: 2026-08-23

This workspace uses a living wiki. The wiki is the source of truth for current project state, decisions, technical investigations, and reusable context.

## Project Snapshot

**Project:** Passage

**Description:** A structured evidence platform for the LDS scripture canon and, later, teachings from Church leaders. The current checkout uses immutable SQLite artifacts, loopback HTTP, and stdio MCP. The approved product direction adds Supabase PostgreSQL, authenticated remote MCP, the complete canon, and later General Conference content through explicit gates.

**Source documents:** Repository plans and code live under `docs/` and `src/`. Maintainer-approved, inactive scripture candidate snapshots may live under `candidates/`. Raw source bytes, Datalab output, correction profiles, detailed review artifacts, source paths, acquisition records, and credentials stay outside the repository under the configured private root.

## Operating Priorities

1. Use `.agents/skills/passage-grounding/SKILL.md` before consequential planning, implementation, diagnosis, or review.
2. Separate implemented behavior from approved future direction. `wiki/decisions.md` controls decisions. The approved product specification controls work beyond the local baseline.
3. Favor the smallest useful vertical slice for a hobby project and a small trusted group. Do not add enterprise administration, speculative scale systems, or generic SaaS controls unless a measured requirement needs them.
4. Use synthetic fixtures for routine work. Private-source processing, test-only candidate use, corpus acceptance, activation, remote deployment, and public submission each require explicit maintainer authority.

## Living Wiki Operating Rules

1. Read `wiki/index.md` before making claims about current project state or prior decisions. Read `wiki/overview.md`, `wiki/decisions.md`, and relevant linked pages as needed.
2. Treat `wiki/decisions.md` as the authoritative decision record. Record confirmed changes with their date, rationale, superseded state, and affected pages.
3. Append every meaningful wiki operation to `wiki/log.md`.
4. Do not silently resolve contradictions. Record competing evidence under `Open Questions` and let the user decide.
5. Keep source summaries short. Record provenance and conclusions without reproducing private or copyrighted source material.
6. Prefer updates and cross-links over duplicate pages.
7. Keep raw source bytes, Datalab output, correction profiles, detailed review artifacts, source paths, acquisition records, and credentials outside Git. Only an exact maintainer-approved derived candidate may enter `candidates/`, with a digest manifest and explicit inactive, unaccepted, `review_required` status.
8. Do not accept or activate a corpus unless the maintainer approves the exact source digest and acquisition record.

## Wiki Architecture

- `wiki/index.md`: master catalog and starting point
- `wiki/overview.md`: current project state
- `wiki/decisions.md`: authoritative decisions
- `wiki/log.md`: append-only operations log
- `wiki/sources/`: summaries of source documents
- `wiki/entities/`: components and other concrete project objects
- `wiki/concepts/`: technical and product concepts
- `wiki/analyses/`: investigations, comparisons, and durable findings

## Standard Workflow

1. Read `wiki/index.md` and `wiki/decisions.md`.
2. Read the relevant linked wiki pages and current repository evidence.
3. Make the requested change or analysis.
4. Update affected wiki pages and cross-links.
5. Append the operation to `wiki/log.md`.
6. Run a wiki health check when decisions, implementation, and living pages may have drifted.

Every wiki page uses YAML frontmatter with `title`, `type`, `created`, `updated`, `sources`, and `tags`.
