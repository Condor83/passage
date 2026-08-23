from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field, model_validator

BOOK_SLUGS = (
    "1-ne",
    "2-ne",
    "jacob",
    "enos",
    "jarom",
    "omni",
    "w-of-m",
    "mosiah",
    "alma",
    "hel",
    "3-ne",
    "4-ne",
    "morm",
    "ether",
    "moro",
)
BOOK_SLUG_SET = frozenset(BOOK_SLUGS)
NEW_TESTAMENT_BOOK_SLUGS = (
    "matt",
    "mark",
    "luke",
    "john",
    "acts",
    "rom",
    "1-cor",
    "2-cor",
    "gal",
    "eph",
    "philip",
    "col",
    "1-thes",
    "2-thes",
    "1-tim",
    "2-tim",
    "titus",
    "philem",
    "heb",
    "james",
    "1-pet",
    "2-pet",
    "1-jn",
    "2-jn",
    "3-jn",
    "jude",
    "rev",
)
NEW_TESTAMENT_BOOK_SLUG_SET = frozenset(NEW_TESTAMENT_BOOK_SLUGS)
_REFERENCE_PATTERN = re.compile(
    r"^bofm/(?P<book>[a-z0-9-]+)/(?P<chapter>[1-9]\d*)/(?P<verse>[1-9]\d*)(?:-(?P<end>[1-9]\d*))?$"
)
_CORPUS_REFERENCE_PATTERN = re.compile(
    r"^(?P<work>bofm|nt)/(?P<book>[a-z0-9-]+)/(?P<chapter>[1-9]\d*)/"
    r"(?P<verse>[1-9]\d*)(?:-(?P<end>[1-9]\d*))?$"
)


def validate_corpus_reference(value: str) -> tuple[str, str, int, int, int | None]:
    """Validate a private corpus reference without expanding the public API contract."""
    match = _CORPUS_REFERENCE_PATTERN.fullmatch(value)
    if match is None:
        raise ValueError(f"invalid corpus reference: {value}")
    groups = match.groupdict()
    work = groups["work"]
    book = groups["book"]
    allowed = BOOK_SLUG_SET if work == "bofm" else NEW_TESTAMENT_BOOK_SLUG_SET
    if book not in allowed:
        raise ValueError(f"unknown {work} corpus book slug: {book}")
    verse = int(groups["verse"])
    end = int(groups["end"]) if groups["end"] else None
    if end is not None and end < verse:
        raise ValueError("range end must not precede its start")
    return work, book, int(groups["chapter"]), verse, end


class CanonicalReference(BaseModel):
    """Stable Book of Mormon passage identifier."""

    model_config = ConfigDict(frozen=True)

    work: str = Field(default="bofm", pattern=r"^bofm$")
    book: str
    chapter: int = Field(ge=1)
    verse: int = Field(ge=1)
    end_verse: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def validate_reference(self) -> CanonicalReference:
        if self.book not in BOOK_SLUG_SET:
            raise ValueError(f"unknown canonical book slug: {self.book}")
        if self.end_verse is not None and self.end_verse < self.verse:
            raise ValueError("range end must not precede its start")
        return self

    @classmethod
    def parse(cls, value: str) -> CanonicalReference:
        match = _REFERENCE_PATTERN.fullmatch(value)
        if match is None:
            raise ValueError(f"invalid canonical reference: {value}")
        groups = match.groupdict()
        return cls(
            book=groups["book"],
            chapter=int(groups["chapter"]),
            verse=int(groups["verse"]),
            end_verse=int(groups["end"]) if groups["end"] else None,
        )

    def passages(self) -> tuple[CanonicalReference, ...]:
        end = self.end_verse or self.verse
        return tuple(
            CanonicalReference(book=self.book, chapter=self.chapter, verse=verse)
            for verse in range(self.verse, end + 1)
        )

    def __str__(self) -> str:
        suffix = f"-{self.end_verse}" if self.end_verse is not None else ""
        return f"{self.work}/{self.book}/{self.chapter}/{self.verse}{suffix}"
