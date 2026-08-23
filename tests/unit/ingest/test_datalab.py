import hashlib
import json
from pathlib import Path

import pytest
from reportlab.pdfgen import canvas

from scripture_chat.ingest.base import ExtractionError, ExtractionLimits
from scripture_chat.ingest.datalab import (
    DatalabApparatusVerseOverride,
    DatalabCorrectionAnchor,
    DatalabCorrectionProfile,
    repair_datalab_pdf,
    write_datalab_repair,
)
from scripture_chat.ingest.validation import StructureManifest, ValidationFinding


def _write_pdf(path: Path, pages: int = 1) -> None:
    document = canvas.Canvas(str(path), pagesize=(612, 792))
    for page in range(pages):
        document.drawString(54, 740, f"Synthetic page {page + 1}")
        document.showPage()
    document.save()


def _write_pdf_with_two_superscripts(path: Path) -> None:
    document = canvas.Canvas(str(path), pagesize=(612, 792))
    document.setFont("Helvetica", 10)
    document.drawString(40, 632, "First verse with")
    document.setFont("Helvetica", 6)
    document.drawString(110, 636, "a")
    document.drawString(150, 636, "b")
    document.showPage()
    document.save()


def _write_pdf_with_large_text_and_one_superscript(path: Path) -> None:
    document = canvas.Canvas(str(path), pagesize=(612, 792))
    document.setFont("Helvetica-Bold", 18)
    document.drawString(40, 620, "Large")
    document.setFont("Helvetica", 10)
    document.drawString(95, 632, "body text")
    document.setFont("Helvetica", 6)
    document.drawString(145, 636, "a")
    document.showPage()
    document.save()


def _write_pdf_with_raised_superscript(path: Path) -> None:
    document = canvas.Canvas(str(path), pagesize=(612, 792))
    document.setFont("Helvetica", 10)
    document.drawString(40, 632, "First verse")
    document.setFont("Helvetica", 6)
    document.drawString(100, 642, "a")
    document.showPage()
    document.save()


def _write_pdf_with_a_marker_below_the_block(path: Path) -> None:
    document = canvas.Canvas(str(path), pagesize=(612, 792))
    document.setFont("Helvetica", 10)
    document.drawString(40, 632, "First verse")
    document.setFont("Helvetica", 6)
    document.drawString(100, 636, "a")
    document.drawString(100, 613, "b")
    document.showPage()
    document.save()


def _write_pdf_with_plain_verse_number(path: Path, number: int) -> None:
    document = canvas.Canvas(str(path), pagesize=(612, 792))
    document.setFont("Helvetica", 10)
    document.drawString(40, 550, f"Continuation. {number} Next verse.")
    document.showPage()
    document.save()


def _block(kind: str, html: str, bbox: list[int]) -> dict[str, object]:
    return {
        "block_type": kind,
        "html": html,
        "bbox": bbox,
        "polygon": [
            [bbox[0], bbox[1]],
            [bbox[2], bbox[1]],
            [bbox[2], bbox[3]],
            [bbox[0], bbox[3]],
        ],
    }


def _write_datalab(path: Path, children: list[dict[str, object]]) -> None:
    path.write_text(
        json.dumps(
            {
                "children": [
                    {
                        "block_type": "Page",
                        "page": 0,
                        "bbox": [0, 0, 1000, 1600],
                        "polygon": [[0, 0], [1000, 0], [1000, 1600], [0, 1600]],
                        "children": children,
                    }
                ],
                "metadata": {"page_stats": [{"page_id": 0, "num_blocks": len(children)}]},
            }
        ),
        encoding="utf-8",
    )


def _write_datalab_pages(path: Path, pages: list[list[dict[str, object]]]) -> None:
    path.write_text(
        json.dumps(
            {
                "children": [
                    {
                        "block_type": "Page",
                        "page": page,
                        "bbox": [0, 0, 1000, 1600],
                        "polygon": [[0, 0], [1000, 0], [1000, 1600], [0, 1600]],
                        "children": children,
                    }
                    for page, children in enumerate(pages)
                ],
                "metadata": {
                    "page_stats": [
                        {"page_id": page, "num_blocks": len(children)}
                        for page, children in enumerate(pages)
                    ]
                },
            }
        ),
        encoding="utf-8",
    )


def _manifest(verse_count: int = 4) -> StructureManifest:
    return StructureManifest(
        schema_version=1,
        source={"fixture": True},
        books={"1-ne": [verse_count]},
    )


def _correction_profile(
    pdf: Path,
    source: Path,
    *,
    false_inline_anchors: list[DatalabCorrectionAnchor] | None = None,
    apparatus_verse_overrides: list[DatalabApparatusVerseOverride] | None = None,
    verified_continuation_anchors: list[DatalabCorrectionAnchor] | None = None,
) -> DatalabCorrectionProfile:
    return DatalabCorrectionProfile(
        profile_id="synthetic-datalab-corrections-v1",
        pdf_sha256=hashlib.sha256(pdf.read_bytes()).hexdigest(),
        datalab_json_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        false_inline_anchors=false_inline_anchors or [],
        apparatus_verse_overrides=apparatus_verse_overrides or [],
        verified_continuation_anchors=verified_continuation_anchors or [],
    )


