from __future__ import annotations

import asyncio
import uuid

import pytest
from psycopg import errors
from psycopg.types.json import Jsonb

from passage.db.postgres import PostgresPools, RequestIdentity
from tests.postgres.conftest import AcceptedSnapshotFixture


def _identity() -> RequestIdentity:
    token = uuid.uuid4().hex
    return RequestIdentity(
        issuer=f"https://synthetic-{token}.supabase.test/auth/v1",
        subject=f"subject-{token}",
        client=f"client-{token}",
    )


def _insert_member(
    pools: PostgresPools,
    identity: RequestIdentity,
    *,
    state: str = "active",
) -> None:
    with pools.maintenance() as connection:
        connection.execute(
            """insert into passage.members(
                   issuer, subject, member_role, state, disabled_at
               ) values (
                   %s, %s, 'member', %s,
                   case when %s = 'disabled' then statement_timestamp() else null end
               )""",
            (identity.issuer, identity.subject, state, state),
        )


def _insert_nonaccepted_passage(pools: PostgresPools, state: str) -> str:
    token = uuid.uuid4().hex
    attempt_id = uuid.uuid4()
    source_version_id = f"source-{token}"
    canonical_passage_id = f"passage-{token}"
    with pools.maintenance() as connection:
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
                f"corpus-{token}",
                f"build-{token}",
                source_version_id,
                (token[1:] + token[:1]) * 2,
                (token[2:] + token[:2]) * 2,
                Jsonb({"schema_version": 2}),
            ),
        )
        connection.execute(
            """insert into passage.canonical_passages(
                   canonical_passage_id, reference, work, book, chapter, verse,
                   canonical_order
               ) values (%s, %s, 'bofm', '1-ne', 1, 1, %s)""",
            (canonical_passage_id, f"synthetic/{token}", int(token[:12], 16)),
        )
        connection.execute(
            """insert into passage.passage_versions(
                   corpus_attempt_id, canonical_passage_id, passage_text,
                   content_hash, source_spans
               ) values (%s, %s, 'Hidden staging text', %s, %s)""",
            (
                attempt_id,
                canonical_passage_id,
                (token[3:] + token[:3]) * 2,
                Jsonb([{"resource": "synthetic", "start": 0, "end": 19}]),
            ),
        )
        if state == "rejected":
            connection.execute(
                """update passage.corpus_versions
                   set state = 'rejected', rejected_at = statement_timestamp(),
                       rejection_code = 'synthetic_failure'
                   where attempt_id = %s""",
                (attempt_id,),
            )
    return canonical_passage_id


def _assert_request_connection_is_clean(
    pools: PostgresPools,
    expected_backend_pid: int,
) -> None:
    with pools.request_pool.connection() as connection:
        backend_pid, issuer, subject, client = connection.execute(
            """select pg_backend_pid(),
                      current_setting('passage.issuer', true),
                      current_setting('passage.subject', true),
                      current_setting('passage.client', true)"""
        ).fetchone()
        visible = connection.execute("select count(*) from passage.passage_versions").fetchone()[0]

    assert backend_pid == expected_backend_pid
    assert issuer in (None, "")
    assert subject in (None, "")
    assert client in (None, "")
    assert visible == 0


def test_request_role_without_context_reads_no_rows(
    postgres_pools: PostgresPools,
    accepted_snapshot: AcceptedSnapshotFixture,
) -> None:
    with postgres_pools.request_pool.connection() as connection:
        current_user = connection.execute("select current_user").fetchone()[0]
        visible = connection.execute("select count(*) from passage.passage_versions").fetchone()[0]

    assert current_user == "passage_request"
    assert visible == 0


def test_active_member_context_reads_only_protected_evidence(
    postgres_pools: PostgresPools,
    accepted_snapshot: AcceptedSnapshotFixture,
) -> None:
    identity = _identity()
    _insert_member(postgres_pools, identity)

    with postgres_pools.request(identity) as connection:
        passages = connection.execute(
            "select canonical_passage_id from passage.passage_versions"
        ).fetchall()
        members = connection.execute("select issuer, subject from passage.members").fetchall()

    assert passages == [(accepted_snapshot.canonical_passage_id,)]
    assert members == [(identity.issuer, identity.subject)]


