from __future__ import annotations

import json
import sqlite3
import sys
from datetime import date
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.shared.memory import create_connected_server_and_client_session

from passage.db.builder import CorpusBuilder
from passage.db.control import ControlStore
from passage.domain.errors import CorpusUnavailableError
from passage.domain.models import (
    ContextRequest,
    CorpusMetadata,
    EvidenceResponse,
    EvidenceSearchRequest,
    LexicalSearchRequest,
    PassageRequest,
    SnapshotRequest,
    SourceApproval,
    TraversalRequest,
    TraversalResponse,
)
from passage.evidence.service import EvidenceService
from passage.ingest.normalize import normalize_extraction
from passage.ingest.validation import StructureManifest
from passage.mcp.server import create_server, run_stdio
from passage.mcp.tools import TOOL_DESCRIPTIONS, ToolHandlers
from tests.unit.ingest.test_validation import extraction

TOOL_NAMES = {
    "get_corpus",
    "get_passage",
    "get_context",
    "search_lexical",
    "traverse_references",
    "search_evidence",
}


def build_active_root(tmp_path: Path) -> Path:
    root = tmp_path / "private"
    manifest = StructureManifest(
        schema_version=1,
        source={},
        books={"1-ne": [4], "2-ne": [2]},
    )
    corpus = normalize_extraction(
        extraction(
            [
                ("bofm/1-ne/1/1", "Faith hope and charity."),
                ("bofm/1-ne/1/2", "Faith is things hoped for."),
                ("bofm/1-ne/1/3", "Hope and charity endure."),
                ("bofm/1-ne/1/4", "Repent and remember."),
                ("bofm/2-ne/1/1", "A faithful witness speaks."),
                ("bofm/2-ne/1/2", "Faith and hope remain."),
            ],
            [
                ("bofm/1-ne/1/1", "bofm/1-ne/1/2"),
                ("bofm/1-ne/1/1", "bible/john/3/16"),
                ("bofm/1-ne/1/2", "bofm/1-ne/1/3"),
                ("bofm/1-ne/1/3", "bofm/1-ne/1/1"),
            ],
        ),
        manifest,
    )
    approval = SourceApproval(
        source_sha256="a" * 64,
        acquisition_url="https://example.test/source.epub",
        acquisition_date=date(2026, 8, 16),
        edition="Current Church edition",
    )
    control = ControlStore(root)
    try:
        published = CorpusBuilder(root, control).build(corpus, approval, "b" * 64)
        control.activate(published.corpus_version, published.retrieval_config)
    finally:
        control.close()
    return root


@pytest.fixture
def active_root(tmp_path: Path) -> Path:
    return build_active_root(tmp_path)


class InMemoryMcpClient:
    def __init__(self, private_root: Path) -> None:
        self.server = create_server(private_root)

    async def list_tools(self):
        async with create_connected_server_and_client_session(self.server._mcp_server) as client:
            return await client.list_tools()

    async def call_tool(self, name: str, arguments: dict[str, Any]):
        async with create_connected_server_and_client_session(self.server._mcp_server) as client:
            return await client.call_tool(name, arguments)


@pytest.fixture
def mcp_client(active_root: Path) -> InMemoryMcpClient:
    return InMemoryMcpClient(active_root)


def structured(result: Any) -> dict[str, Any]:
    assert result.isError is not True
    assert result.structuredContent is not None
    return result.structuredContent


def error_envelope(result: Any) -> dict[str, Any]:
    assert result.isError is True
    assert result.structuredContent is None
    assert len(result.content) == 1
    return json.loads(result.content[0].text)


async def test_discovers_exactly_six_atomic_tools_with_shared_schemas(mcp_client) -> None:
    listed = await mcp_client.list_tools()
    tools = {tool.name: tool for tool in listed.tools}

    assert set(tools) == TOOL_NAMES
    for tool in tools.values():
        assert set(tool.inputSchema["properties"]) == {"request"}
        assert tool.inputSchema["required"] == ["request"]
        assert tool.outputSchema is not None
        assert tool.description == TOOL_DESCRIPTIONS[tool.name]

    assert "exact" in tools["get_passage"].description.lower()
    assert "neighbor" in tools["get_context"].description.lower()
    assert "lexical" in tools["search_lexical"].description.lower()
    assert "official citation" in tools["traverse_references"].description.lower()
    assert "evidence discovery" in tools["search_evidence"].description.lower()
    assert all("interpret" in tool.description.lower() for tool in tools.values())


@pytest.mark.parametrize(
    ("tool_name", "request_payload", "response_type"),
    [
        ("get_corpus", {}, CorpusMetadata),
        ("get_passage", {"reference": "bofm/1-ne/1/1"}, EvidenceResponse),
        (
            "get_context",
            {"reference": "bofm/1-ne/1/2", "before": 1, "after": 1},
            EvidenceResponse,
        ),
        ("search_lexical", {"query": "faith"}, EvidenceResponse),
        (
            "traverse_references",
            {"reference": "bofm/1-ne/1/1", "max_depth": 1},
            TraversalResponse,
        ),
        ("search_evidence", {"query": "faith charity"}, EvidenceResponse),
    ],
)
async def test_each_tool_returns_rich_structured_domain_payload(
    mcp_client,
    tool_name: str,
    request_payload: dict[str, Any],
    response_type: type,
) -> None:
    payload = structured(await mcp_client.call_tool(tool_name, {"request": request_payload}))

    response_type.model_validate(payload)
    assert payload["corpus_version"]
    assert payload["retrieval_config"]


