from __future__ import annotations

import subprocess
from types import SimpleNamespace

import pytest

from tests.postgres import conftest as environment
from tests.postgres.conftest import LocalSupabaseStack, PublishedBinding


def _binding(host: str, host_port: int) -> PublishedBinding:
    return PublishedBinding(
        container="supabase_test_passage",
        container_port="5432/tcp",
        host=host,
        host_port=host_port,
    )


def test_loopback_bindings_accept_complete_local_stack() -> None:
    bindings = tuple(_binding("127.0.0.1", port) for port in environment.EXPECTED_HOST_PORTS)

    environment.assert_loopback_bindings(bindings)


@pytest.mark.parametrize("host", ["0.0.0.0", "::", "", "192.0.2.10"])
def test_loopback_bindings_reject_any_non_loopback_host(host: str) -> None:
    bindings = tuple(
        _binding(host if port == 54322 else "127.0.0.1", port)
        for port in environment.EXPECTED_HOST_PORTS
    )

    with pytest.raises(RuntimeError, match="non-loopback"):
        environment.assert_loopback_bindings(bindings)


def test_loopback_bindings_reject_missing_expected_service() -> None:
    bindings = (_binding("127.0.0.1", 54322),)

    with pytest.raises(RuntimeError, match="did not publish expected loopback ports"):
        environment.assert_loopback_bindings(bindings)


def test_loopback_bindings_reject_empty_stack() -> None:
    with pytest.raises(RuntimeError, match="published no host ports"):
        environment.assert_loopback_bindings(())


def test_binding_parser_handles_ipv4_and_ipv6() -> None:
    assert environment._parse_binding(
        "supabase_db_passage", "5432/tcp -> 127.0.0.1:54322"
    ) == PublishedBinding(
        container="supabase_db_passage",
        container_port="5432/tcp",
        host="127.0.0.1",
        host_port=54322,
    )
    assert environment._parse_binding("supabase_db_passage", "5432/tcp -> [::]:54322").host == "::"


def test_incompatible_cli_names_pinned_acquisition_command() -> None:
    with pytest.raises(RuntimeError, match=r"npx --yes supabase@2\.115\.0 --version"):
        environment.validate_supabase_version("2.114.9")


@pytest.mark.parametrize("version", ["v19.9.0", "invalid", ""])
def test_unsupported_node_version_fails_before_start(version: str) -> None:
    with pytest.raises(RuntimeError, match=r"Node\.js 20 or later"):
        environment.validate_node_version(version)


def test_quiet_commands_discard_sensitive_output(monkeypatch: pytest.MonkeyPatch) -> None:
    observed: dict[str, object] = {}

    def fake_run(*_args: object, **kwargs: object) -> SimpleNamespace:
        observed.update(kwargs)
        return SimpleNamespace(returncode=1)

    monkeypatch.setattr(environment.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError) as failure:
        environment._run_quiet(("supabase", "start"))

    assert observed["stdout"] is subprocess.DEVNULL
    assert observed["stderr"] is subprocess.DEVNULL
    assert "secret" not in str(failure.value).lower()


def test_teardown_runs_when_managed_operation_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []
    bindings = tuple(_binding("127.0.0.1", port) for port in environment.EXPECTED_HOST_PORTS)

    monkeypatch.setattr(environment, "check_prerequisites", lambda: events.append("check"))
    monkeypatch.setattr(environment, "ensure_loopback_network", lambda: events.append("network"))
    monkeypatch.setattr(environment, "start_local_supabase", lambda: events.append("start"))
    monkeypatch.setattr(environment, "project_bindings", lambda: bindings)
    monkeypatch.setattr(environment, "stop_local_supabase", lambda: events.append("stop"))

    with (
        pytest.raises(RuntimeError, match="injected failure"),
        environment.managed_local_supabase(),
    ):
        events.append("yield")
        raise RuntimeError("injected failure")

    assert events == ["check", "network", "stop", "start", "yield", "stop"]


def test_teardown_deletes_ephemeral_synthetic_database(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    commands: list[tuple[str, ...]] = []
    monkeypatch.setattr(
        environment,
        "_run_quiet",
        lambda command, **_kwargs: commands.append(command),
    )

    environment.stop_local_supabase()

    assert len(commands) == 1
    assert "--project-id" in commands[0]
    assert environment.SUPABASE_PROJECT_ID in commands[0]
    assert "--no-backup" in commands[0]


def test_live_stack_publishes_only_expected_loopback_ports(
    local_supabase_stack: LocalSupabaseStack,
) -> None:
    environment.assert_loopback_bindings(local_supabase_stack.bindings)


def test_local_migration_history_contains_phase1_foundation(
    local_supabase_stack: LocalSupabaseStack,
) -> None:
    history = environment._run_captured(
        (*environment.SUPABASE_COMMAND, "migration", "list", "--local"),
        timeout=120,
    )

    assert "20260824221345" in history


def test_local_database_advisors_report_no_error(
    local_supabase_stack: LocalSupabaseStack,
) -> None:
    environment._run_quiet(
        (
            *environment.SUPABASE_COMMAND,
            "db",
            "advisors",
            "--local",
            "--type",
            "all",
            "--level",
            "warn",
            "--fail-on",
            "error",
        ),
        timeout=120,
    )
