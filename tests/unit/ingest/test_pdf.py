from pathlib import Path

import pytest
from reportlab.pdfgen import canvas

from passage.ingest.base import ExtractionError, ExtractionLimits
from passage.ingest.pdf import extract_pdf


def write_pdf(path: Path, lines: list[str]) -> None:
    document = canvas.Canvas(str(path), pagesize=(612, 792))
    y = 740
    for line in lines:
        document.drawString(54, y, line)
        y -= 24
    document.save()


def test_pdf_extracts_text_layer_with_page_and_bbox_provenance(tmp_path: Path) -> None:
    source = tmp_path / "book.pdf"
    write_pdf(
        source,
        [
            "BOOK OF MORMON - PASSAGE PROFILE V1",
            "1 Nephi 3:7 And it came to pass that I, Nephi, said unto my father: I will go and do.",
            "1 Nephi 3:8 I know that the Lord giveth no commandments unto the children of men.",
        ],
    )

    result = extract_pdf(source, ExtractionLimits())

    assert result.profile == "passage-v1"
    assert [event.reference for event in result.passages] == [
        "bofm/1-ne/3/7",
        "bofm/1-ne/3/8",
    ]
    span = result.passages[0].source_spans[0]
    assert span.page == 1
    assert span.bbox[0] >= 0
    assert "I will go and do" in result.passages[0].text


def test_pdf_rejects_missing_text_layer(tmp_path: Path) -> None:
    source = tmp_path / "image-only.pdf"
    write_pdf(source, [])

    with pytest.raises(ExtractionError, match="usable text layer"):
        extract_pdf(source, ExtractionLimits())


def test_pdf_rejects_unknown_profile(tmp_path: Path) -> None:
    source = tmp_path / "unknown.pdf"
    write_pdf(source, ["Some unrelated document", "1 Nephi 3:7 Text"])

    with pytest.raises(ExtractionError, match="unsupported PDF source profile"):
        extract_pdf(source, ExtractionLimits())


def test_pdf_enforces_page_budget(tmp_path: Path) -> None:
    source = tmp_path / "two-pages.pdf"
    document = canvas.Canvas(str(source), pagesize=(612, 792))
    document.drawString(54, 740, "BOOK OF MORMON - PASSAGE PROFILE V1")
    document.showPage()
    document.drawString(54, 740, "1 Nephi 3:7 Text")
    document.save()

    with pytest.raises(ExtractionError, match="page budget"):
        extract_pdf(source, ExtractionLimits(max_pdf_pages=1))
