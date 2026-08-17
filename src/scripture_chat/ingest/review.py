from __future__ import annotations

from collections import defaultdict

from scripture_chat.ingest.normalize import NormalizedCorpus


def render_review_markdown(corpus: NormalizedCorpus) -> str:
    groups: dict[str, list[str]] = defaultdict(list)
    for passage in sorted(corpus.passages, key=lambda item: item.canonical_order):
        location = _location(passage.source_spans[0])
        groups[location].append(
            f"- `{passage.reference}` — {passage.text}\n"
            f"  - content SHA-256: `{passage.content_hash}`"
        )
    lines = ["# Corpus Review", "", f"Normalized digest: `{corpus.normalized_digest}`", ""]
    for location in sorted(groups):
        lines.extend([f"## {location}", "", *groups[location], ""])
    return "\n".join(lines)


def _location(span) -> str:
    if span.kind == "epub":
        return f"EPUB member `{span.member}`"
    return f"PDF page {span.page}"