def test_datalab_repairs_visual_order_verses_and_inline_anchors(tmp_path: Path) -> None:
    pdf = tmp_path / "book.pdf"
    source = tmp_path / "book.pdf.json"
    _write_pdf(pdf)
    _write_datalab(
        source,
        [
            _block("SectionHeader", "<h2>THE FIRST BOOK OF NEPHI</h2>", [200, 80, 800, 120]),
            # Datalab can emit the right column before a chapter heading in the left column.
            _block("Text", "<p>2 Second verse. 3 Third verse.</p>", [530, 100, 970, 260]),
            _block("Text", "<p>4 Fourth verse.</p>", [530, 270, 970, 340]),
            _block("SectionHeader", "<h3>CHAPTER 1</h3>", [180, 300, 420, 340]),
            _block("Text", "<p><i>Chapter summary.</i></p>", [50, 350, 480, 410]),
            _block(
                "Text",
                "<p><b>B</b>EHOLD <sup>a</sup>first <sup>b</sup>verse "
                "with <sup>a</sup>three anchors.</p>",
                [50, 420, 480, 560],
            ),
        ],
    )

    repaired = repair_datalab_pdf(source, pdf, ExtractionLimits(), _manifest())

    assert [passage.reference for passage in repaired.extraction.passages] == [
        "bofm/1-ne/1/1",
        "bofm/1-ne/1/2",
        "bofm/1-ne/1/3",
        "bofm/1-ne/1/4",
    ]
    assert repaired.extraction.passages[0].text == "BEHOLD first verse with three anchors."
    assert [note.anchor for note in repaired.extraction.notes] == ["a", "b", "c"]
    assert {finding.code for finding in repaired.findings} == {
        "apparatus_text_unlinked",
        "inline_anchor_repaired",
    }
    assert repaired.extraction.passages[0].source_spans[0].page == 1


def test_datalab_repairs_a_new_testament_book(tmp_path: Path) -> None:
    pdf = tmp_path / "new-testament.pdf"
    source = tmp_path / "new-testament.pdf.json"
    _write_pdf(pdf)
    _write_datalab(
        source,
        [
            _block(
                "SectionHeader",
                "<h2><span>THE GOSPEL ACCORDING TO</span> <span>ST MATTHEW</span></h2>",
                [200, 80, 800, 120],
            ),
            _block("SectionHeader", "<h3>CHAPTER 1</h3>", [180, 160, 420, 200]),
            _block("Text", "<p><i>Chapter summary.</i></p>", [50, 220, 480, 280]),
            _block(
                "Text",
                "<p>First verse. <sup>2</sup> Second verse.</p>",
                [50, 300, 480, 430],
            ),
        ],
    )
    structure = StructureManifest(
        schema_version=1,
        work="nt",
        source={"fixture": True},
        books={"matt": [2]},
    )

    repaired = repair_datalab_pdf(source, pdf, ExtractionLimits(), structure)

    assert [passage.reference for passage in repaired.extraction.passages] == [
        "nt/matt/1/1",
        "nt/matt/1/2",
    ]
    assert repaired.extraction.profile == "church-new-testament-datalab-marker-v1"


def test_datalab_splits_a_verse_marker_inside_a_continuation_block(tmp_path: Path) -> None:
    pdf = tmp_path / "new-testament.pdf"
    source = tmp_path / "new-testament.pdf.json"
    _write_pdf_with_plain_verse_number(pdf, 3)
    _write_datalab(
        source,
        [
            _block(
                "SectionHeader",
                "<h2>THE GOSPEL ACCORDING TO ST MATTHEW</h2>",
                [200, 80, 800, 120],
            ),
            _block("SectionHeader", "<h3>CHAPTER 1</h3>", [180, 160, 420, 200]),
            _block("Text", "<p><i>Chapter summary.</i></p>", [50, 220, 480, 280]),
            _block("Text", "<p>First verse.</p>", [50, 300, 480, 360]),
            _block("Text", "<p>2 Second verse begins</p>", [50, 370, 480, 430]),
            _block(
                "Text",
                "<p>and continues. 3 Third verse.</p>",
                [50, 440, 480, 520],
            ),
        ],
    )
    structure = StructureManifest(
        schema_version=1,
        work="nt",
        source={"fixture": True},
        books={"matt": [3]},
    )

    repaired = repair_datalab_pdf(source, pdf, ExtractionLimits(), structure)

    assert [passage.text for passage in repaired.extraction.passages] == [
        "First verse.",
        "Second verse begins and continues.",
        "Third verse.",
    ]
    assert "inline_verse_marker_recovered" in {finding.code for finding in repaired.findings}


def test_datalab_joins_a_page_split_verse(tmp_path: Path) -> None:
    pdf = tmp_path / "book.pdf"
    source = tmp_path / "book.pdf.json"
    _write_pdf(pdf)
    _write_datalab(
        source,
        [
            _block("SectionHeader", "<h2>THE FIRST BOOK OF NEPHI</h2>", [200, 80, 800, 120]),
            _block("SectionHeader", "<h3>CHAPTER 1</h3>", [180, 160, 420, 200]),
            _block("Text", "<p><i>Chapter summary.</i></p>", [50, 220, 480, 280]),
            _block("Text", "<p>First verse begins</p>", [50, 300, 480, 360]),
            _block("Text", "<p>and continues.</p>", [50, 370, 480, 430]),
            _block("Text", "<p>2 Second verse.</p>", [50, 440, 480, 500]),
        ],
    )

    repaired = repair_datalab_pdf(source, pdf, ExtractionLimits(), _manifest(2))

    assert repaired.extraction.passages[0].text == "First verse begins and continues."
    assert not any(finding.code == "ambiguous_verse_one_boundary" for finding in repaired.findings)


