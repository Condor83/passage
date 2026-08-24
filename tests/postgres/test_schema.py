from __future__ import annotations

import uuid

import pytest
from psycopg import errors
from psycopg.types.json import Jsonb
from psycopg_pool import PoolTimeout

from passage.db.postgres import PostgresPoolConfig, PostgresPools
from tests.postgres.conftest import AcceptedSnapshotFixture

_EXPECTED_TABLES = {
    "active_snapshot",
    "apparatus_notes",
    "canonical_passages",
    "corpus_versions",
    "members",
    "official_edges",
    "passage_versions",
    "retrieval_configurations",
    "retrieval_snapshots",
    "source_versions",
}


def _insert_staging_attempt(
    connection,
    *,
    build_key: str | None = None,
    corpus_version: str | None = None,
) -> tuple[uuid.UUID, str, str]:
    token = uuid.uuid4().hex
    attempt_id = uuid.uuid4()
    source_version_id = f"source-{token}"
    selected_build_key = build_key or f"build-{token}"
    selected_corpus_version = corpus_version or f"corpus-{token}"
    connection.execute(
        """insert into passage.source_versions(
               source_version_id, source_sha256, acquisition_record_digest,
               edition, language
           ) values (%s, %s, %s, 'Synthetic edition', 'eng')""",
        (source_version_id, token * 2, token[::-1] * 2),
    )
    connection.execute(
        """insert into passage.corpus_versions(
               attempt_id, corpus_version, build_key, source_version_id, state,
               normalized_digest, artifact_digest, manifest
           ) values (%s, %s, %s, %s, 'staging', %s, %s, %s)""",
        (
            attempt_id,
            selected_corpus_version,
            selected_build_key,
            source_version_id,
            (token[1:] + token[:1]) * 2,
            (token[2:] + token[:2]) * 2,
            Jsonb({"schema_version": 2, "source": "synthetic"}),
        ),
    )
    return attempt_id, selected_build_key, selected_corpus_version


def test_pool_configuration_requires_distinct_redacted_dsns() -> None:
    config = PostgresPoolConfig(
        request_dsn="postgresql://request:secret@example.test/passage",
        maintenance_dsn="postgresql://maintenance:other@example.test/passage",
    )

    assert "secret" not in repr(config)
    assert "other" not in repr(config)
    with pytest.raises(ValueError, match="distinct"):
        PostgresPoolConfig(request_dsn="same", maintenance_dsn="same")


def test_pool_connection_failure_redacts_credentials() -> None:
    sentinel = "u3-password-must-not-appear"
    pools = PostgresPools(
        PostgresPoolConfig(
            request_dsn=(
                f"postgresql://passage_request:{sentinel}@127.0.0.1:1/postgres?connect_timeout=1"
            ),
            maintenance_dsn=(
                "postgresql://passage_maintenance:other-secret"
                "@127.0.0.1:1/postgres?connect_timeout=1"
            ),
            min_size=1,
            max_size=1,
            timeout_seconds=0.2,
        )
    )

    with pytest.raises(PoolTimeout) as failure:
        pools.open()

    assert sentinel not in str(failure.value)
    assert "other-secret" not in str(failure.value)


def test_migration_creates_private_forced_rls_schema(postgres_pools: PostgresPools) -> None:
    with postgres_pools.maintenance() as connection:
        tables = {
            row[0]
            for row in connection.execute(
                """select tablename from pg_tables
                   where schemaname = 'passage'"""
            ).fetchall()
        }
        rls = connection.execute(
            """select relname, relrowsecurity, relforcerowsecurity
               from pg_class
               join pg_namespace on pg_namespace.oid = pg_class.relnamespace
               where pg_namespace.nspname = 'passage' and relkind = 'r'"""
        ).fetchall()
        exposed = connection.execute(
            """select role_name
               from (
                 values ('anon'), ('authenticated'), ('service_role'), ('authenticator')
               ) roles(role_name)
               where has_schema_privilege(role_name, 'passage', 'usage')"""
        ).fetchall()

    assert tables == _EXPECTED_TABLES
    assert {row[0] for row in rls} == _EXPECTED_TABLES
    assert all(row[1] is True and row[2] is True for row in rls)
    assert exposed == []


