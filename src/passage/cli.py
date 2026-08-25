from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from passage.config import AppConfig, create_private_file, prepare_private_root
from passage.db.builder import CorpusBuilder
from passage.db.control import AcceptedCorpus, ControlStore
from passage.db.repository import CorpusRepository, create_sqlite_evidence_service
from passage.db.validation import validate_published_artifact
from passage.domain.models import SnapshotRequest, SourceApproval
from passage.eval.cases import load_cases
from passage.eval.phase0 import Phase0ProbeRunner, load_phase0_probe_definition
from passage.eval.runner import EvaluationRunner
from passage.ingest.base import ExtractionLimits, ExtractionResult
from passage.ingest.candidate import load_candidate
from passage.ingest.normalize import NormalizedCorpus, normalize_extraction, serialize_jsonl
from passage.ingest.official_edges import (
    derive_official_edges,
    load_official_reference_correction_profile,
    publish_official_edge_derivation,
)
from passage.ingest.review import render_review_markdown
from passage.ingest.validation import (
    StructureManifest,
    load_default_structure_manifest,
    reconcile_source_spans,
    validate_corpus,
)
from passage.ingest.worker import inspect_source_in_worker


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        result = args.handler(args)
    except Exception as exc:
        _print_json(
            {
                "ok": False,
                "error": {
                    "type": type(exc).__name__,
                    "message": str(exc),
                    "details": _error_details(exc),
                },
            },
            stream=sys.stderr,
        )
        return 1
    _print_json({"ok": True, **result})
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="passage")
    subcommands = parser.add_subparsers(required=True)
    corpus = subcommands.add_parser("corpus")
    corpus_commands = corpus.add_subparsers(required=True)

    inspect = corpus_commands.add_parser("inspect")
    _source_and_data_arguments(inspect)
    inspect.set_defaults(handler=_inspect)

    build = corpus_commands.add_parser("build")
    _source_and_data_arguments(build)
    build.add_argument("--edition", required=True)
    build.add_argument("--acquisition-url")
    build.add_argument("--acquisition-date", type=date.fromisoformat)
    build.add_argument("--language", default="eng")
    build.add_argument("--structure", type=Path)
    build.set_defaults(handler=_build)

    import_candidate = corpus_commands.add_parser("import-candidate")
    import_candidate.add_argument("--candidate", type=Path, required=True)
    import_candidate.add_argument("--manifest", type=Path)
    import_candidate.add_argument("--approved-candidate-sha256", required=True)
    import_candidate.add_argument("--edition", required=True)
    import_candidate.add_argument("--acquisition-url", required=True)
    import_candidate.add_argument("--acquisition-date", type=date.fromisoformat, required=True)
    import_candidate.add_argument("--language", default="eng")
    _data_argument(import_candidate)
    import_candidate.set_defaults(handler=_import_candidate)

    derive_edges = corpus_commands.add_parser("derive-official-edges")
    derive_edges.add_argument("--candidate", type=Path, required=True)
    derive_edges.add_argument("--manifest", type=Path)
    derive_edges.add_argument("--approved-candidate-sha256", required=True)
    derive_edges.add_argument("--corrections", type=Path)
    _data_argument(derive_edges)
    derive_edges.set_defaults(handler=_derive_official_edges)

    verify = corpus_commands.add_parser("verify")
    _data_argument(verify)
    verify.add_argument("--corpus-version")
    verify.set_defaults(handler=_verify)

    activate = corpus_commands.add_parser("activate")
    _data_argument(activate)
    activate.add_argument("--corpus-version")
    activate.add_argument("--retrieval-config")
    activate.set_defaults(handler=_activate)

    metadata = corpus_commands.add_parser("metadata")
    _data_argument(metadata)
    metadata.set_defaults(handler=_metadata)

    serve = subcommands.add_parser("serve")
    _data_argument(serve)
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)
    serve.set_defaults(handler=_serve)

    evaluate = subcommands.add_parser("evaluate")
    _data_argument(evaluate)
    evaluate.add_argument("--cases", type=Path, required=True)
    evaluate.add_argument("--metric-depth", type=int, action="append")
    evaluate.set_defaults(handler=_evaluate)

    phase0_probe = subcommands.add_parser("phase0-probe")
    _data_argument(phase0_probe)
    phase0_probe.add_argument("--definition", type=Path, required=True)
    phase0_probe.set_defaults(handler=_phase0_probe)
    return parser


def _source_and_data_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--source", type=Path, required=True)
    _data_argument(parser)


def _data_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--data-dir", type=Path, required=True)


