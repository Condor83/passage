from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import pdfplumber
from pydantic import Field, model_validator

from scripture_chat.config import AppConfig, create_private_file, prepare_private_root
from scripture_chat.domain.identifiers import validate_corpus_reference
from scripture_chat.domain.models import (
    EpubSourceSpan,
    Identifier,
    PdfSourceSpan,
    Sha256,
    StrictModel,
)
from scripture_chat.ingest.base import (
    ExtractedNote,
    ExtractedPassage,
    ExtractionError,
    ExtractionLimits,
    ExtractionResult,
)
from scripture_chat.ingest.validation import StructureManifest, ValidationFinding

DATALAB_PROFILES = {
    "bofm": "church-book-of-mormon-datalab-marker-v1",
    "nt": "church-new-testament-datalab-marker-v1",
}

_BOOK_TITLES = {
    "THE FIRST BOOK OF NEPHI": "1-ne",
    "THE SECOND BOOK OF NEPHI": "2-ne",
    "THE BOOK OF JACOB": "jacob",
    "THE BOOK OF ENOS": "enos",
    "THE BOOK OF JAROM": "jarom",
    "THE BOOK OF OMNI": "omni",
    "THE WORDS OF MORMON": "w-of-m",
    "THE BOOK OF MOSIAH": "mosiah",
    "THE BOOK OF ALMA": "alma",
    "THE BOOK OF HELAMAN": "hel",
    "THIRD NEPHI THE BOOK OF NEPHI": "3-ne",
    "FOURTH NEPHITHE BOOK OF NEPHI": "4-ne",
    "THE BOOK OF MORMON": "morm",
    "THE BOOK OF ETHER": "ether",
    "THE BOOK OF MORONI": "moro",
}
_NEW_TESTAMENT_BOOK_TITLES = {
    "THE GOSPEL ACCORDING TOST MATTHEW": "matt",
    "THE GOSPEL ACCORDING TOST MARK": "mark",
    "THE GOSPEL ACCORDING TOST LUKE": "luke",
    "THE GOSPEL ACCORDING TOST JOHN": "john",
    "THE ACTS OF THE APOSTLES": "acts",
    "THE EPISTLE OF PAUL THE APOSTLETO THEROMANS": "rom",
    "THE FIRST EPISTLE OFPAUL THE APOSTLE TO THECORINTHIANS": "1-cor",
    "THE SECOND EPISTLE OFPAUL THE APOSTLE TO THECORINTHIANS": "2-cor",
    "THE EPISTLE OF PAUL THE APOSTLETO THEGALATIANS": "gal",
    "THE EPISTLE OF PAUL THE APOSTLETO THEEPHESIANS": "eph",
    "THE EPISTLE OF PAUL THE APOSTLETO THEPHILIPPIANS": "philip",
    "THE EPISTLE OF PAUL THE APOSTLETO THECOLOSSIANS": "col",
    "THE FIRST EPISTLE OFPAUL THE APOSTLE TO THETHESSALONIANS": "1-thes",
    "THE SECOND EPISTLE OFPAUL THE APOSTLE TO THETHESSALONIANS": "2-thes",
    "THE FIRST EPISTLE OFPAUL THE APOSTLE TOTIMOTHY": "1-tim",
    "THE SECOND EPISTLE OFPAUL THE APOSTLE TOTIMOTHY": "2-tim",
    "THE EPISTLE OF PAUL TOTITUS": "titus",
    "THE EPISTLE OF PAUL TOPHILEMON": "philem",
    "THE EPISTLE OF PAUL THE APOSTLETO THEHEBREWS": "heb",
    "THE GENERAL EPISTLE OFJAMES": "james",
    "THE FIRST EPISTLE GENERAL OFPETER": "1-pet",
    "THE SECOND EPISTLE GENERAL OFPETER": "2-pet",
    "THE FIRST EPISTLE GENERAL OF JOHN": "1-jn",
    "THE SECOND EPISTLE OF JOHN": "2-jn",
    "THE THIRD EPISTLE OFJOHN": "3-jn",
    "THE GENERAL EPISTLE OFJUDE": "jude",
    "THE REVELATIONOF ST JOHN THE DIVINE": "rev",
}
_BOOK_TITLES_BY_WORK = {
    "bofm": _BOOK_TITLES,
    "nt": _NEW_TESTAMENT_BOOK_TITLES,
}
_CHAPTER = re.compile(r"CHAPTER (\d+)")
_LEADING_NUMBER = re.compile(
    r"^(?:\[\[verse:(?P<marked>\d{1,3})\]\]|(?P<plain>\d{1,3}))\s+"
    r"(?P<content>\S.*)$"
)
_VERSE_MARKER = re.compile(r"\[\[verse:(\d{1,3})\]\]")
_MARKER = re.compile(r"\[\[marker:([^]]+)]]")
_APPARATUS_TOKEN = re.compile(
    r"(?<!\S)(?:(?:(?:\d+)\s+)?(?P<verse>\d+)\s*(?P<numbered>[a-k])|"
    r"(?P<continuation>[b-k]))(?=\s)"
)
_APPARATUS_LABEL_ONLY = re.compile(r"(?:(?:\d+)\s+)?\d+[a-k]|[b-k]")
_APPARATUS_NUMBERED_LABEL_ONLY = re.compile(r"(?:(?:\d+)\s+)?(?P<verse>\d+)(?P<anchor>[a-k])")


class DatalabCorrectionAnchor(StrictModel):
    reference: str
    anchor: str = Field(pattern=r"^[a-k]$")


class DatalabApparatusVerseOverride(DatalabCorrectionAnchor):
    source_verse: int = Field(ge=1)


class DatalabCorrectionProfile(StrictModel):
    """Private source-specific repairs bound to exact PDF and Marker JSON bytes."""

    profile_id: Identifier
    pdf_sha256: Sha256
    datalab_json_sha256: Sha256
    false_inline_anchors: list[DatalabCorrectionAnchor] = Field(default_factory=list)
    apparatus_verse_overrides: list[DatalabApparatusVerseOverride] = Field(default_factory=list)
    verified_continuation_anchors: list[DatalabCorrectionAnchor] = Field(default_factory=list)

    @model_validator(mode="after")
    def reject_duplicate_rules(self) -> DatalabCorrectionProfile:
        collections = (
            self.false_inline_anchors,
            self.apparatus_verse_overrides,
            self.verified_continuation_anchors,
        )
        for rules in collections:
            keys = [(rule.reference, rule.anchor) for rule in rules]
            if len(keys) != len(set(keys)):
                raise ValueError("Datalab correction profile contains duplicate rules")
        return self


