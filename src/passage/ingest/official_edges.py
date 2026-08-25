from __future__ import annotations

import hashlib
import os
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from passage.config import AppConfig, create_private_file, prepare_private_root
from passage.domain.models import (
    ApparatusNote,
    Identifier,
    ReferenceEdge,
    ReferenceTarget,
    Sha256,
    StrictModel,
)
from passage.domain.references import (
    is_external_reference_target,
    is_internal_reference_target,
    reference_target_key,
)
from passage.ingest.apparatus import (
    CHURCH_PDF_REFERENCE_GRAMMAR_VERSION,
    OfficialReferenceParseCode,
    OfficialReferenceParseState,
    parse_church_pdf_footnote,
)
from passage.ingest.candidate import CandidateManifest, validate_candidate_records
from passage.ingest.normalize import (
    NormalizedCorpus,
    build_reference_edges,
    canonical_json_bytes,
    serialize_jsonl,
    with_recomputed_digest,
)
from passage.ingest.validation import StructureManifest, validate_corpus


class OfficialEdgeFinding(StrictModel):
    note_id: str
    origin_reference: str
    anchor: str
    state: OfficialReferenceParseState
    code: OfficialReferenceParseCode


class OfficialReferenceReplacementNote(StrictModel):
    anchor: str = Field(pattern=r"^[a-z]$")
    label: str | None = None
    text: str | None = Field(default=None, min_length=1)
    targets: list[ReferenceTarget] | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def reject_duplicate_targets(self) -> OfficialReferenceReplacementNote:
        if self.targets is not None:
            keys = [reference_target_key(target) for target in self.targets]
            if len(keys) != len(set(keys)):
                raise ValueError("replacement note contains duplicate targets")
        return self


class OfficialReferenceNoteCorrection(StrictModel):
    note_id: Identifier
    expected_text_sha256: Sha256
    replacements: list[OfficialReferenceReplacementNote] = Field(min_length=1)

    @model_validator(mode="after")
    def reject_duplicate_anchors(self) -> OfficialReferenceNoteCorrection:
        anchors = [replacement.anchor for replacement in self.replacements]
        if len(anchors) != len(set(anchors)):
            raise ValueError("note correction contains duplicate replacement anchors")
        return self


class OfficialReferenceCorrectionProfile(StrictModel):
    schema_version: Literal[1]
    profile_id: Identifier
    source_candidate_sha256: Sha256
    corrections: list[OfficialReferenceNoteCorrection] = Field(min_length=1)

    @model_validator(mode="after")
    def reject_duplicate_notes(self) -> OfficialReferenceCorrectionProfile:
        note_ids = [correction.note_id for correction in self.corrections]
        if len(note_ids) != len(set(note_ids)):
            raise ValueError("official reference correction profile contains duplicate notes")
        return self


class OfficialEdgeDerivationReport(StrictModel):
    grammar_version: Literal["official-reference-v2"]
    source_candidate_sha256: Sha256
    correction_profile_digest: Sha256 | None = None
    total_note_count: int = Field(ge=0)
    parsed_note_count: int = Field(ge=0)
    unresolved_external_note_count: int = Field(ge=0)
    no_reference_note_count: int = Field(ge=0)
    blocking_note_count: int = Field(ge=0)
    internal_edge_count: int = Field(ge=0)
    external_edge_count: int = Field(ge=0)
    edge_count: int = Field(ge=0)
    normalized_digest: Sha256
    successor_candidate_sha256: Sha256
    complete: bool
    findings: list[OfficialEdgeFinding] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_counts(self) -> OfficialEdgeDerivationReport:
        if self.blocking_note_count != len(self.findings):
            raise ValueError("blocking note count does not match findings")
        if self.complete != (not self.findings):
            raise ValueError("complete state does not match findings")
        if self.edge_count != self.internal_edge_count + self.external_edge_count:
            raise ValueError("edge count does not match target-kind counts")
        classified = (
            self.parsed_note_count + self.no_reference_note_count + self.blocking_note_count
        )
        if self.total_note_count != classified:
            raise ValueError("total note count does not match classifications")
        if self.unresolved_external_note_count > self.parsed_note_count:
            raise ValueError("external note count exceeds parsed note count")
        return self


@dataclass(frozen=True, slots=True)
class OfficialEdgeDerivation:
    corpus: NormalizedCorpus
    report: OfficialEdgeDerivationReport


@dataclass(frozen=True, slots=True)
class PublishedOfficialEdgeDerivation:
    report_path: Path
    edge_preview_path: Path
    candidate_path: Path | None
    manifest_path: Path | None
    successor_candidate_sha256: str