def _private_root(args: argparse.Namespace) -> Path:
    root = args.data_dir.expanduser().absolute()
    config = AppConfig(private_root=root)
    return prepare_private_root(config, _repository_root())


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _inspect(args: argparse.Namespace) -> dict[str, Any]:
    root = _private_root(args)
    source = args.source.expanduser().absolute()
    extraction = _extract(source, root)
    return {
        "source": str(source),
        "source_sha256": _sha256_file(source),
        "source_format": extraction.source_format,
        "source_profile": extraction.profile,
        "passage_count": len(extraction.passages),
        "note_count": len(extraction.notes),
        "edge_count": len(extraction.edges),
    }


def _build(args: argparse.Namespace) -> dict[str, Any]:
    root = _private_root(args)
    source = args.source.expanduser().absolute()
    extraction = _extract(source, root)
    reconcile_source_spans(extraction)
    structure, structure_path = _load_structure(source, args.structure)
    corpus = normalize_extraction(extraction, structure)
    validate_corpus(corpus, structure)
    approval = _load_approval(source, args, _sha256_file(source))
    recipe_fingerprint = _digest_json(
        {
            "source_profile": extraction.profile,
            "structure": structure.model_dump(mode="json"),
            "normalizer": "passage-v1",
        }
    )
    with ControlStore(root) as control:
        published = CorpusBuilder(root, control).build(
            corpus,
            approval,
            recipe_fingerprint,
        )
    derived = _publish_review_artifacts(root, corpus)
    return {
        "source": str(source),
        "structure_manifest": structure_path,
        "corpus_version": published.corpus_version,
        "retrieval_config": published.retrieval_config,
        "artifact_digest": published.artifact_digest,
        "normalized_digest": corpus.normalized_digest,
        "derived_artifacts": derived,
        "active": False,
    }


def _import_candidate(args: argparse.Namespace) -> dict[str, Any]:
    root = _private_root(args)
    candidate = args.candidate.expanduser().absolute()
    manifest = args.manifest.expanduser().absolute() if args.manifest is not None else None
    loaded = load_candidate(candidate, manifest)
    if loaded.candidate_sha256 != args.approved_candidate_sha256:
        raise ValueError("candidate does not match the explicitly approved digest")
    approval = SourceApproval(
        source_sha256=loaded.candidate_sha256,
        acquisition_url=args.acquisition_url,
        acquisition_date=args.acquisition_date,
        edition=args.edition,
        language=args.language,
    )
    recipe_fingerprint = _digest_json(
        {
            "candidate_manifest": loaded.manifest.model_dump(mode="json"),
            "structure": loaded.structure.model_dump(mode="json"),
            "normalizer": "passage-v1",
            "candidate_importer": "passage-candidate-v1",
        }
    )
    derived = _publish_review_artifacts(root, loaded.corpus)
    with ControlStore(root) as control:
        published = CorpusBuilder(root, control).build(
            loaded.corpus,
            approval,
            recipe_fingerprint,
        )
    return {
        "candidate": str(candidate),
        "candidate_sha256": loaded.candidate_sha256,
        "normalized_digest": loaded.corpus.normalized_digest,
        "corpus_version": published.corpus_version,
        "retrieval_config": published.retrieval_config,
        "artifact_digest": published.artifact_digest,
        "derived_artifacts": derived,
        "accepted": True,
        "active": False,
    }


