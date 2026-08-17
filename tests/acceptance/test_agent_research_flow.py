from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from scripture_chat.config import AppConfig
from scripture_chat.http.app import create_app
from tests.mcp.test_mcp_tools import TOOL_NAMES, build_active_root, structured


def _snapshot(payload: dict) -> dict[str, str]:
    return {
        "corpus_version": payload["corpus_version"],
        "retrieval_config": payload["retrieval_config"],
    }


async def test_model_free_agent_research_flow_uses_both_real_transports(
    tmp_path: Path,
) -> None:
    root = build_active_root(tmp_path)
    app = create_app(AppConfig(private_root=root))
    with TestClient(app, base_url="http://localhost") as http:
        http_metadata = http.get("/v1/corpus").json()
        http_snapshot = _snapshot(http_metadata)
        http_lexical = http.post(
            "/v1/search/lexical",
            json={**http_snapshot, "query": "faith charity"},
        ).json()
        http_evidence = http.post(
            "/v1/evidence/search",
            json={**http_snapshot, "query": "faith charity"},
        ).json()
        origin = http_evidence["records"][0]["passage"]["reference"]
        http_traversal = http.post(
            "/v1/references/traverse",
            json={**http_snapshot, "reference": origin},
        ).json()
        http_context = http.get(
            f"/v1/passages/{origin}/context",
            params={**http_snapshot, "before": 1, "after": 1},
        ).json()

    parameters = StdioServerParameters(
        command=sys.executable,
        args=["-m", "scripture_chat.mcp.server"],
        cwd=Path.cwd(),
        env={"SCRIPTURE_CHAT_PRIVATE_ROOT": str(root)},
    )
    async with (
        stdio_client(parameters) as (read_stream, write_stream),
        ClientSession(read_stream, write_stream) as mcp,
    ):
        await mcp.initialize()
        listed = await mcp.list_tools()
        mcp_metadata = structured(await mcp.call_tool("get_corpus", {"request": {}}))
        mcp_snapshot = _snapshot(mcp_metadata)
        mcp_lexical = structured(
            await mcp.call_tool(
                "search_lexical",
                {"request": {**mcp_snapshot, "query": "faith charity"}},
            )
        )
        mcp_evidence = structured(
            await mcp.call_tool(
                "search_evidence",
                {"request": {**mcp_snapshot, "query": "faith charity"}},
            )
        )
        mcp_origin = mcp_evidence["records"][0]["passage"]["reference"]
        mcp_traversal = structured(
            await mcp.call_tool(
                "traverse_references",
                {"request": {**mcp_snapshot, "reference": mcp_origin}},
            )
        )
        mcp_context = structured(
            await mcp.call_tool(
                "get_context",
                {
                    "request": {
                        **mcp_snapshot,
                        "reference": mcp_origin,
                        "before": 1,
                        "after": 1,
                    }
                },
            )
        )

    assert {tool.name for tool in listed.tools} == TOOL_NAMES
    assert http_snapshot == mcp_snapshot
    assert http_lexical == mcp_lexical
    assert http_evidence == mcp_evidence
    assert http_traversal == mcp_traversal
    assert http_context == mcp_context
    assert http_context["records"][0]["passage"]["reference"] == origin