def test_datalab_keeps_italic_text_after_verse_one_starts(tmp_path: Path) -> None:
    pdf = tmp_path / "book.pdf"
    source = tmp_path / "book.pdf.json"
    _write_pdf(pdf)
    _write_datalab(
        source,
        [
            _block("SectionHeader", "<h2>THE FIRST BOOK OF NEPHI</h2>", [200, 80, 800, 120]),
            _block("SectionHeader", "<h3>CHAPTER 1</h3>", [180, 160, 420, 200]),
            _block("Text", "<p><i>Chapter summary.</i></p>", [50, 220, 480, 280]),
            _block("Text", "<p>First verse begins</p>", [50, 300, 480, 360]),
            _block("Text", "<p><i>and has italic text.</i></p>", [50, 370, 480, 430]),
            _block("Text", "<p>2 Second verse.</p>", [50, 440, 480, 500]),
        ],
    )

    repaired = repair_datalab_pdf(source, pdf, ExtractionLimits(), _manifest(2))

    assert repaired.extraction.passages[0].text == ("First verse begins and has italic text.")
    assert not any(finding.code == "ambiguous_verse_one_boundary" for finding in repaired.findings)


def test_datalab_fails_closed_when_structure_is_incomplete(tmp_path: Path) -> None:
    pdf = tmp_path / "book.pdf"
    source = tmp_path / "book.pdf.json"
    _write_pdf(pdf)
    _write_datalab(
        source,
        [
            _block("SectionHeader", "<h2>THE FIRST BOOK OF NEPHI</h2>", [200, 80, 800, 120]),
            _block("SectionHeader", "<h3>CHAPTER 1</h3>", [180, 160, 420, 200]),
            _block("Text", "<p>Chapter summary.</p>", [50, 220, 480, 280]),
            _block("Text", "<p>First verse.</p>", [50, 300, 480, 360]),
            _block("Text", "<p>2 Second verse.</p>", [50, 370, 480, 430]),
        ],
    )

    with pytest.raises(ExtractionError, match="canonical structure"):
        repair_datalab_pdf(source, pdf, ExtractionLimits(), _manifest(3))


def test_datalab_recognizes_a_plain_text_chapter_summary(tmp_path: Path) -> None:
    pdf = tmp_path / "book.pdf"
    source = tmp_path / "book.pdf.json"
    _write_pdf(pdf)
    _write_datalab(
        source,
        [
            _block("SectionHeader", "<h2>THE FIRST BOOK OF NEPHI</h2>", [200, 80, 800, 120]),
            _block("SectionHeader", "<h3>CHAPTER 1</h3>", [180, 160, 420, 200]),
            _block(
                "Text",
                "<p>A topic is introduced—The account continues. About 600 B.C.</p>",
                [50, 220, 480, 280],
            ),
            _block("Text", "<p>First verse.</p>", [50, 300, 480, 360]),
            _block("Text", "<p>2 Second verse.</p>", [50, 370, 480, 430]),
        ],
    )

    repaired = repair_datalab_pdf(source, pdf, ExtractionLimits(), _manifest(2))

    assert repaired.extraction.passages[0].text == "First verse."
    assert not any(finding.code == "ambiguous_verse_one_boundary" for finding in repaired.findings)


def test_datalab_writes_an_inactive_private_candidate(tmp_path: Path) -> None:
    pdf = tmp_path / "book.pdf"
    source = tmp_path / "book.pdf.json"
    output = tmp_path / "private"
    repository = tmp_path / "repository"
    output.mkdir(mode=0o700)
    repository.mkdir()
    _write_pdf(pdf)
    _write_datalab(
        source,
        [
            _block("SectionHeader", "<h2>THE FIRST BOOK OF NEPHI</h2>", [200, 80, 800, 120]),
            _block("SectionHeader", "<h3>CHAPTER 1</h3>", [180, 160, 420, 200]),
            _block("Text", "<p><i>Summary.</i></p>", [50, 220, 480, 280]),
            _block("Text", "<p>First verse.</p>", [50, 300, 480, 360]),
            _block("Text", "<p>2 Second verse.</p>", [50, 370, 480, 430]),
        ],
    )
    structure = _manifest(2)
    repaired = repair_datalab_pdf(source, pdf, ExtractionLimits(), structure)

    artifacts = write_datalab_repair(
        output,
        repaired,
        structure,
        repository_root=repository,
    )

    report = json.loads(artifacts.report.read_text(encoding="utf-8"))
    assert report["status"] == "review_required"
    assert report["passage_count"] == 2
    assert report["active"] is False
    assert report["pdf_sha256"] == repaired.pdf_sha256
    assert report["datalab_json_sha256"] == repaired.datalab_json_sha256
    assert report["structure_digest"] == repaired.structure_digest
    assert report["recipe_fingerprint"] == repaired.recipe_fingerprint
    assert artifacts.candidate.is_file()
    assert artifacts.candidate.stat().st_mode & 0o777 == 0o600

    revised = repaired.model_copy(
        update={
            "findings": [ValidationFinding(code="manual_review", message="review recipe changed")]
        }
    )
    revised_artifacts = write_datalab_repair(
        output,
        revised,
        structure,
        repository_root=repository,
    )
    assert revised_artifacts.directory != artifacts.directory

    with pytest.raises(ValueError, match="outside the repository"):
        write_datalab_repair(
            repository / "private",
            repaired,
            structure,
            repository_root=repository,
        )