@pytest.mark.parametrize(
    ("method_name", "request_model"),
    [
        ("get_corpus", SnapshotRequest()),
        ("get_passage", PassageRequest(reference="bofm/1-ne/1/1")),
        ("get_context", ContextRequest(reference="bofm/1-ne/1/1")),
        ("search_lexical", LexicalSearchRequest(query="faith")),
        ("traverse_references", TraversalRequest(reference="bofm/1-ne/1/1")),
        ("search_evidence", EvidenceSearchRequest(query="faith")),
    ],
)
def test_handlers_forward_one_shared_request_to_one_matching_service_method(
    method_name: str,
    request_model: object,
) -> None:
    service = Mock(spec=EvidenceService)
    expected = object()
    getattr(service, method_name).return_value = expected
    handlers = ToolHandlers(service)

    result = getattr(handlers, method_name)(request_model)

    assert result is expected
    getattr(service, method_name).assert_called_once_with(request_model)
    for other_name in TOOL_NAMES - {method_name}:
        getattr(service, other_name).assert_not_called()


@pytest.mark.parametrize(
    ("tool_name", "request_payload", "expected_code"),
    [
        (
            "get_corpus",
            {"corpus_version": "missing", "retrieval_config": "missing"},
            "version_unavailable",
        ),
        ("get_passage", {"reference": "bofm/1-ne/2/1"}, "passage_not_found"),
        ("get_context", {"reference": "bofm/1-ne/2/1"}, "passage_not_found"),
        (
            "search_lexical",
            {"query": "faith", "corpus_version": "missing", "retrieval_config": "missing"},
            "version_unavailable",
        ),
        ("traverse_references", {"reference": "bofm/1-ne/2/1"}, "passage_not_found"),
        (
            "search_evidence",
            {"query": "faith", "corpus_version": "missing", "retrieval_config": "missing"},
            "version_unavailable",
        ),
    ],
)
async def test_each_tool_returns_stable_domain_error_envelope(
    mcp_client,
    tool_name: str,
    request_payload: dict[str, Any],
    expected_code: str,
) -> None:
    envelope = error_envelope(await mcp_client.call_tool(tool_name, {"request": request_payload}))

    assert envelope["error"]["code"] == expected_code
    assert set(envelope["error"]) == {"code", "message", "detail"}


async def test_unexpected_error_is_opaque_and_never_echoes_private_or_query_text(
    active_root: Path,
) -> None:
    private_query = "private phrase that must not leak"

    class ExplodingService(EvidenceService):
        def search_evidence(self, request: EvidenceSearchRequest) -> EvidenceResponse:
            raise RuntimeError(f"source excerpt and query: {request.query}")

    server = create_server(active_root, service_factory=ExplodingService)
    async with create_connected_server_and_client_session(server._mcp_server) as client:
        result = await client.call_tool(
            "search_evidence",
            {"request": {"query": private_query}},
        )

    envelope = error_envelope(result)
    error = envelope["error"]
    assert error["code"] == "internal_error"
    assert error["message"] == "internal server error"
    assert set(error["detail"]) == {"incident_id"}
    assert len(error["detail"]["incident_id"]) == 32
    assert all(character in "0123456789abcdef" for character in error["detail"]["incident_id"])
    assert private_query not in json.dumps(envelope)


@pytest.mark.parametrize(
    ("tool_name", "request_payload", "code", "message", "fields"),
    [
        (
            "get_passage",
            {"reference": "private malformed reference"},
            "invalid_query",
            "request validation failed",
            ["reference"],
        ),
        (
            "search_lexical",
            {"query": "private query", "limit": 101},
            "limit_exceeded",
            "request exceeds a supported limit",
            ["limit"],
        ),
        (
            "search_lexical",
            {"query": "q" * 513},
            "limit_exceeded",
            "request exceeds a supported limit",
            ["query"],
        ),
        (
            "search_lexical",
            {"query": "faith", "filters": {"books": ["1-ne"] * 16}},
            "limit_exceeded",
            "request exceeds a supported limit",
            ["filters.books"],
        ),
        (
            "search_lexical",
            {
                "query": "faith",
                "filters": {"reference_ranges": ["bofm/1-ne/1/1"] * 51},
            },
            "limit_exceeded",
            "request exceeds a supported limit",
            ["filters.reference_ranges"],
        ),
    ],
)
async def test_request_validation_errors_are_sanitized_and_match_http_shape(
    mcp_client,
    tool_name: str,
    request_payload: dict[str, Any],
    code: str,
    message: str,
    fields: list[str],
) -> None:
    envelope = error_envelope(await mcp_client.call_tool(tool_name, {"request": request_payload}))

    assert envelope == {
        "error": {
            "code": code,
            "message": message,
            "detail": {"fields": fields},
        }
    }
    assert all(str(value) not in json.dumps(envelope) for value in request_payload.values())