def _derive_official_edges(args: argparse.Namespace) -> dict[str, Any]:
    root = _private_root(args)
    candidate = args.candidate.expanduser().absolute()
    manifest = args.manifest.expanduser().absolute() if args.manifest is not None else None
    loaded = load_candidate(candidate, manifest)
    if loaded.candidate_sha256 != args.approved_candidate_sha256:
        raise ValueError("candidate does not match the explicitly approved digest")
    if loaded.corpus.source_format != "pdf":
        raise ValueError("official-reference-v2 requires a PDF-derived candidate")
    if loaded.manifest.scope != "book-of-mormon":
        raise ValueError("official-reference-v2 supports only Book of Mormon candidates")
    correction_profile = None
    if args.corrections is not None:
        corrections = args.corrections.expanduser().resolve(strict=True)
        if corrections.is_relative_to(_repository_root().resolve()):
            raise ValueError("official reference correction profiles must remain outside Git")
        if not corrections.is_relative_to(root.resolve()):
            raise ValueError(
                "official reference correction profiles must remain under the private root"
            )
        correction_profile = load_official_reference_correction_profile(corrections)

    derivation = derive_official_edges(
        loaded.corpus,
        loaded.structure,
        source_candidate_sha256=loaded.candidate_sha256,
        correction_profile=correction_profile,
    )
    published = publish_official_edge_derivation(
        root,
        derivation,
        repository_root=_repository_root(),
        scope="book-of-mormon",
    )
    return {
        "source_candidate": str(candidate),
        "source_candidate_sha256": loaded.candidate_sha256,
        "grammar_version": derivation.report.grammar_version,
        "correction_profile_digest": derivation.report.correction_profile_digest,
        "parsed_note_count": derivation.report.parsed_note_count,
        "no_reference_note_count": derivation.report.no_reference_note_count,
        "blocking_note_count": derivation.report.blocking_note_count,
        "internal_edge_count": derivation.report.internal_edge_count,
        "external_edge_count": derivation.report.external_edge_count,
        "edge_count": derivation.report.edge_count,
        "successor_candidate_sha256": published.successor_candidate_sha256,
        "report": str(published.report_path),
        "edge_preview": str(published.edge_preview_path),
        "candidate": str(published.candidate_path) if published.candidate_path else None,
        "manifest": str(published.manifest_path) if published.manifest_path else None,
        "complete": derivation.report.complete,
        "ready_for_import": published.candidate_path is not None,
        "accepted": False,
        "active": False,
    }


def _verify(args: argparse.Namespace) -> dict[str, Any]:
    root = _private_root(args)
    with ControlStore(root) as control:
        accepted = _select_accepted(control, args.corpus_version)
        validate_published_artifact(accepted.artifact_path)
    return {
        "corpus_version": accepted.corpus_version,
        "retrieval_config": accepted.retrieval_config,
        "artifact_digest": accepted.artifact_digest,
        "verified": True,
    }


def _activate(args: argparse.Namespace) -> dict[str, Any]:
    root = _private_root(args)
    if (args.corpus_version is None) != (args.retrieval_config is None):
        raise ValueError("corpus version and retrieval configuration must be supplied together")
    with ControlStore(root) as control:
        accepted = _select_accepted(control, args.corpus_version)
        corpus_version = accepted.corpus_version
        retrieval_config = (
            accepted.retrieval_config if args.retrieval_config is None else args.retrieval_config
        )
        with CorpusRepository.open(control, corpus_version, retrieval_config):
            pass
        control.activate(corpus_version, retrieval_config)
    return {
        "corpus_version": corpus_version,
        "retrieval_config": retrieval_config,
        "active": True,
    }


def _metadata(args: argparse.Namespace) -> dict[str, Any]:
    root = _private_root(args)
    with ControlStore(root) as control:
        metadata = create_sqlite_evidence_service(control).get_corpus(SnapshotRequest())
    return {"metadata": metadata.model_dump(mode="json")}


def _serve(args: argparse.Namespace) -> dict[str, Any]:
    import uvicorn

    from passage.http.app import create_app

    root = args.data_dir.expanduser().absolute()
    allowed_origins = tuple(
        f"http://{authority}:{args.port}" for authority in ("127.0.0.1", "localhost", "[::1]")
    )
    config = AppConfig(
        private_root=root,
        host=args.host,
        port=args.port,
        allowed_origins=allowed_origins,
    )
    prepare_private_root(config, Path.cwd())
    uvicorn.run(create_app(config), host=config.host, port=config.port)
    return {"host": config.host, "port": config.port, "stopped": True}


def _evaluate(args: argparse.Namespace) -> dict[str, Any]:
    root = _private_root(args)
    cases = load_cases(args.cases)
    with ControlStore(root) as control:
        accepted = _select_accepted(control, None)
        run = EvaluationRunner(create_sqlite_evidence_service(control)).run(
            cases,
            corpus_version=accepted.corpus_version,
            retrieval_config=accepted.retrieval_config,
            metric_depths=args.metric_depth,
            output_directory=root / "evaluations",
        )
    return {
        "corpus_version": run.report.identities.corpus_version,
        "retrieval_config": run.report.identities.retrieval_config,
        "report_digest": run.report.report_digest,
        "eligible": run.report.eligible,
        "ineligibility_reasons": run.report.ineligibility_reasons,
        "report_path": str(run.path),
    }


