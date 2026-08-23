from __future__ import annotations

from pathlib import Path

from pydantic import Field

from passage.domain.models import EpubSourceSpan, PdfSourceSpan, StrictModel


class ExtractionError(ValueError):
    """A source cannot be safely or unambiguously extracted."""


class ExtractionLimits(StrictModel):
    max_source_bytes: int = Field(default=100 * 1024 * 1024, ge=1)
    max_zip_members: int = Field(default=5_000, ge=1)
    max_expanded_bytes: int = Field(default=500 * 1024 * 1024, ge=1)
    max_compression_ratio: float = Field(default=100.0, gt=1)
    max_xml_nodes: int = Field(default=2_000_000, ge=1)
    max_xml_text_chars: int = Field(default=100_000_000, ge=1)
    max_pdf_pages: int = Field(default=1_000, ge=1)
    max_pdf_objects: int = Field(default=10_000_000, ge=1)
    max_pdf_chars: int = Field(default=100_000_000, ge=1)
    max_memory_bytes: int = Field(default=1_500 * 1024 * 1024, ge=1)
    wall_seconds: float = Field(default=120.0, gt=0)


class ExtractedPassage(StrictModel):
    reference: str
    text: str
    source_spans: list[EpubSourceSpan | PdfSourceSpan]


class ExtractedNote(StrictModel):
    note_id: str
    origin_reference: str
    anchor: str
    kind: str
    label: str | None = None
    text: str | None = None
    source_spans: list[EpubSourceSpan | PdfSourceSpan]


class ExtractedEdge(StrictModel):
    origin_reference: str
    origin_anchor: str
    target: str
    source_attribution: str
    source_spans: list[EpubSourceSpan | PdfSourceSpan]


class ExtractionResult(StrictModel):
    source_path: Path
    source_format: str
    profile: str
    passages: list[ExtractedPassage]
    notes: list[ExtractedNote] = Field(default_factory=list)
    edges: list[ExtractedEdge] = Field(default_factory=list)
