from __future__ import annotations

import multiprocessing
import queue
import tempfile
from pathlib import Path
from typing import Any

from scripture_chat.ingest.base import (
    ExtractionError,
    ExtractionLimits,
    ExtractionResult,
)
from scripture_chat.ingest.epub import extract_epub
from scripture_chat.ingest.pdf import extract_pdf


def inspect_source(path: Path, limits: ExtractionLimits) -> ExtractionResult:
    suffix = path.suffix.lower()
    if suffix == ".epub":
        return extract_epub(path, limits)
    if suffix == ".pdf":
        return extract_pdf(path, limits)
    raise ExtractionError(f"unsupported source format: {suffix or '<none>'}")


def inspect_source_in_worker(
    path: Path,
    limits: ExtractionLimits,
    workspace_root: Path,
) -> ExtractionResult:
    if path.stat().st_size > limits.max_source_bytes:
        raise ExtractionError("source-byte budget exceeded")
    workspace_root.mkdir(mode=0o700, parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="scripture-chat-", dir=workspace_root):
        context = multiprocessing.get_context("spawn")
        result_queue = context.Queue(maxsize=1)
        process = context.Process(
            target=_worker_entry,
            args=(str(path), limits.model_dump(mode="json"), result_queue),
        )
        process.start()
        process.join(limits.wall_seconds)
        if process.is_alive():
            process.terminate()
            process.join(5)
            raise ExtractionError("extraction wall-time budget exceeded")
        try:
            success, payload = result_queue.get(timeout=1)
        except queue.Empty as exc:
            raise ExtractionError(
                f"extraction worker exited without a result (code {process.exitcode})"
            ) from exc
        finally:
            result_queue.close()
        if not success:
            raise ExtractionError(str(payload))
        return ExtractionResult.model_validate(payload)


def _worker_entry(path: str, limits_data: dict[str, Any], result_queue: Any) -> None:
    try:
        result = inspect_source(Path(path), ExtractionLimits.model_validate(limits_data))
        result_queue.put((True, result.model_dump(mode="json")))
    except Exception as exc:
        result_queue.put((False, str(exc)))
