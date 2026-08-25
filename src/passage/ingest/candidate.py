from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from pydantic import Field

from passage.domain.models import (
    ApparatusNote,
    Identifier,
    Passage,
    ReferenceEdge,
    Sha256,
    SourceSpan,
    StrictModel,
)
from passage.ingest.normalize import (
    NormalizedCorpus,
    serialize_jsonl,
)
from passage.ingest.validation import (
    StructureManifest,
    load_default_structure_manifest,
    load_new_testament_structure_manifest,
    validate_corpus,
)

MAX_CANDIDATE_BYTES = 64 * 1024 * 1024


class CandidateManifest(StrictModel):
    schema_version: Literal[1]
    scope: Literal["book-of-mormon", "new-testament"]
    artifact: Identifier
    candidate_sha256: Sha256
    normalized_digest: Sha256
    source_format: Literal["epub", "pdf"]
    status: Literal["review_required"]
    active: Literal[False]
    accepted: Literal[False]
    passage_count: int = Field(ge=1)
    note_anchor_count: int = Field(ge=0)
    edge_count: int = Field(ge=0)


class _CorpusHeader(StrictModel):
    type: Literal["corpus"]
    source_format: Literal["epub", "pdf"]
    source_profile: Identifier
    normalized_digest: Sha256


@dataclass(frozen=True, slots=True)
class LoadedCandidate:
    corpus: NormalizedCorpus
    manifest: CandidateManifest
    structure: StructureManifest
    candidate_sha256: str


def load_candidate(
    candidate_path: Path,
    manifest_path: Path | None = None,
    *,
    structure: StructureManifest | None = None,
) -> LoadedCandidate:
    candidate = candidate_path.expanduser().absolute()
    manifest_file = (
        manifest_path.expanduser().absolute()
        if manifest_path is not None
        else candidate.with_name("manifest.json")
    )
    manifest = CandidateManifest.model_validate_json(manifest_file.read_text(encoding="utf-8"))
    if manifest.artifact != candidate.name:
        raise ValueError("candidate filename does not match manifest artifact")
    with candidate.open("rb") as stream:
        payload = stream.read(MAX_CANDIDATE_BYTES + 1)
    if len(payload) > MAX_CANDIDATE_BYTES:
        raise ValueError("candidate exceeds the 64 MiB import limit")
    candidate_sha256 = hashlib.sha256(payload).hexdigest()
    if candidate_sha256 != manifest.candidate_sha256:
        raise ValueError("candidate digest does not match manifest")

    header, passages, notes, edges = _parse_records(payload)
    corpus = NormalizedCorpus(
        source_format=header.source_format,
        source_profile=header.source_profile,
        passages=passages,
        notes=notes,
        edges=edges,
        normalized_digest=header.normalized_digest,
    )
    if corpus.normalized_digest != manifest.normalized_digest:
        raise ValueError("candidate normalized digest does not match manifest")
    if corpus.source_format != manifest.source_format:
        raise ValueError("candidate source format does not match manifest")
    if len(corpus.passages) != manifest.passage_count:
        raise ValueError("candidate passage count does not match manifest")
    if len(corpus.notes) != manifest.note_anchor_count:
        raise ValueError("candidate note count does not match manifest")
    if len(corpus.edges) != manifest.edge_count:
        raise ValueError("candidate edge count does not match manifest")
    if serialize_jsonl(corpus) != payload:
        raise ValueError("candidate does not match its canonical serialized form")
    validate_candidate_records(corpus)

    resolved_structure = structure or _default_structure(manifest.scope)
    expected_work = "bofm" if manifest.scope == "book-of-mormon" else "nt"
    if resolved_structure.work != expected_work:
        raise ValueError("candidate scope does not match structure manifest")
    validate_corpus(corpus, resolved_structure)
    return LoadedCandidate(corpus, manifest, resolved_structure, candidate_sha256)


def validate_candidate_records(corpus: NormalizedCorpus) -> None:
    def has_mismatched_span(spans: list[SourceSpan]) -> bool:
        return any(span.kind != corpus.source_format for span in spans)

    if (
        any(has_mismatched_span(passage.source_spans) for passage in corpus.passages)
        or any(has_mismatched_span(note.source_spans) for note in corpus.notes)
        or any(has_mismatched_span(edge.source_spans) for edge in corpus.edges)
    ):
        raise ValueError("candidate source span kind does not match source format")

    anchors = Counter((note.origin_reference, note.anchor) for note in corpus.notes)
    if any(count > 1 for count in anchors.values()):
        raise ValueError("candidate contains duplicate apparatus anchors")

    official_by_reference: dict[str, list[str]] = defaultdict(list)
    for note in corpus.notes:
        if note.note_kind == "official-footnote":
            official_by_reference[note.origin_reference].append(note.anchor)
    for reference_anchors in official_by_reference.values():
        expected = [chr(ord("a") + index) for index in range(len(reference_anchors))]
        if sorted(reference_anchors) != expected:
            raise ValueError("candidate official footnote anchors are not sequential")


def _parse_records(
    payload: bytes,
) -> tuple[_CorpusHeader, list[Passage], list[ApparatusNote], list[ReferenceEdge]]:
    if not payload.endswith(b"\n"):
        raise ValueError("candidate must end with a newline")
    lines = payload.splitlines()
    if not lines:
        raise ValueError("candidate contains no records")

    header: _CorpusHeader | None = None
    passages: list[Passage] = []
    notes: list[ApparatusNote] = []
    edges: list[ReferenceEdge] = []
    record_phase = 0
    phases = {"corpus": 0, "passage": 1, "note": 2, "edge": 3}
    for line_number, line in enumerate(lines, start=1):
        if not line:
            raise ValueError(f"candidate line {line_number} is blank")
        try:
            record: Any = json.loads(line)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"candidate line {line_number} is not valid JSON") from exc
        if not isinstance(record, dict):
            raise ValueError(f"candidate line {line_number} is not an object")
        record_type = record.get("type")
        if record_type not in phases:
            raise ValueError(f"candidate line {line_number} has an unknown record type")
        phase = phases[record_type]
        if phase < record_phase:
            raise ValueError("candidate records are not grouped in canonical order")
        record_phase = phase
        if record_type == "corpus":
            if line_number != 1 or header is not None:
                raise ValueError("candidate must contain one corpus header as its first record")
            header = _CorpusHeader.model_validate(record)
            continue
        if header is None:
            raise ValueError("candidate must begin with a corpus header")
        body = {key: value for key, value in record.items() if key != "type"}
        if record_type == "passage":
            passages.append(Passage.model_validate(body))
        elif record_type == "note":
            notes.append(ApparatusNote.model_validate(body))
        else:
            edges.append(ReferenceEdge.model_validate(body))
    if header is None:
        raise ValueError("candidate contains no corpus header")
    return header, passages, notes, edges


def _default_structure(scope: str) -> StructureManifest:
    if scope == "book-of-mormon":
        return load_default_structure_manifest()
    return load_new_testament_structure_manifest()
