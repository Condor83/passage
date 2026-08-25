from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from importlib.resources import files
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal
from zipfile import ZipFile

import pdfplumber
from pydantic import Field, model_validator

from passage.domain.identifiers import BOOK_SLUG_SET, NEW_TESTAMENT_BOOK_SLUG_SET
from passage.domain.models import (
    EpubSourceSpan,
    InternalChapterReferenceTarget,
    InternalReferenceTarget,
    PdfSourceSpan,
    StrictModel,
)
from passage.ingest.apparatus import (
    CHURCH_PDF_REFERENCE_GRAMMAR_VERSION,
    OFFICIAL_REFERENCE_GRAMMAR_VERSION,
)
from passage.ingest.base import ExtractionResult

if TYPE_CHECKING:
    from passage.ingest.normalize import NormalizedCorpus


class StructureManifest(StrictModel):
    schema_version: int = Field(ge=1)
    work: Literal["bofm", "nt"] = "bofm"
    source: dict[str, Any]
    books: dict[str, list[int]]

    @model_validator(mode="after")
    def validate_books(self) -> StructureManifest:
        if not self.books:
            raise ValueError("structure manifest contains no books")
        allowed = BOOK_SLUG_SET if self.work == "bofm" else NEW_TESTAMENT_BOOK_SLUG_SET
        unknown = set(self.books) - allowed
        if unknown:
            raise ValueError(f"unknown books in structure manifest: {sorted(unknown)}")
        for slug, counts in self.books.items():
            if not counts or any(count < 1 for count in counts):
                raise ValueError(f"invalid chapter counts for {slug}")
        return self

    def expected_references(self) -> list[str]:
        references: list[str] = []
        for book, counts in self.books.items():
            for chapter, verse_count in enumerate(counts, start=1):
                references.extend(
                    f"{self.work}/{book}/{chapter}/{verse}" for verse in range(1, verse_count + 1)
                )
        return references


class ValidationFinding(StrictModel):
    code: str
    message: str
    references: list[str] = Field(default_factory=list)


class CorpusValidationError(ValueError):
    def __init__(self, findings: list[ValidationFinding]) -> None:
        self.findings = findings
        super().__init__(f"corpus validation failed with {len(findings)} finding(s)")


def load_default_structure_manifest() -> StructureManifest:
    resource = files("passage").joinpath("data/book_of_mormon_structure.json")
    return StructureManifest.model_validate_json(resource.read_text(encoding="utf-8"))


def load_new_testament_structure_manifest() -> StructureManifest:
    resource = files("passage").joinpath("data/new_testament_structure.json")
    return StructureManifest.model_validate_json(resource.read_text(encoding="utf-8"))


