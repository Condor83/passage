do $$
begin
  if not exists (select 1 from pg_roles where rolname = 'passage_request') then
    create role passage_request
      login noinherit nosuperuser nocreatedb nocreaterole noreplication nobypassrls;
  end if;
  if not exists (select 1 from pg_roles where rolname = 'passage_maintenance') then
    create role passage_maintenance
      login noinherit nosuperuser nocreatedb nocreaterole noreplication nobypassrls;
  end if;
  if exists (
    select 1 from pg_roles
    where rolname in ('passage_request', 'passage_maintenance')
      and (
        rolsuper or rolinherit or rolcreaterole or rolcreatedb
        or rolreplication or rolbypassrls or not rolcanlogin
      )
  ) then
    raise exception 'Passage database roles have unsafe attributes'
      using errcode = '42501';
  end if;
end
$$;
alter role passage_request set search_path = pg_catalog;
alter role passage_maintenance set search_path = pg_catalog;
revoke passage_maintenance from passage_request;

create schema passage authorization postgres;
revoke all on schema passage from public, anon, authenticated, service_role, authenticator;
grant usage on schema passage to passage_request, passage_maintenance;

alter default privileges for role postgres in schema passage
  revoke all on tables from public, anon, authenticated, service_role;
alter default privileges for role postgres in schema passage
  revoke all on sequences from public, anon, authenticated, service_role;
alter default privileges for role postgres in schema passage
  revoke execute on functions from public, anon, authenticated, service_role;

create table passage.source_versions (
  source_version_id text primary key check (source_version_id <> ''),
  source_sha256 text not null unique check (source_sha256 ~ '^[0-9a-f]{64}$'),
  acquisition_record_digest text not null
    check (acquisition_record_digest ~ '^[0-9a-f]{64}$'),
  edition text not null check (edition <> ''),
  language text not null check (language ~ '^[a-z]{3}$'),
  created_at timestamptz not null default statement_timestamp()
);

create table passage.corpus_versions (
  attempt_id uuid primary key,
  corpus_version text not null check (corpus_version <> ''),
  build_key text not null check (build_key <> ''),
  source_version_id text not null
    references passage.source_versions (source_version_id) on delete restrict,
  state text not null check (state in ('staging', 'validated', 'accepted', 'rejected')),
  normalized_digest text not null check (normalized_digest ~ '^[0-9a-f]{64}$'),
  artifact_digest text not null check (artifact_digest ~ '^[0-9a-f]{64}$'),
  manifest jsonb not null check (jsonb_typeof(manifest) = 'object'),
  created_at timestamptz not null default statement_timestamp(),
  validated_at timestamptz,
  accepted_at timestamptz,
  rejected_at timestamptz,
  rejection_code text,
  unique (attempt_id, corpus_version),
  constraint corpus_versions_state_timestamps_check check (
    (
      state = 'staging'
      and validated_at is null
      and accepted_at is null
      and rejected_at is null
      and rejection_code is null
    )
    or (
      state = 'validated'
      and validated_at is not null
      and accepted_at is null
      and rejected_at is null
      and rejection_code is null
    )
    or (
      state = 'accepted'
      and validated_at is not null
      and accepted_at is not null
      and rejected_at is null
      and rejection_code is null
    )
    or (
      state = 'rejected'
      and accepted_at is null
      and rejected_at is not null
      and rejection_code is not null
      and rejection_code <> ''
    )
  )
);

create unique index corpus_versions_live_build_key_idx
  on passage.corpus_versions (build_key)
  where state in ('staging', 'validated', 'accepted');
create unique index corpus_versions_live_identity_idx
  on passage.corpus_versions (corpus_version)
  where state in ('staging', 'validated', 'accepted');
create index corpus_versions_source_version_id_idx
  on passage.corpus_versions (source_version_id);

create table passage.canonical_passages (
  canonical_passage_id text primary key check (canonical_passage_id <> ''),
  reference text not null unique check (reference <> ''),
  work text not null check (work <> ''),
  book text not null check (book <> ''),
  chapter integer not null check (chapter > 0),
  verse integer not null check (verse > 0),
  end_verse integer check (end_verse is null or end_verse >= verse),
  canonical_order bigint not null unique check (canonical_order >= 0),
  created_at timestamptz not null default statement_timestamp()
);

