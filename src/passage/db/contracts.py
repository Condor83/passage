from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol, Self

from passage.domain.models import (
    LexicalMode,
    Passage,
    ReferenceEdge,
    SearchFilters,
    SnapshotSelector,
)


@dataclass(frozen=True, slots=True)
class LexicalQuery:
    text: str
    mode: LexicalMode
    near_distance: int | None = None


@dataclass(frozen=True, slots=True)
class RepositorySearchHit:
    reference: str
    passage: Passage
    raw_score: float


@dataclass(frozen=True, slots=True)
class RepositorySearchPage:
    hits: list[RepositorySearchHit]
    has_more: bool


class ActiveSnapshot(Protocol):
    @property
    def corpus_version(self) -> str: ...

    @property
    def retrieval_config(self) -> str: ...


class AcceptedSnapshot(Protocol):
    @property
    def corpus_version(self) -> str: ...

    @property
    def retrieval_config(self) -> str: ...

    @property
    def manifest(self) -> dict[str, Any]: ...

    @property
    def accepted_at(self) -> datetime: ...


class ControlState(Protocol):
    def get_active(self) -> ActiveSnapshot | None: ...
    def get_accepted(self, corpus_version: str) -> AcceptedSnapshot | None: ...

    def get_config(self, config_id: str) -> dict[str, Any] | None: ...


class EvidenceRepository(Protocol):
    corpus_version: str
    retrieval_config: str

    def close(self) -> None: ...

    def get_passage(self, reference: str) -> Passage: ...

    def get_context(self, reference: str, before: int, after: int) -> list[Passage]: ...

    def search_lexical(
        self,
        query: LexicalQuery,
        filters: SearchFilters | None,
        after: tuple[float, int] | None,
        limit: int,
    ) -> RepositorySearchPage: ...

    def all_edges(self) -> list[ReferenceEdge]: ...

    def passage_count(self) -> int: ...


class RepositorySessionFactory(Protocol):
    def __call__(self, corpus_version: str, retrieval_config: str) -> EvidenceRepository: ...


class SnapshotSession(Protocol):
    accepted: AcceptedSnapshot
    config: dict[str, object]
    repository: EvidenceRepository

    @property
    def corpus_version(self) -> str: ...

    @property
    def retrieval_config(self) -> str: ...

    def __enter__(self) -> Self: ...

    def __exit__(self, *exc_info: object) -> None: ...


class SnapshotProvider(Protocol):
    def pin(self, selector: SnapshotSelector) -> SnapshotSession: ...
