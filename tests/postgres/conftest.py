from __future__ import annotations

import json
import re
import secrets
import subprocess
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field

import pytest
from psycopg import connect, sql
from psycopg.conninfo import make_conninfo
from psycopg.types.json import Jsonb

from passage.db.postgres import PostgresPoolConfig, PostgresPools

SUPABASE_CLI_VERSION = "2.115.0"
SUPABASE_COMMAND = ("npx", "--yes", f"supabase@{SUPABASE_CLI_VERSION}")
SUPABASE_PROJECT_ID = "passage"
SUPABASE_NETWORK = "passage-local"
LOOPBACK_HOST = "127.0.0.1"
EXPECTED_HOST_PORTS = frozenset({54321, 54322, 54324})
_NETWORK_BINDING_OPTION = "com.docker.network.bridge.host_binding_ipv4"


@dataclass(frozen=True, slots=True)
class PublishedBinding:
    container: str
    container_port: str
    host: str
    host_port: int


@dataclass(frozen=True, slots=True)
class LocalSupabaseStack:
    bindings: tuple[PublishedBinding, ...]
    database_url: str = field(repr=False)
    api_url: str
    anon_key: str = field(repr=False)
    service_role_key: str = field(repr=False)


def _run_captured(command: tuple[str, ...], *, timeout: int = 30) -> str:
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as error:
        raise RuntimeError(f"{command[0]} prerequisite is unavailable") from error
    if result.returncode != 0:
        raise RuntimeError(f"{command[0]} prerequisite check failed")
    return result.stdout.strip()


def _status_value(status: dict[str, object], *names: str) -> str:
    for name in names:
        value = status.get(name)
        if isinstance(value, str) and value:
            return value
    raise RuntimeError("Supabase status omitted a required local endpoint")


def local_status() -> tuple[str, str, str, str]:
    raw = _run_captured((*SUPABASE_COMMAND, "status", "-o", "json"), timeout=120)
    try:
        status = json.loads(raw)
    except json.JSONDecodeError as error:
        raise RuntimeError("Supabase status returned invalid JSON") from error
    if not isinstance(status, dict):
        raise RuntimeError("Supabase status returned an invalid payload")
    return (
        _status_value(status, "DB_URL", "db_url"),
        _status_value(status, "API_URL", "api_url"),
        _status_value(status, "ANON_KEY", "anon_key"),
        _status_value(status, "SERVICE_ROLE_KEY", "service_role_key"),
    )


