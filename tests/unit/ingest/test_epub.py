from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile

import pytest

from scripture_chat.ingest.base import ExtractionError, ExtractionLimits
from scripture_chat.ingest.epub import extract_epub


def make_epub(chapter: str, extra_members: dict[str, bytes] | None = None) -> bytes:
    payload = BytesIO()
    with ZipFile(payload, "w") as archive:
        archive.writestr("mimetype", "application/epub+zip", compress_type=ZIP_STORED)
        archive.writestr(
            "META-INF/container.xml",
            """<?xml version="1.0"?>
            <container xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
              <rootfiles><rootfile full-path="OEBPS/content.opf"
                media-type="application/oebps-package+xml"/></rootfiles>
            </container>""",
            compress_type=ZIP_DEFLATED,
        )
        archive.writestr(
            "OEBPS/content.opf",
            """<?xml version="1.0"?>
            <package xmlns="http://www.idpf.org/2007/opf" version="3.0">
              <metadata>
                <dc:title xmlns:dc="http://purl.org/dc/elements/1.1/">Book of Mormon</dc:title>
              </metadata>
              <manifest>
                <item id="chapter" href="chapter.xhtml"
                  media-type="application/xhtml+xml"/>
              </manifest>
              <spine><itemref idref="chapter"/></spine>
            </package>""",
            compress_type=ZIP_DEFLATED,
        )
        archive.writestr("OEBPS/chapter.xhtml", chapter, compress_type=ZIP_DEFLATED)
        for name, content in (extra_members or {}).items():
            archive.writestr(name, content, compress_type=ZIP_DEFLATED)
    return payload.getvalue()


VALID_CHAPTER = """<html xmlns="http://www.w3.org/1999/xhtml"><body>
<section data-scripture-profile="scripture-chat-v1">
<p data-reference="bofm/1-ne/3/7">
  And it came to pass that I, Nephi, said unto my father: I will go and do.
</p>
<p data-reference="bofm/1-ne/3/8">
  And it came to pass that I said unto my father:
  I know that the Lord giveth no commandments.
</p>
<a data-origin="bofm/1-ne/3/7" data-anchor="a"
  data-target="bofm/1-ne/3/8" data-source="official-footnote">a</a>
<aside data-note-id="note-a" data-origin="bofm/1-ne/3/7"
  data-anchor="a" data-kind="footnote">See verse 8.</aside>
</section></body></html>"""


def test_epub_preserves_passages_apparatus_and_source_members(tmp_path: Path) -> None:
    source = tmp_path / "book.epub"
    source.write_bytes(make_epub(VALID_CHAPTER))

    result = extract_epub(source, ExtractionLimits())

    assert result.profile == "scripture-chat-v1"
    assert [event.reference for event in result.passages] == [
        "bofm/1-ne/3/7",
        "bofm/1-ne/3/8",
    ]
    assert result.passages[0].source_spans[0].member == "OEBPS/chapter.xhtml"
    assert result.notes[0].note_id == "note-a"
    assert result.edges[0].target == "bofm/1-ne/3/8"


def test_epub_rejects_traversal_member(tmp_path: Path) -> None:
    source = tmp_path / "hostile.epub"
    source.write_bytes(make_epub(VALID_CHAPTER, {"../escape": b"bad"}))

    with pytest.raises(ExtractionError, match="unsafe EPUB member"):
        extract_epub(source, ExtractionLimits())


def test_epub_rejects_dtd_or_entity_input(tmp_path: Path) -> None:
    source = tmp_path / "entity.epub"
    chapter = """<!DOCTYPE html [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
    <html xmlns="http://www.w3.org/1999/xhtml"><body>&xxe;</body></html>"""
    source.write_bytes(make_epub(chapter))

    with pytest.raises(ExtractionError, match="DTD|entity|unsafe XML"):
        extract_epub(source, ExtractionLimits())


def test_epub_enforces_expanded_byte_budget(tmp_path: Path) -> None:
    source = tmp_path / "large.epub"
    source.write_bytes(make_epub(VALID_CHAPTER))

    with pytest.raises(ExtractionError, match="expanded-byte"):
        extract_epub(source, ExtractionLimits(max_expanded_bytes=200))


def test_epub_rejects_unknown_profile(tmp_path: Path) -> None:
    source = tmp_path / "unknown.epub"
    source.write_bytes(
        make_epub("<html xmlns='http://www.w3.org/1999/xhtml'><body>text</body></html>")
    )

    with pytest.raises(ExtractionError, match="unsupported EPUB source profile"):
        extract_epub(source, ExtractionLimits())