create index canonical_passages_book_chapter_verse_idx
  on passage.canonical_passages (work, book, chapter, verse);

create table passage.passage_versions (
  corpus_attempt_id uuid not null
    references passage.corpus_versions (attempt_id) on delete cascade,
  canonical_passage_id text not null
    references passage.canonical_passages (canonical_passage_id) on delete restrict,
  passage_text text not null check (passage_text <> ''),
  content_hash text not null check (content_hash ~ '^[0-9a-f]{64}$'),
  source_spans jsonb not null check (
    jsonb_typeof(source_spans) = 'array' and jsonb_array_length(source_spans) > 0
  ),
  search_vector tsvector generated always as (
    to_tsvector('english'::regconfig, passage_text)
  ) stored,
  primary key (corpus_attempt_id, canonical_passage_id)
);

create index passage_versions_canonical_passage_id_idx
  on passage.passage_versions (canonical_passage_id);
create index passage_versions_search_vector_idx
  on passage.passage_versions using gin (search_vector);

create table passage.apparatus_notes (
  corpus_attempt_id uuid not null,
  note_id text not null check (note_id <> ''),
  origin_passage_id text not null,
  anchor text not null check (anchor <> ''),
  label text,
  note_text text,
  note_kind text not null check (note_kind <> ''),
  source_spans jsonb not null check (
    jsonb_typeof(source_spans) = 'array' and jsonb_array_length(source_spans) > 0
  ),
  primary key (corpus_attempt_id, note_id),
  foreign key (corpus_attempt_id, origin_passage_id)
    references passage.passage_versions (corpus_attempt_id, canonical_passage_id)
    on delete cascade
);

create index apparatus_notes_origin_passage_id_idx
  on passage.apparatus_notes (corpus_attempt_id, origin_passage_id);

create table passage.official_edges (
  corpus_attempt_id uuid not null,
  edge_id text not null check (edge_id <> ''),
  origin_passage_id text not null,
  origin_anchor text not null check (origin_anchor <> ''),
  target jsonb not null check (jsonb_typeof(target) = 'object'),
  source_attribution text not null check (source_attribution <> ''),
  grammar_version text not null check (grammar_version <> ''),
  source_spans jsonb not null check (
    jsonb_typeof(source_spans) = 'array' and jsonb_array_length(source_spans) > 0
  ),
  primary key (corpus_attempt_id, edge_id),
  foreign key (corpus_attempt_id, origin_passage_id)
    references passage.passage_versions (corpus_attempt_id, canonical_passage_id)
    on delete cascade
);

create index official_edges_origin_passage_id_idx
  on passage.official_edges (corpus_attempt_id, origin_passage_id);

create table passage.retrieval_configurations (
  config_id text primary key check (config_id <> ''),
  corpus_attempt_id uuid not null
    references passage.corpus_versions (attempt_id) on delete restrict,
  backend text not null check (backend in ('sqlite', 'postgresql')),
  configuration jsonb not null check (jsonb_typeof(configuration) = 'object'),
  created_at timestamptz not null default statement_timestamp(),
  unique (corpus_attempt_id, config_id)
);

create index retrieval_configurations_corpus_attempt_id_idx
  on passage.retrieval_configurations (corpus_attempt_id);

create table passage.retrieval_snapshots (
  snapshot_id text primary key check (snapshot_id <> ''),
  corpus_attempt_id uuid not null,
  corpus_version text not null,
  retrieval_config_id text not null,
  official_edge_set_id text not null check (official_edge_set_id <> ''),
  derived_graph_version text not null check (derived_graph_version <> ''),
  relationship_vocabulary_version text not null
    check (relationship_vocabulary_version <> ''),
  vector_config_id text not null check (vector_config_id <> ''),
  publication_policy_id text not null check (publication_policy_id <> ''),
  created_at timestamptz not null default statement_timestamp(),
  foreign key (corpus_attempt_id, corpus_version)
    references passage.corpus_versions (attempt_id, corpus_version) on delete restrict,
  foreign key (corpus_attempt_id, retrieval_config_id)
    references passage.retrieval_configurations (corpus_attempt_id, config_id)
    on delete restrict,
  unique (corpus_attempt_id, retrieval_config_id)
);

