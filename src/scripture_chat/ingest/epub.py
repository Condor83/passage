from __future__ import annotations

import posixpath
import re
import stat
from pathlib import Path, PurePosixPath
from zipfile import BadZipFile, ZipFile, ZipInfo

from defusedxml import ElementTree

from scripture_chat.domain.identifiers import CanonicalReference
from scripture_chat.domain.models import EpubSourceSpan
from scripture_chat.ingest.base import (
    ExtractedEdge,
    ExtractedNote,
    ExtractedPassage,
    ExtractionError,
    ExtractionLimits,
    ExtractionResult,
)
from scripture_chat.ingest.source_profiles import EPUB_PROFILE

_REMOTE_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def extract_epub(path: Path, limits: ExtractionLimits) -> ExtractionResult:
    _check_source_size(path, limits)
    try:
        with ZipFile(path) as archive:
            members = _validate_archive(archive, limits)
            container = _parse_xml(_read_member(archive, members, "META-INF/container.xml"), limits)
            rootfile = next(iter(container.findall(".//{*}rootfile")), None)
            if rootfile is None or not rootfile.attrib.get("full-path"):
                raise ExtractionError("EPUB container has no rootfile")
            opf_name = _safe_member_name(rootfile.attrib["full-path"])
            opf = _parse_xml(_read_member(archive, members, opf_name), limits)
            spine_members = _resolve_spine(opf_name, opf, members)
            return _extract_spine(path, archive, members, spine_members, limits)
    except BadZipFile as exc:
        raise ExtractionError("invalid EPUB ZIP container") from exc


def _check_source_size(path: Path, limits: ExtractionLimits) -> None:
    if path.stat().st_size > limits.max_source_bytes:
        raise ExtractionError("source-byte budget exceeded")


def _validate_archive(archive: ZipFile, limits: ExtractionLimits) -> dict[str, ZipInfo]:
    infos = archive.infolist()
    if len(infos) > limits.max_zip_members:
        raise ExtractionError("EPUB member budget exceeded")
    members: dict[str, ZipInfo] = {}
    expanded = 0
    for info in infos:
        name = _safe_member_name(info.filename)
        if name in members:
            raise ExtractionError(f"duplicate EPUB member: {name}")
        if info.flag_bits & 0x1:
            raise ExtractionError(f"encrypted EPUB member: {name}")
        mode = info.external_attr >> 16
        if mode and stat.S_ISLNK(mode):
            raise ExtractionError(f"symlink EPUB member: {name}")
        expanded += info.file_size
        if expanded > limits.max_expanded_bytes:
            raise ExtractionError("EPUB expanded-byte budget exceeded")
        if info.file_size:
            ratio = info.file_size / max(info.compress_size, 1)
            if ratio > limits.max_compression_ratio:
                raise ExtractionError("EPUB compression-ratio budget exceeded")
        members[name] = info
    return members


def _safe_member_name(name: str) -> str:
    if not name or "\\" in name or _REMOTE_SCHEME.match(name):
        raise ExtractionError(f"unsafe EPUB member: {name}")
    candidate = PurePosixPath(name)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ExtractionError(f"unsafe EPUB member: {name}")
    normalized = posixpath.normpath(name)
    if normalized in (".", "..") or normalized.startswith("../"):
        raise ExtractionError(f"unsafe EPUB member: {name}")
    return normalized


def _read_member(archive: ZipFile, members: dict[str, ZipInfo], name: str) -> bytes:
    try:
        info = members[_safe_member_name(name)]
    except KeyError as exc:
        raise ExtractionError(f"missing EPUB member: {name}") from exc
    return archive.read(info)


def _parse_xml(payload: bytes, limits: ExtractionLimits):
    upper = payload.upper()
    if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper:
        raise ExtractionError("DTD or entity declarations are forbidden in EPUB XML")
    try:
        root = ElementTree.fromstring(payload)
    except Exception as exc:
        raise ExtractionError("unsafe XML or malformed EPUB document") from exc
    nodes = 0
    text_chars = 0
    for element in root.iter():
        nodes += 1
        text_chars += len(element.text or "") + len(element.tail or "")
        if nodes > limits.max_xml_nodes or text_chars > limits.max_xml_text_chars:
            raise ExtractionError("EPUB XML budget exceeded")
    return root


