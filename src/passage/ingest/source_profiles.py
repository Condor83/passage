from __future__ import annotations

import re

EPUB_PROFILE = "passage-v1"
EPUB_PROFILE_MARKER = 'data-scripture-profile="passage-v1"'
PDF_PROFILE_MARKER = "BOOK OF MORMON - PASSAGE PROFILE V1"

PDF_BOOK_SLUGS = {
    "1 nephi": "1-ne",
    "2 nephi": "2-ne",
    "jacob": "jacob",
    "enos": "enos",
    "jarom": "jarom",
    "omni": "omni",
    "words of mormon": "w-of-m",
    "mosiah": "mosiah",
    "alma": "alma",
    "helaman": "hel",
    "3 nephi": "3-ne",
    "4 nephi": "4-ne",
    "mormon": "morm",
    "ether": "ether",
    "moroni": "moro",
}
PDF_VERSE_PATTERN = re.compile(
    r"^(?P<book>1 Nephi|2 Nephi|Jacob|Enos|Jarom|Omni|Words of Mormon|"
    r"Mosiah|Alma|Helaman|3 Nephi|4 Nephi|Mormon|Ether|Moroni) "
    r"(?P<chapter>[1-9]\d*):(?P<verse>[1-9]\d*) (?P<text>\S.*)$",
    re.IGNORECASE,
)