def test_datalab_recognizes_a_split_plain_text_summary(tmp_path: Path) -> None:
    pdf = tmp_path / "book.pdf"
    source = tmp_path / "book.pdf.json"
    _write_pdf(pdf)
    _write_datalab(
        source,
        [
            _block("SectionHeader", "<h2>THE FIRST BOOK OF NEPHI</h2>", [200, 80, 800, 120]),
            _block("SectionHeader", "<h3>CHAPTER 1</h3>", [180, 160, 420, 200]),
            _block("Text", "<p>A topic begins and continues unless</p>", [50, 220, 480, 280]),
            _block(
                "Text",
                "<p>the people repent—The account continues. About 600 B.C.</p>",
                [50, 290, 480, 350],
            ),
            _block("Text", "<p>First verse.</p>", [50, 360, 480, 420]),
            _block("Text", "<p>2 Second verse.</p>", [50, 430, 480, 490]),
        ],
    )

    repaired = repair_datalab_pdf(source, pdf, ExtractionLimits(), _manifest(2))

    assert repaired.extraction.passages[0].text == "First verse."
    assert not any(finding.code == "ambiguous_verse_one_boundary" for finding in repaired.findings)


def test_datalab_links_page_local_apparatus_by_verse_and_anchor(tmp_path: Path) -> None:
    pdf = tmp_path / "book.pdf"
    source = tmp_path / "book.pdf.json"
    _write_pdf(pdf)
    _write_datalab(
        source,
        [
            _block("SectionHeader", "<h2>THE FIRST BOOK OF NEPHI</h2>", [200, 80, 800, 120]),
            _block("SectionHeader", "<h3>CHAPTER 1</h3>", [180, 160, 420, 200]),
            _block("Text", "<p><i>Summary.</i></p>", [50, 220, 480, 280]),
            _block(
                "Text",
                "<p>First <sup>a</sup>verse with <sup>b</sup>notes.</p>",
                [50, 300, 480, 360],
            ),
            _block("Text", "<p>2 Second verse.</p>", [50, 370, 480, 430]),
            _block(
                "Text",
                "<p>1 1a First note. b Second note.</p>",
                [50, 1080, 300, 1500],
            ),
        ],
    )

    repaired = repair_datalab_pdf(source, pdf, ExtractionLimits(), _manifest(2))

    assert [(note.anchor, note.text) for note in repaired.extraction.notes] == [
        ("a", "First note."),
        ("b", "Second note."),
    ]
    assert not any(finding.code == "apparatus_text_unlinked" for finding in repaired.findings)


def test_datalab_reads_apparatus_tables_by_column(tmp_path: Path) -> None:
    pdf = tmp_path / "book.pdf"
    source = tmp_path / "book.pdf.json"
    _write_pdf(pdf)
    _write_datalab(
        source,
        [
            _block("SectionHeader", "<h2>THE FIRST BOOK OF NEPHI</h2>", [200, 80, 800, 120]),
            _block("SectionHeader", "<h3>CHAPTER 1</h3>", [180, 160, 420, 200]),
            _block("Text", "<p><i>Summary.</i></p>", [50, 220, 480, 280]),
            _block(
                "Text",
                "<p>First <sup>a</sup>verse with <sup>b</sup>notes.</p>",
                [50, 300, 480, 360],
            ),
            _block(
                "Text",
                "<p>2 Second <sup>a</sup>verse with <sup>b</sup>notes.</p>",
                [50, 370, 480, 430],
            ),
            _block(
                "Table",
                "<table><tr><td>1 1a First.</td><td>2a Third.</td></tr>"
                "<tr><td>b Second.</td><td>b Fourth.</td></tr></table>",
                [50, 1080, 950, 1500],
            ),
        ],
    )

    repaired = repair_datalab_pdf(source, pdf, ExtractionLimits(), _manifest(2))

    assert [
        (note.origin_reference, note.anchor, note.text) for note in repaired.extraction.notes
    ] == [
        ("bofm/1-ne/1/1", "a", "First."),
        ("bofm/1-ne/1/1", "b", "Second."),
        ("bofm/1-ne/1/2", "a", "Third."),
        ("bofm/1-ne/1/2", "b", "Fourth."),
    ]


