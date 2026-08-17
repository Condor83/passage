from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from mcp.server.fastmcp import Context as FastMCPContext
from mcp.server.fastmcp import FastMCP

from scripture_chat.domain.models import (
    ContextRequest,
    CorpusMetadata,
    EvidenceResponse,
    EvidenceSearchRequest,
    LexicalSearchRequest,
    PassageRequest,
    SnapshotRequest,
    TraversalRequest,
    TraversalResponse,
)
from scripture_chat.evidence.service import EvidenceService

TOOL_DESCRIPTIONS = {
    "get_corpus": (
        "Return corpus and retrieval-configuration metadata for snapshot selection. "
        "This reports available evidence operations and bounds; it does not interpret "
        "or synthesize scripture."
    ),
    "get_passage": (
        "Perform an exact canonical passage lookup with provenance in one pinned snapshot. "
        "This retrieves source evidence; it does not interpret or synthesize the passage."
    ),
    "get_context": (
        "Retrieve bounded ordered neighboring passages around an exact canonical reference. "
        "This supplies source context; it does not interpret or synthesize meaning."
    ),
    "search_lexical": (
        "Run literal lexical matching in phrase, terms, prefix, or NEAR mode with "
        "explicit match basis and completeness. This does not add semantic aliases, "
        "interpret, or synthesize results."
    ),
    "traverse_references": (
        "Traverse bounded official citation links from an exact canonical passage and "
        "return paths, external targets, and frontier. Citations are source evidence, "
        "not interpretation or synthesis."
    ),
    "search_evidence": (
        "Perform ranked evidence discovery through the explicitly selected lexical and official "
        "citation lanes, returning provenance and ranking components. This finds evidence; it does "
        "not interpret or synthesize an answer."
    ),
}


@dataclass(frozen=True, slots=True)
class ToolHandlers:
    service: EvidenceService

    def get_corpus(self, request: SnapshotRequest) -> CorpusMetadata:
        return self.service.get_corpus(request)

    def get_passage(self, request: PassageRequest) -> EvidenceResponse:
        return self.service.get_passage(request)

    def get_context(self, request: ContextRequest) -> EvidenceResponse:
        return self.service.get_context(request)

    def search_lexical(self, request: LexicalSearchRequest) -> EvidenceResponse:
        return self.service.search_lexical(request)

    def traverse_references(self, request: TraversalRequest) -> TraversalResponse:
        return self.service.traverse_references(request)

    def search_evidence(self, request: EvidenceSearchRequest) -> EvidenceResponse:
        return self.service.search_evidence(request)


HandlerResolver = Callable[[FastMCPContext], ToolHandlers]


def register_tools(
    server: FastMCP,
    resolve_handlers: HandlerResolver | None = None,
) -> None:
    resolver = resolve_handlers or _resolve_lifespan_handlers

    @server.tool(
        name="get_corpus",
        description=TOOL_DESCRIPTIONS["get_corpus"],
        structured_output=True,
    )
    def get_corpus(request: SnapshotRequest, ctx: FastMCPContext) -> CorpusMetadata:
        return resolver(ctx).get_corpus(request)

    @server.tool(
        name="get_passage",
        description=TOOL_DESCRIPTIONS["get_passage"],
        structured_output=True,
    )
    def get_passage(request: PassageRequest, ctx: FastMCPContext) -> EvidenceResponse:
        return resolver(ctx).get_passage(request)

    @server.tool(
        name="get_context",
        description=TOOL_DESCRIPTIONS["get_context"],
        structured_output=True,
    )
    def get_context(request: ContextRequest, ctx: FastMCPContext) -> EvidenceResponse:
        return resolver(ctx).get_context(request)

    @server.tool(
        name="search_lexical",
        description=TOOL_DESCRIPTIONS["search_lexical"],
        structured_output=True,
    )
    def search_lexical(request: LexicalSearchRequest, ctx: FastMCPContext) -> EvidenceResponse:
        return resolver(ctx).search_lexical(request)

    @server.tool(
        name="traverse_references",
        description=TOOL_DESCRIPTIONS["traverse_references"],
        structured_output=True,
    )
    def traverse_references(
        request: TraversalRequest,
        ctx: FastMCPContext,
    ) -> TraversalResponse:
        return resolver(ctx).traverse_references(request)

    @server.tool(
        name="search_evidence",
        description=TOOL_DESCRIPTIONS["search_evidence"],
        structured_output=True,
    )
    def search_evidence(
        request: EvidenceSearchRequest,
        ctx: FastMCPContext,
    ) -> EvidenceResponse:
        return resolver(ctx).search_evidence(request)


def _resolve_lifespan_handlers(ctx: FastMCPContext) -> ToolHandlers:
    runtime = ctx.request_context.lifespan_context
    handlers = getattr(runtime, "handlers", None)
    if not isinstance(handlers, ToolHandlers):
        raise RuntimeError("MCP tool runtime is unavailable")
    return handlers
