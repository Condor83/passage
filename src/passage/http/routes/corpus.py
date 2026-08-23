from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from passage.domain.models import CorpusMetadata, SnapshotRequest
from passage.evidence.service import EvidenceService
from passage.http.dependencies import ERROR_RESPONSES, get_evidence_service

router = APIRouter(prefix="/v1", tags=["corpus"])


@router.get(
    "/corpus",
    response_model=CorpusMetadata,
    responses=ERROR_RESPONSES,
)
async def get_corpus(
    request: Annotated[SnapshotRequest, Depends()],
    service: Annotated[EvidenceService, Depends(get_evidence_service)],
) -> CorpusMetadata:
    return service.get_corpus(request)
