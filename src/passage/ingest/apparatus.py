from __future__ import annotations

import re
from enum import StrEnum
from typing import Literal, cast

from pydantic import Field

from passage.domain.identifiers import CanonicalReference
from passage.domain.models import (
    ExternalChapterReferenceTarget,
    ExternalReferenceTarget,
    InternalChapterReferenceTarget,
    InternalReferenceTarget,
    ReferenceTarget,
    StrictModel,
)
from passage.domain.references import reference_target_key
from passage.ingest.base import ExtractionError

OFFICIAL_REFERENCE_GRAMMAR_VERSION: Literal["official-reference-v1"] = "official-reference-v1"
CHURCH_PDF_REFERENCE_GRAMMAR_VERSION: Literal["official-reference-v2"] = "official-reference-v2"

_TARGET_PATTERN = re.compile(
    r"^(?P<work>[a-z][a-z0-9-]*)/(?P<book>[a-z0-9-]+)/"
    r"(?P<chapter>[1-9]\d*)/(?P<verse>[1-9]\d*)(?:-(?P<end>[1-9]\d*))?$"
)
_AMBIGUOUS_SYNTAX = re.compile(r",|\s+(?:and|or)\s+", re.IGNORECASE)
_EXTERNAL_WORKS = frozenset({"bible", "dc", "pgp"})
_CHURCH_BOOKS: dict[str, tuple[Literal["bofm", "bible", "dc", "pgp"], str]] = {
    "1 Ne.": ("bofm", "1-ne"),
    "2 Ne.": ("bofm", "2-ne"),
    "Jacob": ("bofm", "jacob"),
    "Enos": ("bofm", "enos"),
    "Jarom": ("bofm", "jarom"),
    "Omni": ("bofm", "omni"),
    "W of M": ("bofm", "w-of-m"),
    "Mosiah": ("bofm", "mosiah"),
    "Alma": ("bofm", "alma"),
    "Hel.": ("bofm", "hel"),
    "3 Ne.": ("bofm", "3-ne"),
    "4 Ne.": ("bofm", "4-ne"),
    "Morm.": ("bofm", "morm"),
    "Ether": ("bofm", "ether"),
    "Moro.": ("bofm", "moro"),
    "Gen.": ("bible", "gen"),
    "Ex.": ("bible", "ex"),
    "Lev.": ("bible", "lev"),
    "Num.": ("bible", "num"),
    "Deut.": ("bible", "deut"),
    "Josh.": ("bible", "josh"),
    "Judg.": ("bible", "judg"),
    "Ruth": ("bible", "ruth"),
    "1 Sam.": ("bible", "1-sam"),
    "2 Sam.": ("bible", "2-sam"),
    "1 Kgs.": ("bible", "1-kgs"),
    "2 Kgs.": ("bible", "2-kgs"),
    "1 Chr.": ("bible", "1-chr"),
    "2 Chr.": ("bible", "2-chr"),
    "Ezra": ("bible", "ezra"),
    "Neh.": ("bible", "neh"),
    "Esth.": ("bible", "esth"),
    "Job": ("bible", "job"),
    "Ps.": ("bible", "ps"),
    "Prov.": ("bible", "prov"),
    "Eccl.": ("bible", "eccl"),
    "Song.": ("bible", "song"),
    "Isa.": ("bible", "isa"),
    "Jer.": ("bible", "jer"),
    "Lam.": ("bible", "lam"),
    "Ezek.": ("bible", "ezek"),
    "Dan.": ("bible", "dan"),
    "Hosea": ("bible", "hosea"),
    "Joel": ("bible", "joel"),
    "Amos": ("bible", "amos"),
    "Obad.": ("bible", "obad"),
    "Jonah": ("bible", "jonah"),
    "Micah": ("bible", "micah"),
    "Nahum": ("bible", "nahum"),
    "Hab.": ("bible", "hab"),
    "Zeph.": ("bible", "zeph"),
    "Hag.": ("bible", "hag"),
    "Zech.": ("bible", "zech"),
    "Mal.": ("bible", "mal"),
    "Matt.": ("bible", "matt"),
    "Mark": ("bible", "mark"),
    "Luke": ("bible", "luke"),
    "John": ("bible", "john"),
    "Acts": ("bible", "acts"),
    "Rom.": ("bible", "rom"),
    "1 Cor.": ("bible", "1-cor"),
    "2 Cor.": ("bible", "2-cor"),
    "Gal.": ("bible", "gal"),
    "Eph.": ("bible", "eph"),
    "Philip.": ("bible", "philip"),
    "Col.": ("bible", "col"),
    "1 Thes.": ("bible", "1-thes"),
    "2 Thes.": ("bible", "2-thes"),
    "1 Tim.": ("bible", "1-tim"),
    "2 Tim.": ("bible", "2-tim"),
    "Titus": ("bible", "titus"),
    "Philem.": ("bible", "philem"),
    "Heb.": ("bible", "heb"),
    "James": ("bible", "james"),
    "1 Pet.": ("bible", "1-pet"),
    "2 Pet.": ("bible", "2-pet"),
    "1 Jn.": ("bible", "1-jn"),
    "2 Jn.": ("bible", "2-jn"),
    "3 Jn.": ("bible", "3-jn"),
    "Jude": ("bible", "jude"),
    "Rev.": ("bible", "rev"),
    "JST Gen.": ("bible", "jst-gen"),
    "JST Isa.": ("bible", "jst-isa"),
    "JST Matt.": ("bible", "jst-matt"),
    "JST Rev.": ("bible", "jst-rev"),
    "D&C": ("dc", "section"),
    "Moses": ("pgp", "moses"),
    "Abr.": ("pgp", "abr"),
    "JS—M": ("pgp", "js-m"),
    "JS—H": ("pgp", "js-h"),
    "A of F": ("pgp", "a-of-f"),
}
_CHURCH_BOOK_ALTERNATION = "|".join(
    re.escape(label) for label in sorted(_CHURCH_BOOKS, key=len, reverse=True)
)
_CHURCH_BOOK_PATTERN = re.compile(rf"^(?P<label>{_CHURCH_BOOK_ALTERNATION})\s*")
_CHURCH_REFERENCE_START = re.compile(rf"(?:{_CHURCH_BOOK_ALTERNATION})(?=\s*[1-9]\d*)")
_CHURCH_ANY_REFERENCE_SIGNAL = re.compile(
    rf"(?:{_CHURCH_BOOK_ALTERNATION})\s*[1-9]\d*(?:\s*:\s*[1-9]\d*)?"
)
_CHURCH_UNKNOWN_REFERENCE_SIGNAL = re.compile(
    r"(?:^|;\s*)(?:[1-3]\s+)?[A-Z][A-Za-z]{0,8}\.\s*[1-9]\d*\s*:\s*[1-9]\d*"
)
_CHURCH_TOPIC_SUFFIX = re.compile(r"\.\s+(?=(?:TG|IE|HEB|GR|OR|BD)\b)")
_CHURCH_VERSE = re.compile(
    r"^(?P<verse>[1-9]\d*)(?:\s*[-\u2013]\s*(?P<end>[1-9]\d*))?"
    r"(?:\s+\((?P<context>(?:[1-9]\d*(?:\s*[-\u2013]\s*[1-9]\d*)?"
    r"(?:\s*,\s*[1-9]\d*(?:\s*[-\u2013]\s*[1-9]\d*)?)*|Bible Appendix|"
    r"[A-Za-z0-9.&— ]+\s+[1-9]\d*:[1-9]\d*\s+note\s+[a-z]))\))?$"
)
_CHURCH_CHAPTER = re.compile(r"^(?P<chapter>[1-9]\d*)(?:\s*[-\u2013]\s*(?P<end>[1-9]\d*))?$")
_TRAILING_PDF_HEADING = re.compile(r"\s*\[[A-Z][A-Z ]+\]\s*$")
_TRAILING_CHAPTER_PROSE = re.compile(r"\s+for\s+[^.;]+$", re.IGNORECASE)


