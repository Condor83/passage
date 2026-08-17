from __future__ import annotations

import hashlib
import json
from typing import Any

from pydantic import Field

from scripture_chat.domain.models import (
    ApparatusNote,
    Passage,
    ReferenceEdge,
    StrictModel,
)
from scripture_chat.ingest.apparatus import normalize_target
from scripture_chat.ingest.base import ExtractionResult
from scripture_chat.ingest.validation import StructureManifest


class NormalizedCorpus(StrictModel):
    source_format: str
    source_profile: str
    passages: list[Passage]
    notes: list[ApparatusNote] = Field(default_factory=list)
    edges: list[ReferenceEdge] = Field(default_factory=list)
    normalized_digest: str


def normalize_extraction(
    extraction: ExtractionResult,
    structure: StructureManifest,
) -> NormalizedCorpus:
    order_by_reference = {
        reference: index for index, reference in enumerate(structure.expected_references())
    }
    passages = [
        Passage(
            reference=event.reference,
            text=event.text,
            canonical_order=order_by_reference.get(event.reference, len(order_by_reference)),
            content_hash=_sha256(event.text.encode("utf-8")),
            source_spans=event.source_spans,
        )
        for event in extraction.passages
    ]
    notes = [
        ApparatusNote(
            note_id=event.note_id,
            origin_reference=event.origin_reference,
            anchor=event.anchor,
            label=event.label,
            text=event.text,
            note_kind=event.kind,
            source_spans=event.source_spans,
        )
        for event in extraction.notes
    ]
    edges = [
        ReferenceEdge(
            edge_id=_stable_id(
                event.origin_reference,
                event.origin_anchor,
                event.target,
                event.source_attribution,
            ),
            origin_reference=event.origin_reference,
            origin_anchor=event.origin_anchor,
            target=normalize_target(event.target),
            source_attribution=event.source_attribution,
        )
        for event in extraction.edges
    ]
    records = {
        "source_format": extraction.source_format,
        "source_profile": extraction.profile,
        "passages": [passage.model_dump(mode="json") for passage in passages],
        "notes": [note.model_dump(mode="json") for note in notes],
        "edges": [edge.model_dump(mode="json") for edge in edges],
    }
    digest = _sha256(_canonical_json(records))
    return NormalizedCorpus(**records, normalized_digest=digest)


def serialize_jsonl(corpus: NormalizedCorpus) -> bytes:
    lines: list[bytes] = [
        _canonical_json(
            {
                "type": "corpus",
                "source_format": corpus.source_format,
                "source_profile": corpus.source_profile,
                "normalized_digest": corpus.normalized_digest,
            }
        )
    ]
    for passage in sorted(corpus.passages, key=lambda item: (item.canonical_order, item.reference)):
        lines.append(_canonical_json({"type": "passage", **passage.model_dump(mode="json")}))
    for note in sorted(corpus.notes, key=lambda item: item.note_id):
        lines.append(_canonical_json({"type": "note", **note.model_dump(mode="json")}))
    for edge in sorted(corpus.edges, key=lambda item: item.edge_id):
        lines.append(_canonical_json({"type": "edge", **edge.model_dump(mode="json")}))
    return b"\n".join(lines) + b"\n"


def canonical_projection(corpus: NormalizedCorpus) -> bytes:
    projection = [
        {
            "reference": passage.reference,
            "text": passage.text,
            "canonical_order": passage.canonical_order,
            "content_hash": passage.content_hash,
        }
        for passage in sorted(corpus.passages, key=lambda item: item.canonical_order)
    ]
    return _canonical_json(projection)


def _stable_id(*parts: str) -> str:
    return hashlib.sha256("\x1f".join(parts).encode()).hexdigest()[:32]


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
