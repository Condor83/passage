from __future__ import annotations

import json
import os
import uuid
from collections.abc import AsyncIterator, Callable, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import ContentBlock
from pydantic import ValidationError

from scripture_chat.config import AppConfig, prepare_private_root
from scripture_chat.db.control import ControlStore
from scripture_chat.domain.errors import (
    CorpusUnavailableError,
    ErrorCode,
    ScriptureChatError,
    is_limit_violation,
)
from scripture_chat.domain.models import SnapshotRequest
from scripture_chat.evidence.service import EvidenceService
from scripture_chat.mcp.tools import ToolHandlers, register_tools

PRIVATE_ROOT_ENV = "SCRIPTURE_CHAT_PRIVATE_ROOT"

ControlFactory = Callable[[Path], ControlStore]
ServiceFactory = Callable[[ControlStore], EvidenceService]
ToolCallResult = Sequence[ContentBlock] | dict[str, Any]


@dataclass(frozen=True, slots=True)
class McpRuntime:
    control: ControlStore
    service: EvidenceService
    handlers: ToolHandlers


class ScriptureChatFastMCP(FastMCP):
    async def call_tool(self, name: str, arguments: dict[str, Any]) -> ToolCallResult:
        try:
            return await super().call_tool(name, arguments)
        except Exception as exc:
            domain_error = _find_exception(exc, ScriptureChatError)
            if domain_error is not None:
                envelope = _domain_error_envelope(domain_error)
            else:
                validation_error = _find_exception(exc, ValidationError)
                if validation_error is not None:
                    envelope = _validation_error_envelope(validation_error)
                else:
                    envelope = _internal_error_envelope()
            raise ToolError(_canonical_json(envelope)) from exc


def create_server(
    private_root: Path,
    *,
    control_factory: ControlFactory = ControlStore,
    service_factory: ServiceFactory = EvidenceService,
) -> ScriptureChatFastMCP:
    config = AppConfig(private_root=private_root)
    root = prepare_private_root(config, Path.cwd())

    @asynccontextmanager
    async def lifespan(_: FastMCP) -> AsyncIterator[McpRuntime]:
        control = control_factory(root)
        try:
            active = control.get_active()
            if active is None:
                raise CorpusUnavailableError()
            service = service_factory(control)
            service.get_corpus(
                SnapshotRequest(
                    corpus_version=active.corpus_version,
                    retrieval_config=active.retrieval_config,
                )
            )
            yield McpRuntime(
                control=control,
                service=service,
                handlers=ToolHandlers(service),
            )
        finally:
            control.close()

    server = ScriptureChatFastMCP(
        name="scripture-chat",
        instructions=(
            "Retrieve local scripture evidence through atomic, snapshot-aware operations. "
            "The server returns source evidence and provenance, not doctrinal interpretation."
        ),
        lifespan=lifespan,
    )
    register_tools(server)
    return server


def run_stdio(server: FastMCP) -> None:
    server.run(transport="stdio")


def main() -> None:
    raw_root = os.environ.get(PRIVATE_ROOT_ENV)
    if raw_root is None:
        raise RuntimeError(f"{PRIVATE_ROOT_ENV} is required")
    private_root = Path(raw_root)
    if not private_root.is_absolute():
        raise RuntimeError(f"{PRIVATE_ROOT_ENV} must be an absolute path")
    run_stdio(create_server(private_root))


def _domain_error_envelope(error: ScriptureChatError) -> dict[str, Any]:
    if error.code is ErrorCode.INTERNAL_ERROR:
        return _internal_error_envelope()
    return {
        "error": {
            "code": error.code.value,
            "message": error.message,
            "detail": error.detail,
        }
    }


def _validation_error_envelope(error: ValidationError) -> dict[str, Any]:
    errors = error.errors(include_url=False, include_context=True, include_input=True)
    fields = sorted({_validation_field(tuple(item["loc"])) for item in errors})
    limit_exceeded = any(is_limit_violation(item) for item in errors)
    if limit_exceeded:
        code = ErrorCode.LIMIT_EXCEEDED
        message = "request exceeds a supported limit"
    else:
        code = ErrorCode.INVALID_QUERY
        message = "request validation failed"
    return {
        "error": {
            "code": code.value,
            "message": message,
            "detail": {"fields": fields},
        }
    }


def _validation_field(location: tuple[Any, ...]) -> str:
    parts = [str(part) for part in location]
    if parts and parts[0] in {"body", "path", "query", "request"}:
        parts.pop(0)
    return ".".join(parts) if parts else "request"


def _internal_error_envelope() -> dict[str, Any]:
    return {
        "error": {
            "code": ErrorCode.INTERNAL_ERROR.value,
            "message": "internal server error",
            "detail": {"incident_id": uuid.uuid4().hex},
        }
    }


def _find_exception[T: BaseException](
    error: BaseException,
    error_type: type[T],
) -> T | None:
    current: BaseException | None = error
    visited: set[int] = set()
    while current is not None and id(current) not in visited:
        if isinstance(current, error_type):
            return current
        visited.add(id(current))
        current = current.__cause__ or current.__context__
    return None


def _canonical_json(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


if __name__ == "__main__":
    main()