class OfficialReferenceParseState(StrEnum):
    PARSED = "parsed"
    UNRESOLVED_EXTERNAL = "unresolved_external"
    UNSUPPORTED = "unsupported"
    AMBIGUOUS = "ambiguous"
    INVALID = "invalid"
    NO_REFERENCE = "no_reference"


class OfficialReferenceParseCode(StrEnum):
    PARSED = "official_reference_parsed"
    UNRESOLVED_EXTERNAL_TARGET = "official_reference_unresolved_external_target"
    UNSUPPORTED_SYNTAX = "official_reference_unsupported_syntax"
    AMBIGUOUS_SYNTAX = "official_reference_ambiguous_syntax"
    INVALID_CANONICAL_TARGET = "official_reference_invalid_canonical_target"
    DUPLICATE_TARGET = "official_reference_duplicate_target"
    NO_REFERENCE = "official_reference_not_present"


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


def parse_church_pdf_footnote(
    value: str,
    *,
    valid_internal_references: set[str],
) -> OfficialReferenceParseResult:
    raw_text = value
    candidate = value.strip()
    if not candidate:
        return _church_failure(raw_text, OfficialReferenceParseState.UNSUPPORTED)
    if not _CHURCH_ANY_REFERENCE_SIGNAL.search(candidate):
        if _CHURCH_UNKNOWN_REFERENCE_SIGNAL.search(candidate):
            return _church_failure(raw_text, OfficialReferenceParseState.UNSUPPORTED)
        return OfficialReferenceParseResult(
            grammar_version=CHURCH_PDF_REFERENCE_GRAMMAR_VERSION,
            raw_text=raw_text,
            state=OfficialReferenceParseState.NO_REFERENCE,
            code=OfficialReferenceParseCode.NO_REFERENCE,
        )
    suffix = _CHURCH_TOPIC_SUFFIX.search(candidate)
    if suffix is not None:
        candidate = candidate[: suffix.start()]
    if candidate.startswith(("IE ", "BD ")):
        reference_start = _first_church_reference_start(candidate)
        if reference_start is None:
            return _church_failure(raw_text, OfficialReferenceParseState.UNSUPPORTED)
        candidate = candidate[reference_start:]
    candidate = candidate.replace(", quoted in ", "; ")
    see_also = candidate.find(". See also ")
    if see_also >= 0:
        remainder = candidate[see_also + len(". See also ") :]
        candidate = (
            f"{candidate[:see_also]}; {remainder}"
            if _CHURCH_ANY_REFERENCE_SIGNAL.search(remainder)
            else candidate[:see_also]
        )
    candidate = _TRAILING_PDF_HEADING.sub("", candidate)
    candidate = candidate.removeprefix("See also ").removeprefix("See ").strip()
    candidate = candidate.removesuffix(";").removesuffix(".").strip()
    if _CHURCH_BOOK_PATTERN.match(candidate) is None:
        reference_start = _first_church_reference_start(candidate)
        if reference_start is None or not candidate[:reference_start].rstrip().endswith(
            (" in", " spans")
        ):
            return _church_failure(raw_text, OfficialReferenceParseState.UNSUPPORTED)
        candidate = candidate[reference_start:]
    if ":" not in candidate:
        candidate = _TRAILING_CHAPTER_PROSE.sub("", candidate)

    members = [member.strip() for member in candidate.split(";")]
    if any(not member for member in members):
        return _church_failure(raw_text, OfficialReferenceParseState.UNSUPPORTED)

    current_book: tuple[Literal["bofm", "bible", "dc", "pgp"], str] | None = None
    current_label: str | None = None
    targets: list[ReferenceTarget] = []
    normalized_members: list[str] = []
    seen: set[str] = set()
    has_external = False
    for member in members:
        book_match = _CHURCH_BOOK_PATTERN.match(member)
        if book_match is not None:
            current_label = book_match.group("label")
            current_book = _CHURCH_BOOKS[current_label]
            member = member[book_match.end() :]
        if current_book is None or current_label is None:
            return _church_failure(raw_text, OfficialReferenceParseState.UNSUPPORTED)
        if ":" not in member:
            chapter_match = _CHURCH_CHAPTER.fullmatch(member)
            if chapter_match is None:
                return _church_failure(raw_text, OfficialReferenceParseState.UNSUPPORTED)
            chapter = int(chapter_match.group("chapter"))
            end_chapter = int(chapter_match.group("end")) if chapter_match.group("end") else None
            if end_chapter is not None and end_chapter < chapter:
                return _church_failure(raw_text, OfficialReferenceParseState.INVALID)
            work, book = current_book
            label = f"{current_label} {member}"
            if work == "bofm":
                chapters = range(chapter, (end_chapter or chapter) + 1)
                if any(
                    not any(
                        reference.startswith(f"bofm/{book}/{candidate_chapter}/")
                        for reference in valid_internal_references
                    )
                    for candidate_chapter in chapters
                ):
                    return _church_failure(raw_text, OfficialReferenceParseState.INVALID)
                chapter_target: ReferenceTarget = InternalChapterReferenceTarget(
                    book=book,
                    chapter=chapter,
                    end_chapter=end_chapter,
                    label=label,
                )
            else:
                chapter_target = ExternalChapterReferenceTarget(
                    work=cast(Literal["bible", "dc", "pgp"], work),
                    book=book,
                    chapter=chapter,
                    end_chapter=end_chapter,
                    unit="section" if work == "dc" else "chapter",
                    label=label,
                )
                has_external = True
            key = _target_key(chapter_target)
            if key in seen:
                return _church_failure(
                    raw_text,
                    OfficialReferenceParseState.INVALID,
                    OfficialReferenceParseCode.DUPLICATE_TARGET,
                )
            seen.add(key)
            targets.append(chapter_target)
            normalized_members.append(key)
            continue
        chapter_text, verse_text = member.split(":", maxsplit=1)
        if not chapter_text.isdigit() or int(chapter_text) < 1:
            return _church_failure(raw_text, OfficialReferenceParseState.INVALID)
        chapter = int(chapter_text)
        verse_members = _split_top_level_commas(verse_text)
        if not verse_members:
            return _church_failure(raw_text, OfficialReferenceParseState.UNSUPPORTED)
        for verse_member in verse_members:
            verse_match = _CHURCH_VERSE.fullmatch(verse_member.strip())
            if verse_match is None:
                return _church_failure(raw_text, OfficialReferenceParseState.UNSUPPORTED)
            verse = int(verse_match.group("verse"))
            end = int(verse_match.group("end")) if verse_match.group("end") else None
            if end is not None and end < verse:
                return _church_failure(raw_text, OfficialReferenceParseState.INVALID)
            work, book = current_book
            label = f"{current_label} {chapter}:{verse_member.strip()}"
            if work == "bofm":
                normalized = f"bofm/{book}/{chapter}/{verse}" + (f"-{end}" if end else "")
                try:
                    reference = CanonicalReference.parse(normalized)
                except ValueError:
                    return _church_failure(raw_text, OfficialReferenceParseState.INVALID)
                if any(
                    str(passage) not in valid_internal_references
                    for passage in reference.passages()
                ):
                    return _church_failure(raw_text, OfficialReferenceParseState.INVALID)
                target: ReferenceTarget = InternalReferenceTarget(
                    book=book,
                    chapter=chapter,
                    verse=verse,
                    end_verse=end,
                    label=label,
                )
            else:
                target = ExternalReferenceTarget(
                    work=cast(Literal["bible", "dc", "pgp"], work),
                    book=book,
                    chapter=chapter,
                    verse=verse,
                    end_verse=end,
                    label=label,
                )
                has_external = True
            key = _target_key(target)
            if key in seen:
                return _church_failure(
                    raw_text,
                    OfficialReferenceParseState.INVALID,
                    OfficialReferenceParseCode.DUPLICATE_TARGET,
                )
            seen.add(key)
            targets.append(target)
            normalized_members.append(key)

    state = (
        OfficialReferenceParseState.UNRESOLVED_EXTERNAL
        if has_external
        else OfficialReferenceParseState.PARSED
    )
    code = (
        OfficialReferenceParseCode.UNRESOLVED_EXTERNAL_TARGET
        if has_external
        else OfficialReferenceParseCode.PARSED
    )
    return OfficialReferenceParseResult(
        grammar_version=CHURCH_PDF_REFERENCE_GRAMMAR_VERSION,
        raw_text=raw_text,
        normalized_text="; ".join(normalized_members),
        state=state,
        code=code,
        targets=targets,
    )


def _church_failure(
    raw_text: str,
    state: OfficialReferenceParseState,
    code: OfficialReferenceParseCode | None = None,
) -> OfficialReferenceParseResult:
    if code is None:
        code = (
            OfficialReferenceParseCode.INVALID_CANONICAL_TARGET
            if state is OfficialReferenceParseState.INVALID
            else OfficialReferenceParseCode.UNSUPPORTED_SYNTAX
        )
    return OfficialReferenceParseResult(
        grammar_version=CHURCH_PDF_REFERENCE_GRAMMAR_VERSION,
        raw_text=raw_text,
        state=state,
        code=code,
    )


def _split_top_level_commas(value: str) -> list[str]:
    members: list[str] = []
    start = 0
    depth = 0
    for index, character in enumerate(value):
        if character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
            if depth < 0:
                return []
        elif character == "," and depth == 0:
            members.append(value[start:index].strip())
            start = index + 1
    if depth != 0:
        return []
    members.append(value[start:].strip())
    return members if all(members) else []


def _first_church_reference_start(value: str) -> int | None:
    match = _CHURCH_REFERENCE_START.search(value)
    return match.start() if match else None


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
    return reference_target_key(target)
