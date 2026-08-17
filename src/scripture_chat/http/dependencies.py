from __future__ import annotations

import uuid
from collections.abc import Mapping
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from scripture_chat.domain.errors import ErrorCode, ScriptureChatError, is_limit_violation
from scripture_chat.evidence.service import EvidenceService


class HttpErrorDetail(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    code: ErrorCode
    message: str
    detail: dict[str, Any] | None = None


class HttpErrorEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    error: HttpErrorDetail


ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {"model": HttpErrorEnvelope, "description": "Invalid request or exceeded limit"},
    403: {"model": HttpErrorEnvelope, "description": "Request origin is not allowed"},
    404: {"model": HttpErrorEnvelope, "description": "Requested passage or version not found"},
    409: {"model": HttpErrorEnvelope, "description": "Snapshot configuration unavailable"},
    500: {"model": HttpErrorEnvelope, "description": "Opaque internal error"},
    503: {"model": HttpErrorEnvelope, "description": "No usable corpus is active"},
    "4XX": {"model": HttpErrorEnvelope, "description": "Typed client error"},
}

_STATUS_BY_CODE = {
    ErrorCode.INVALID_REFERENCE: 400,
    ErrorCode.INVALID_QUERY: 400,
    ErrorCode.LIMIT_EXCEEDED: 400,
    ErrorCode.PASSAGE_NOT_FOUND: 404,
    ErrorCode.VERSION_UNAVAILABLE: 404,
    ErrorCode.CORPUS_UNAVAILABLE: 503,
    ErrorCode.CONFIG_UNAVAILABLE: 409,
    ErrorCode.INTERNAL_ERROR: 500,
}


def get_evidence_service(request: Request) -> EvidenceService:
    return request.app.state.evidence_service


async def handle_scripture_chat_error(
    _request: Request,
    error: ScriptureChatError,
) -> JSONResponse:
    if error.code is ErrorCode.INTERNAL_ERROR:
        return internal_error_response()
    return error_response(
        status_code=_STATUS_BY_CODE[error.code],
        code=error.code,
        message=error.message,
        detail=error.detail,
    )


async def handle_request_validation_error(
    _request: Request,
    error: RequestValidationError,
) -> JSONResponse:
    errors = error.errors()
    limit_exceeded = any(is_limit_violation(item) for item in errors)
    code = ErrorCode.LIMIT_EXCEEDED if limit_exceeded else ErrorCode.INVALID_QUERY
    message = "request exceeds a supported limit" if limit_exceeded else "request validation failed"
    fields = sorted({_validation_field(item) for item in errors})
    return error_response(
        status_code=400,
        code=code,
        message=message,
        detail={"fields": fields},
    )


async def handle_unexpected_error(_request: Request, _error: Exception) -> JSONResponse:
    return internal_error_response()


def error_response(
    *,
    status_code: int,
    code: ErrorCode,
    message: str,
    detail: dict[str, Any] | None = None,
) -> JSONResponse:
    envelope = HttpErrorEnvelope(error=HttpErrorDetail(code=code, message=message, detail=detail))
    return JSONResponse(
        status_code=status_code,
        content=envelope.model_dump(mode="json"),
        headers={"X-Content-Type-Options": "nosniff"},
    )


def internal_error_response() -> JSONResponse:
    return error_response(
        status_code=500,
        code=ErrorCode.INTERNAL_ERROR,
        message="internal server error",
        detail={"incident_id": uuid.uuid4().hex},
    )


def _validation_field(error: Mapping[str, Any]) -> str:
    parts = [str(part) for part in error.get("loc", ())]
    if parts and parts[0] in {"body", "query", "path"}:
        parts.pop(0)
    return ".".join(parts) or "request"
