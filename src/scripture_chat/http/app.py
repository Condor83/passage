from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import cast

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError

from scripture_chat.config import AppConfig
from scripture_chat.db.control import ControlStore
from scripture_chat.domain.errors import ScriptureChatError
from scripture_chat.domain.models import SnapshotRequest
from scripture_chat.evidence.service import EvidenceService
from scripture_chat.http.dependencies import (
    handle_request_validation_error,
    handle_scripture_chat_error,
    handle_unexpected_error,
)
from scripture_chat.http.routes import corpus, evidence, passages
from scripture_chat.http.security import LocalRequestSecurityMiddleware, LocalSecurityPolicy

ControlStoreFactory = Callable[[Path], ControlStore]
EvidenceServiceFactory = Callable[[ControlStore], EvidenceService]
ExceptionHandler = Callable[[Request, Exception], Response | Awaitable[Response]]


def create_app(
    config: AppConfig,
    *,
    control_store_factory: ControlStoreFactory = ControlStore,
    evidence_service_factory: EvidenceServiceFactory = EvidenceService,
) -> FastAPI:
    security_policy = LocalSecurityPolicy.from_config(config)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        control: ControlStore | None = None
        try:
            control = control_store_factory(config.private_root)
            app.state.control_store = control
            service = evidence_service_factory(control)
            app.state.evidence_service = service
            service.get_corpus(SnapshotRequest())
            yield
        finally:
            if control is not None:
                control.close()

    app = FastAPI(
        title="Scripture Chat Evidence API",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.add_middleware(LocalRequestSecurityMiddleware, policy=security_policy)
    app.add_exception_handler(
        ScriptureChatError,
        cast(ExceptionHandler, handle_scripture_chat_error),
    )
    app.add_exception_handler(
        RequestValidationError,
        cast(ExceptionHandler, handle_request_validation_error),
    )
    app.add_exception_handler(Exception, handle_unexpected_error)

    app.include_router(corpus.router)
    app.include_router(passages.router)
    app.include_router(evidence.router)
    return app