create index retrieval_snapshots_corpus_identity_idx
  on passage.retrieval_snapshots (corpus_attempt_id, corpus_version);
create index retrieval_snapshots_retrieval_config_id_idx
  on passage.retrieval_snapshots (retrieval_config_id);

create table passage.active_snapshot (
  singleton boolean primary key default true check (singleton),
  snapshot_id text not null
    references passage.retrieval_snapshots (snapshot_id) on delete restrict,
  activated_at timestamptz not null default statement_timestamp()
);

create index active_snapshot_snapshot_id_idx
  on passage.active_snapshot (snapshot_id);

create table passage.members (
  issuer text not null check (issuer <> ''),
  subject text not null check (subject <> ''),
  member_role text not null check (member_role in ('owner', 'member')),
  state text not null check (state in ('active', 'disabled')),
  created_at timestamptz not null default statement_timestamp(),
  updated_at timestamptz not null default statement_timestamp(),
  disabled_at timestamptz,
  primary key (issuer, subject),
  constraint members_disabled_timestamp_check check (
    (state = 'active' and disabled_at is null)
    or (state = 'disabled' and disabled_at is not null)
  )
);

create index members_active_identity_idx
  on passage.members (issuer, subject)
  where state = 'active';

create function passage.enforce_corpus_lifecycle()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  if tg_op = 'INSERT' then
    if new.state <> 'staging' then
      raise exception 'new corpus attempts must begin in staging state'
        using errcode = '23514';
    end if;
    return new;
  end if;

  if tg_op = 'DELETE' then
    if old.state <> 'rejected' then
      raise exception 'only rejected corpus attempts may be deleted'
        using errcode = '55000';
    end if;
    return old;
  end if;

  if old.state in ('accepted', 'rejected') then
    raise exception 'terminal corpus attempts are immutable'
      using errcode = '55000';
  end if;

  if old.state = 'staging' and new.state not in ('staging', 'validated', 'rejected') then
    raise exception 'invalid corpus lifecycle transition'
      using errcode = '23514';
  end if;

  if old.state = 'validated' and new.state not in ('accepted', 'rejected') then
    raise exception 'invalid corpus lifecycle transition'
      using errcode = '23514';
  end if;

  if old.state = 'validated' and (
    new.attempt_id,
    new.corpus_version,
    new.build_key,
    new.source_version_id,
    new.normalized_digest,
    new.artifact_digest,
    new.manifest,
    new.created_at,
    new.validated_at
  ) is distinct from (
    old.attempt_id,
    old.corpus_version,
    old.build_key,
    old.source_version_id,
    old.normalized_digest,
    old.artifact_digest,
    old.manifest,
    old.created_at,
    old.validated_at
  ) then
    raise exception 'validated corpus identity and manifest are immutable'
      using errcode = '55000';
  end if;

  return new;
end
$$;

create trigger corpus_versions_lifecycle_guard
before insert or update or delete on passage.corpus_versions
for each row execute function passage.enforce_corpus_lifecycle();

create function passage.enforce_corpus_child_mutability()
returns trigger
language plpgsql
set search_path = ''
as $$
declare
  parent_state text;
  parent_attempt uuid;
begin
  parent_attempt := case when tg_op = 'DELETE'
    then old.corpus_attempt_id else new.corpus_attempt_id end;

  select state into parent_state
  from passage.corpus_versions
  where attempt_id = parent_attempt;

  if tg_op in ('INSERT', 'UPDATE') and parent_state is distinct from 'staging' then
    raise exception 'corpus children are mutable only while staging'
      using errcode = '55000';
  end if;
  if (
    tg_op = 'DELETE'
    and parent_state is not null
    and parent_state not in ('staging', 'rejected')
  ) then
    raise exception 'validated or accepted corpus children cannot be deleted'
      using errcode = '55000';
  end if;

  return case when tg_op = 'DELETE' then old else new end;
end
$$;

create trigger passage_versions_mutability_guard
before insert or update or delete on passage.passage_versions
for each row execute function passage.enforce_corpus_child_mutability();
create trigger apparatus_notes_mutability_guard
before insert or update or delete on passage.apparatus_notes
for each row execute function passage.enforce_corpus_child_mutability();
create trigger official_edges_mutability_guard
before insert or update or delete on passage.official_edges
for each row execute function passage.enforce_corpus_child_mutability();