def test_datalab_joins_split_table_labels_to_their_text_columns(tmp_path: Path) -> None:
    pdf = tmp_path / "book.pdf"
    source = tmp_path / "book.pdf.json"
    _write_pdf(pdf)
    _write_datalab(
        source,
        [
            _block("SectionHeader", "<h2>THE FIRST BOOK OF NEPHI</h2>", [200, 80, 800, 120]),
            _block("SectionHeader", "<h3>CHAPTER 1</h3>", [180, 160, 420, 200]),
            _block("Text", "<p><i>Summary.</i></p>", [50, 220, 480, 280]),
            _block("Text", "<p>First <sup>a</sup>verse.</p>", [50, 300, 480, 360]),
            _block("Text", "<p>2 Second <sup>a</sup>verse.</p>", [50, 370, 480, 430]),
            _block(
                "Table",
                "<table><tr><td>1 1a</td><td>First note.</td>"
                "<td>2a</td><td>Second note.</td></tr></table>",
                [50, 1080, 950, 1500],
            ),
        ],
    )

    repaired = repair_datalab_pdf(source, pdf, ExtractionLimits(), _manifest(2))

    assert [note.text for note in repaired.extraction.notes] == [
        "First note.",
        "Second note.",
    ]


def test_datalab_recovers_numbered_entries_from_irregular_table_rows(tmp_path: Path) -> None:
    pdf = tmp_path / "book.pdf"
    source = tmp_path / "book.pdf.json"
    _write_pdf(pdf)
    _write_datalab(
        source,
        [
            _block("SectionHeader", "<h2>THE FIRST BOOK OF NEPHI</h2>", [200, 80, 800, 120]),
            _block("SectionHeader", "<h3>CHAPTER 1</h3>", [180, 160, 420, 200]),
            _block("Text", "<p><i>Summary.</i></p>", [50, 220, 480, 280]),
            _block("Text", "<p>First <sup>a</sup>verse.</p>", [50, 300, 480, 360]),
            _block("Text", "<p>2 Second <sup>a</sup>verse.</p>", [50, 370, 480, 430]),
            _block(
                "Table",
                "<table><tr><td></td><td></td><td>Prior continuation.</td>"
                "<td>b</td><td>Other column.</td></tr>"
                "<tr><td>1 1a</td><td>First note.</td>"
                "<td>2a</td><td>Second note.</td><td></td></tr></table>",
                [50, 1080, 950, 1500],
            ),
        ],
    )

    repaired = repair_datalab_pdf(source, pdf, ExtractionLimits(), _manifest(2))

    assert [note.text for note in repaired.extraction.notes] == [
        "First note.",
        "Second note.",
    ]


def test_datalab_reconciles_equal_page_verse_anchor_sequences(tmp_path: Path) -> None:
    pdf = tmp_path / "book.pdf"
    source = tmp_path / "book.pdf.json"
    _write_pdf(pdf)
    _write_datalab(
        source,
        [
            _block("SectionHeader", "<h2>THE FIRST BOOK OF NEPHI</h2>", [200, 80, 800, 120]),
            _block("SectionHeader", "<h3>CHAPTER 1</h3>", [180, 160, 420, 200]),
            _block("Text", "<p><i>Summary.</i></p>", [50, 220, 480, 280]),
            _block(
                "Text",
                "<p>First <sup>a</sup>verse with <sup>b</sup>notes.</p>",
                [50, 300, 480, 360],
            ),
            _block("Text", "<p>2 Second verse.</p>", [50, 370, 480, 430]),
            _block(
                "Footnote",
                "<p>1 1a First note. c OCR-damaged label.</p>",
                [50, 1080, 950, 1500],
            ),
        ],
    )

    repaired = repair_datalab_pdf(source, pdf, ExtractionLimits(), _manifest(2))

    assert [note.text for note in repaired.extraction.notes] == [
        "First note.",
        "OCR-damaged label.",
    ]
    assert any(finding.code == "apparatus_anchor_reconciled" for finding in repaired.findings)


def test_datalab_reads_indented_footnote_blocks_in_column_order(tmp_path: Path) -> None:
    pdf = tmp_path / "book.pdf"
    source = tmp_path / "book.pdf.json"
    _write_pdf(pdf)
    _write_datalab(
        source,
        [
            _block("SectionHeader", "<h2>THE FIRST BOOK OF NEPHI</h2>", [200, 80, 800, 120]),
            _block("SectionHeader", "<h3>CHAPTER 1</h3>", [180, 160, 420, 200]),
            _block("Text", "<p><i>Summary.</i></p>", [50, 220, 480, 280]),
            _block(
                "Text",
                "<p>First <sup>a</sup>verse with <sup>b</sup>notes.</p>",
                [50, 300, 480, 360],
            ),
            _block(
                "Text",
                "<p>2 Second <sup>a</sup>verse.</p>",
                [50, 370, 480, 430],
            ),
            _block("Footnote", "<p>1 1a First note.</p>", [50, 1080, 300, 1120]),
            _block("Footnote", "<p>b Second note.</p>", [75, 1120, 300, 1160]),
            _block("Footnote", "<p>2a Third note.</p>", [50, 1160, 300, 1200]),
        ],
    )

    repaired = repair_datalab_pdf(source, pdf, ExtractionLimits(), _manifest(2))

    assert [
        (note.origin_reference, note.anchor, note.text) for note in repaired.extraction.notes
    ] == [
        ("bofm/1-ne/1/1", "a", "First note."),
        ("bofm/1-ne/1/1", "b", "Second note."),
        ("bofm/1-ne/1/2", "a", "Third note."),
    ]