def derive_official_edges(
    corpus: NormalizedCorpus,
    structure: StructureManifest,
    *,
    source_candidate_sha256: str,
    correction_profile: OfficialReferenceCorrectionProfile | None = None,
) -> OfficialEdgeDerivation:
    if corpus.edges:
        raise ValueError("official edges can only be derived from an edge-free source candidate")
    if structure.work != "bofm":
        raise ValueError("official-reference-v2 supports only Book of Mormon candidates")
    actual_source_candidate_sha256 = hashlib.sha256(serialize_jsonl(corpus)).hexdigest()
    if actual_source_candidate_sha256 != source_candidate_sha256:
        raise ValueError("source candidate does not match the supplied digest")

    corrected_corpus, target_overrides, correction_profile_digest = _apply_correction_profile(
        corpus,
        source_candidate_sha256=source_candidate_sha256,
        correction_profile=correction_profile,
    )

    valid_internal_references = set(structure.expected_references())
    edges: list[ReferenceEdge] = []
    findings: list[OfficialEdgeFinding] = []
    parsed_note_count = 0
    unresolved_external_note_count = 0
    no_reference_note_count = 0
    official_notes = [
        note for note in corrected_corpus.notes if note.note_kind == "official-footnote"
    ]

    for note in official_notes:
        override = target_overrides.get(note.note_id)
        if override is not None:
            parsed_note_count += 1
            if any(is_external_reference_target(target) for target in override):
                unresolved_external_note_count += 1
            edges.extend(
                build_reference_edges(
                    origin_reference=note.origin_reference,
                    origin_anchor=note.anchor,
                    targets=override,
                    source_attribution="official-footnote",
                    grammar_version=CHURCH_PDF_REFERENCE_GRAMMAR_VERSION,
                    source_spans=note.source_spans,
                )
            )
            continue
        result = parse_church_pdf_footnote(
            note.text or "",
            valid_internal_references=valid_internal_references,
        )
        if result.state is OfficialReferenceParseState.NO_REFERENCE:
            no_reference_note_count += 1
            continue
        if not result.targets:
            findings.append(
                OfficialEdgeFinding(
                    note_id=note.note_id,
                    origin_reference=note.origin_reference,
                    anchor=note.anchor,
                    state=result.state,
                    code=result.code,
                )
            )
            continue
        parsed_note_count += 1
        if result.state is OfficialReferenceParseState.UNRESOLVED_EXTERNAL:
            unresolved_external_note_count += 1
        edges.extend(
            build_reference_edges(
                origin_reference=note.origin_reference,
                origin_anchor=note.anchor,
                targets=result.targets,
                source_attribution="official-footnote",
                grammar_version=CHURCH_PDF_REFERENCE_GRAMMAR_VERSION,
                source_spans=note.source_spans,
            )
        )

    derived_corpus = with_recomputed_digest(corrected_corpus, edges=edges)
    validate_candidate_records(derived_corpus)
    validate_corpus(derived_corpus, structure)
    payload = serialize_jsonl(derived_corpus)
    internal_edge_count = sum(is_internal_reference_target(edge.target) for edge in edges)
    external_edge_count = len(edges) - internal_edge_count
    report = OfficialEdgeDerivationReport(
        grammar_version=CHURCH_PDF_REFERENCE_GRAMMAR_VERSION,
        source_candidate_sha256=source_candidate_sha256,
        correction_profile_digest=correction_profile_digest,
        total_note_count=len(official_notes),
        parsed_note_count=parsed_note_count,
        unresolved_external_note_count=unresolved_external_note_count,
        no_reference_note_count=no_reference_note_count,
        blocking_note_count=len(findings),
        internal_edge_count=internal_edge_count,
        external_edge_count=external_edge_count,
        edge_count=len(edges),
        normalized_digest=derived_corpus.normalized_digest,
        successor_candidate_sha256=hashlib.sha256(payload).hexdigest(),
        complete=not findings,
        findings=findings,
    )
    return OfficialEdgeDerivation(corpus=derived_corpus, report=report)


