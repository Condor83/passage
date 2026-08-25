from __future__ import annotations

import hashlib
import json
from typing import Any, Literal, cast

from pydantic import Field

from passage.domain.models import (
    ApparatusNote,
    Identifier,
    Passage,
    ReferenceEdge,
    ReferenceTarget,
    SourceSpan,
    StrictModel,
)
from passage.domain.references import reference_target_key
from passage.ingest.apparatus import (
    OFFICIAL_REFERENCE_GRAMMAR_VERSION,
    require_official_references,
)
from passage.ingest.base import ExtractionResult
from passage.ingest.validation import StructureManifest


class NormalizedCorpus(StrictModel):
    source_format: Literal["epub", "pdf"]
    source_profile: Identifier
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
    valid_internal_references = set(structure.expected_references())
    edges: list[ReferenceEdge] = []
    for event in extraction.edges:
        parsed = require_official_references(
            event.target,
            valid_internal_references=valid_internal_references,
        )
        edges.extend(
            build_reference_edges(
                origin_reference=event.origin_reference,
                origin_anchor=event.origin_anchor,
                targets=parsed.targets,
                source_attribution=event.source_attribution,
                grammar_version=OFFICIAL_REFERENCE_GRAMMAR_VERSION,
                source_spans=event.source_spans,
            )
        )
    corpus = NormalizedCorpus(
        source_format=cast(Literal["epub", "pdf"], extraction.source_format),
        source_profile=extraction.profile,
        passages=passages,
        notes=notes,
        edges=edges,
        normalized_digest="0" * 64,
    )
    return with_recomputed_digest(corpus)


def build_reference_edges(
    *,
    origin_reference: str,
    origin_anchor: str,
    targets: list[ReferenceTarget],
    source_attribution: str,
    grammar_version: str,
    source_spans: list[SourceSpan],
) -> list[ReferenceEdge]:
    identity = canonical_json_bytes([span.model_dump(mode="json") for span in source_spans]).decode(
        "utf-8"
    )
    return [
        ReferenceEdge(
            edge_id=_stable_id(
                origin_reference,
                origin_anchor,
                reference_target_key(target),
                source_attribution,
                grammar_version,
                identity,
            ),
            origin_reference=origin_reference,
            origin_anchor=origin_anchor,
            target=target,
            source_attribution=source_attribution,
            grammar_version=grammar_version,
            source_spans=source_spans,
        )
        for target in targets
    ]


def with_recomputed_digest(
    corpus: NormalizedCorpus,
    *,
    edges: list[ReferenceEdge] | None = None,
) -> NormalizedCorpus:
    updated = corpus.model_copy(update={"edges": corpus.edges if edges is None else edges})
    records = {
        "source_format": updated.source_format,
        "source_profile": updated.source_profile,
        "passages": [
            passage.model_dump(mode="json")
            for passage in sorted(
                updated.passages, key=lambda item: (item.canonical_order, item.reference)
            )
        ],
        "notes": [
            note.model_dump(mode="json")
            for note in sorted(updated.notes, key=lambda item: item.note_id)
        ],
        "edges": [
            edge.model_dump(mode="json")
            for edge in sorted(updated.edges, key=lambda item: item.edge_id)
        ],
    }
    return updated.model_copy(update={"normalized_digest": _sha256(canonical_json_bytes(records))})


def serialize_jsonl(corpus: NormalizedCorpus) -> bytes:
    lines: list[bytes] = [
        canonical_json_bytes(
            {
                "type": "corpus",
                "source_format": corpus.source_format,
                "source_profile": corpus.source_profile,
                "normalized_digest": corpus.normalized_digest,
            }
        )
    ]
    for passage in sorted(corpus.passages, key=lambda item: (item.canonical_order, item.reference)):
        lines.append(canonical_json_bytes({"type": "passage", **passage.model_dump(mode="json")}))
    for note in sorted(corpus.notes, key=lambda item: item.note_id):
        lines.append(canonical_json_bytes({"type": "note", **note.model_dump(mode="json")}))
    for edge in sorted(corpus.edges, key=lambda item: item.edge_id):
        lines.append(canonical_json_bytes({"type": "edge", **edge.model_dump(mode="json")}))
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
    return canonical_json_bytes(projection)


def _stable_id(*parts: str) -> str:
    return hashlib.sha256("\x1f".join(parts).encode()).hexdigest()[:32]


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
