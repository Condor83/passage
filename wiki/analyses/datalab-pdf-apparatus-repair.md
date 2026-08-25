---
title: Datalab PDF Apparatus Repair
type: analysis
created: 2026-08-23
updated: 2026-08-25
sources:
  - src/passage/ingest/datalab.py
  - src/passage/ingest/validation.py
  - src/passage/db/validation.py
  - tests/unit/ingest/test_datalab.py
  - tests/unit/ingest/test_validation.py
  - tests/integration/test_candidate_cli.py
  - tests/integration/test_corpus_build.py
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
- The last canonical verse could absorb every later body block when the source continued with post-canon material and no explicit terminal boundary existed.
- Superscript glyphs could sit slightly outside the Datalab block box.
- New Testament footer tables could merge chapter and verse labels, shift continuation labels into the prior verse, or separate labels from their text cells.

## Repair Method

### Canonical structure

The parser reconstructs passages in visual column order and compares the result with a packaged text-free structure manifest. The repair supports the Book of Mormon manifest and the 27-book New Testament manifest. It fails if the extracted references do not equal the selected manifest.

Canonical identity equality alone does not prove terminal fidelity: once the final expected reference has started, unrelated later text can still be appended to it. The current checkout therefore permits a digest-bound private profile to declare the first excluded PDF page and the terminal canonical reference. The parser requires that reference to be the structure manifest's final record, requires the boundary to be encountered, fails if the boundary arrives before that record, and ignores later pages only after the assertion succeeds.

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

The writer rejects a private root inside the repository. It normalizes and validates the extraction before creating repair files, then writes a mode-`0600` candidate and report under the configured private root. Corpus validation rejects scripture passage text over 10,000 characters, more than 64 source spans, or a PDF provenance window over eight pages. The report and repair digest bind the PDF, Datalab JSON, text-free structure manifest, parser recipe, optional correction profile, normalized corpus, and findings. A changed input, recipe, profile, or finding produces a new immutable repair directory. A separately approved copy may enter `candidates/` with its exact digest and lifecycle state. Writing or copying a candidate does not accept or activate it.

## Historical Results and Current Quarantine

### Book of Mormon result reported before the terminal audit

The prior repair reported:

- 6,604 nonempty canonical passages;
- 9,826 unique official footnote anchors with nonempty text;
- 4,972 passages with at least one footnote;
- sequential anchor sets for every passage with notes;
- zero unlinked inline anchors;
- zero unmatched parsed footer entries;
- 376 Datalab-omitted markers recovered;
- one false inline marker removed; and
- one duplicate parsed footer entry ignored.

That result is not fidelity-valid. A later text-free audit found that `bofm/moro/10/34`, the final canonical record, contained 1,027,420 characters and 3,486 source spans across PDF pages 554-795. The parser had never recognized the end of the canonical work, so it appended post-canon material to the final verse. Base candidate SHA-256 `1dfd7b927e9fe5f4987a5bb5a3c8d1a0398eec6004cd01f45e86d50096a1e6b4`, technically selected local corpus `corpus-7ba9051125f848e1aed71c46`, and typed successor SHA-256 `5207e9c1c003f12798053c667a997e8e0697495f8f4a9cafb2e112ef3aee7fa5` are quarantined from evidence and evaluation. The control pointer may still technically select the old corpus, but editorial authority is withdrawn.

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

The New Testament status is unchanged by the Book of Mormon diagnosis. It remains inactive, unaccepted, and `review_required`.

## Implemented Safeguards, Not a Rebuilt Corpus

The current checkout implements the digest-bound terminal-page cutoff, writer-time corpus validation, and the 10,000-character, 64-span, and eight-page-window backstops. Published SQLite validation applies the same per-passage integrity rules before repository access. Focused regressions cover preservation of a legitimate final-verse continuation, exclusion of later pages, fail-closed boundary errors, rejection before repair files are created, rejection of a digest-consistent oversized candidate without control-state change, and rejection of a digest-consistent legacy artifact already recorded as accepted.

The full source-independent gate passes 321 tests plus formatting, lint, and type checking. This establishes current checkout behavior only. The exact approved PDF, Marker JSON, and original Datalab profile are absent on this host, so no repaired private candidate, rebound edge set, or new exact digest is claimed here.

## Why the Candidate Still Requires Review

The prior repair proved many internal PDF-to-parser reconciliation properties, but the missing terminal boundary shows why those properties did not establish whole-work fidelity. On 2026-08-25 the maintainer confirmed the defect, withdrew editorial authority from the affected Book of Mormon identities, and authorized repair and private rebuild.

`official-reference-v2` remains grammar-capability resolved, including typed whole-unit targets and approved digest-bound reference repairs. Its prior exact run inherited the corrupted base, so its corpus proof is quarantined. After the exact private inputs are restored, Passage must rebuild privately, rebind or rederive official edges, verify the result, and ask the maintainer to approve the new exact digest. Acceptance and activation are separate later decisions.

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

- What proportionate independent comparison should accompany the rebuilt Book of Mormon before a new exact-digest approval decision?
- Should a future independent EPUB comparison become a required acceptance check for this repaired PDF corpus?