class DatalabRepair(StrictModel):
    extraction: ExtractionResult
    findings: list[ValidationFinding] = Field(default_factory=list)
    raw_apparatus_blocks: int = 0
    pdf_sha256: Sha256
    datalab_json_sha256: Sha256
    structure_digest: Sha256
    recipe_fingerprint: Sha256
    correction_profile_digest: Sha256 | None = None


class DatalabRepairArtifacts(StrictModel):
    directory: Path
    candidate: Path
    report: Path


def write_datalab_repair(
    private_root: Path,
    repaired: DatalabRepair,
    structure: StructureManifest,
    *,
    repository_root: Path,
) -> DatalabRepairArtifacts:
    """Write an immutable private candidate without accepting or activating it."""
    from scripture_chat.ingest.normalize import normalize_extraction, serialize_jsonl

    private_root = prepare_private_root(
        AppConfig(private_root=private_root),
        repository_root,
    )
    corpus = normalize_extraction(repaired.extraction, structure)
    report_payload = {
        "status": "review_required",
        "active": False,
        "accepted": False,
        "source_format": repaired.extraction.source_format,
        "source_profile": repaired.extraction.profile,
        "pdf_sha256": repaired.pdf_sha256,
        "datalab_json_sha256": repaired.datalab_json_sha256,
        "structure_digest": repaired.structure_digest,
        "recipe_fingerprint": repaired.recipe_fingerprint,
        "correction_profile_digest": repaired.correction_profile_digest,
        "normalized_digest": corpus.normalized_digest,
        "passage_count": len(corpus.passages),
        "note_anchor_count": len(corpus.notes),
        "edge_count": len(corpus.edges),
        "raw_apparatus_blocks": repaired.raw_apparatus_blocks,
        "finding_count": len(repaired.findings),
        "findings": [finding.model_dump(mode="json") for finding in repaired.findings],
    }
    repair_digest = hashlib.sha256(
        json.dumps(report_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    report_payload["repair_digest"] = repair_digest
    directory = private_root / "repairs" / repair_digest
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    candidate = directory / "candidate.jsonl"
    report = directory / "report.json"
    _write_immutable(candidate, serialize_jsonl(corpus))
    _write_immutable(
        report,
        (json.dumps(report_payload, sort_keys=True, indent=2) + "\n").encode("utf-8"),
    )
    return DatalabRepairArtifacts(directory=directory, candidate=candidate, report=report)


@dataclass
class _Fragment:
    page: int
    bbox: tuple[float, float, float, float]
    text: str
    width_ratio: float
    italic: bool
    rendered_page_size: tuple[float, float]


@dataclass
class _Verse:
    reference: str
    fragments: list[_Fragment] = field(default_factory=list)


@dataclass
class _RawApparatus:
    page: int
    bbox: tuple[float, float, float, float]
    html: str
    rendered_page_size: tuple[float, float]


@dataclass
class _ApparatusEntry:
    page: int
    verse: int
    anchor: str
    text: str
    raw: _RawApparatus
    explicit_verse: bool


_NoteCandidate = tuple[str, str, str, PdfSourceSpan, frozenset[int]]


class _MarkupText(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._superscript_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "sup":
            self._superscript_depth += 1
        elif tag == "br":
            self.parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag == "sup":
            self._superscript_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._superscript_depth:
            marker = data.strip()
            if marker.isdigit():
                self.parts.append(f" [[verse:{marker}]] ")
            elif marker:
                self.parts.append(f" [[marker:{marker}]] ")
        else:
            self.parts.append(data)


class _ApparatusText(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"br", "li", "p", "td", "tr"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"li", "p", "td", "tr"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


class _TableCells(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "tr":
            self._row = []
        elif tag == "td":
            if self._row is None:
                self._row = []
            self._cell = []
        elif tag == "br" and self._cell is not None:
            self._cell.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag == "td" and self._row is not None and self._cell is not None:
            self._row.append(" ".join("".join(self._cell).split()))
            self._cell = None
        elif tag == "tr" and self._row is not None:
            self.rows.append(self._row)
            self._row = None

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)


def repair_datalab_pdf(
    json_path: Path,
    pdf_path: Path,
    limits: ExtractionLimits,
    structure: StructureManifest,
    correction_profile: DatalabCorrectionProfile | None = None,
) -> DatalabRepair:
    """Repair hosted Marker JSON into a complete, inactive extraction candidate."""
    _check_file(json_path, limits.max_source_bytes, "Datalab JSON")
    _check_file(pdf_path, limits.max_source_bytes, "PDF")
    datalab_json_sha256 = _sha256_file(json_path)
    pdf_sha256 = _sha256_file(pdf_path)
    correction_profile_digest = _validate_correction_profile(
        correction_profile,
        structure,
        pdf_sha256=pdf_sha256,
        datalab_json_sha256=datalab_json_sha256,
    )
    try:
        payload = json.loads(json_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ExtractionError("malformed Datalab JSON") from exc
    pages = payload.get("children")
    if not isinstance(pages, list) or not pages:
        raise ExtractionError("Datalab JSON contains no pages")
    if len(pages) > limits.max_pdf_pages:
        raise ExtractionError("PDF page budget exceeded")

    page_sizes = _pdf_page_sizes(pdf_path, limits)
    if len(page_sizes) != len(pages):
        raise ExtractionError("Datalab and PDF page counts differ")

    parser = _DatalabParser(pdf_path, structure, page_sizes, correction_profile)
    for page_index, page in enumerate(pages):
        parser.consume_page(page_index, page)
    return parser.finish(
        pdf_sha256=pdf_sha256,
        datalab_json_sha256=datalab_json_sha256,
        structure_digest=_canonical_digest(structure.model_dump(mode="json")),
        recipe_fingerprint=_repair_recipe_fingerprint(),
        correction_profile_digest=correction_profile_digest,
    )


class _DatalabParser:
    def __init__(
        self,
        pdf_path: Path,
        structure: StructureManifest,
        page_sizes: list[tuple[float, float]],
        correction_profile: DatalabCorrectionProfile | None,
    ) -> None:
        self.pdf_path = pdf_path
        self.structure = structure
        self.book_titles = {
            _heading_key(title): slug
            for title, slug in _BOOK_TITLES_BY_WORK[structure.work].items()
        }
        self.first_book = next(iter(structure.books))
        self.page_sizes = page_sizes
        self.findings: list[ValidationFinding] = []
        self.verses: dict[str, _Verse] = {}
        self.book: str | None = None
        self.chapter: int | None = None
        self.current_verse: int | None = None
        self.pending: list[_Fragment] = []
        self.started = False
        self.raw_apparatus_blocks = 0
        self.raw_apparatus: list[_RawApparatus] = []
        self.source_order = 0
        self.false_inline_anchors = {
            (rule.reference, rule.anchor)
            for rule in (
                correction_profile.false_inline_anchors if correction_profile is not None else []
            )
        }
        self.apparatus_verse_overrides = {
            (rule.reference, rule.anchor): rule.source_verse
            for rule in (
                correction_profile.apparatus_verse_overrides
                if correction_profile is not None
                else []
            )
        }
        self.verified_continuation_anchors = {
            (rule.reference, rule.anchor)
            for rule in (
                correction_profile.verified_continuation_anchors
                if correction_profile is not None
                else []
            )
        }
        self.profile = (
            correction_profile.profile_id
            if correction_profile is not None
            else DATALAB_PROFILES[self.structure.work]
        )

    def consume_page(self, page_index: int, page: Any) -> None:
        if not isinstance(page, dict) or page.get("block_type") != "Page":
            raise ExtractionError("Datalab page tree is malformed")
        bbox = _bbox(page)
        page_width = bbox[2] - bbox[0]
        if page_width <= 0:
            raise ExtractionError("Datalab page has an invalid bounding box")
        children = page.get("children", [])
        if not isinstance(children, list):
            raise ExtractionError("Datalab page children are malformed")
        page_height = bbox[3] - bbox[1]
        for child in children:
            if not isinstance(child, dict):
                continue
            child_bbox = _bbox(child)
            kind = child.get("block_type")
            narrow_bottom_text = (
                kind == "Text"
                and (child_bbox[2] - child_bbox[0]) / page_width < 0.35
                and child_bbox[1] > bbox[1] + page_height * 0.65
            )
            if (
                kind not in {"Footnote", "ListGroup", "PageFooter", "Table"}
                and not narrow_bottom_text
            ):
                continue
            child_html = child.get("html", "")
            if not isinstance(child_html, str) or not child_html.strip():
                continue
            self.raw_apparatus_blocks += 1
            self.raw_apparatus.append(
                _RawApparatus(
                    page=page_index,
                    bbox=child_bbox,
                    html=child_html,
                    rendered_page_size=(page_width, bbox[3] - bbox[1]),
                )
            )
        for block in _visual_order(page, children):
            kind = block.get("block_type")
            if kind not in {"SectionHeader", "Text"}:
                continue
            text = _markup_text(block.get("html", ""))
            if not text:
                continue
            if kind == "SectionHeader":
                self._consume_heading(text)
                continue
            if not self.started or self.book is None or self.chapter is None:
                continue
            block_bbox = _bbox(block)
            fragment = _Fragment(
                page=page_index,
                bbox=block_bbox,
                text=text,
                width_ratio=(block_bbox[2] - block_bbox[0]) / page_width,
                italic="<i>" in str(block.get("html", "")),
                rendered_page_size=(page_width, bbox[3] - bbox[1]),
            )
            self._consume_text(fragment)

    def _consume_heading(self, text: str) -> None:
        title = _plain_text(text)
        slug = self.book_titles.get(_heading_key(title))
        if slug is not None:
            if not self.started and slug != self.first_book:
                return
            self._finalize_chapter()
            self.started = True
            self.book = slug
            self.chapter = 1 if len(self.structure.books[slug]) == 1 else None
            self.current_verse = None
            self.pending = []
            return
        match = _CHAPTER.fullmatch(title)
        if match is not None and self.started:
            self._finalize_chapter()
            self.chapter = int(match.group(1))
            self.current_verse = None
            self.pending = []

    def _consume_text(self, fragment: _Fragment) -> None:
        match = _LEADING_NUMBER.match(fragment.text)
        if match is not None:
            number = int(match.group("marked") or match.group("plain"))
            expected = 2 if self.current_verse is None else self.current_verse + 1
            if number == expected:
                if self.current_verse is None:
                    self._materialize_verse_one()
                self._add_numbered_fragment(fragment, number, match.group("content"))
                return
            if fragment.width_ratio < 0.35:
                return
        expected = 2 if self.current_verse is None else self.current_verse + 1
        marker = _VERSE_MARKER.search(fragment.text)
        plain_marker = re.search(rf"(?<!\S){expected}\s+(?=\S)", fragment.text)
        recovered_plain_marker = (
            marker is None
            and plain_marker is not None
            and self._pdf_contains_verse_number(fragment, expected)
        )
        if (marker is not None and int(marker.group(1)) == expected) or recovered_plain_marker:
            boundary = marker if marker is not None else plain_marker
            if boundary is None:  # pragma: no cover - narrowed by the branch condition
                raise AssertionError("verse boundary was not selected")
            prefix = fragment.text[: boundary.start()].strip()
            suffix = fragment.text[boundary.end() :].strip()
            if prefix:
                prefix_fragment = _Fragment(
                    page=fragment.page,
                    bbox=fragment.bbox,
                    text=prefix,
                    width_ratio=fragment.width_ratio,
                    italic=fragment.italic,
                    rendered_page_size=fragment.rendered_page_size,
                )
                if self.current_verse is None:
                    self.pending.append(prefix_fragment)
                else:
                    self._verse(self.current_verse).fragments.append(prefix_fragment)
            if self.current_verse is None:
                self._materialize_verse_one()
            self._add_numbered_fragment(fragment, expected, suffix)
            if recovered_plain_marker:
                self.findings.append(
                    ValidationFinding(
                        code="inline_verse_marker_recovered",
                        message="a plain Datalab verse marker was verified in the PDF text layer",
                        references=[self._reference(expected)],
                    )
                )
            return
        if self.current_verse is None:
            if fragment.width_ratio >= 0.35:
                self.pending.append(fragment)
            return
        if fragment.width_ratio >= 0.35:
            self._verse(self.current_verse).fragments.append(fragment)

    def _add_numbered_fragment(self, fragment: _Fragment, number: int, content: str) -> None:
        pieces: list[tuple[int, str]] = []
        current_number = number
        remaining = content
        while True:
            next_number = current_number + 1
            boundary = re.search(
                rf"\s+(?:\[\[verse:{next_number}\]\]|{next_number})\s+(?=\S)",
                remaining,
            )
            if boundary is None:
                pieces.append((current_number, remaining))
                break
            pieces.append((current_number, remaining[: boundary.start()]))
            remaining = remaining[boundary.end() :]
            current_number = next_number
        for verse_number, verse_text in pieces:
            split_fragment = _Fragment(
                page=fragment.page,
                bbox=fragment.bbox,
                text=verse_text.strip(),
                width_ratio=fragment.width_ratio,
                italic=fragment.italic,
                rendered_page_size=fragment.rendered_page_size,
            )
            self._verse(verse_number).fragments.append(split_fragment)
            self.current_verse = verse_number

    def _materialize_verse_one(self) -> None:
        if not self.pending:
            return
        start: int | None = None
        summary_seen = False
        for index, fragment in enumerate(self.pending):
            if not summary_seen:
                summary_seen = (index == 0 and fragment.italic) or _looks_like_summary(
                    fragment.text
                )
                continue
            if not _looks_like_summary(fragment.text):
                start = index
                break
        verse_fragments = self.pending[start:] if start is not None else self.pending[-1:]
        if not verse_fragments:
            verse_fragments = self.pending[-1:]
        discarded = self.pending[: -len(verse_fragments)]
        summary_continuation = bool(discarded and _looks_like_summary(discarded[-1].text))
        discarded_non_italic = (
            []
            if summary_continuation
            else [
                fragment
                for fragment in discarded
                if not fragment.italic and not _looks_like_summary(fragment.text)
            ]
        )
        if discarded_non_italic:
            reference = self._reference(1)
            self.findings.append(
                ValidationFinding(
                    code="ambiguous_verse_one_boundary",
                    message="unnumbered non-italic blocks precede the inferred verse 1 boundary",
                    references=[reference],
                )
            )
        self._verse(1).fragments.extend(verse_fragments)
        self.current_verse = 1
        self.pending = []

    def _finalize_chapter(self) -> None:
        if self.book is None or self.chapter is None:
            self.pending = []
            return
        if self.current_verse is None:
            self._materialize_verse_one()
        self.pending = []

    def _reference(self, verse: int) -> str:
        if self.book is None or self.chapter is None:
            raise ExtractionError("Datalab parser has no canonical context")
        return f"{self.structure.work}/{self.book}/{self.chapter}/{verse}"

    def _verse(self, verse: int) -> _Verse:
        reference = self._reference(verse)
        return self.verses.setdefault(reference, _Verse(reference=reference))

    def finish(
        self,
        *,
        pdf_sha256: str,
        datalab_json_sha256: str,
        structure_digest: str,
        recipe_fingerprint: str,
        correction_profile_digest: str | None,
    ) -> DatalabRepair:
        self._finalize_chapter()
        expected = self.structure.expected_references()
        actual = set(self.verses)
        if actual != set(expected):
            missing = sorted(set(expected) - actual)
            extra = sorted(actual - set(expected))
            detail = f"missing={len(missing)}, extra={len(extra)}"
            raise ExtractionError(f"Datalab repair does not match canonical structure ({detail})")

        passages: list[ExtractedPassage] = []
        note_candidates: list[_NoteCandidate] = []
        for reference in expected:
            verse = self.verses[reference]
            text_parts: list[str] = []
            anchors: list[tuple[str, str, PdfSourceSpan]] = []
            spans: list[EpubSourceSpan | PdfSourceSpan] = []
            for fragment in verse.fragments:
                span = self._span(fragment)
                spans.append(span)
                repaired, observed_markers = _extract_markers(fragment.text)
                text_parts.append(repaired)
                for marker in observed_markers:
                    canonical = chr(ord("a") + len(anchors))
                    anchors.append((canonical, marker, span))
            passage_text = " ".join(part for part in text_parts if part).strip()
            verse_pages = frozenset(fragment.page for fragment in verse.fragments)
            passages.append(
                ExtractedPassage(
                    reference=reference,
                    text=passage_text,
                    source_spans=spans,
                )
            )
            for canonical, observed_marker, span in anchors:
                if observed_marker != canonical:
                    self.findings.append(
                        ValidationFinding(
                            code="inline_anchor_repaired",
                            message=(
                                f"inline apparatus marker {observed_marker!r} "
                                f"normalized to {canonical!r}"
                            ),
                            references=[reference],
                        )
                    )
                note_id = hashlib.sha256(f"{reference}\x1f{canonical}".encode()).hexdigest()[:32]
                note_candidates.append((note_id, reference, canonical, span, verse_pages))
        notes, unmatched_notes, unmatched_entries = self._link_apparatus(note_candidates)
        if unmatched_notes:
            self.findings.append(
                ValidationFinding(
                    code="apparatus_text_unlinked",
                    message=f"{len(unmatched_notes)} inline anchors have no linked footnote text",
                    references=unmatched_notes,
                )
            )
        if unmatched_entries:
            self.findings.append(
                ValidationFinding(
                    code="apparatus_entry_unmatched",
                    message=f"{unmatched_entries} parsed footnote entries have no inline anchor",
                )
            )
        return DatalabRepair(
            extraction=ExtractionResult(
                source_path=self.pdf_path,
                source_format="pdf",
                profile=self.profile,
                passages=passages,
                notes=notes,
            ),
            findings=self.findings,
            raw_apparatus_blocks=self.raw_apparatus_blocks,
            pdf_sha256=pdf_sha256,
            datalab_json_sha256=datalab_json_sha256,
            structure_digest=structure_digest,
            recipe_fingerprint=recipe_fingerprint,
            correction_profile_digest=correction_profile_digest,
        )

    def _link_apparatus(
        self,
        candidates: list[_NoteCandidate],
    ) -> tuple[list[ExtractedNote], list[str], int]:
        entries = _parse_apparatus(self.raw_apparatus)
        available = list(entries)
        resolved: dict[str, _ApparatusEntry] = {}
        remaining: list[_NoteCandidate] = []
        profile_false_ids = {
            note_id
            for note_id, reference, anchor, _marker_span, _verse_pages in candidates
            if (reference, anchor) in self.false_inline_anchors
        }
        for note_id, reference, anchor, marker_span, verse_pages in candidates:
            if note_id in profile_false_ids:
                continue
            verse = int(reference.rsplit("/", 1)[-1])
            match_indexes = [
                index
                for index, entry in enumerate(available)
                if entry.page == marker_span.page - 1
                and entry.verse == verse
                and entry.anchor == anchor
            ]
            if match_indexes:
                resolved[note_id] = available.pop(match_indexes[0])
                continue
            match_indexes = [
                index
                for index, entry in enumerate(available)
                if entry.page in verse_pages and entry.verse == verse and entry.anchor == anchor
            ]
            if len(match_indexes) != 1:
                remaining.append((note_id, reference, anchor, marker_span, verse_pages))
                continue
            resolved[note_id] = available.pop(match_indexes[0])

        corrected_references: set[str] = set()
        still_remaining: list[_NoteCandidate] = []
        for candidate in remaining:
            note_id, reference, anchor, marker_span, verse_pages = candidate
            source_verse = self.apparatus_verse_overrides.get((reference, anchor))
            if source_verse is None:
                still_remaining.append(candidate)
                continue
            match_indexes = [
                index
                for index, entry in enumerate(available)
                if entry.verse == source_verse
                and entry.anchor == anchor
                and (entry.page == marker_span.page - 1 or entry.page in verse_pages)
            ]
            if len(match_indexes) != 1:
                still_remaining.append(candidate)
                continue
            resolved[note_id] = available.pop(match_indexes[0])
            corrected_references.add(reference)
        remaining = still_remaining
        if profile_false_ids or corrected_references:
            references = {
                reference
                for note_id, reference, _anchor, _marker_span, _verse_pages in candidates
                if note_id in profile_false_ids
            }
            references.update(corrected_references)
            self.findings.append(
                ValidationFinding(
                    code="source_profile_correction",
                    message="verified New Testament PDF OCR defects were corrected",
                    references=sorted(references),
                )
            )

        grouped: dict[tuple[int, int], list[_NoteCandidate]] = {}
        for candidate in remaining:
            key = (candidate[3].page - 1, int(candidate[1].rsplit("/", 1)[-1]))
            grouped.setdefault(key, []).append(candidate)
        for (page, verse), group in grouped.items():
            matching_entries = [
                entry for entry in available if entry.page == page and entry.verse == verse
            ]
            chapters = {candidate[1].rsplit("/", 1)[0] for candidate in group}
            if len(group) != len(matching_entries) or len(chapters) != 1:
                continue
            ordered_candidates = sorted(group, key=lambda candidate: candidate[2])
            ordered_entries = sorted(matching_entries, key=lambda entry: entry.anchor)
            for candidate, entry in zip(ordered_candidates, ordered_entries, strict=True):
                resolved[candidate[0]] = entry
            matched_ids = {id(entry) for entry in matching_entries}
            available = [entry for entry in available if id(entry) not in matched_ids]
            self.findings.append(
                ValidationFinding(
                    code="apparatus_anchor_reconciled",
                    message="apparatus anchors were reconciled by page, verse, count, and order",
                    references=sorted({candidate[1] for candidate in group}),
                )
            )

        false_positive_ids = profile_false_ids.union(
            self._pdf_false_positive_candidates(candidates, resolved)
        )
        recovered_notes, recovered_entry_ids, anchor_overrides = self._recover_missing_candidates(
            candidates,
            false_positive_ids,
            resolved,
            available,
        )
        available = [entry for entry in available if id(entry) not in recovered_entry_ids]
        assigned_anchors: dict[str, set[str]] = {}
        for note_id, reference, anchor, _span, _pages in candidates:
            if note_id not in false_positive_ids:
                assigned_anchors.setdefault(reference, set()).add(
                    anchor_overrides.get(note_id, anchor)
                )
        for note in recovered_notes:
            assigned_anchors.setdefault(note.origin_reference, set()).add(note.anchor)
        references_by_page_verse: dict[tuple[int, int], list[str]] = {}
        for reference, verse_record in self.verses.items():
            verse_number = int(reference.rsplit("/", 1)[-1])
            for page in {fragment.page for fragment in verse_record.fragments}:
                references_by_page_verse.setdefault((page, verse_number), []).append(reference)
        false_entry_ids = {
            id(entry)
            for entry in available
            if not (page_references := references_by_page_verse.get((entry.page, entry.verse), []))
            or (
                any(
                    (reference, entry.anchor) in self.false_inline_anchors
                    for reference in page_references
                )
            )
            or all(
                entry.anchor in assigned_anchors.get(reference, set())
                for reference in page_references
            )
        }
        if false_entry_ids:
            self.findings.append(
                ValidationFinding(
                    code="apparatus_entry_false_positive",
                    message=(
                        f"{len(false_entry_ids)} invalid or duplicate parsed footer entries "
                        "were ignored"
                    ),
                )
            )
            available = [entry for entry in available if id(entry) not in false_entry_ids]
        notes: list[ExtractedNote] = []
        for note_id, reference, anchor, marker_span, _verse_pages in candidates:
            if note_id in false_positive_ids:
                continue
            effective_anchor = anchor_overrides.get(note_id, anchor)
            effective_note_id = hashlib.sha256(
                f"{reference}\x1f{effective_anchor}".encode()
            ).hexdigest()[:32]
            resolved_entry = resolved.get(note_id)
            if resolved_entry is None:
                notes.append(
                    ExtractedNote(
                        note_id=effective_note_id,
                        origin_reference=reference,
                        anchor=effective_anchor,
                        kind="official-footnote-anchor",
                        label=effective_anchor,
                        text=None,
                        source_spans=[marker_span],
                    )
                )
                continue
            notes.append(
                ExtractedNote(
                    note_id=effective_note_id,
                    origin_reference=reference,
                    anchor=effective_anchor,
                    kind="official-footnote",
                    label=effective_anchor,
                    text=resolved_entry.text,
                    source_spans=[self._apparatus_span(resolved_entry.raw)],
                )
            )
        notes.extend(recovered_notes)
        reference_order = {
            reference: index for index, reference in enumerate(self.structure.expected_references())
        }
        notes.sort(key=lambda note: (reference_order[note.origin_reference], note.anchor))
        unmatched_references = sorted(
            {note.origin_reference for note in notes if note.text is None}
        )
        return notes, unmatched_references, len(available)

    def _pdf_false_positive_candidates(
        self,
        candidates: list[_NoteCandidate],
        resolved: dict[str, _ApparatusEntry],
    ) -> set[str]:
        groups: dict[tuple[str, int, tuple[float, float, float, float]], list[_NoteCandidate]] = {}
        for candidate in candidates:
            span = candidate[3]
            groups.setdefault((candidate[1], span.page, span.bbox), []).append(candidate)

        false_positive_ids: set[str] = set()
        references: set[str] = set()
        with pdfplumber.open(self.pdf_path) as document:
            for (reference, page, bbox), group in groups.items():
                unresolved = [candidate for candidate in group if candidate[0] not in resolved]
                if not unresolved:
                    continue
                chars = [
                    char
                    for char in document.pages[page - 1].chars
                    if float(char["x0"]) >= bbox[0] - 1
                    and float(char["x1"]) <= bbox[2] + 1
                    and float(char["top"]) >= bbox[1] - 8
                    and float(char["bottom"]) <= bbox[3] + 8
                ]
                superscript_count = _count_pdf_superscripts(chars, bbox)
                resolved_count = len(group) - len(unresolved)
                if resolved_count == 0 or superscript_count != resolved_count:
                    continue
                false_positive_ids.update(candidate[0] for candidate in unresolved)
                references.add(reference)
        if false_positive_ids:
            self.findings.append(
                ValidationFinding(
                    code="inline_anchor_false_positive",
                    message=(
                        f"{len(false_positive_ids)} unlinked inline markers were absent "
                        "from the PDF text layer"
                    ),
                    references=sorted(references),
                )
            )
        return false_positive_ids

    def _recover_missing_candidates(
        self,
        candidates: list[_NoteCandidate],
        false_positive_ids: set[str],
        resolved: dict[str, _ApparatusEntry],
        available: list[_ApparatusEntry],
    ) -> tuple[list[ExtractedNote], set[int], dict[str, str]]:
        reference_order = {
            reference: index for index, reference in enumerate(self.structure.expected_references())
        }
        references_by_page_verse: dict[tuple[int, int], list[str]] = {}
        for reference, verse in self.verses.items():
            verse_number = int(reference.rsplit("/", 1)[-1])
            for page in {fragment.page for fragment in verse.fragments}:
                references_by_page_verse.setdefault((page, verse_number), []).append(reference)
        for references in references_by_page_verse.values():
            references.sort(key=reference_order.__getitem__)

        entries_by_page_verse: dict[tuple[int, int], list[_ApparatusEntry]] = {}
        for entry in available:
            entries_by_page_verse.setdefault((entry.page, entry.verse), []).append(entry)

        candidate_references = {candidate[0]: candidate[1] for candidate in candidates}
        resolved_anchors: dict[str, set[str]] = {}
        for note_id, entry in resolved.items():
            resolved_anchors.setdefault(candidate_references[note_id], set()).add(entry.anchor)

        proposals: dict[str, list[_ApparatusEntry]] = {}
        for key, entries in entries_by_page_verse.items():
            references = references_by_page_verse.get(key, [])
            if len(references) == 1:
                proposals.setdefault(references[0], []).extend(entries)
                continue
            unassigned: list[_ApparatusEntry] = []
            for entry in entries:
                possible = [
                    reference
                    for reference in references
                    if entry.anchor not in resolved_anchors.get(reference, set())
                    and entry.anchor not in {item.anchor for item in proposals.get(reference, [])}
                ]
                if len(possible) == 1:
                    proposals.setdefault(possible[0], []).append(entry)
                else:
                    unassigned.append(entry)
            if (
                len(references) == len(unassigned)
                and len({entry.anchor for entry in unassigned}) == 1
            ):
                for reference, entry in zip(references, unassigned, strict=True):
                    proposals.setdefault(reference, []).append(entry)

        candidate_anchors: dict[str, set[str]] = {}
        resolved_ids_by_reference: dict[str, list[str]] = {}
        for note_id, reference, anchor, _span, _pages in candidates:
            if note_id not in false_positive_ids:
                resolved_entry = resolved.get(note_id)
                candidate_anchors.setdefault(reference, set()).add(
                    resolved_entry.anchor if resolved_entry is not None else anchor
                )
                if resolved_entry is not None:
                    resolved_ids_by_reference.setdefault(reference, []).append(note_id)

        recovered: list[ExtractedNote] = []
        recovered_entry_ids: set[int] = set()
        recovered_references: list[str] = []
        anchor_overrides: dict[str, str] = {}
        with pdfplumber.open(self.pdf_path) as document:
            for reference, proposed_entries in proposals.items():
                existing = candidate_anchors.get(reference, set())
                entries = [
                    entry
                    for entry in proposed_entries
                    if entry.anchor not in existing
                    and (reference, entry.anchor) not in self.false_inline_anchors
                ]
                combined = existing.union(entry.anchor for entry in entries)
                if any(not entry.explicit_verse for entry in entries) and (
                    self._pdf_superscript_count(document, reference) != len(combined)
                ):
                    entries = [
                        entry
                        for entry in entries
                        if entry.explicit_verse
                        or ((reference, entry.anchor) in self.verified_continuation_anchors)
                    ]
                    combined = existing.union(entry.anchor for entry in entries)
                proposed = [entry.anchor for entry in entries]
                if not entries or len(set(proposed)) != len(proposed):
                    continue
                sequential = {chr(ord("a") + index) for index in range(len(combined))}
                if combined != sequential:
                    continue
                for entry in entries:
                    note_id = hashlib.sha256(f"{reference}\x1f{entry.anchor}".encode()).hexdigest()[
                        :32
                    ]
                    recovered.append(
                        ExtractedNote(
                            note_id=note_id,
                            origin_reference=reference,
                            anchor=entry.anchor,
                            kind="official-footnote",
                            label=entry.anchor,
                            text=entry.text,
                            source_spans=[self._apparatus_span(entry.raw)],
                        )
                    )
                    recovered_entry_ids.add(id(entry))
                recovered_references.append(reference)
                for note_id in resolved_ids_by_reference.get(reference, []):
                    anchor_overrides[note_id] = resolved[note_id].anchor
        if recovered:
            self.findings.append(
                ValidationFinding(
                    code="inline_anchor_recovered",
                    message=(
                        f"{len(recovered)} inline anchors omitted by Datalab were recovered "
                        "from unique sequential footer entries"
                    ),
                    references=sorted(recovered_references, key=reference_order.__getitem__),
                )
            )
        return recovered, recovered_entry_ids, anchor_overrides

    def _pdf_superscript_count(
        self,
        document: pdfplumber.PDF,
        reference: str,
    ) -> int:
        spans: set[tuple[int, tuple[float, float, float, float]]] = set()
        for fragment in self.verses[reference].fragments:
            source_width, source_height = self.page_sizes[fragment.page]
            rendered_width, rendered_height = fragment.rendered_page_size
            spans.add(
                (
                    fragment.page,
                    (
                        fragment.bbox[0] * source_width / rendered_width,
                        fragment.bbox[1] * source_height / rendered_height,
                        fragment.bbox[2] * source_width / rendered_width,
                        fragment.bbox[3] * source_height / rendered_height,
                    ),
                )
            )
        count = 0
        for page, bbox in spans:
            chars = [
                char
                for char in document.pages[page].chars
                if float(char["x0"]) >= bbox[0] - 1
                and float(char["x1"]) <= bbox[2] + 1
                and float(char["top"]) >= bbox[1] - 8
                and float(char["bottom"]) <= bbox[3] + 8
            ]
            count += _count_pdf_superscripts(chars, bbox)
        return count

    def _pdf_contains_verse_number(self, fragment: _Fragment, number: int) -> bool:
        source_width, source_height = self.page_sizes[fragment.page]
        rendered_width, rendered_height = fragment.rendered_page_size
        bbox = (
            max(0.0, fragment.bbox[0] * source_width / rendered_width - 1),
            max(0.0, fragment.bbox[1] * source_height / rendered_height - 3),
            min(source_width, fragment.bbox[2] * source_width / rendered_width + 1),
            min(source_height, fragment.bbox[3] * source_height / rendered_height + 3),
        )
        with pdfplumber.open(self.pdf_path) as document:
            text = document.pages[fragment.page].crop(bbox).extract_text() or ""
        return re.search(rf"(?<!\d){number}(?!\d)", text) is not None

    def _span(self, fragment: _Fragment) -> PdfSourceSpan:
        source_width, source_height = self.page_sizes[fragment.page]
        page_bbox = fragment.bbox
        rendered_width, rendered_height = fragment.rendered_page_size
        x_scale = source_width / rendered_width
        y_scale = source_height / rendered_height
        bbox = (
            max(0.0, page_bbox[0] * x_scale),
            max(0.0, page_bbox[1] * y_scale),
            min(source_width, page_bbox[2] * x_scale),
            min(source_height, page_bbox[3] * y_scale),
        )
        span = PdfSourceSpan(page=fragment.page + 1, bbox=bbox, order=self.source_order)
        self.source_order += 1
        return span

    def _apparatus_span(self, raw: _RawApparatus) -> PdfSourceSpan:
        source_width, source_height = self.page_sizes[raw.page]
        rendered_width, rendered_height = raw.rendered_page_size
        x_scale = source_width / rendered_width
        y_scale = source_height / rendered_height
        span = PdfSourceSpan(
            page=raw.page + 1,
            bbox=(
                raw.bbox[0] * x_scale,
                raw.bbox[1] * y_scale,
                min(source_width, raw.bbox[2] * x_scale),
                min(source_height, raw.bbox[3] * y_scale),
            ),
            order=self.source_order,
        )
        self.source_order += 1
        return span


def _visual_order(page: dict[str, Any], children: list[Any]) -> list[dict[str, Any]]:
    page_bbox = _bbox(page)
    midpoint = (page_bbox[0] + page_bbox[2]) / 2
    margin = (page_bbox[2] - page_bbox[0]) * 0.08
    items = [
        child
        for child in children
        if isinstance(child, dict) and child.get("block_type") in {"Text", "SectionHeader"}
    ]

    def order(group: list[dict[str, Any]]) -> list[dict[str, Any]]:
        spanning = [
            block
            for block in group
            if _bbox(block)[0] < midpoint - margin and _bbox(block)[2] > midpoint + margin
        ]
        if not spanning:
            return sorted(
                group,
                key=lambda block: (
                    0 if _bbox(block)[0] < midpoint else 1,
                    _bbox(block)[1],
                ),
            )
        separator = min(spanning, key=lambda block: _bbox(block)[1])
        separator_y = _bbox(separator)[1]
        before = [
            block for block in group if block is not separator and _bbox(block)[1] < separator_y
        ]
        after = [block for block in group if block is not separator and block not in before]
        return [*order(before), separator, *order(after)]

    return order(items)


def _markup_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    parser = _MarkupText()
    parser.feed(value)
    return " ".join("".join(parser.parts).split())


def _plain_text(value: str) -> str:
    return _MARKER.sub("", value).strip()


def _heading_key(value: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "", value.upper())


def _extract_markers(value: str) -> tuple[str, list[str]]:
    markers = _MARKER.findall(value)
    return " ".join(_MARKER.sub("", value).split()), markers


def _parse_apparatus(raw_blocks: list[_RawApparatus]) -> list[_ApparatusEntry]:
    entries: list[_ApparatusEntry] = []
    for page in sorted({block.page for block in raw_blocks}):
        blocks = [block for block in raw_blocks if block.page == page]
        blocks.sort(key=_apparatus_reading_order)
        current: _ApparatusEntry | None = None
        for block in blocks:
            for text in _apparatus_streams(block.html):
                position = 0
                for token in _APPARATUS_TOKEN.finditer(text):
                    prefix = text[position : token.start()].strip()
                    if current is not None and prefix:
                        current.text = f"{current.text} {prefix}".strip()
                    numbered = token.group("numbered")
                    continuation = token.group("continuation")
                    if numbered is not None:
                        verse = int(token.group("verse"))
                        anchor = numbered
                    elif continuation is not None and current is not None:
                        verse = current.verse
                        anchor = continuation
                    else:
                        position = token.end()
                        continue
                    if current is not None:
                        entries.append(current)
                    current = _ApparatusEntry(
                        page=page,
                        verse=verse,
                        anchor=anchor,
                        text="",
                        raw=block,
                        explicit_verse=numbered is not None,
                    )
                    position = token.end()
                suffix = text[position:].strip()
                if current is not None and suffix:
                    current.text = f"{current.text} {suffix}".strip()
        if current is not None:
            entries.append(current)
        for block in blocks:
            for fallback in _split_table_entries(block):
                match_index = next(
                    (
                        index
                        for index, entry in enumerate(entries)
                        if entry.page == fallback.page
                        and entry.verse == fallback.verse
                        and entry.anchor == fallback.anchor
                    ),
                    None,
                )
                if match_index is None:
                    entries.append(fallback)
                else:
                    entries[match_index] = fallback
    return entries


def _split_table_entries(block: _RawApparatus) -> list[_ApparatusEntry]:
    if "<table" not in block.html.lower():
        return []
    table = _TableCells()
    table.feed(block.html)
    groups: dict[int, list[tuple[str, str]]] = {}
    for row in table.rows:
        for index, cell in enumerate(row[:-1]):
            if not _APPARATUS_LABEL_ONLY.fullmatch(cell):
                continue
            text = row[index + 1].strip()
            if not text or _APPARATUS_LABEL_ONLY.fullmatch(text):
                continue
            group = index // 2 if index % 2 == 0 else (index + 1) // 2
            groups.setdefault(group, []).append((cell, text))

    recovered: list[_ApparatusEntry] = []
    for items in groups.values():
        current_verse: int | None = None
        for item_index, (label, text) in enumerate(items):
            match = _APPARATUS_NUMBERED_LABEL_ONLY.fullmatch(label)
            if match is not None:
                current_verse = int(match.group("verse"))
                anchor = match.group("anchor")
                explicit_verse = True
            else:
                if current_verse is None:
                    next_numbered = next(
                        (
                            _APPARATUS_NUMBERED_LABEL_ONLY.fullmatch(next_label)
                            for next_label, _next_text in items[item_index + 1 :]
                            if _APPARATUS_NUMBERED_LABEL_ONLY.fullmatch(next_label) is not None
                        ),
                        None,
                    )
                    if next_numbered is None:
                        continue
                    current_verse = int(next_numbered.group("verse")) - 1
                anchor = label
                explicit_verse = False
            recovered.append(
                _ApparatusEntry(
                    page=block.page,
                    verse=current_verse,
                    anchor=anchor,
                    text=text,
                    raw=block,
                    explicit_verse=explicit_verse,
                )
            )
    return recovered


def _apparatus_reading_order(block: _RawApparatus) -> tuple[int, float, float]:
    page_width = block.rendered_page_size[0]
    center = (block.bbox[0] + block.bbox[2]) / 2
    column = min(2, int(center * 3 / page_width))
    return column, block.bbox[1], block.bbox[0]


def _dominant_alphabetic_size(chars: list[dict[str, Any]]) -> float:
    sizes = Counter(round(float(char["size"]), 1) for char in chars if str(char["text"]).isalpha())
    return sizes.most_common(1)[0][0] if sizes else 0.0


def _count_pdf_superscripts(
    chars: list[dict[str, Any]],
    bbox: tuple[float, float, float, float],
) -> int:
    body_size = _dominant_alphabetic_size(chars)
    body_tops = [
        float(char["top"])
        for char in chars
        if float(char["size"]) >= body_size * 0.9
        and bbox[1] - 2 <= float(char["top"]) <= bbox[3] + 2
    ]
    return sum(
        str(char["text"]) in "abcdefghijk"
        and float(char["size"]) < body_size * 0.8
        and min(
            (abs(float(char["top"]) - body_top) for body_top in body_tops),
            default=float("inf"),
        )
        <= 8
        for char in chars
    )


def _apparatus_streams(value: str) -> list[str]:
    if "<table" in value.lower():
        table = _TableCells()
        table.feed(value)
        if table.rows:
            width = max(len(row) for row in table.rows)
            columns = [
                [row[column] for row in table.rows if column < len(row) and row[column]]
                for column in range(width)
            ]
            groups: list[tuple[int, ...]] = []
            column = 0
            while column < width:
                label_only = bool(columns[column]) and all(
                    _APPARATUS_LABEL_ONLY.fullmatch(cell) for cell in columns[column]
                )
                next_is_text = (
                    column + 1 < width
                    and bool(columns[column + 1])
                    and not all(
                        _APPARATUS_LABEL_ONLY.fullmatch(cell) for cell in columns[column + 1]
                    )
                )
                if label_only and next_is_text:
                    groups.append((column, column + 1))
                    column += 2
                else:
                    groups.append((column,))
                    column += 1
            return [
                " ".join(
                    " ".join(row[index] for index in group if index < len(row) and row[index])
                    for row in table.rows
                    if any(index < len(row) and row[index] for index in group)
                )
                for group in groups
            ]
    parser = _ApparatusText()
    parser.feed(value)
    return [" ".join("".join(parser.parts).split())]


def _looks_like_summary(value: str) -> bool:
    first = value[:1]
    return (
        bool(first and first.islower())
        or "—" in value
        or bool(re.search(r"\b(?:B\.C\.|A\.D\.)", value))
        or value.startswith(("An account ", "WHO IS "))
    )


def _bbox(block: dict[str, Any]) -> tuple[float, float, float, float]:
    value = block.get("bbox")
    if (
        not isinstance(value, list)
        or len(value) != 4
        or not all(isinstance(item, int | float) for item in value)
    ):
        raise ExtractionError("Datalab block has an invalid bounding box")
    return tuple(float(item) for item in value)  # type: ignore[return-value]


def _check_file(path: Path, maximum: int, label: str) -> None:
    if not path.is_file():
        raise FileNotFoundError(path)
    if path.stat().st_size > maximum:
        raise ExtractionError(f"{label} source-byte budget exceeded")


def _validate_correction_profile(
    profile: DatalabCorrectionProfile | None,
    structure: StructureManifest,
    *,
    pdf_sha256: str,
    datalab_json_sha256: str,
) -> str | None:
    if profile is None:
        return None
    if profile.pdf_sha256 != pdf_sha256 or profile.datalab_json_sha256 != datalab_json_sha256:
        raise ExtractionError("Datalab correction profile does not match source identities")
    expected_references = set(structure.expected_references())
    rules = (
        *profile.false_inline_anchors,
        *profile.apparatus_verse_overrides,
        *profile.verified_continuation_anchors,
    )
    for rule in rules:
        work, _book, _chapter, _verse, end_verse = validate_corpus_reference(rule.reference)
        if (
            work != structure.work
            or end_verse is not None
            or rule.reference not in expected_references
        ):
            raise ExtractionError("Datalab correction profile contains an out-of-corpus reference")
    return _canonical_digest(profile.model_dump(mode="json"))


def _repair_recipe_fingerprint() -> str:
    from scripture_chat.ingest import normalize

    if normalize.__file__ is None:  # pragma: no cover - Python modules have source paths here
        raise RuntimeError("normalization module has no source path")
    payload = {
        "parser_sha256": _sha256_file(Path(__file__)),
        "normalizer_sha256": _sha256_file(Path(normalize.__file__)),
        "recipe": "datalab-repair-v1",
    }
    return _canonical_digest(payload)


def _canonical_digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def _write_immutable(path: Path, payload: bytes) -> None:
    if path.exists():
        if path.read_bytes() != payload:
            raise ValueError(f"repair artifact identity collision: {path}")
        return
    create_private_file(path, payload)


def _pdf_page_sizes(path: Path, limits: ExtractionLimits) -> list[tuple[float, float]]:
    try:
        with pdfplumber.open(path) as document:
            if len(document.pages) > limits.max_pdf_pages:
                raise ExtractionError("PDF page budget exceeded")
            return [(float(page.width), float(page.height)) for page in document.pages]
    except ExtractionError:
        raise
    except Exception as exc:
        raise ExtractionError("malformed or unsupported PDF") from exc