create function passage.reject_update_or_delete()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  raise exception '% rows are immutable', tg_table_name using errcode = '55000';
end
$$;

create trigger source_versions_immutable
before update or delete on passage.source_versions
for each row execute function passage.reject_update_or_delete();
create trigger canonical_passages_immutable
before update or delete on passage.canonical_passages
for each row execute function passage.reject_update_or_delete();
create trigger retrieval_configurations_immutable
before update or delete on passage.retrieval_configurations
for each row execute function passage.reject_update_or_delete();
create trigger retrieval_snapshots_immutable
before update or delete on passage.retrieval_snapshots
for each row execute function passage.reject_update_or_delete();

create function passage.require_accepted_corpus()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  if not exists (
    select 1
    from passage.corpus_versions
    where attempt_id = new.corpus_attempt_id and state = 'accepted'
  ) then
    raise exception 'retrieval records require an accepted corpus'
      using errcode = '23514';
  end if;
  return new;
end
$$;

create trigger retrieval_configurations_accepted_corpus_guard
before insert on passage.retrieval_configurations
for each row execute function passage.require_accepted_corpus();
create trigger retrieval_snapshots_accepted_corpus_guard
before insert on passage.retrieval_snapshots
for each row execute function passage.require_accepted_corpus();

create function passage.set_active_snapshot_activated_at()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  new.activated_at := statement_timestamp();
  return new;
end
$$;

create trigger active_snapshot_activated_at
before update on passage.active_snapshot
for each row execute function passage.set_active_snapshot_activated_at();

create function passage.set_member_updated_at()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  new.updated_at := statement_timestamp();
  return new;
end
$$;

create trigger members_updated_at
before update on passage.members
for each row execute function passage.set_member_updated_at();

alter table passage.source_versions enable row level security;
alter table passage.source_versions force row level security;
alter table passage.corpus_versions enable row level security;
alter table passage.corpus_versions force row level security;
alter table passage.canonical_passages enable row level security;
alter table passage.canonical_passages force row level security;
alter table passage.passage_versions enable row level security;
alter table passage.passage_versions force row level security;
alter table passage.apparatus_notes enable row level security;
alter table passage.apparatus_notes force row level security;
alter table passage.official_edges enable row level security;
alter table passage.official_edges force row level security;
alter table passage.retrieval_configurations enable row level security;
alter table passage.retrieval_configurations force row level security;
alter table passage.retrieval_snapshots enable row level security;
alter table passage.retrieval_snapshots force row level security;
alter table passage.active_snapshot enable row level security;
alter table passage.active_snapshot force row level security;
alter table passage.members enable row level security;
alter table passage.members force row level security;

create policy members_request_self on passage.members
for select to passage_request
using (
  state = 'active'
  and issuer = nullif(current_setting('passage.issuer', true), '')
  and subject = nullif(current_setting('passage.subject', true), '')
  and nullif(current_setting('passage.client', true), '') is not null
);

create function passage.has_active_member_context()
returns boolean
language sql
stable
security invoker
set search_path = ''
as $$
  select exists (
    select 1
    from passage.members
    where state = 'active'
      and issuer = nullif(current_setting('passage.issuer', true), '')
      and subject = nullif(current_setting('passage.subject', true), '')
      and nullif(current_setting('passage.client', true), '') is not null
  )
$$;

revoke execute on function passage.has_active_member_context() from public;
grant execute on function passage.has_active_member_context() to passage_request;