def _run_quiet(command: tuple[str, ...], *, timeout: int = 300) -> None:
    try:
        result = subprocess.run(
            command,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as error:
        raise RuntimeError(f"{command[0]} command could not complete") from error
    if result.returncode != 0:
        raise RuntimeError(f"{command[0]} command failed; sensitive output was suppressed")


def validate_node_version(value: str) -> None:
    match = re.fullmatch(r"v?(\d+)(?:\.\d+){2}", value.strip())
    if match is None or int(match.group(1)) < 20:
        raise RuntimeError("Supabase CLI requires Node.js 20 or later")


def validate_supabase_version(value: str) -> None:
    if value.strip() != SUPABASE_CLI_VERSION:
        command = " ".join((*SUPABASE_COMMAND, "--version"))
        raise RuntimeError(
            f"Supabase CLI {SUPABASE_CLI_VERSION} is required; verify it with `{command}`"
        )


def check_prerequisites() -> None:
    validate_node_version(_run_captured(("node", "--version")))
    validate_supabase_version(_run_captured((*SUPABASE_COMMAND, "--version"), timeout=120))
    _run_captured(("docker", "version", "--format", "{{.Server.Version}}"))


def ensure_loopback_network() -> None:
    inspect = subprocess.run(
        (
            "docker",
            "network",
            "inspect",
            SUPABASE_NETWORK,
            "--format",
            f'{{{{index .Options "{_NETWORK_BINDING_OPTION}"}}}}',
        ),
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if inspect.returncode != 0:
        _run_quiet(
            (
                "docker",
                "network",
                "create",
                "--driver",
                "bridge",
                "--opt",
                f"{_NETWORK_BINDING_OPTION}={LOOPBACK_HOST}",
                SUPABASE_NETWORK,
            )
        )
        return
    if inspect.stdout.strip() != LOOPBACK_HOST:
        raise RuntimeError(
            f"Docker network {SUPABASE_NETWORK} does not default published ports to loopback"
        )


def _parse_binding(container: str, value: str) -> PublishedBinding:
    try:
        container_port, address = value.split(" -> ", maxsplit=1)
        if address.startswith("["):
            host, port = address[1:].split("]:", maxsplit=1)
        else:
            host, port = address.rsplit(":", maxsplit=1)
        return PublishedBinding(
            container=container,
            container_port=container_port,
            host=host,
            host_port=int(port),
        )
    except (ValueError, IndexError) as error:
        raise RuntimeError("Docker returned an unrecognized published-port binding") from error


def project_bindings() -> tuple[PublishedBinding, ...]:
    names = _run_captured(
        (
            "docker",
            "ps",
            "--filter",
            f"label=com.supabase.cli.project={SUPABASE_PROJECT_ID}",
            "--format",
            "{{.Names}}",
        )
    ).splitlines()
    bindings: list[PublishedBinding] = []
    for name in names:
        output = _run_captured(("docker", "port", name))
        bindings.extend(_parse_binding(name, line) for line in output.splitlines())
    return tuple(bindings)


def assert_loopback_bindings(bindings: tuple[PublishedBinding, ...]) -> None:
    if not bindings:
        raise RuntimeError("Passage Supabase published no host ports")
    unsafe = [binding for binding in bindings if binding.host != LOOPBACK_HOST]
    if unsafe:
        endpoints = ", ".join(f"{item.host}:{item.host_port}" for item in unsafe)
        raise RuntimeError(f"Passage Supabase exposed non-loopback endpoints: {endpoints}")
    host_ports = {binding.host_port for binding in bindings}
    missing = EXPECTED_HOST_PORTS - host_ports
    if missing:
        ports = ", ".join(str(port) for port in sorted(missing))
        raise RuntimeError(f"Passage Supabase did not publish expected loopback ports: {ports}")


def start_local_supabase() -> None:
    _run_quiet(
        (
            *SUPABASE_COMMAND,
            "start",
            "--network-id",
            SUPABASE_NETWORK,
            "--yes",
            "--log-level",
            "error",
        )
    )


def stop_local_supabase() -> None:
    _run_quiet(
        (
            *SUPABASE_COMMAND,
            "stop",
            "--project-id",
            SUPABASE_PROJECT_ID,
            "--no-backup",
            "--yes",
            "--log-level",
            "error",
        )
    )


@contextmanager
def managed_local_supabase() -> Iterator[LocalSupabaseStack]:
    check_prerequisites()
    ensure_loopback_network()
    stop_local_supabase()
    try:
        start_local_supabase()
        bindings = project_bindings()
        assert_loopback_bindings(bindings)
        database_url, api_url, anon_key, service_role_key = local_status()
        yield LocalSupabaseStack(
            bindings=bindings,
            database_url=database_url,
            api_url=api_url,
            anon_key=anon_key,
            service_role_key=service_role_key,
        )
    finally:
        stop_local_supabase()


@pytest.fixture(scope="session")
def local_supabase_stack() -> Iterator[LocalSupabaseStack]:
    with managed_local_supabase() as stack:
        yield stack


@pytest.fixture(scope="session")
def postgres_pool_config(local_supabase_stack: LocalSupabaseStack) -> PostgresPoolConfig:
    request_password = secrets.token_urlsafe(32)
    maintenance_password = secrets.token_urlsafe(32)
    with connect(local_supabase_stack.database_url, autocommit=True) as connection:
        connection.execute(
            sql.SQL("alter role {} password {}").format(
                sql.Identifier("passage_request"),
                sql.Literal(request_password),
            )
        )
        connection.execute(
            sql.SQL("alter role {} password {}").format(
                sql.Identifier("passage_maintenance"),
                sql.Literal(maintenance_password),
            )
        )
    return PostgresPoolConfig(
        request_dsn=make_conninfo(
            local_supabase_stack.database_url,
            user="passage_request",
            password=request_password,
        ),
        maintenance_dsn=make_conninfo(
            local_supabase_stack.database_url,
            user="passage_maintenance",
            password=maintenance_password,
        ),
        min_size=1,
        max_size=1,
        timeout_seconds=10,
    )


@pytest.fixture(scope="session")
def postgres_pools(postgres_pool_config: PostgresPoolConfig) -> Iterator[PostgresPools]:
    with PostgresPools(postgres_pool_config) as pools:
        yield pools


@dataclass(frozen=True, slots=True)
class AcceptedSnapshotFixture:
    attempt_id: uuid.UUID
    corpus_version: str
    canonical_passage_id: str
    snapshot_id: str


@pytest.fixture(scope="session")
def accepted_snapshot(postgres_pools: PostgresPools) -> AcceptedSnapshotFixture:
    token = uuid.uuid4().hex
    attempt_id = uuid.uuid4()
    source_version_id = f"source-{token}"
    corpus_version = f"corpus-{token}"
    canonical_passage_id = f"passage-{token}"
    config_id = f"postgresql-{token}"
    snapshot_id = f"snapshot-{token}"

    with postgres_pools.maintenance() as connection:
        connection.execute(
            """insert into passage.source_versions(
                   source_version_id, source_sha256, acquisition_record_digest,
                   edition, language
               ) values (%s, %s, %s, %s, %s)""",
            (source_version_id, "a" * 64, "b" * 64, "Synthetic edition", "eng"),
        )
        connection.execute(
            """insert into passage.corpus_versions(
                   attempt_id, corpus_version, build_key, source_version_id, state,
                   normalized_digest, artifact_digest, manifest
               ) values (%s, %s, %s, %s, 'staging', %s, %s, %s)""",
            (
                attempt_id,
                corpus_version,
                f"build-{token}",
                source_version_id,
                "c" * 64,
                "d" * 64,
                Jsonb({"schema_version": 2, "source": "synthetic"}),
            ),
        )
        connection.execute(
            """insert into passage.canonical_passages(
                   canonical_passage_id, reference, work, book, chapter, verse,
                   canonical_order
               ) values (%s, %s, 'bofm', '1-ne', 1, 1, 0)""",
            (canonical_passage_id, f"bofm/1-ne/1/{token[:4]}"),
        )
        connection.execute(
            """insert into passage.passage_versions(
                   corpus_attempt_id, canonical_passage_id, passage_text,
                   content_hash, source_spans
               ) values (%s, %s, %s, %s, %s)""",
            (
                attempt_id,
                canonical_passage_id,
                "Synthetic faith and hope.",
                "e" * 64,
                Jsonb([{"resource": "synthetic", "start": 0, "end": 25}]),
            ),
        )
        connection.execute(
            """update passage.corpus_versions
               set state = 'validated', validated_at = statement_timestamp()
               where attempt_id = %s""",
            (attempt_id,),
        )
        connection.execute(
            """update passage.corpus_versions
               set state = 'accepted', accepted_at = statement_timestamp()
               where attempt_id = %s""",
            (attempt_id,),
        )
        connection.execute(
            """insert into passage.retrieval_configurations(
                   config_id, corpus_attempt_id, backend, configuration
               ) values (%s, %s, 'postgresql', %s)""",
            (config_id, attempt_id, Jsonb({"lexical": "postgresql-english-v1"})),
        )
        connection.execute(
            """insert into passage.retrieval_snapshots(
                   snapshot_id, corpus_attempt_id, corpus_version,
                   retrieval_config_id, official_edge_set_id,
                   derived_graph_version, relationship_vocabulary_version,
                   vector_config_id, publication_policy_id
               ) values (%s, %s, %s, %s, %s, 'none', 'none', 'none', 'evidence-v1')""",
            (snapshot_id, attempt_id, corpus_version, config_id, f"official-{token}"),
        )
        connection.execute(
            """insert into passage.active_snapshot(singleton, snapshot_id)
               values (true, %s)""",
            (snapshot_id,),
        )

    return AcceptedSnapshotFixture(
        attempt_id=attempt_id,
        corpus_version=corpus_version,
        canonical_passage_id=canonical_passage_id,
        snapshot_id=snapshot_id,
    )
