from __future__ import annotations

import re
from enum import StrEnum
from typing import Literal, cast

from pydantic import Field

from passage.domain.identifiers import CanonicalReference
from passage.domain.models import (
    ExternalReferenceTarget,
    InternalReferenceTarget,
    ReferenceTarget,
    StrictModel,
)
from passage.ingest.base import ExtractionError

OFFICIAL_REFERENCE_GRAMMAR_VERSION = "official-reference-v1"

_TARGET_PATTERN = re.compile(
    r"^(?P<work>[a-z][a-z0-9-]*)/(?P<book>[a-z0-9-]+)/"
    r"(?P<chapter>[1-9]\d*)/(?P<verse>[1-9]\d*)(?:-(?P<end>[1-9]\d*))?$"
)
_AMBIGUOUS_SYNTAX = re.compile(r",|\s+(?:and|or)\s+", re.IGNORECASE)
_EXTERNAL_WORKS = frozenset({"bible", "dc", "pgp"})


class OfficialReferenceParseState(StrEnum):
    PARSED = "parsed"
    UNRESOLVED_EXTERNAL = "unresolved_external"
    UNSUPPORTED = "unsupported"
    AMBIGUOUS = "ambiguous"
    INVALID = "invalid"


class OfficialReferenceParseCode(StrEnum):
    PARSED = "official_reference_parsed"
    UNRESOLVED_EXTERNAL_TARGET = "official_reference_unresolved_external_target"
    UNSUPPORTED_SYNTAX = "official_reference_unsupported_syntax"
    AMBIGUOUS_SYNTAX = "official_reference_ambiguous_syntax"
    INVALID_CANONICAL_TARGET = "official_reference_invalid_canonical_target"
    DUPLICATE_TARGET = "official_reference_duplicate_target"


class OfficialReferenceParseResult(StrictModel):
    grammar_version: str = OFFICIAL_REFERENCE_GRAMMAR_VERSION
    raw_text: str
    normalized_text: str | None = None
    state: OfficialReferenceParseState
    code: OfficialReferenceParseCode
    targets: list[ReferenceTarget] = Field(default_factory=list)


class OfficialReferenceParseError(ExtractionError):
    def __init__(self, result: OfficialReferenceParseResult) -> None:
        self.result = result
        super().__init__(result.code.value)


def parse_official_references(
    value: str,
    *,
    valid_internal_references: set[str],
) -> OfficialReferenceParseResult:
    raw_text = value
    candidate = value.strip()
    if candidate.endswith("."):
        candidate = candidate[:-1].rstrip()
    if not candidate:
        return _failure(
            raw_text,
            OfficialReferenceParseState.UNSUPPORTED,
            OfficialReferenceParseCode.UNSUPPORTED_SYNTAX,
        )
    if _AMBIGUOUS_SYNTAX.search(candidate):
        return _failure(
            raw_text,
            OfficialReferenceParseState.AMBIGUOUS,
            OfficialReferenceParseCode.AMBIGUOUS_SYNTAX,
        )

    members = [member.strip() for member in candidate.split(";")]
    if any(not member for member in members):
        return _failure(
            raw_text,
            OfficialReferenceParseState.UNSUPPORTED,
            OfficialReferenceParseCode.UNSUPPORTED_SYNTAX,
        )

    targets: list[ReferenceTarget] = []
    normalized_members: list[str] = []
    seen: set[str] = set()
    has_external = False
    for member in members:
        match = _TARGET_PATTERN.fullmatch(member)
        if match is None:
            return _failure(
                raw_text,
                OfficialReferenceParseState.UNSUPPORTED,
                OfficialReferenceParseCode.UNSUPPORTED_SYNTAX,
            )
        groups = match.groupdict()
        work = groups["work"]
        normalized = _normalized_member(groups)
        if work == "bofm":
            try:
                reference = CanonicalReference.parse(normalized)
            except ValueError:
                return _failure(
                    raw_text,
                    OfficialReferenceParseState.INVALID,
                    OfficialReferenceParseCode.INVALID_CANONICAL_TARGET,
                )
            if any(
                str(passage) not in valid_internal_references for passage in reference.passages()
            ):
                return _failure(
                    raw_text,
                    OfficialReferenceParseState.INVALID,
                    OfficialReferenceParseCode.INVALID_CANONICAL_TARGET,
                )
            target: ReferenceTarget = InternalReferenceTarget(
                book=reference.book,
                chapter=reference.chapter,
                verse=reference.verse,
                end_verse=reference.end_verse,
            )
        elif work in _EXTERNAL_WORKS:
            verse = int(groups["verse"])
            end = int(groups["end"]) if groups["end"] else None
            if end is not None and end < verse:
                return _failure(
                    raw_text,
                    OfficialReferenceParseState.INVALID,
                    OfficialReferenceParseCode.INVALID_CANONICAL_TARGET,
                )
            target = ExternalReferenceTarget(
                work=cast(Literal["bible", "dc", "pgp"], work),
                book=groups["book"],
                chapter=int(groups["chapter"]),
                verse=verse,
                end_verse=end,
            )
            has_external = True
        else:
            return _failure(
                raw_text,
                OfficialReferenceParseState.UNSUPPORTED,
                OfficialReferenceParseCode.UNSUPPORTED_SYNTAX,
            )

        target_key = _target_key(target)
        if target_key in seen:
            return _failure(
                raw_text,
                OfficialReferenceParseState.INVALID,
                OfficialReferenceParseCode.DUPLICATE_TARGET,
            )
        seen.add(target_key)
        targets.append(target)
        normalized_members.append(target_key)

    if has_external:
        state = OfficialReferenceParseState.UNRESOLVED_EXTERNAL
        code = OfficialReferenceParseCode.UNRESOLVED_EXTERNAL_TARGET
    else:
        state = OfficialReferenceParseState.PARSED
        code = OfficialReferenceParseCode.PARSED
    return OfficialReferenceParseResult(
        raw_text=raw_text,
        normalized_text="; ".join(normalized_members),
        state=state,
        code=code,
        targets=targets,
    )


def require_official_references(
    value: str,
    *,
    valid_internal_references: set[str],
) -> OfficialReferenceParseResult:
    result = parse_official_references(
        value,
        valid_internal_references=valid_internal_references,
    )
    if not result.targets:
        raise OfficialReferenceParseError(result)
    return result


def reference_target_key(target: ReferenceTarget) -> str:
    return _target_key(target)


def _failure(
    raw_text: str,
    state: OfficialReferenceParseState,
    code: OfficialReferenceParseCode,
) -> OfficialReferenceParseResult:
    return OfficialReferenceParseResult(raw_text=raw_text, state=state, code=code)


def _normalized_member(groups: dict[str, str | None]) -> str:
    suffix = f"-{groups['end']}" if groups["end"] else ""
    return f"{groups['work']}/{groups['book']}/{groups['chapter']}/{groups['verse']}{suffix}"


def _target_key(target: ReferenceTarget) -> str:
    suffix = f"-{target.end_verse}" if target.end_verse is not None else ""
    return f"{target.work}/{target.book}/{target.chapter}/{target.verse}{suffix}"