def test_datalab_reads_page_footer_apparatus(tmp_path: Path) -> None:
    pdf = tmp_path / "book.pdf"
    source = tmp_path / "book.pdf.json"
    _write_pdf(pdf)
    _write_datalab(
        source,
        [
            _block("SectionHeader", "<h2>THE FIRST BOOK OF NEPHI</h2>", [200, 80, 800, 120]),
            _block("SectionHeader", "<h3>CHAPTER 1</h3>", [180, 160, 420, 200]),
            _block("Text", "<p><i>Summary.</i></p>", [50, 220, 480, 280]),
            _block("Text", "<p>First <sup>a</sup>verse.</p>", [50, 300, 480, 360]),
            _block("Text", "<p>2 Second verse.</p>", [50, 370, 480, 430]),
            _block("PageFooter", "<p>1 1a Footer note.</p>", [50, 1080, 300, 1140]),
        ],
    )

    repaired = repair_datalab_pdf(source, pdf, ExtractionLimits(), _manifest(2))

    assert [(note.anchor, note.text) for note in repaired.extraction.notes] == [
        ("a", "Footer note.")
    ]


def test_datalab_reads_list_group_apparatus(tmp_path: Path) -> None:
    pdf = tmp_path / "book.pdf"
    source = tmp_path / "book.pdf.json"
    _write_pdf(pdf)
    _write_datalab(
        source,
        [
            _block("SectionHeader", "<h2>THE FIRST BOOK OF NEPHI</h2>", [200, 80, 800, 120]),
            _block("SectionHeader", "<h3>CHAPTER 1</h3>", [180, 160, 420, 200]),
            _block("Text", "<p><i>Summary.</i></p>", [50, 220, 480, 280]),
            _block(
                "Text",
                "<p>First <sup>a</sup>verse with <sup>b</sup>notes.</p>",
                [50, 300, 480, 360],
            ),
            _block("Text", "<p>2 Second verse.</p>", [50, 370, 480, 430]),
            _block(
                "ListGroup",
                "<ul><li>1 1a First note.</li><li>b Second note.</li></ul>",
                [50, 1080, 300, 1500],
            ),
        ],
    )

    repaired = repair_datalab_pdf(source, pdf, ExtractionLimits(), _manifest(2))

    assert [(note.anchor, note.text) for note in repaired.extraction.notes] == [
        ("a", "First note."),
        ("b", "Second note."),
    ]


def test_datalab_links_a_split_verse_marker_to_its_start_page_footer(
    tmp_path: Path,
) -> None:
    pdf = tmp_path / "book.pdf"
    source = tmp_path / "book.pdf.json"
    _write_pdf(pdf, pages=2)
    _write_datalab_pages(
        source,
        [
            [
                _block("SectionHeader", "<h2>THE FIRST BOOK OF NEPHI</h2>", [200, 80, 800, 120]),
                _block("SectionHeader", "<h3>CHAPTER 1</h3>", [180, 160, 420, 200]),
                _block("Text", "<p><i>Summary.</i></p>", [50, 220, 480, 280]),
                _block("Text", "<p>First verse begins</p>", [50, 300, 480, 360]),
                _block("PageFooter", "<p>1 1a Split note.</p>", [50, 1080, 300, 1140]),
            ],
            [
                _block(
                    "Text",
                    "<p>and continues with an <sup>a</sup>anchor.</p>",
                    [50, 100, 480, 160],
                ),
                _block("Text", "<p>2 Second verse.</p>", [50, 170, 480, 230]),
            ],
        ],
    )

    repaired = repair_datalab_pdf(source, pdf, ExtractionLimits(), _manifest(2))

    assert [(note.anchor, note.text) for note in repaired.extraction.notes] == [
        ("a", "Split note.")
    ]


def test_datalab_discards_an_unlinked_marker_absent_from_the_pdf_text_layer(
    tmp_path: Path,
) -> None:
    pdf = tmp_path / "book.pdf"
    source = tmp_path / "book.pdf.json"
    _write_pdf_with_two_superscripts(pdf)
    _write_datalab(
        source,
        [
            _block("SectionHeader", "<h2>THE FIRST BOOK OF NEPHI</h2>", [200, 80, 800, 120]),
            _block("SectionHeader", "<h3>CHAPTER 1</h3>", [180, 160, 420, 200]),
            _block("Text", "<p><i>Summary.</i></p>", [50, 220, 480, 280]),
            _block(
                "Text",
                "<p>First <sup>a</sup>verse with <sup>b</sup>two "
                "real notes and <sup>c</sup>one false marker.</p>",
                [50, 300, 480, 360],
            ),
            _block("Text", "<p>2 Second verse.</p>", [50, 370, 480, 430]),
            _block("Footnote", "<p>1 1a First note.</p>", [50, 1080, 300, 1120]),
            _block("Footnote", "<p>b Second note.</p>", [75, 1120, 300, 1160]),
        ],
    )

    repaired = repair_datalab_pdf(source, pdf, ExtractionLimits(), _manifest(2))

    assert [(note.anchor, note.text) for note in repaired.extraction.notes] == [
        ("a", "First note."),
        ("b", "Second note."),
    ]
    assert any(finding.code == "inline_anchor_false_positive" for finding in repaired.findings)