def test_application_roles_are_non_bypass_and_separate(postgres_pools: PostgresPools) -> None:
    with postgres_pools.maintenance() as connection:
        roles = connection.execute(
            """select rolname, rolsuper, rolinherit, rolcreaterole, rolcreatedb,
                      rolcanlogin, rolreplication, rolbypassrls
               from pg_roles
               where rolname in ('passage_request', 'passage_maintenance')
               order by rolname"""
        ).fetchall()
        can_assume_maintenance = connection.execute(
            """select pg_has_role(
                 'passage_request', 'passage_maintenance', 'member'
               )"""
        ).fetchone()[0]

    assert roles == [
        ("passage_maintenance", False, False, False, False, True, False, False),
        ("passage_request", False, False, False, False, True, False, False),
    ]
    assert can_assume_maintenance is False


def test_foreign_keys_policy_columns_and_search_are_indexed(
    postgres_pools: PostgresPools,
    accepted_snapshot: AcceptedSnapshotFixture,
) -> None:
    with postgres_pools.maintenance() as connection:
        missing_foreign_key_indexes = connection.execute(
            """select constraint_name, column_name
               from (
                 select constraint_name, table_name, column_name
                 from information_schema.key_column_usage
                 join information_schema.table_constraints
                   using (constraint_catalog, constraint_schema, constraint_name,
                          table_catalog, table_schema, table_name)
                 where constraint_schema = 'passage'
                   and constraint_type = 'FOREIGN KEY'
               ) foreign_keys
               where not exists (
                 select 1
                 from pg_indexes
                 where schemaname = 'passage'
                   and tablename = foreign_keys.table_name
                   and indexdef like '%' || foreign_keys.column_name || '%'
               )"""
        ).fetchall()
        search_index = connection.execute(
            """select indexdef from pg_indexes
               where schemaname = 'passage'
                 and indexname = 'passage_versions_search_vector_idx'"""
        ).fetchone()
        matches = connection.execute(
            """select canonical_passage_id
               from passage.passage_versions
               where search_vector @@ to_tsquery('english', 'faith & hope')"""
        ).fetchall()

    assert missing_foreign_key_indexes == []
    assert search_index is not None and "USING gin" in search_index[0]
    assert matches == [(accepted_snapshot.canonical_passage_id,)]


def test_accepted_corpus_and_children_are_immutable(
    postgres_pools: PostgresPools,
    accepted_snapshot: AcceptedSnapshotFixture,
) -> None:
    with postgres_pools.maintenance() as connection:
        with pytest.raises(errors.ObjectNotInPrerequisiteState), connection.transaction():
            connection.execute(
                """update passage.corpus_versions set manifest = '{}'::jsonb
                   where attempt_id = %s""",
                (accepted_snapshot.attempt_id,),
            )
        with pytest.raises(errors.ObjectNotInPrerequisiteState), connection.transaction():
            connection.execute(
                """update passage.passage_versions set passage_text = 'changed'
                   where corpus_attempt_id = %s""",
                (accepted_snapshot.attempt_id,),
            )
        with pytest.raises(errors.ObjectNotInPrerequisiteState), connection.transaction():
            connection.execute(
                "delete from passage.corpus_versions where attempt_id = %s",
                (accepted_snapshot.attempt_id,),
            )


def test_active_snapshot_refreshes_activation_timestamp(
    postgres_pools: PostgresPools,
    accepted_snapshot: AcceptedSnapshotFixture,
) -> None:
    with postgres_pools.maintenance() as connection:
        before = connection.execute(
            "select activated_at from passage.active_snapshot where singleton"
        ).fetchone()[0]
        connection.execute("select pg_sleep(0.01)")
        after = connection.execute(
            """update passage.active_snapshot
               set snapshot_id = %s
               where singleton
               returning activated_at""",
            (accepted_snapshot.snapshot_id,),
        ).fetchone()[0]

    assert after > before