create policy source_versions_request_read on passage.source_versions
for select to passage_request
using (
  (select passage.has_active_member_context())
  and exists (
    select 1 from passage.corpus_versions
    where source_version_id = source_versions.source_version_id and state = 'accepted'
  )
);
create policy corpus_versions_request_read on passage.corpus_versions
for select to passage_request
using ((select passage.has_active_member_context()) and state = 'accepted');
create policy canonical_passages_request_read on passage.canonical_passages
for select to passage_request
using (
  (select passage.has_active_member_context())
  and exists (
    select 1
    from passage.passage_versions
    join passage.corpus_versions
      on corpus_versions.attempt_id = passage_versions.corpus_attempt_id
    where passage_versions.canonical_passage_id = canonical_passages.canonical_passage_id
      and corpus_versions.state = 'accepted'
  )
);
create policy passage_versions_request_read on passage.passage_versions
for select to passage_request
using (
  (select passage.has_active_member_context())
  and exists (
    select 1 from passage.corpus_versions
    where attempt_id = passage_versions.corpus_attempt_id and state = 'accepted'
  )
);
create policy apparatus_notes_request_read on passage.apparatus_notes
for select to passage_request
using (
  (select passage.has_active_member_context())
  and exists (
    select 1 from passage.corpus_versions
    where attempt_id = apparatus_notes.corpus_attempt_id and state = 'accepted'
  )
);
create policy official_edges_request_read on passage.official_edges
for select to passage_request
using (
  (select passage.has_active_member_context())
  and exists (
    select 1 from passage.corpus_versions
    where attempt_id = official_edges.corpus_attempt_id and state = 'accepted'
  )
);
create policy retrieval_configurations_request_read on passage.retrieval_configurations
for select to passage_request
using (
  (select passage.has_active_member_context())
  and exists (
    select 1 from passage.corpus_versions
    where attempt_id = retrieval_configurations.corpus_attempt_id and state = 'accepted'
  )
);
create policy retrieval_snapshots_request_read on passage.retrieval_snapshots
for select to passage_request
using (
  (select passage.has_active_member_context())
  and exists (
    select 1 from passage.corpus_versions
    where attempt_id = retrieval_snapshots.corpus_attempt_id and state = 'accepted'
  )
);
create policy active_snapshot_request_read on passage.active_snapshot
for select to passage_request
using ((select passage.has_active_member_context()));

create policy source_versions_maintenance_all on passage.source_versions
for all to passage_maintenance using (true) with check (true);
create policy corpus_versions_maintenance_all on passage.corpus_versions
for all to passage_maintenance using (true) with check (true);
create policy canonical_passages_maintenance_all on passage.canonical_passages
for all to passage_maintenance using (true) with check (true);
create policy passage_versions_maintenance_all on passage.passage_versions
for all to passage_maintenance using (true) with check (true);
create policy apparatus_notes_maintenance_all on passage.apparatus_notes
for all to passage_maintenance using (true) with check (true);
create policy official_edges_maintenance_all on passage.official_edges
for all to passage_maintenance using (true) with check (true);
create policy retrieval_configurations_maintenance_all on passage.retrieval_configurations
for all to passage_maintenance using (true) with check (true);
create policy retrieval_snapshots_maintenance_all on passage.retrieval_snapshots
for all to passage_maintenance using (true) with check (true);
create policy active_snapshot_maintenance_all on passage.active_snapshot
for all to passage_maintenance using (true) with check (true);
create policy members_maintenance_all on passage.members
for all to passage_maintenance using (true) with check (true);

grant select, insert on passage.source_versions to passage_maintenance;
grant select, insert, update, delete on passage.corpus_versions to passage_maintenance;
grant select, insert on passage.canonical_passages to passage_maintenance;
grant select, insert, update, delete on passage.passage_versions to passage_maintenance;
grant select, insert, update, delete on passage.apparatus_notes to passage_maintenance;
grant select, insert, update, delete on passage.official_edges to passage_maintenance;
grant select, insert on passage.retrieval_configurations to passage_maintenance;
grant select, insert on passage.retrieval_snapshots to passage_maintenance;
grant select, insert, update on passage.active_snapshot to passage_maintenance;
grant select, insert, update on passage.members to passage_maintenance;

grant select on passage.source_versions to passage_request;
grant select on passage.corpus_versions to passage_request;
grant select on passage.canonical_passages to passage_request;
grant select on passage.passage_versions to passage_request;
grant select on passage.apparatus_notes to passage_request;
grant select on passage.official_edges to passage_request;
grant select on passage.retrieval_configurations to passage_request;
grant select on passage.retrieval_snapshots to passage_request;
grant select on passage.active_snapshot to passage_request;
grant select on passage.members to passage_request;

revoke all on all tables in schema passage from public, anon, authenticated, service_role;
revoke all on all sequences in schema passage from public, anon, authenticated, service_role;
revoke execute on all functions in schema passage from public, anon, authenticated, service_role;