async def test_empty_search_is_a_successful_snapshot_identified_result(mcp_client) -> None:
    metadata = structured(await mcp_client.call_tool("get_corpus", {"request": {}}))
    result = await mcp_client.call_tool(
        "search_lexical",
        {
            "request": {
                "query": "unfindable",
                "corpus_version": metadata["corpus_version"],
                "retrieval_config": metadata["retrieval_config"],
            }
        },
    )
    payload = structured(result)

    assert payload["records"] == []
    assert payload["completeness"] == {"truncated": False, "cursor": None, "frontier": []}
    assert payload["corpus_version"] == metadata["corpus_version"]
    assert payload["retrieval_config"] == metadata["retrieval_config"]


async def test_model_free_agent_sequence_keeps_one_explicit_snapshot(mcp_client) -> None:
    metadata = structured(await mcp_client.call_tool("get_corpus", {"request": {}}))
    snapshot = {
        "corpus_version": metadata["corpus_version"],
        "retrieval_config": metadata["retrieval_config"],
    }
    lexical = structured(
        await mcp_client.call_tool(
            "search_lexical", {"request": {**snapshot, "query": "faith charity"}}
        )
    )
    evidence = structured(
        await mcp_client.call_tool(
            "search_evidence", {"request": {**snapshot, "query": "faith charity"}}
        )
    )
    origin = evidence["records"][0]["passage"]["reference"]
    traversal = structured(
        await mcp_client.call_tool(
            "traverse_references", {"request": {**snapshot, "reference": origin}}
        )
    )
    context = structured(
        await mcp_client.call_tool(
            "get_context",
            {"request": {**snapshot, "reference": origin, "before": 1, "after": 1}},
        )
    )

    assert lexical["records"]
    assert traversal["records"]
    assert context["records"][0]["passage"]["reference"] == origin
    assert {
        lexical["corpus_version"],
        evidence["corpus_version"],
        traversal["corpus_version"],
        context["corpus_version"],
    } == {metadata["corpus_version"]}


async def test_server_lifespan_closes_control_store_when_client_task_is_cancelled(
    active_root: Path,
) -> None:
    stores: list[TrackingControlStore] = []

    class TrackingControlStore(ControlStore):
        closed = False

        def close(self) -> None:
            super().close()
            self.closed = True

    def control_factory(root: Path) -> TrackingControlStore:
        store = TrackingControlStore(root)
        stores.append(store)
        return store

    server = create_server(active_root, control_factory=control_factory)
    async with create_connected_server_and_client_session(server._mcp_server) as client:
        await client.list_tools()

    assert len(stores) == 1
    assert stores[0].closed is True
    with pytest.raises(sqlite3.ProgrammingError):
        stores[0].connection.execute("SELECT 1")


async def test_initialization_fails_and_closes_store_without_an_active_snapshot(
    tmp_path: Path,
) -> None:
    stores: list[TrackingControlStore] = []

    class TrackingControlStore(ControlStore):
        closed = False

        def close(self) -> None:
            super().close()
            self.closed = True

    def control_factory(root: Path) -> TrackingControlStore:
        store = TrackingControlStore(root)
        stores.append(store)
        return store

    server = create_server(tmp_path / "empty", control_factory=control_factory)
    with pytest.raises(BaseExceptionGroup) as caught:
        async with create_connected_server_and_client_session(
            server._mcp_server,
            raise_exceptions=True,
        ):
            pass

    assert caught.value.subgroup(CorpusUnavailableError) is not None

    assert len(stores) == 1
    assert stores[0].closed is True
    with pytest.raises(sqlite3.ProgrammingError):
        stores[0].connection.execute("SELECT 1")


def test_server_rejects_private_root_inside_repository() -> None:
    with pytest.raises(ValueError, match="outside the repository"):
        create_server(Path.cwd() / "src")


def test_server_runner_selects_stdio_and_never_a_network_transport(active_root: Path) -> None:
    server = create_server(active_root)
    server.run = Mock()

    run_stdio(server)

    server.run.assert_called_once_with(transport="stdio")


async def test_real_stdio_session_discovers_and_calls_tools(active_root: Path) -> None:
    parameters = StdioServerParameters(
        command=sys.executable,
        args=["-m", "passage.mcp.server"],
        cwd=Path.cwd(),
        env={"PASSAGE_PRIVATE_ROOT": str(active_root)},
    )

    async with (
        stdio_client(parameters) as (read_stream, write_stream),
        ClientSession(read_stream, write_stream) as session,
    ):
        initialized = await session.initialize()
        listed = await session.list_tools()
        result = await session.call_tool("get_corpus", {"request": {}})

    assert {tool.name for tool in listed.tools} == TOOL_NAMES
    assert initialized.serverInfo.name == "passage"
    assert structured(result)["corpus_version"]