def test_lifecycle_allows_rejected_cleanup_and_retry(
    postgres_pools: PostgresPools,
) -> None:
    with postgres_pools.maintenance() as connection:
        attempt_id, build_key, corpus_version = _insert_staging_attempt(connection)
        canonical_passage_id = f"retry-{attempt_id.hex}"
        connection.execute(
            """insert into passage.canonical_passages(
                   canonical_passage_id, reference, work, book, chapter, verse,
                   canonical_order
               ) values (%s, %s, 'bofm', '1-ne', 1, 1, %s)""",
            (
                canonical_passage_id,
                f"synthetic/retry/{attempt_id.hex}",
                int(attempt_id.hex[:12], 16),
            ),
        )
        connection.execute(
            """insert into passage.passage_versions(
                   corpus_attempt_id, canonical_passage_id, passage_text,
                   content_hash, source_spans
               ) values (%s, %s, 'Rejected retry text', %s, %s)""",
            (
                attempt_id,
                canonical_passage_id,
                attempt_id.hex * 2,
                Jsonb([{"resource": "synthetic", "start": 0, "end": 19}]),
            ),
        )
        with pytest.raises(errors.UniqueViolation), connection.transaction():
            _insert_staging_attempt(
                connection,
                build_key=build_key,
                corpus_version=corpus_version,
            )

        connection.execute(
            """update passage.corpus_versions
               set state = 'rejected', rejected_at = statement_timestamp(),
                   rejection_code = 'synthetic_failure'
               where attempt_id = %s""",
            (attempt_id,),
        )
        retry_id, _, _ = _insert_staging_attempt(
            connection,
            build_key=build_key,
            corpus_version=corpus_version,
        )
        connection.execute(
            "delete from passage.corpus_versions where attempt_id = %s",
            (attempt_id,),
        )
        states = connection.execute(
            """select attempt_id, state from passage.corpus_versions
               where build_key = %s""",
            (build_key,),
        ).fetchall()
        rejected_child_count = connection.execute(
            """select count(*) from passage.passage_versions
               where corpus_attempt_id = %s""",
            (attempt_id,),
        ).fetchone()[0]

    assert states == [(retry_id, "staging")]
    assert rejected_child_count == 0


def test_lifecycle_rejects_invalid_transition(
    postgres_pools: PostgresPools,
) -> None:
    with postgres_pools.maintenance() as connection:
        attempt_id, _, _ = _insert_staging_attempt(connection)
        with pytest.raises(errors.CheckViolation), connection.transaction():
            connection.execute(
                """update passage.corpus_versions
                   set state = 'accepted', accepted_at = statement_timestamp()
                   where attempt_id = %s""",
                (attempt_id,),
            )


def test_retrieval_snapshot_requires_one_complete_accepted_binding(
    postgres_pools: PostgresPools,
    accepted_snapshot: AcceptedSnapshotFixture,
) -> None:
    required = {
        "corpus_attempt_id",
        "corpus_version",
        "retrieval_config_id",
        "official_edge_set_id",
        "derived_graph_version",
        "relationship_vocabulary_version",
        "vector_config_id",
        "publication_policy_id",
    }
    with postgres_pools.maintenance() as connection:
        columns = connection.execute(
            """select column_name, is_nullable
               from information_schema.columns
               where table_schema = 'passage'
                 and table_name = 'retrieval_snapshots'"""
        ).fetchall()
        config_id = connection.execute(
            """select retrieval_config_id from passage.retrieval_snapshots
               where snapshot_id = %s""",
            (accepted_snapshot.snapshot_id,),
        ).fetchone()[0]
        with pytest.raises(errors.UniqueViolation), connection.transaction():
            connection.execute(
                """insert into passage.retrieval_snapshots(
                       snapshot_id, corpus_attempt_id, corpus_version,
                       retrieval_config_id, official_edge_set_id,
                       derived_graph_version, relationship_vocabulary_version,
                       vector_config_id, publication_policy_id
                   ) values (%s, %s, %s, %s, 'other', 'none', 'none', 'none', 'other')""",
                (
                    f"{accepted_snapshot.snapshot_id}-duplicate",
                    accepted_snapshot.attempt_id,
                    accepted_snapshot.corpus_version,
                    config_id,
                ),
            )

    assert required <= {name for name, _ in columns}
    assert all(nullable == "NO" for name, nullable in columns if name in required)
