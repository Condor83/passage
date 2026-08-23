# Passage Repository Map

Verify every path in the current tree before relying on this map.

## Authority and current state

- `wiki/decisions.md`: authoritative confirmed decisions and supersessions.
- `wiki/overview.md`: current implemented state and approved direction.
- `docs/specs/2026-08-23-passage-product-specification.md`: approved gated evolution beyond the local baseline.
- `docs/plans/2026-08-16-001-feat-scripture-chat-plan.md`: historical authority for the implemented local SQLite baseline.
- `pyproject.toml` and `uv.lock`: Python version, dependencies, lint rules, and test configuration.
- `src/passage/config.py`: private-root boundary, restrictive file modes, and current loopback configuration.
- `src/passage/cli.py`: current local corpus lifecycle, service, and evaluation commands.

The active Python distribution, package, CLI, configuration prefix, service titles, and MCP identity use Passage. Historical plan filenames remain unchanged.

## Current architecture

- `src/passage/domain/`: request, response, identity, canonical-reference, provenance, and error contracts.
- `src/passage/ingest/`: bounded EPUB, text-layer PDF, Datalab repair, normalization, validation, and text-free structure manifests.
- `src/passage/db/`: immutable SQLite corpus construction, validation, control state, activation, and read-only access.
- `src/passage/evidence/`: snapshot pinning, lexical retrieval, ranking, official-reference traversal, and the shared evidence service.
- `src/passage/http/`: FastAPI routes, stable errors, loopback controls, and application lifecycle.
- `src/passage/mcp/`: stdio MCP server and local tool adapters.
- `src/passage/eval/`: versioned evaluation cases, metrics, identity-bound reports, and performance data.

The approved PostgreSQL, Supabase Auth, remote MCP, note, and derived-graph systems are not implemented unless current files prove otherwise.

## Test routing

- Domain identifiers and request bounds: `tests/unit/test_identifiers.py`
- Ingestion, normalization, and validation: `tests/unit/ingest/`
- Ranking and evaluation: `tests/unit/evidence/` and `tests/unit/eval/`
- Persistence, FTS, activation, CLI, and retrieval: `tests/integration/`
- HTTP contracts and local security: `tests/api/test_http_api.py`
- MCP schemas, errors, lifecycle, and tools: `tests/mcp/test_mcp_tools.py`
- HTTP/MCP equivalence: `tests/contract/test_interface_parity.py`
- Model-free two-transport research flow: `tests/acceptance/test_agent_research_flow.py`

Run focused tests first. The complete source-independent gate is:

```bash
uv sync --all-extras --dev
uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv run pytest
```

Plain `uv run pytest` does not collect coverage. Use an explicit coverage invocation when coverage is required.

## Current corpus lifecycle

The current CLI supports separate inspect, build, verify, activate, metadata, serve, and evaluate actions. Treat them as separate authority levels.

- Inspect reads and fingerprints an explicit source.
- Build requires source approval and creates an accepted but inactive immutable artifact plus private review files.
- Verify revalidates a published artifact.
- Activate changes the active corpus and retrieval pointer.
- Serve exposes only the active corpus on loopback.
- Evaluate reads an accepted corpus and writes a private report without changing defaults.

The Datalab repair path can create an inactive, unaccepted `review_required` candidate. Its exact PDF, Marker JSON, structure, recipe, and correction-profile identities remain private. The writer must reject output inside the repository.

Use repository fixtures for source-independent workflows. Real sources, approval records, correction profiles, databases, repairs, reviews, overlays, evaluation outputs, and private paths belong outside Git.
