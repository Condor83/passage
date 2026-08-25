---
title: Datalab PDF Apparatus Repair
type: analysis
created: 2026-08-23
updated: 2026-08-23
sources:
  - src/passage/ingest/datalab.py
  - tests/unit/ingest/test_datalab.py
  - docs/plans/2026-08-16-001-feat-scripture-chat-plan.md
tags: [datalab, pdf, ingestion, footnotes, provenance, repair]
---

# Datalab PDF Apparatus Repair

## Context

Datalab produced useful structured PDF output, but its reading order and inline apparatus markup were not reliable enough for direct corpus acceptance. The repair had to preserve all canonical passages, connect official footnote text to its origin anchor, and fail closed when evidence did not agree.

Raw source files, source paths, Datalab output, correction profiles, and detailed review artifacts remain outside Git. The maintainer separately approved exact inactive candidate snapshots for `candidates/`; that copy does not accept or activate either corpus.

## Observed Failure Modes

- Right-column body blocks could appear before a left-column chapter heading.
- Verse 1 had no printed verse number and required a chapter-summary boundary.
- A block could contain multiple numbered verses or a verse could cross blocks and pages.
- Footnote continuation blocks were indented. Sorting them by exact horizontal position moved continuations after later entries.
- Some apparatus blocks were labeled `PageFooter` or narrow bottom `Text`, not `Footnote`.
- Datalab omitted valid inline markers, emitted false markers from italic letters, and sometimes returned the wrong marker label.
- A verse could start on one page while a later marker appeared on the next page.
- Superscript glyphs could sit slightly outside the Datalab block box.
- New Testament footer tables could merge chapter and verse labels, shift continuation labels into the prior verse, or separate labels from their text cells.

## Repair Method

### Canonical structure

The parser reconstructs passages in visual column order and compares the result with a packaged text-free structure manifest. The repair supports the Book of Mormon manifest and the 27-book New Testament manifest. It fails if the extracted references do not equal the selected manifest.

### Footnote reading order

Footer blocks use three-column visual order. Blocks sort by column and vertical position, so indentation no longer changes semantic order. Tables are read column-first. `Footnote`, `PageFooter`, `Table`, and qualifying narrow bottom text blocks can supply apparatus content.

### Marker reconciliation

The parser first links an inline anchor to a footer entry by page, verse, and label. It permits a page-boundary fallback only when the verse source spans and available entry make the result unique. It can recover explicit and continuation labels from irregular table cells when the final label set is sequential. A narrow private correction profile records source-specific OCR defects that required direct PDF review. The parser applies that profile only when its stored PDF and Datalab JSON digests match the exact input bytes. The profile and its exact correction rules stay outside Git.

### PDF glyph verification

The verifier uses the dominant alphabetic font size as the body size. A valid superscript must:

- contain a lowercase label from `a` through `k`;
- use a font smaller than 80 percent of the dominant body font; and
- sit within eight PDF points of a body-text line in the same source block.

This rule permits raised superscripts near block boundaries without counting a marker from the next verse.

### Immutable output

The writer rejects a private root inside the repository. It normalizes the extraction and writes a mode-`0600` candidate and report under the configured private root. The report and repair digest bind the PDF, Datalab JSON, text-free structure manifest, parser recipe, optional correction profile, normalized corpus, and findings. A changed input, recipe, profile, or finding produces a new immutable repair directory. A separately approved copy may enter `candidates/` with its exact digest and lifecycle state. Writing or copying a candidate does not accept or activate it.

## Verified Results

### Book of Mormon

**HIGH confidence within the supplied PDF and Datalab evidence:**

- 6,604 nonempty canonical passages;
- 9,826 unique official footnote anchors with nonempty text;
- 4,972 passages with at least one footnote;
- sequential anchor sets for every passage with notes;
- zero unlinked inline anchors;
- zero unmatched parsed footer entries;
- 376 Datalab-omitted markers recovered;
- one false inline marker removed; and
- one duplicate parsed footer entry ignored.

### New Testament

**HIGH confidence within the supplied PDF and Datalab evidence:**

- 27 books, 260 chapters, and 7,957 nonempty canonical passages;
- 10,091 unique official footnote anchors with nonempty text;
- zero ambiguous verse-one boundaries;
- zero unlinked inline anchors;
- zero unmatched parsed footer entries;
- 66 unique sequential footer anchors recovered after Datalab omitted their body markers;
- nine false body markers and two false footer continuations removed through the reviewed source profile; and
- five malformed footer labels reassigned to their verified origin passages.

The source-independent repository gate now passes with 170 tests. Ruff formatting, Ruff checks, and mypy also pass.

## Why the Candidate Still Requires Review

The repair proves internal PDF-to-parser reconciliation. It does not provide an independent editorial comparison against a separate official structured source. On 2026-08-24 the maintainer vouched for the Book of Mormon's Church-public-PDF source and approved its exact candidate digest for the local beta; that candidate is now accepted and active in the private local runtime. The New Testament candidate remains inactive, unaccepted, and `review_required`.

The repaired notes contain footnote text, but official citation targets inside that text have not been converted into typed relationship edges. Edge parsing is separate future work.

## Reproduction

Use synthetic fixtures for routine development:

```bash
uv run pytest tests/unit/ingest/test_datalab.py -q
uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv run pytest
```

A private-source repair must use explicit local source paths and a configured private root outside the repository. Do not place those values in committed commands or logs.

Source-specific correction profiles are private review artifacts. Routine repository tests use synthetic PDFs, Marker JSON, and digest-bound synthetic profiles.

## Related Pages

- [Project Overview](../overview.md)
- [Corpus Fidelity and Acceptance](../concepts/corpus-fidelity-and-acceptance.md)
- [Decision Log](../decisions.md)

## Open Questions

- What exact grammar should convert footnote citation text into typed internal and external reference targets?
- Should a future independent EPUB comparison become a required acceptance check for this repaired PDF corpus?
