from __future__ import annotations

import hashlib
import json
import math
import platform
import time
from collections.abc import Callable

from passage.domain.models import (
    ContextRequest,
    LexicalSearchRequest,
    PassageRequest,
    SnapshotRequest,
    StrictModel,
    TraversalRequest,
)
from passage.evidence.service import EvidenceService


class LatencySummary(StrictModel):
    p50_ms: float
    p95_ms: float
    iterations: int


class PerformanceReport(StrictModel):
    corpus_version: str
    retrieval_config: str
    workstation: dict[str, str]
    query_set_digest: str
    warmup_count: int
    measured_iterations: int
    concurrency: int = 1
    transport_boundary: str = "in-process EvidenceService"
    cache_state: str = "warm"
    acceptance_gate: bool = False
    operations: dict[str, LatencySummary]


def measure_performance(
    service: EvidenceService,
    *,
    reference: str,
    query: str,
    warmup_count: int = 2,
    iterations: int = 20,
) -> PerformanceReport:
    if not 0 <= warmup_count <= 100:
        raise ValueError("warmup_count must be between 0 and 100")
    if not 1 <= iterations <= 1000:
        raise ValueError("iterations must be between 1 and 1000")
    metadata = service.get_corpus(SnapshotRequest())
    operations: dict[str, Callable[[], object]] = {
        "passage_lookup": lambda: service.get_passage(
            PassageRequest(
                reference=reference,
                corpus_version=metadata.corpus_version,
                retrieval_config=metadata.retrieval_config,
            )
        ),
        "context_lookup": lambda: service.get_context(
            ContextRequest(
                reference=reference,
                corpus_version=metadata.corpus_version,
                retrieval_config=metadata.retrieval_config,
            )
        ),
        "lexical_search": lambda: service.search_lexical(
            LexicalSearchRequest(
                query=query,
                corpus_version=metadata.corpus_version,
                retrieval_config=metadata.retrieval_config,
            )
        ),
        "official_traversal": lambda: service.traverse_references(
            TraversalRequest(
                reference=reference,
                corpus_version=metadata.corpus_version,
                retrieval_config=metadata.retrieval_config,
            )
        ),
    }
    summaries: dict[str, LatencySummary] = {}
    for name, operation in operations.items():
        for _ in range(warmup_count):
            operation()
        measurements = []
        for _ in range(iterations):
            started = time.perf_counter_ns()
            operation()
            measurements.append((time.perf_counter_ns() - started) / 1_000_000)
        measurements.sort()
        summaries[name] = LatencySummary(
            p50_ms=_percentile(measurements, 0.50),
            p95_ms=_percentile(measurements, 0.95),
            iterations=iterations,
        )
    query_set_digest = hashlib.sha256(
        json.dumps(
            {"reference": reference, "query": query},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return PerformanceReport(
        corpus_version=metadata.corpus_version,
        retrieval_config=metadata.retrieval_config,
        workstation={
            "platform": platform.platform(),
            "machine": platform.machine(),
            "python": platform.python_version(),
        },
        query_set_digest=query_set_digest,
        warmup_count=warmup_count,
        measured_iterations=iterations,
        operations=summaries,
    )


def _percentile(values: list[float], quantile: float) -> float:
    index = max(0, math.ceil(len(values) * quantile) - 1)
    return values[index]
