from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Annotated, Any, Literal

from pydantic import (
    AnyHttpUrl,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

from scripture_chat.domain.identifiers import (
    BOOK_SLUG_SET,
    CanonicalReference,
    validate_corpus_reference,
)

Identifier = Annotated[
    str,
    StringConstraints(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9._-]+$"),
]
Sha256 = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, use_enum_values=False)


class SourceFormat(StrEnum):
    EPUB = "epub"
    PDF = "pdf"


class LexicalMode(StrEnum):
    PHRASE = "phrase"
    TERMS = "terms"
    PREFIX = "prefix"
    NEAR = "near"


class Direction(StrEnum):
    OUTBOUND = "outbound"
    INBOUND = "inbound"
    BOTH = "both"


class EvidenceLane(StrEnum):
    LEXICAL = "lexical"
    OFFICIAL = "official"


class AttemptState(StrEnum):
    BUILDING = "building"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    QUARANTINED = "quarantined"


class SourceApproval(StrictModel):
    source_sha256: Sha256
    acquisition_url: AnyHttpUrl
    acquisition_date: date
    edition: Annotated[str, StringConstraints(min_length=1, max_length=200)]
    language: Annotated[str, StringConstraints(pattern=r"^[a-z]{3}$")] = "eng"


class BuildIdentity(StrictModel):
    approval: SourceApproval
    source_profile: Identifier
    recipe_fingerprint: Sha256
    normalized_digest: Sha256
    artifact_digest: Sha256


class SnapshotSelector(StrictModel):
    corpus_version: Identifier | None = None
    retrieval_config: Identifier | None = None

    @model_validator(mode="after")
    def require_pair(self) -> SnapshotSelector:
        if (self.corpus_version is None) != (self.retrieval_config is None):
            raise ValueError("corpus_version and retrieval_config must be supplied together")
        return self


class SearchFilters(StrictModel):
    books: list[str] | None = None
    reference_ranges: list[str] | None = None

    @field_validator("books")
    @classmethod
    def validate_books(cls, books: list[str] | None) -> list[str] | None:
        if books is None:
            return None
        if not 1 <= len(books) <= 15:
            raise ValueError("books must contain 1-15 entries")
        if len(set(books)) != len(books):
            raise ValueError("books must be unique")
        unknown = set(books) - BOOK_SLUG_SET
        if unknown:
            raise ValueError(f"unknown canonical book slugs: {sorted(unknown)}")
        return books

    @field_validator("reference_ranges")
    @classmethod
    def validate_ranges(cls, ranges: list[str] | None) -> list[str] | None:
        if ranges is None:
            return None
        if not 1 <= len(ranges) <= 50:
            raise ValueError("reference_ranges must contain 1-50 entries")
        if len(set(ranges)) != len(ranges):
            raise ValueError("reference_ranges must be unique")
        for value in ranges:
            CanonicalReference.parse(value)
        return ranges


class SnapshotRequest(SnapshotSelector):
    pass


class PassageRequest(SnapshotSelector):
    reference: str

    @field_validator("reference")
    @classmethod
    def validate_reference(cls, value: str) -> str:
        CanonicalReference.parse(value)
        return value


class ContextRequest(PassageRequest):
    before: int = Field(default=3, ge=0, le=20)
    after: int = Field(default=3, ge=0, le=20)

    @model_validator(mode="after")
    def validate_window(self) -> ContextRequest:
        if self.before + self.after > 40:
            raise ValueError("context window may contain at most 40 neighbors")
        return self


class SearchRequest(SnapshotSelector):
    query: Annotated[str, StringConstraints(min_length=1, max_length=512, strip_whitespace=True)]
    filters: SearchFilters | None = None
    limit: int = Field(default=20, ge=1, le=100)
    cursor: Annotated[str, StringConstraints(min_length=1, max_length=4096)] | None = None


class LexicalSearchRequest(SearchRequest):
    mode: LexicalMode = LexicalMode.TERMS
    near_distance: int | None = Field(default=None, ge=1, le=20)

    @model_validator(mode="after")
    def validate_near_distance(self) -> LexicalSearchRequest:
        if self.mode is LexicalMode.NEAR and self.near_distance is None:
            object.__setattr__(self, "near_distance", 5)
        elif self.mode is not LexicalMode.NEAR and self.near_distance is not None:
            raise ValueError("near_distance is valid only in near mode")
        return self