def validate_corpus(corpus: NormalizedCorpus, structure: StructureManifest) -> None:
    findings: list[ValidationFinding] = []
    expected = structure.expected_references()
    expected_set = set(expected)
    actual = [passage.reference for passage in corpus.passages]
    counts = Counter(actual)
    duplicates = sorted(reference for reference, count in counts.items() if count > 1)
    missing = sorted(expected_set - set(actual))
    extra = sorted(set(actual) - expected_set)
    if duplicates:
        findings.append(
            ValidationFinding(
                code="duplicate_passage",
                message="canonical references are duplicated",
                references=duplicates,
            )
        )
    if missing:
        findings.append(
            ValidationFinding(
                code="missing_passage",
                message="canonical structure is incomplete",
                references=missing,
            )
        )
    if extra:
        findings.append(
            ValidationFinding(
                code="unexpected_passage",
                message="canonical structure contains unexpected passages",
                references=extra,
            )
        )
    order = {reference: index for index, reference in enumerate(expected)}
    for passage in corpus.passages:
        if passage.reference in order and passage.canonical_order != order[passage.reference]:
            findings.append(
                ValidationFinding(
                    code="wrong_canonical_order",
                    message="passage order does not match the structure manifest",
                    references=[passage.reference],
                )
            )
        expected_hash = hashlib.sha256(passage.text.encode("utf-8")).hexdigest()
        if passage.content_hash != expected_hash:
            findings.append(
                ValidationFinding(
                    code="content_hash_mismatch",
                    message="passage content hash does not match its text",
                    references=[passage.reference],
                )
            )
        if not passage.source_spans:
            findings.append(
                ValidationFinding(
                    code="missing_source_span",
                    message="passage has no retained source span",
                    references=[passage.reference],
                )
            )
    actual_set = set(actual)
    for note in corpus.notes:
        if note.origin_reference not in actual_set or not note.source_spans:
            findings.append(
                ValidationFinding(
                    code="orphan_apparatus",
                    message="apparatus note lacks an accepted origin or source span",
                    references=[note.origin_reference],
                )
            )
    edge_counts = Counter(edge.edge_id for edge in corpus.edges)
    duplicate_edges = sorted(edge_id for edge_id, count in edge_counts.items() if count > 1)
    if duplicate_edges:
        findings.append(
            ValidationFinding(
                code="duplicate_official_edge",
                message="official reference edges are duplicated",
                references=duplicate_edges,
            )
        )
    for edge in corpus.edges:
        if edge.origin_reference not in actual_set:
            findings.append(
                ValidationFinding(
                    code="orphan_edge",
                    message="reference edge origin is absent",
                    references=[edge.origin_reference],
                )
            )
        if not edge.source_spans:
            findings.append(
                ValidationFinding(
                    code="official_edge_missing_source_span",
                    message="official reference edge has no retained source span",
                    references=[edge.origin_reference],
                )
            )
        if edge.grammar_version not in {
            OFFICIAL_REFERENCE_GRAMMAR_VERSION,
            CHURCH_PDF_REFERENCE_GRAMMAR_VERSION,
        }:
            findings.append(
                ValidationFinding(
                    code="unsupported_official_reference_grammar",
                    message="official reference edge uses an unsupported grammar version",
                    references=[edge.origin_reference],
                )
            )
        if isinstance(edge.target, InternalReferenceTarget):
            target = f"bofm/{edge.target.book}/{edge.target.chapter}/{edge.target.verse}" + (
                f"-{edge.target.end_verse}" if edge.target.end_verse else ""
            )
            target_references = _expand_target(target)
            absent_targets = sorted(set(target_references) - actual_set)
            if absent_targets:
                findings.append(
                    ValidationFinding(
                        code="broken_local_edge",
                        message="reference edge target is absent",
                        references=absent_targets,
                    )
                )
        elif isinstance(edge.target, InternalChapterReferenceTarget):
            end_chapter = edge.target.end_chapter or edge.target.chapter
            absent_chapters = [
                f"bofm/{edge.target.book}/{chapter}"
                for chapter in range(edge.target.chapter, end_chapter + 1)
                if not any(
                    reference.startswith(f"bofm/{edge.target.book}/{chapter}/")
                    for reference in actual_set
                )
            ]
            if absent_chapters:
                findings.append(
                    ValidationFinding(
                        code="broken_local_edge",
                        message="reference edge chapter target is absent",
                        references=absent_chapters,
                    )
                )
    if findings:
        raise CorpusValidationError(findings)


def reconcile_source_spans(extraction: ExtractionResult) -> None:
    if extraction.source_format == "epub":
        _reconcile_epub(extraction)
    elif extraction.source_format == "pdf":
        _reconcile_pdf(extraction)
    else:
        raise CorpusValidationError(
            [ValidationFinding(code="unsupported_source", message="unknown source format")]
        )