def test_datalab_recovers_a_footer_entry_omitted_from_body_html(tmp_path: Path) -> None:
    pdf = tmp_path / "book.pdf"
    source = tmp_path / "book.pdf.json"
    _write_pdf_with_two_superscripts(pdf)
    _write_datalab(
        source,
        [
            _block("SectionHeader", "<h2>THE FIRST BOOK OF NEPHI</h2>", [200, 80, 800, 120]),
            _block("SectionHeader", "<h3>CHAPTER 1</h3>", [180, 160, 420, 200]),
            _block("Text", "<p><i>Summary.</i></p>", [50, 220, 480, 280]),
            _block(
                "Text",
                "<p>First <sup>a</sup>verse with one omitted marker.</p>",
                [50, 300, 480, 360],
            ),
            _block("Text", "<p>2 Second verse.</p>", [50, 370, 480, 430]),
            _block("Footnote", "<p>1 1a First note.</p>", [50, 1080, 300, 1120]),
            _block("Footnote", "<p>b Recovered note.</p>", [75, 1120, 300, 1160]),
        ],
    )

    repaired = repair_datalab_pdf(source, pdf, ExtractionLimits(), _manifest(2))

    assert [(note.anchor, note.text) for note in repaired.extraction.notes] == [
        ("a", "First note."),
        ("b", "Recovered note."),
    ]
    assert any(finding.code == "inline_anchor_recovered" for finding in repaired.findings)


def test_datalab_recovers_a_unique_sequential_footer_entry_without_body_ocr(
    tmp_path: Path,
) -> None:
    pdf = tmp_path / "book.pdf"
    source = tmp_path / "book.pdf.json"
    _write_pdf(pdf)
    _write_datalab(
        source,
        [
            _block("SectionHeader", "<h2>THE FIRST BOOK OF NEPHI</h2>", [200, 80, 800, 120]),
            _block("SectionHeader", "<h3>CHAPTER 1</h3>", [180, 160, 420, 200]),
            _block("Text", "<p><i>Summary.</i></p>", [50, 220, 480, 280]),
            _block("Text", "<p>First verse.</p>", [50, 300, 480, 360]),
            _block("Text", "<p>2 Second verse.</p>", [50, 370, 480, 430]),
            _block("Footnote", "<p>1 1a Recovered note.</p>", [50, 1080, 300, 1120]),
        ],
    )

    repaired = repair_datalab_pdf(source, pdf, ExtractionLimits(), _manifest(2))

    assert [(note.anchor, note.text) for note in repaired.extraction.notes] == [
        ("a", "Recovered note.")
    ]
    assert any(finding.code == "inline_anchor_recovered" for finding in repaired.findings)


def test_datalab_uses_the_dominant_body_font_to_verify_superscripts(tmp_path: Path) -> None:
    pdf = tmp_path / "book.pdf"
    source = tmp_path / "book.pdf.json"
    _write_pdf_with_large_text_and_one_superscript(pdf)
    _write_datalab(
        source,
        [
            _block("SectionHeader", "<h2>THE FIRST BOOK OF NEPHI</h2>", [200, 80, 800, 120]),
            _block("SectionHeader", "<h3>CHAPTER 1</h3>", [180, 160, 420, 200]),
            _block("Text", "<p><i>Summary.</i></p>", [50, 220, 480, 280]),
            _block("Text", "<p>First verse with an omitted marker.</p>", [50, 300, 480, 360]),
            _block("Text", "<p>2 Second verse.</p>", [50, 370, 480, 430]),
            _block("Footnote", "<p>1 1a Recovered note.</p>", [50, 1080, 300, 1120]),
        ],
    )

    repaired = repair_datalab_pdf(source, pdf, ExtractionLimits(), _manifest(2))

    assert [(note.anchor, note.text) for note in repaired.extraction.notes] == [
        ("a", "Recovered note.")
    ]


def test_datalab_recovers_a_missing_label_despite_a_duplicate_footer_label(
    tmp_path: Path,
) -> None:
    pdf = tmp_path / "book.pdf"
    source = tmp_path / "book.pdf.json"
    _write_pdf_with_two_superscripts(pdf)
    _write_datalab(
        source,
        [
            _block("SectionHeader", "<h2>THE FIRST BOOK OF NEPHI</h2>", [200, 80, 800, 120]),
            _block("SectionHeader", "<h3>CHAPTER 1</h3>", [180, 160, 420, 200]),
            _block("Text", "<p><i>Summary.</i></p>", [50, 220, 480, 280]),
            _block("Text", "<p>First <sup>a</sup>verse.</p>", [50, 300, 480, 360]),
            _block("Text", "<p>2 Second verse.</p>", [50, 370, 480, 430]),
            _block("Footnote", "<p>1 1a First note.</p>", [50, 1080, 300, 1120]),
            _block("Footnote", "<p>1a Duplicate label.</p>", [50, 1120, 300, 1160]),
            _block("Footnote", "<p>b Recovered note.</p>", [75, 1160, 300, 1200]),
        ],
    )

    repaired = repair_datalab_pdf(source, pdf, ExtractionLimits(), _manifest(2))

    assert [(note.anchor, note.text) for note in repaired.extraction.notes] == [
        ("a", "First note."),
        ("b", "Recovered note."),
    ]
    assert any(finding.code == "apparatus_entry_false_positive" for finding in repaired.findings)
    assert not any(finding.code == "apparatus_entry_unmatched" for finding in repaired.findings)


