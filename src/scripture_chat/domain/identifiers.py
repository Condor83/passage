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
_REFERENCE_PATTERN = re.compile(
    r"^bofm/(?P<book>[a-z0-9-]+)/(?P<chapter>[1-9]\d*)/(?P<verse>[1-9]\d*)(?:-(?P<end>[1-9]\d*))?$"
)


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