def _phase0_probe(args: argparse.Namespace) -> dict[str, Any]:
    root = _private_root(args)
    definition = load_phase0_probe_definition(args.definition.expanduser().absolute())
    with ControlStore(root) as control:
        accepted = _select_accepted(control, None)
        run = Phase0ProbeRunner(create_sqlite_evidence_service(control)).run(
            definition,
            corpus_version=accepted.corpus_version,
            retrieval_config=accepted.retrieval_config,
            output_directory=root / "evaluations",
        )
    return {
        "corpus_version": run.report.corpus_version,
        "retrieval_config": run.report.retrieval_config,
        "report_digest": run.report.report_digest,
        "report_path": str(run.path),
        "present_lanes": run.report.present_lanes,
        "absent_lanes": run.report.absent_lanes,
        "zero_citation_errors": run.report.zero_citation_errors,
        "zero_evidence_class_errors": run.report.zero_evidence_class_errors,
        "no_fatal_atomic_contract_problem": run.report.no_fatal_atomic_contract_problem,
        "h1_claim": run.report.h1_claim,
        "h1_status": run.report.h1_status,
        "promotion_eligible": run.report.promotion_eligible,
    }


def _extract(source: Path, root: Path) -> ExtractionResult:
    if not source.is_file():
        raise FileNotFoundError(source)
    return inspect_source_in_worker(source, ExtractionLimits(), root / "workspaces")


def _load_structure(
    source: Path,
    explicit_path: Path | None,
) -> tuple[StructureManifest, str]:
    sidecar = Path(f"{source}.structure.json")
    path = explicit_path or (sidecar if sidecar.is_file() else None)
    if path is None:
        return load_default_structure_manifest(), "packaged:book_of_mormon_structure.json"
    absolute = path.expanduser().absolute()
    return (
        StructureManifest.model_validate_json(absolute.read_text(encoding="utf-8")),
        str(absolute),
    )


def _load_approval(
    source: Path,
    args: argparse.Namespace,
    source_sha256: str,
) -> SourceApproval:
    if args.acquisition_url is not None or args.acquisition_date is not None:
        if args.acquisition_url is None or args.acquisition_date is None:
            raise ValueError("acquisition URL and date must be supplied together")
        return SourceApproval(
            source_sha256=source_sha256,
            acquisition_url=args.acquisition_url,
            acquisition_date=args.acquisition_date,
            edition=args.edition,
            language=args.language,
        )
    sidecar = Path(f"{source}.approval.json")
    if not sidecar.is_file():
        raise ValueError(
            f"source approval is required: pass acquisition URL/date or provide {sidecar.name}"
        )
    approval = SourceApproval.model_validate_json(sidecar.read_text(encoding="utf-8"))
    if approval.source_sha256 != source_sha256:
        raise ValueError("source approval digest does not match source bytes")
    if approval.edition != args.edition or approval.language != args.language:
        raise ValueError("source approval edition/language does not match command")
    return approval


def _publish_review_artifacts(root: Path, corpus: NormalizedCorpus) -> list[str]:
    directory = root / "reviews" / corpus.normalized_digest
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    review_path = directory / "review.md"
    normalized_path = directory / "normalized.jsonl"
    overlay_path = directory / "overlays.json"
    artifacts = {
        review_path: render_review_markdown(corpus).encode("utf-8"),
        normalized_path: serialize_jsonl(corpus),
    }
    if corpus.source_format == "pdf":
        overlays = [
            {
                "reference": passage.reference,
                "source_spans": [
                    span.model_dump(mode="json")
                    for span in passage.source_spans
                    if span.kind == "pdf"
                ],
            }
            for passage in corpus.passages
        ]
        artifacts[overlay_path] = (
            json.dumps(overlays, sort_keys=True, separators=(",", ":")) + "\n"
        ).encode("utf-8")
    for path, payload in artifacts.items():
        if path.exists():
            if path.read_bytes() != payload:
                raise ValueError(f"derived artifact identity collision: {path}")
        else:
            create_private_file(path, payload)
    return [str(path) for path in artifacts]


def _select_accepted(control: ControlStore, corpus_version: str | None) -> AcceptedCorpus:
    accepted = (
        control.get_accepted(corpus_version)
        if corpus_version is not None
        else control.latest_accepted()
    )
    if accepted is None:
        raise ValueError("no matching accepted corpus is available")
    return accepted


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def _digest_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _error_details(exc: Exception) -> Any:
    if isinstance(exc, ValidationError):
        return exc.errors(include_url=False)
    findings = getattr(exc, "findings", None)
    if findings is not None:
        return [finding.model_dump(mode="json") for finding in findings]
    detail = getattr(exc, "detail", None)
    return detail


def _print_json(payload: dict[str, Any], *, stream=sys.stdout) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True), file=stream)


if __name__ == "__main__":
    raise SystemExit(main())