def test_datalab_verifies_a_superscript_raised_above_the_datalab_box(tmp_path: Path) -> None:
    pdf = tmp_path / "book.pdf"
    source = tmp_path / "book.pdf.json"
    _write_pdf_with_raised_superscript(pdf)
    _write_datalab(
        source,
        [
            _block("SectionHeader", "<h2>THE FIRST BOOK OF NEPHI</h2>", [200, 80, 800, 120]),
            _block("SectionHeader", "<h3>CHAPTER 1</h3>", [180, 160, 420, 200]),
            _block("Text", "<p><i>Summary.</i></p>", [50, 220, 480, 280]),
            _block("Text", "<p>First verse with an omitted marker.</p>", [50, 300, 480, 360]),
            _block("Text", "<p>2 Second verse.</p>", [50, 370, 480, 430]),
            _block("Footnote", "<p>1 1a Recovered note.</p>", [50, 1080, 300, 1120]),
        ],
    )

    repaired = repair_datalab_pdf(source, pdf, ExtractionLimits(), _manifest(2))

    assert [(note.anchor, note.text) for note in repaired.extraction.notes] == [
        ("a", "Recovered note.")
    ]


def test_datalab_does_not_count_a_marker_below_the_datalab_box(tmp_path: Path) -> None:
    pdf = tmp_path / "book.pdf"
    source = tmp_path / "book.pdf.json"
    _write_pdf_with_a_marker_below_the_block(pdf)
    _write_datalab(
        source,
        [
            _block("SectionHeader", "<h2>THE FIRST BOOK OF NEPHI</h2>", [200, 80, 800, 120]),
            _block("SectionHeader", "<h3>CHAPTER 1</h3>", [180, 160, 420, 200]),
            _block("Text", "<p><i>Summary.</i></p>", [50, 220, 480, 280]),
            _block("Text", "<p>First verse with an omitted marker.</p>", [50, 300, 480, 360]),
            _block("Text", "<p>2 Second verse.</p>", [50, 370, 480, 430]),
            _block("Footnote", "<p>1 1a Recovered note.</p>", [50, 1080, 300, 1120]),
        ],
    )

    repaired = repair_datalab_pdf(source, pdf, ExtractionLimits(), _manifest(2))

    assert [(note.anchor, note.text) for note in repaired.extraction.notes] == [
        ("a", "Recovered note.")
    ]


def test_digest_bound_profile_repairs_a_synthetic_merged_chapter_and_verse_label(
    tmp_path: Path,
) -> None:
    pdf = tmp_path / "book.pdf"
    source = tmp_path / "book.pdf.json"
    _write_pdf(pdf, pages=2)
    pages: list[list[dict[str, object]]] = []
    for chapter in range(1, 3):
        children: list[dict[str, object]] = []
        if chapter == 1:
            children.append(
                _block(
                    "SectionHeader",
                    "<h2>THE GOSPEL ACCORDING TO ST. MATTHEW</h2>",
                    [200, 80, 800, 120],
                )
            )
        children.extend(
            [
                _block(
                    "SectionHeader",
                    f"<h3>CHAPTER {chapter}</h3>",
                    [180, 160, 420, 200],
                ),
                _block("Text", "<p><i>Summary.</i></p>", [50, 220, 480, 280]),
                _block(
                    "Text",
                    "<p>First <sup>a</sup>verse.</p>" if chapter == 2 else "<p>First verse.</p>",
                    [50, 300, 480, 360],
                ),
            ]
        )
        if chapter == 2:
            children.append(_block("Footnote", "<p>21a Repaired note.</p>", [50, 1080, 300, 1140]))
        pages.append(children)
    _write_datalab_pages(source, pages)
    structure = StructureManifest(
        schema_version=1,
        work="nt",
        source={"fixture": True},
        books={"matt": [1, 1]},
    )
    profile = _correction_profile(
        pdf,
        source,
        apparatus_verse_overrides=[
            DatalabApparatusVerseOverride(
                reference="nt/matt/2/1",
                anchor="a",
                source_verse=21,
            )
        ],
    )

    repaired = repair_datalab_pdf(
        source,
        pdf,
        ExtractionLimits(),
        structure,
        profile,
    )

    assert [
        (note.origin_reference, note.anchor, note.text) for note in repaired.extraction.notes
    ] == [("nt/matt/2/1", "a", "Repaired note.")]
    assert repaired.extraction.profile == profile.profile_id
    assert repaired.correction_profile_digest is not None
    assert any(finding.code == "source_profile_correction" for finding in repaired.findings)


def test_correction_profile_rejects_a_different_source_identity(tmp_path: Path) -> None:
    pdf = tmp_path / "book.pdf"
    source = tmp_path / "book.pdf.json"
    _write_pdf(pdf)
    _write_datalab(
        source,
        [
            _block("SectionHeader", "<h2>THE FIRST BOOK OF NEPHI</h2>", [200, 80, 800, 120]),
            _block("SectionHeader", "<h3>CHAPTER 1</h3>", [180, 160, 420, 200]),
            _block("Text", "<p><i>Summary.</i></p>", [50, 220, 480, 280]),
            _block("Text", "<p>First verse.</p>", [50, 300, 480, 360]),
        ],
    )
    profile = _correction_profile(pdf, source).model_copy(update={"pdf_sha256": "0" * 64})

    with pytest.raises(ExtractionError, match="does not match source identities"):
        repair_datalab_pdf(source, pdf, ExtractionLimits(), _manifest(1), profile)