class TraversalRequest(PassageRequest):
    direction: Direction = Direction.OUTBOUND
    max_depth: int = Field(default=1, ge=0, le=3)
    max_nodes: int = Field(default=50, ge=1, le=200)
    include_external: bool = True


class EvidenceSearchRequest(SearchRequest):
    lanes: list[EvidenceLane] = Field(
        default_factory=lambda: [EvidenceLane.LEXICAL, EvidenceLane.OFFICIAL]
    )
    official_depth: int = Field(default=1, ge=0, le=3)

    @field_validator("lanes")
    @classmethod
    def validate_lanes(cls, lanes: list[EvidenceLane]) -> list[EvidenceLane]:
        if lanes not in (
            [EvidenceLane.LEXICAL],
            [EvidenceLane.LEXICAL, EvidenceLane.OFFICIAL],
        ):
            raise ValueError('lanes must be ["lexical"] or ["lexical", "official"] in that order')
        return lanes


class EpubSourceSpan(StrictModel):
    kind: Literal["epub"] = "epub"
    member: str
    fragment: str | None = None
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    order: int = Field(ge=0)


class PdfSourceSpan(StrictModel):
    kind: Literal["pdf"] = "pdf"
    page: int = Field(ge=1)
    bbox: tuple[float, float, float, float]
    order: int = Field(ge=0)


SourceSpan = EpubSourceSpan | PdfSourceSpan


class Passage(StrictModel):
    reference: str
    text: str
    canonical_order: int = Field(ge=0)
    content_hash: Sha256
    source_spans: list[SourceSpan]

    @field_validator("reference")
    @classmethod
    def validate_passage_reference(cls, value: str) -> str:
        _work, _book, _chapter, _verse, end_verse = validate_corpus_reference(value)
        if end_verse is not None:
            raise ValueError("a passage reference must identify one verse")
        return value


class ApparatusNote(StrictModel):
    note_id: Identifier
    origin_reference: str
    anchor: str
    label: str | None = None
    text: str | None = None
    note_kind: Identifier
    source_spans: list[SourceSpan]


class ReferenceTarget(StrictModel):
    work: Identifier
    book: str
    chapter: int = Field(ge=1)
    verse: int = Field(ge=1)
    end_verse: int | None = Field(default=None, ge=1)
    label: str | None = None
    in_corpus: bool


class ReferenceEdge(StrictModel):
    edge_id: Identifier
    origin_reference: str
    origin_anchor: str
    target: ReferenceTarget
    source_attribution: str


class Completeness(StrictModel):
    truncated: bool = False
    cursor: str | None = None
    frontier: list[str] = Field(default_factory=list)


class RetrievalBasis(StrictModel):
    lane: EvidenceLane
    match_kind: str
    raw_score: float | None = None
    score_components: dict[str, float] = Field(default_factory=dict)
    tie_break: int
    relationship_path: list[str] = Field(default_factory=list)


class EvidenceRecord(StrictModel):
    passage: Passage
    context: list[Passage] = Field(default_factory=list)
    corpus_version: Identifier
    retrieval_config: Identifier
    applied_filters: SearchFilters | None = None
    applied_limits: dict[str, int | bool | str]
    basis: list[RetrievalBasis]
    provenance: list[SourceSpan]


class EvidenceResponse(StrictModel):
    records: list[EvidenceRecord]
    corpus_version: Identifier
    retrieval_config: Identifier
    applied: dict[str, Any]
    completeness: Completeness


class TraversalResponse(EvidenceResponse):
    external_targets: list[ReferenceTarget] = Field(default_factory=list)


class CorpusMetadata(StrictModel):
    corpus_version: Identifier
    retrieval_config: Identifier
    edition: str
    language: str
    source_sha256: Sha256
    schema_version: int = Field(ge=1)
    importer_version: str
    enabled_lanes: list[EvidenceLane]
    supported_operations: list[str]
    bounds: dict[str, int]
    accepted_at: datetime