def _resolve_spine(
    opf_name: str,
    opf,
    members: dict[str, ZipInfo],
) -> list[str]:
    manifest: dict[str, str] = {}
    base = posixpath.dirname(opf_name)
    for item in opf.findall(".//{*}manifest/{*}item"):
        item_id = item.attrib.get("id")
        href = item.attrib.get("href")
        media_type = item.attrib.get("media-type")
        if not item_id or not href:
            continue
        if _REMOTE_SCHEME.match(href) or href.startswith(("/", "#")):
            raise ExtractionError(f"unsafe EPUB manifest target: {href}")
        target = _safe_member_name(posixpath.join(base, href.split("#", 1)[0]))
        if target not in members:
            raise ExtractionError(f"EPUB manifest target is missing: {target}")
        if media_type in {"application/xhtml+xml", "text/html"}:
            manifest[item_id] = target
    spine: list[str] = []
    for itemref in opf.findall(".//{*}spine/{*}itemref"):
        target = manifest.get(itemref.attrib.get("idref", ""))
        if target is None:
            raise ExtractionError("EPUB spine references a missing XHTML manifest item")
        spine.append(target)
    if not spine:
        raise ExtractionError("EPUB spine contains no XHTML documents")
    return spine


def _extract_spine(
    path: Path,
    archive: ZipFile,
    members: dict[str, ZipInfo],
    spine_members: list[str],
    limits: ExtractionLimits,
) -> ExtractionResult:
    passages: list[ExtractedPassage] = []
    notes: list[ExtractedNote] = []
    edges: list[ExtractedEdge] = []
    profile_found = False
    order = 0
    for member in spine_members:
        payload = _read_member(archive, members, member)
        root = _parse_xml(payload, limits)
        if any(
            element.attrib.get("data-scripture-profile") == EPUB_PROFILE
            for element in root.iter()
        ):
            profile_found = True
        decoded = payload.decode("utf-8", errors="strict")
        for element in root.iter():
            reference = element.attrib.get("data-reference")
            if reference:
                CanonicalReference.parse(reference)
                text = _element_text(element)
                if not text:
                    raise ExtractionError(f"empty passage: {reference}")
                span = _epub_span(member, decoded, text, order)
                passages.append(
                    ExtractedPassage(reference=reference, text=text, source_spans=[span])
                )
                order += 1
            note_id = element.attrib.get("data-note-id")
            if note_id:
                origin = _required(element.attrib, "data-origin", "note")
                CanonicalReference.parse(origin)
                notes.append(
                    ExtractedNote(
                        note_id=note_id,
                        origin_reference=origin,
                        anchor=_required(element.attrib, "data-anchor", "note"),
                        kind=_required(element.attrib, "data-kind", "note"),
                        label=element.attrib.get("data-label"),
                        text=_element_text(element) or None,
                        source_spans=[_epub_span(member, decoded, _element_text(element), order)],
                    )
                )
                order += 1
            target = element.attrib.get("data-target")
            if target:
                origin = _required(element.attrib, "data-origin", "reference")
                CanonicalReference.parse(origin)
                edges.append(
                    ExtractedEdge(
                        origin_reference=origin,
                        origin_anchor=_required(element.attrib, "data-anchor", "reference"),
                        target=target,
                        source_attribution=_required(element.attrib, "data-source", "reference"),
                        source_spans=[_epub_span(member, decoded, _element_text(element), order)],
                    )
                )
                order += 1
    if not profile_found:
        raise ExtractionError("unsupported EPUB source profile")
    if not passages:
        raise ExtractionError("EPUB profile contains no passages")
    return ExtractionResult(
        source_path=path,
        source_format="epub",
        profile=EPUB_PROFILE,
        passages=passages,
        notes=notes,
        edges=edges,
    )


def _element_text(element) -> str:
    return " ".join("".join(element.itertext()).split())


def _epub_span(member: str, decoded: str, text: str, order: int) -> EpubSourceSpan:
    start = decoded.find(text) if text else -1
    if start < 0:
        start = 0
    return EpubSourceSpan(
        member=member,
        start=start,
        end=max(start + len(text), start + 1),
        order=order,
    )


def _required(attributes: dict[str, str], name: str, kind: str) -> str:
    value = attributes.get(name)
    if not value:
        raise ExtractionError(f"{kind} is missing {name}")
    return value
