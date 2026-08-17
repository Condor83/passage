from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from scripture_chat.domain.models import (
    EvidenceResponse,
    EvidenceSearchRequest,
    LexicalSearchRequest,
    TraversalRequest,
    TraversalResponse,
)
from scripture_chat.evidence.service import EvidenceService
from scripture_chat.http.dependencies import ERROR_RESPONSES, get_evidence_service

router = APIRouter(prefix="/v1", tags=["evidence"])


@router.post(
    "/search/lexical",
    response_model=EvidenceResponse,
    responses=ERROR_RESPONSES,
)
async def search_lexical(
    request: LexicalSearchRequest,
    service: Annotated[EvidenceService, Depends(get_evidence_service)],
) -> EvidenceResponse:
    return service.search_lexical(request)


@router.post(
    "/references/traverse",
    response_model=TraversalResponse,
    responses=ERROR_RESPONSES,
)
async def traverse_references(
    request: TraversalRequest,
    service: Annotated[EvidenceService, Depends(get_evidence_service)],
) -> TraversalResponse:
    return service.traverse_references(request)


@router.post(
    "/evidence/search",
    response_model=EvidenceResponse,
    responses=ERROR_RESPONSES,
)
async def search_evidence(
    request: EvidenceSearchRequest,
    service: Annotated[EvidenceService, Depends(get_evidence_service)],
) -> EvidenceResponse:
    return service.search_evidence(request)
