from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

import pdfplumber

from scripture_chat.domain.models import PdfSourceSpan
from scripture_chat.ingest.base import (
    ExtractedPassage,
    ExtractionError,
    ExtractionLimits,
    ExtractionResult,
)
from scripture_chat.ingest.source_profiles import (
    EPUB_PROFILE,
    PDF_BOOK_SLUGS,
    PDF_PROFILE_MARKER,
    PDF_VERSE_PATTERN,
)


def extract_pdf(path: Path, limits: ExtractionLimits) -> ExtractionResult:
    if path.stat().st_size > limits.max_source_bytes:
        raise ExtractionError("source-byte budget exceeded")
    try:
        with pdfplumber.open(path) as document:
            if len(document.pages) > limits.max_pdf_pages:
                raise ExtractionError("PDF page budget exceeded")
            lines: list[tuple[int, str, tuple[float, float, float, float]]] = []
            total_objects = 0
            total_chars = 0
            for page_number, page in enumerate(document.pages, start=1):
                total_objects += len(page.chars)
                total_chars += len(page.chars)
                if total_objects > limits.max_pdf_objects:
                    raise ExtractionError("PDF object budget exceeded")
                if total_chars > limits.max_pdf_chars:
                    raise ExtractionError("PDF character budget exceeded")
                lines.extend(_page_lines(page_number, page))
    except ExtractionError:
        raise
    except Exception as exc:
        raise ExtractionError("malformed or unsupported PDF") from exc

    if not lines:
        raise ExtractionError("PDF has no usable text layer")
    if not any(PDF_PROFILE_MARKER in text for _, text, _ in lines):
        raise ExtractionError("unsupported PDF source profile")

    passages: list[ExtractedPassage] = []
    order = 0
    for page_number, text, bbox in lines:
        match = PDF_VERSE_PATTERN.fullmatch(text)
        if match is None:
            continue
        groups = match.groupdict()
        slug = PDF_BOOK_SLUGS[groups["book"].lower()]
        reference = f"bofm/{slug}/{groups['chapter']}/{groups['verse']}"
        passages.append(
            ExtractedPassage(
                reference=reference,
                text=groups["text"],
                source_spans=[PdfSourceSpan(page=page_number, bbox=bbox, order=order)],
            )
        )
        order += 1
    if not passages:
        raise ExtractionError("PDF profile contains no recognizable passages")
    return ExtractionResult(
        source_path=path,
        source_format="pdf",
        profile=EPUB_PROFILE,
        passages=passages,
    )


def _page_lines(
    page_number: int, page: Any
) -> list[tuple[int, str, tuple[float, float, float, float]]]:
    words = page.extract_words(
        x_tolerance=2,
        y_tolerance=2,
        keep_blank_chars=False,
        use_text_flow=True,
    )
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for word in words:
        if word["top"] < 30 or word["bottom"] > page.height - 30:
            continue
        grouped[round(float(word["top"]) / 2)].append(word)
    lines: list[tuple[int, str, tuple[float, float, float, float]]] = []
    for key in sorted(grouped):
        line_words = sorted(grouped[key], key=lambda item: float(item["x0"]))
        text = " ".join(str(item["text"]) for item in line_words).strip()
        if not text:
            continue
        bbox = (
            min(float(item["x0"]) for item in line_words),
            min(float(item["top"]) for item in line_words),
            max(float(item["x1"]) for item in line_words),
            max(float(item["bottom"]) for item in line_words),
        )
        lines.append((page_number, text, bbox))
    return lines
