from pathlib import Path

from scripture_chat.ingest.base import ExtractionLimits
from scripture_chat.ingest.epub import extract_epub
from scripture_chat.ingest.normalize import canonical_projection, normalize_extraction
from scripture_chat.ingest.pdf import extract_pdf
from scripture_chat.ingest.validation import (
    StructureManifest,
    reconcile_source_spans,
    validate_corpus,
)
from tests.unit.ingest.test_epub import make_epub
from tests.unit.ingest.test_pdf import write_pdf

CHAPTER = """<html xmlns="http://www.w3.org/1999/xhtml"><body>
<section data-scripture-profile="scripture-chat-v1">
<p data-reference="bofm/1-ne/1/1">I, Nephi, having been born of goodly parents.</p>
<p data-reference="bofm/1-ne/1/2">Yea, I make a record in the language of my father.</p>
</section></body></html>"""
MANIFEST = StructureManifest(schema_version=1, source={}, books={"1-ne": [2]})


def test_equivalent_epub_and_pdf_have_identical_canonical_projection(tmp_path: Path) -> None:
    epub_path = tmp_path / "source.epub"
    epub_path.write_bytes(make_epub(CHAPTER))
    pdf_path = tmp_path / "source.pdf"
    write_pdf(
        pdf_path,
        [
            "BOOK OF MORMON - SCRIPTURE CHAT PROFILE V1",
            "1 Nephi 1:1 I, Nephi, having been born of goodly parents.",
            "1 Nephi 1:2 Yea, I make a record in the language of my father.",
        ],
    )

    epub_extraction = extract_epub(epub_path, ExtractionLimits())
    pdf_extraction = extract_pdf(pdf_path, ExtractionLimits())
    reconcile_source_spans(epub_extraction)
    reconcile_source_spans(pdf_extraction)
    epub = normalize_extraction(epub_extraction, MANIFEST)
    pdf = normalize_extraction(pdf_extraction, MANIFEST)
    validate_corpus(epub, MANIFEST)
    validate_corpus(pdf, MANIFEST)

    assert canonical_projection(epub) == canonical_projection(pdf)
