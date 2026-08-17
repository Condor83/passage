from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from scripture_chat.db.control import ControlStore
from scripture_chat.domain.errors import ScriptureChatError
from scripture_chat.domain.models import (
    ContextRequest,
    EvidenceSearchRequest,
    LexicalSearchRequest,
    PassageRequest,
    SnapshotRequest,
    TraversalRequest,
)
from scripture_chat.evidence.service import EvidenceService
from tests.mcp.test_mcp_tools import InMemoryMcpClient, build_active_root


@pytest.fixture
def parity_root(tmp_path: Path) -> Path:
    return build_active_root(tmp_path)


@pytest.fixture
def parity_surfaces(parity_root: Path):
    control = ControlStore(parity_root)
    try:
        yield EvidenceService(control), InMemoryMcpClient(parity_root)
    finally:
        control.close()


def normalized_mcp_result(result: Any) -> dict[str, Any]:
    assert result.isError is not True
    assert result.structuredContent is not None
    return result.structuredContent


def normalized_mcp_error(result: Any) -> dict[str, Any]:
    assert result.isError is True
    assert result.structuredContent is None
    return json.loads(result.content[0].text)


def documented_error_shape(error: ScriptureChatError) -> dict[str, Any]:
    return {
        "error": {
            "code": error.code.value,
            "message": error.message,
            "detail": error.detail,
        }
    }


@pytest.mark.parametrize(
    ("tool_name", "request_model", "request_payload", "service_call"),
    [
        ("get_corpus", SnapshotRequest, {}, EvidenceService.get_corpus),
        (
            "get_passage",
            PassageRequest,
            {"reference": "bofm/1-ne/1/1"},
            EvidenceService.get_passage,
        ),
        (
            "get_context",
            ContextRequest,
            {"reference": "bofm/1-ne/1/2", "before": 1, "after": 1},
            EvidenceService.get_context,
        ),
        (
            "search_lexical",
            LexicalSearchRequest,
            {"query": "faith charity", "limit": 2},
            EvidenceService.search_lexical,
        ),
        (
            "traverse_references",
            TraversalRequest,
            {"reference": "bofm/1-ne/1/1", "max_depth": 2, "max_nodes": 2},
            EvidenceService.traverse_references,
        ),
        (
            "search_evidence",
            EvidenceSearchRequest,
            {"query": "faith charity", "limit": 2},
            EvidenceService.search_evidence,
        ),
    ],
)
async def test_success_payload_matches_shared_http_domain_contract_fixture(
    parity_surfaces,
    tool_name: str,
    request_model: type,
    request_payload: dict[str, Any],
    service_call: Callable,
) -> None:
    service, client = parity_surfaces
    metadata = service.get_corpus(SnapshotRequest())
    pinned_payload = {
        **request_payload,
        "corpus_version": metadata.corpus_version,
        "retrieval_config": metadata.retrieval_config,
    }
    request = request_model.model_validate(pinned_payload)
    domain_payload = service_call(service, request).model_dump(mode="json")

    mcp_result = await client.call_tool(tool_name, {"request": pinned_payload})

    assert normalized_mcp_result(mcp_result) == domain_payload


@pytest.mark.parametrize(
    ("tool_name", "request_model", "request_payload", "service_call"),
    [
        (
            "get_corpus",
            SnapshotRequest,
            {"corpus_version": "missing", "retrieval_config": "missing"},
            EvidenceService.get_corpus,
        ),
        (
            "get_passage",
            PassageRequest,
            {"reference": "bofm/1-ne/2/1"},
            EvidenceService.get_passage,
        ),
        (
            "get_context",
            ContextRequest,
            {"reference": "bofm/1-ne/2/1"},
            EvidenceService.get_context,
        ),
        (
            "search_lexical",
            LexicalSearchRequest,
            {"query": "faith", "corpus_version": "missing", "retrieval_config": "missing"},
            EvidenceService.search_lexical,
        ),
        (
            "traverse_references",
            TraversalRequest,
            {"reference": "bofm/1-ne/2/1"},
            EvidenceService.traverse_references,
        ),
        (
            "search_evidence",
            EvidenceSearchRequest,
            {"query": "faith", "corpus_version": "missing", "retrieval_config": "missing"},
            EvidenceService.search_evidence,
        ),
    ],
)
async def test_error_payload_matches_documented_http_domain_contract_fixture(
    parity_surfaces,
    tool_name: str,
    request_model: type,
    request_payload: dict[str, Any],
    service_call: Callable,
) -> None:
    service, client = parity_surfaces
    request = request_model.model_validate(request_payload)
    with pytest.raises(ScriptureChatError) as caught:
        service_call(service, request)

    mcp_result = await client.call_tool(tool_name, {"request": request_payload})

    assert normalized_mcp_error(mcp_result) == documented_error_shape(caught.value)