def _reconcile_epub(extraction: ExtractionResult) -> None:
    findings: list[ValidationFinding] = []
    with ZipFile(extraction.source_path) as archive:
        records = [
            (passage.text, passage.source_spans, passage.reference)
            for passage in extraction.passages
        ] + [
            (note.text or note.anchor, note.source_spans, note.origin_reference)
            for note in extraction.notes
        ]
        for expected, spans, reference in records:
            for span in spans:
                if not isinstance(span, EpubSourceSpan):
                    findings.append(
                        ValidationFinding(
                            code="source_span_kind_mismatch",
                            message="EPUB record carries a non-EPUB source span",
                            references=[reference],
                        )
                    )
                    continue
                try:
                    source = archive.read(span.member).decode("utf-8")
                except Exception:
                    findings.append(
                        ValidationFinding(
                            code="source_span_unreadable",
                            message="EPUB source member cannot be read",
                            references=[reference],
                        )
                    )
                    continue
                observed = " ".join(source[span.start : span.end].split())
                if expected and expected not in observed:
                    findings.append(
                        ValidationFinding(
                            code="source_span_mismatch",
                            message="EPUB source span does not contain normalized content",
                            references=[reference],
                        )
                    )
        for edge in extraction.edges:
            for span in edge.source_spans:
                if not isinstance(span, EpubSourceSpan):
                    findings.append(
                        ValidationFinding(
                            code="source_span_kind_mismatch",
                            message="EPUB edge carries a non-EPUB source span",
                            references=[edge.origin_reference],
                        )
                    )
                    continue
                try:
                    source = archive.read(span.member).decode("utf-8")
                except Exception:
                    findings.append(
                        ValidationFinding(
                            code="source_span_unreadable",
                            message="EPUB edge source member cannot be read",
                            references=[edge.origin_reference],
                        )
                    )
                    continue
                observed = source[span.start : span.end]
                expected_attributes = {
                    "data-origin": edge.origin_reference,
                    "data-anchor": edge.origin_anchor,
                    "data-target": edge.target,
                    "data-source": edge.source_attribution,
                }
                if not all(
                    _raw_attribute_value(observed, name) == value
                    for name, value in expected_attributes.items()
                ):
                    findings.append(
                        ValidationFinding(
                            code="source_span_mismatch",
                            message=(
                                "EPUB edge source span does not contain its exact "
                                "relationship attributes"
                            ),
                            references=[edge.origin_reference],
                        )
                    )
    if findings:
        raise CorpusValidationError(findings)


def _reconcile_pdf(extraction: ExtractionResult) -> None:
    findings: list[ValidationFinding] = []
    with pdfplumber.open(extraction.source_path) as document:
        for expected, spans, reference in _source_expectations(extraction):
            for span in spans:
                if not isinstance(span, PdfSourceSpan) or span.page > len(document.pages):
                    findings.append(
                        ValidationFinding(
                            code="source_span_kind_mismatch",
                            message="PDF record carries an invalid PDF source span",
                            references=[reference],
                        )
                    )
                    continue
                observed = " ".join(
                    (document.pages[span.page - 1].crop(span.bbox).extract_text() or "").split()
                )
                if expected and expected not in observed:
                    findings.append(
                        ValidationFinding(
                            code="source_span_mismatch",
                            message="PDF overlay does not contain normalized content",
                            references=[reference],
                        )
                    )
    if findings:
        raise CorpusValidationError(findings)


def _source_expectations(extraction: ExtractionResult):
    for passage in extraction.passages:
        yield passage.text, passage.source_spans, passage.reference
    for note in extraction.notes:
        yield note.text or note.anchor, note.source_spans, note.origin_reference
    for edge in extraction.edges:
        yield edge.origin_anchor, edge.source_spans, edge.origin_reference


def _raw_attribute_value(start_tag: str, name: str) -> str | None:
    match = re.search(
        rf"(?:^|\s){re.escape(name)}\s*=\s*(?:\"([^\"]*)\"|'([^']*)')",
        start_tag,
    )
    if match is None:
        return None
    return match.group(1) if match.group(1) is not None else match.group(2)


def write_finding_report(path: Path, findings: list[ValidationFinding]) -> None:
    payload = {
        "status": "blocked" if findings else "accepted",
        "finding_count": len(findings),
        "findings": [finding.model_dump(mode="json") for finding in findings],
    }
    path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def _expand_target(value: str) -> list[str]:
    if "-" not in value.rsplit("/", 1)[-1]:
        return [value]
    prefix, verse_range = value.rsplit("/", 1)
    start, end = (int(part) for part in verse_range.split("-", 1))
    return [f"{prefix}/{verse}" for verse in range(start, end + 1)]