def publish_official_edge_derivation(
    private_root: Path,
    derivation: OfficialEdgeDerivation,
    *,
    repository_root: Path,
    scope: Literal["book-of-mormon"],
) -> PublishedOfficialEdgeDerivation:
    report = OfficialEdgeDerivationReport.model_validate(derivation.report.model_dump(mode="json"))
    root = prepare_private_root(
        AppConfig(private_root=private_root.expanduser().absolute()),
        repository_root.expanduser().absolute(),
    )
    output_dir = (
        root
        / "official-reference-derivations"
        / report.source_candidate_sha256
        / report.grammar_version
    )
    if report.correction_profile_digest is not None:
        output_dir /= report.correction_profile_digest
    output_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(output_dir, 0o700, follow_symlinks=False)

    edge_preview_payload = _edge_preview(derivation.corpus.edges)
    report_payload = _json_line(report.model_dump(mode="json"))
    report_path = output_dir / "report.json"
    preview_path = output_dir / "official-edges.jsonl"
    _publish_exact(report_path, report_payload)
    _publish_exact(preview_path, edge_preview_payload)

    candidate_path: Path | None = None
    manifest_path: Path | None = None
    if report.complete:
        candidate_payload = serialize_jsonl(derivation.corpus)
        candidate_path = output_dir / "candidate.jsonl"
        manifest_path = output_dir / "manifest.json"
        manifest = CandidateManifest(
            schema_version=1,
            scope=scope,
            artifact=candidate_path.name,
            candidate_sha256=report.successor_candidate_sha256,
            normalized_digest=derivation.corpus.normalized_digest,
            source_format=derivation.corpus.source_format,
            status="review_required",
            active=False,
            accepted=False,
            passage_count=len(derivation.corpus.passages),
            note_anchor_count=len(derivation.corpus.notes),
            edge_count=len(derivation.corpus.edges),
        )
        _publish_exact(candidate_path, candidate_payload)
        _publish_exact(manifest_path, _json_line(manifest.model_dump(mode="json")))

    return PublishedOfficialEdgeDerivation(
        report_path=report_path,
        edge_preview_path=preview_path,
        candidate_path=candidate_path,
        manifest_path=manifest_path,
        successor_candidate_sha256=report.successor_candidate_sha256,
    )


def _edge_preview(edges: list[ReferenceEdge]) -> bytes:
    return b"".join(
        _json_line({"type": "edge", **edge.model_dump(mode="json")})
        for edge in sorted(edges, key=lambda item: item.edge_id)
    )


def load_official_reference_correction_profile(
    path: Path,
) -> OfficialReferenceCorrectionProfile:
    return OfficialReferenceCorrectionProfile.model_validate_json(path.read_text(encoding="utf-8"))


def _apply_correction_profile(
    corpus: NormalizedCorpus,
    *,
    source_candidate_sha256: str,
    correction_profile: OfficialReferenceCorrectionProfile | None,
) -> tuple[NormalizedCorpus, dict[str, list[ReferenceTarget]], str | None]:
    if correction_profile is None:
        return corpus, {}, None
    if correction_profile.source_candidate_sha256 != source_candidate_sha256:
        raise ValueError("official reference correction profile does not match source candidate")

    corrections = {correction.note_id: correction for correction in correction_profile.corrections}
    source_note_ids = {note.note_id for note in corpus.notes}
    missing = sorted(set(corrections) - source_note_ids)
    if missing:
        raise ValueError("official reference correction profile names a missing note")

    corrected_notes: list[ApparatusNote] = []
    target_overrides: dict[str, list[ReferenceTarget]] = {}
    for note in corpus.notes:
        correction = corrections.get(note.note_id)
        if correction is None:
            corrected_notes.append(note)
            continue
        actual_text_sha256 = hashlib.sha256((note.text or "").encode("utf-8")).hexdigest()
        if actual_text_sha256 != correction.expected_text_sha256:
            raise ValueError("official reference correction profile does not match note text")
        for replacement in correction.replacements:
            if (
                replacement.anchor == note.anchor
                and replacement.text is None
                and replacement.label is None
                and replacement.targets is None
            ):
                raise ValueError("a replacement note must change content or targets")
            if replacement.anchor != note.anchor and replacement.text is None:
                raise ValueError("a split replacement note must supply text")
            replacement_text = replacement.text if replacement.text is not None else note.text
            replacement_label = replacement.label if replacement.label is not None else note.label
            note_id = (
                note.note_id
                if replacement.anchor == note.anchor
                else hashlib.sha256(
                    (
                        f"{source_candidate_sha256}\0{note.note_id}\0"
                        f"{replacement.anchor}\0{replacement_text}"
                    ).encode()
                ).hexdigest()[:32]
            )
            corrected_note = note.model_copy(
                update={
                    "note_id": note_id,
                    "anchor": replacement.anchor,
                    "label": replacement_label,
                    "text": replacement_text,
                }
            )
            corrected_notes.append(corrected_note)
            if replacement.targets is not None:
                target_overrides[note_id] = replacement.targets

    corrected_corpus = corpus.model_copy(update={"notes": corrected_notes})
    profile_digest = hashlib.sha256(
        canonical_json_bytes(correction_profile.model_dump(mode="json"))
    ).hexdigest()
    return corrected_corpus, target_overrides, profile_digest


def _json_line(value: object) -> bytes:
    return canonical_json_bytes(value) + b"\n"


def _publish_exact(path: Path, payload: bytes) -> None:
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(8)}.tmp")
    try:
        create_private_file(temporary, payload)
        try:
            os.link(temporary, path, follow_symlinks=False)
        except FileExistsError:
            if path.read_bytes() != payload:
                raise ValueError(f"existing derivation artifact differs: {path.name}") from None
        else:
            _fsync_directory(path.parent)
    finally:
        temporary.unlink(missing_ok=True)


def _fsync_directory(path: Path) -> None:
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    descriptor = os.open(path, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
