from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import cast

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError

from passage.config import AppConfig
from passage.db.control import ControlStore
from passage.domain.errors import PassageError
from passage.domain.models import SnapshotRequest
from passage.evidence.service import EvidenceService
from passage.http.dependencies import (
    handle_passage_error,
    handle_request_validation_error,
    handle_unexpected_error,
)
from passage.http.routes import corpus, evidence, passages
from passage.http.security import LocalRequestSecurityMiddleware, LocalSecurityPolicy

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
        title="Passage Evidence API",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.add_middleware(LocalRequestSecurityMiddleware, policy=security_policy)
    app.add_exception_handler(
        PassageError,
        cast(ExceptionHandler, handle_passage_error),
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
