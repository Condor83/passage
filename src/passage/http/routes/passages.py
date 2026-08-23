from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from passage.domain.models import ContextRequest, EvidenceResponse, PassageRequest
from passage.evidence.service import EvidenceService
from passage.http.dependencies import ERROR_RESPONSES, get_evidence_service

router = APIRouter(prefix="/v1/passages", tags=["passages"])


@router.get(
    "/{reference:path}/context",
    response_model=EvidenceResponse,
    responses=ERROR_RESPONSES,
)
async def get_context(
    request: Annotated[ContextRequest, Depends()],
    service: Annotated[EvidenceService, Depends(get_evidence_service)],
) -> EvidenceResponse:
    return service.get_context(request)


@router.get(
    "/{reference:path}",
    response_model=EvidenceResponse,
    responses=ERROR_RESPONSES,
)
async def get_passage(
    request: Annotated[PassageRequest, Depends()],
    service: Annotated[EvidenceService, Depends(get_evidence_service)],
) -> EvidenceResponse:
    return service.get_passage(request)
