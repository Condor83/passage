# Local Supabase

Passage has a loopback-safe local Supabase harness and one imperative Phase 1 migration for the non-exposed PostgreSQL application schema, roles, RLS policies, lifecycle constraints, and retrieval foundation. It has no seed data, PostgreSQL repository, remote project link, or deployed service.

The configuration enables PostgreSQL, Auth, the API gateway, PostgREST, and local email capture. It disables Realtime, Storage, vector buckets, Edge Functions, Analytics, Studio, and seeding because Phase 1 does not need them.

## Verified environment

- Supabase CLI `2.115.0`, invoked reproducibly as `npx --yes supabase@2.115.0`
- Node.js `26.7.0`; the CLI requires Node.js 20 or later
- Native Docker Engine `29.7.2` through the default `/var/run/docker.sock` context
- Local PostgreSQL `17.6.1`
- Local Auth `v2.195.0`

The native Linux stack passed database and Auth health checks and the automated loopback boundary test on 2026-08-24.

## Loopback-safe runtime

Docker Desktop previously published the API, database, and mail ports on all host interfaces even when a custom bridge requested loopback defaults. Passage now uses native Docker Engine and a dedicated bridge whose default published-port address is `127.0.0.1`:

```bash
docker network create \
  --driver bridge \
  --opt com.docker.network.bridge.host_binding_ipv4=127.0.0.1 \
  passage-local
npx --yes supabase@2.115.0 start --network-id passage-local
```

`tests/postgres/conftest.py` creates the bridge when absent, checks the Node.js, CLI, and Docker prerequisites before startup, suppresses secret-bearing startup output, and refuses to yield the stack unless ports `54321`, `54322`, and `54324` are all published on `127.0.0.1`. Any `0.0.0.0`, `[::]`, missing-service, startup, or prerequisite result fails closed. The session fixture removes any stale synthetic Passage stack before startup and stops it with `--no-backup` after the session, including after test failure, so every run applies migrations to an empty local database.

The safe manual stop command is:

```bash
npx --yes supabase@2.115.0 stop --project-id passage --no-backup
```

Do not print `supabase start` or `supabase status` JSON output into routine logs. Those commands can include local development keys.

## Current database foundation

`supabase/migrations/20260824221345_phase1_foundation.sql` is the generated imperative U3 migration. It creates the private `passage` schema, versioned synthetic evidence tables, complete retrieval-snapshot binding, lifecycle and immutability guards, stored PostgreSQL full-text search with a GIN index, non-bypass request and maintenance logins, forced RLS, and explicit grants. `src/passage/db/postgres/connection.py` provides separate bounded synchronous pools and transaction-local request identity context.

U4 owns synthetic import, whole-version validation, and activation behavior on this foundation. Do not link, pull, push, reset, or migrate a remote project; process private sources; or activate a real corpus during local development.