def test_active_member_cannot_read_staging_or_rejected_corpora(
    postgres_pools: PostgresPools,
    accepted_snapshot: AcceptedSnapshotFixture,
) -> None:
    identity = _identity()
    _insert_member(postgres_pools, identity)
    hidden = {
        _insert_nonaccepted_passage(postgres_pools, "staging"),
        _insert_nonaccepted_passage(postgres_pools, "rejected"),
    }

    with postgres_pools.request(identity) as connection:
        visible = {
            row[0]
            for row in connection.execute(
                "select canonical_passage_id from passage.passage_versions"
            ).fetchall()
        }

    assert visible == {accepted_snapshot.canonical_passage_id}
    assert visible.isdisjoint(hidden)


def test_partial_blank_and_mismatched_context_reads_no_rows(
    postgres_pools: PostgresPools,
    accepted_snapshot: AcceptedSnapshotFixture,
) -> None:
    identity = _identity()
    _insert_member(postgres_pools, identity)
    contexts = [
        (identity.issuer, identity.subject, ""),
        ("", identity.subject, identity.client),
        (identity.issuer, f"{identity.subject}-other", identity.client),
        (" ", identity.subject, identity.client),
    ]

    with postgres_pools.request_pool.connection() as connection:
        for issuer, subject, client in contexts:
            with connection.transaction():
                connection.execute(
                    "select set_config('passage.issuer', %s, true)",
                    (issuer,),
                )
                connection.execute(
                    "select set_config('passage.subject', %s, true)",
                    (subject,),
                )
                connection.execute(
                    "select set_config('passage.client', %s, true)",
                    (client,),
                )
                visible = connection.execute(
                    "select count(*) from passage.passage_versions"
                ).fetchone()[0]
            assert visible == 0


def test_disabled_and_absent_members_read_no_rows(
    postgres_pools: PostgresPools,
    accepted_snapshot: AcceptedSnapshotFixture,
) -> None:
    disabled = _identity()
    absent = _identity()
    _insert_member(postgres_pools, disabled, state="disabled")

    for identity in (disabled, absent):
        with postgres_pools.request(identity) as connection:
            visible = connection.execute(
                "select count(*) from passage.passage_versions"
            ).fetchone()[0]
        assert visible == 0


def test_request_role_cannot_write_or_assume_maintenance(
    postgres_pools: PostgresPools,
    accepted_snapshot: AcceptedSnapshotFixture,
) -> None:
    identity = _identity()
    _insert_member(postgres_pools, identity)

    with postgres_pools.request(identity) as connection:
        with pytest.raises(errors.InsufficientPrivilege), connection.transaction():
            connection.execute(
                "update passage.members set member_role = 'owner' where subject = %s",
                (identity.subject,),
            )
        with pytest.raises(errors.InsufficientPrivilege), connection.transaction():
            connection.execute("set role passage_maintenance")


def test_transaction_context_clears_after_success_error_and_cancellation(
    postgres_pools: PostgresPools,
    accepted_snapshot: AcceptedSnapshotFixture,
) -> None:
    identity = _identity()
    _insert_member(postgres_pools, identity)

    with postgres_pools.request(identity) as connection:
        success_pid = connection.execute("select pg_backend_pid()").fetchone()[0]
    _assert_request_connection_is_clean(postgres_pools, success_pid)

    with (
        pytest.raises(RuntimeError, match="injected"),
        postgres_pools.request(identity) as connection,
    ):
        error_pid = connection.execute("select pg_backend_pid()").fetchone()[0]
        raise RuntimeError("injected")
    _assert_request_connection_is_clean(postgres_pools, error_pid)

    with (
        pytest.raises(asyncio.CancelledError),
        postgres_pools.request(identity) as connection,
    ):
        cancellation_pid = connection.execute("select pg_backend_pid()").fetchone()[0]
        raise asyncio.CancelledError
    _assert_request_connection_is_clean(postgres_pools, cancellation_pid)


def test_identity_values_are_parameter_bound(
    postgres_pools: PostgresPools,
    accepted_snapshot: AcceptedSnapshotFixture,
) -> None:
    identity = RequestIdentity(
        issuer="https://synthetic.supabase.test/auth/v1",
        subject="subject'; set role passage_maintenance; --",
        client="client'quoted",
    )

    with postgres_pools.request(identity) as connection:
        current_user = connection.execute("select current_user").fetchone()[0]
        visible = connection.execute("select count(*) from passage.passage_versions").fetchone()[0]

    assert current_user == "passage_request"
    assert visible == 0
