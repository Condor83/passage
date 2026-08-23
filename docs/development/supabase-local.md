# Local Supabase

Passage has a local Supabase configuration but no PostgreSQL application schema, migration, seed data, remote project link, or deployed service.

The configuration enables PostgreSQL, Auth, the API gateway, PostgREST, and local email capture. It disables Realtime, Storage, vector buckets, Edge Functions, Analytics, Studio, and seeding because the first proof does not need them.

## Verified environment

- Supabase CLI `2.115.0`
- Docker Engine `29.4.0`
- Local PostgreSQL `17.6`
- Local Auth `v2.195.0`

The stack passed database and Auth health checks on 2026-08-23. It was stopped after the check.

## Loopback stop condition

On the current Docker Desktop setup, `supabase start --network-id passage-local` published the API, database, and mail ports on all host interfaces even though the Docker network set `com.docker.network.bridge.host_binding_ipv4=127.0.0.1`. This does not meet Passage's loopback boundary.

Keep the local stack stopped until a current inspection proves that every published port binds to `127.0.0.1`. Do not use private source data or credentials in this stack before that proof. `docker ps` must not show `0.0.0.0` or `[::]` for any Passage Supabase port.

The current safe stop command is:

```bash
supabase stop --project-id passage
```

Do not print `supabase start` or `supabase status` JSON output into routine logs. Those commands can include local development keys.

## Next database step

The execution session must select and record the schema workflow before adding SQL. Use the project Supabase and PostgreSQL skills, current official documentation, synthetic data, and explicit local flags. Do not link, pull, push, reset, or migrate a remote project during local preparation.
