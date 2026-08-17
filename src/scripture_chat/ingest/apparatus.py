from __future__ import annotations

import re

from scripture_chat.domain.identifiers import CanonicalReference
from scripture_chat.domain.models import ReferenceTarget
from scripture_chat.ingest.base import ExtractionError

_EXTERNAL_REFERENCE = re.compile(
    r"^(?P<work>bible|dc|pgp)/(?P<book>[a-z0-9-]+)/(?P<chapter>[1-9]\d*)/(?P<verse>[1-9]\d*)(?:-(?P<end>[1-9]\d*))?$"
)


def normalize_target(value: str) -> ReferenceTarget:
    if value.startswith("bofm/"):
        reference = CanonicalReference.parse(value)
        return ReferenceTarget(
            work="bofm",
            book=reference.book,
            chapter=reference.chapter,
            verse=reference.verse,
            end_verse=reference.end_verse,
            in_corpus=True,
        )
    match = _EXTERNAL_REFERENCE.fullmatch(value)
    if match is None:
        raise ExtractionError(f"invalid external reference target: {value}")
    groups = match.groupdict()
    end = int(groups["end"]) if groups["end"] else None
    verse = int(groups["verse"])
    if end is not None and end < verse:
        raise ExtractionError(f"invalid external reference range: {value}")
    return ReferenceTarget(
        work=groups["work"],
        book=groups["book"],
        chapter=int(groups["chapter"]),
        verse=verse,
        end_verse=end,
        in_corpus=False,
    )
